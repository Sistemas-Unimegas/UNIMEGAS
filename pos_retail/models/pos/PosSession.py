# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, registry
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID

import logging

_logger = logging.getLogger(__name__)


# TODO: workflow of pos session and account bank statement odoo 13
#       - pos session create, session will reading all payment_method_ids (payment methods) (1)
#       - from (1) they create statement_ids (account bank statement) and add it to pos session (2)
#       - from (2) when close session , they push to account brank statement with relation 1 to 1 (one-to-one). 1 account bank statement - 1 account bank statement line
#       - summary: 1 payment method - 1 account journal - 1 account bank statement - 1 account bank statement line

class PosSession(models.Model):
    _inherit = "pos.session"

    required_reinstall_cache = fields.Boolean('Reinstall Datas', default=0,
                                              help='If checked, when session start, all pos caches will remove and reinstall')
    mobile_responsive = fields.Boolean('Mobile Display')
    pos_branch_id = fields.Many2one('pos.branch', string='Branch')
    lock_state = fields.Selection([
        ('unlock', 'Un lock'),
        ('locked', 'Locked')
    ], default='unlock',
        string='Lock state',
        help='Unlock: when pos session start, pos not lock screen\n'
             'locked: when pos session start, pos auto lock screen')

    def close_session_and_validate(self):
        for session in self:
            session.action_pos_session_closing_control()
            session.action_pos_session_validate()
            session._validate_session()
        return True

    def register_license(self, license):
        self.env['ir.config_parameter'].sudo().set_param('license', license)
        return True

    def action_pos_session_closing_control(self):
        for session in self:
            orders = self.env['pos.order'].search([
                ('state', '=', 'draft'),
                ('session_id', '=', session.id),
                ('picking_id', '=', None)
            ])
            for order in orders:
                if order._is_pos_order_paid():
                    order.action_pos_order_paid()
                    self.env.cr.commit()
            self.env['pos.backup.orders'].search([
                ('config_id', '=', session.config_id.id)
            ]).unlink()
        res = super(PosSession, self).action_pos_session_closing_control()
        return res

    def _get_backup_session(self, order):
        # todo: we create new pos session or get pos session rescue, and add pos_session_id of draft order to this session
        # todo: for current session can close and rescue session use next session
        closed_session = order.session_id
        rescue_session = self.search([
            ('state', 'not in', ('closed', 'closing_control')),
            ('rescue', '=', True),
            ('config_id', '=', closed_session.config_id.id),
        ], limit=1)
        if rescue_session:
            return rescue_session.id
        new_session = self.create({
            'config_id': closed_session.config_id.id,
            'name': _('(BACKUP FOR %(session)s)') % {'session': closed_session.name},
            'rescue': True,
        })
        new_session.action_pos_session_open()
        return new_session.id

    def _check_if_no_draft_orders(self):
        orders_not_done = self.order_ids.filtered(
            lambda order: order.state not in ['cancel', 'paid', 'done', 'invoiced'])
        if len(orders_not_done) >= 1:
            for session in self:
                if session.rescue:
                    raise UserError(_('It not possible close session backup if have orders not full fill payment, \n '
                                      'Please register payment or cancel orders with reference in list:  %s ' % [order.pos_reference for order in orders_not_done]))
            _logger.warning('Total orders_not_done is %s' % len(orders_not_done))
            for order in orders_not_done:
                rescue_session_id = self._get_backup_session(order)
                order.write({'session_id': rescue_session_id})
                self.env.cr.commit()
        return super(PosSession, self)._check_if_no_draft_orders()

    def action_pos_session_validate(self):
        for session in self:
            orders = self.env['pos.order'].search([
                ('state', '=', 'draft'),
                ('session_id', '=', session.id),
                ('picking_id', '=', None)
            ])
            for order in orders:
                if order._is_pos_order_paid():
                    order.action_pos_order_paid()
                    self.env.cr.commit()
        return super(PosSession, self).action_pos_session_validate()

    def _create_account_move(self):
        core = super(PosSession, self)._create_account_move()
        if self.config_id.analytic_account_id:
            for statement in self.statement_ids:
                for move_line in statement.move_line_ids:
                    move_line.write({
                        'analytic_account_id': self.config_id.analytic_account_id.id
                    })
        return core

    def lock_session(self, vals):
        return self.sudo().write(vals)

    @api.model
    def create(self, vals):
        config = self.env['pos.config'].browse(vals.get('config_id'))
        vals.update({'mobile_responsive': config.mobile_responsive})
        if config.pos_branch_id:
            vals.update({'pos_branch_id': config.pos_branch_id.id})
        else:
            vals.update({'pos_branch_id': self.env['pos.branch'].sudo().get_default_branch()})
        if config.pos_branch_id and not self.env.user.pos_branch_id:
            raise UserError('[ %s ] have set Branch is [ %s ] but your account user not set Branch like that. \n'
                            'Please contact your admin system \n'
                            'And go to Setting/Users: choice user [ %s ] Tab Point of Sale and setting Branch' % (
                                config.name, config.pos_branch_id.name, self.env.user.login))
        return super(PosSession, self).create(vals)

    def switch_mobile_mode(self):
        return self.write({'mobile_responsive': True})

    def switch_full_screen(self):
        return self.write({'mobile_responsive': False})

    def update_required_reinstall_cache(self):
        return self.write({'required_reinstall_cache': False})

    def get_pos_session(self, session_id):
        if session_id:
            session = self.browse(int(session_id))
        if session:
            if session.user_id.has_group('point_of_sale.group_pos_manager'):
                admin = 1
            else:
                admin = 0
            pos_session = {"id": session.id,
                           "name": session.name,
                           "user_id": [session.user_id.id,
                                       session.user_id.name],
                           "cash_control": session.cash_control,
                           "state": session.state,
                           "stop_at": session.stop_at,
                           "config_id": [session.config_id.id,
                                         session.config_id.display_name],
                           "start_at": session.start_at,
                           "currency_id": [session.currency_id.id,
                                           session.currency_id.name],
                           "cash_register_balance_end_real": (
                               session.cash_register_balance_end_real),
                           "cash_register_total_entry_encoding": (
                               session.cash_register_total_entry_encoding),
                           "cash_register_difference": (
                               session.cash_register_difference),
                           "cash_register_balance_start": (
                               session.cash_register_balance_start),
                           "cash_register_balance_end": (
                               session.cash_register_balance_end),
                           "is_admin": (admin)
                           }
            return pos_session
        else:
            return

    def get_cashbox(self, session_id, balance):
        is_delete = True
        access_model = self.env['ir.model.access'].sudo().search(
            [('name', 'ilike', 'account.cashbox.line user')]
        )
        # Hide Delete icon in POS Closing Balance popup if Technical Settings/Show Full Accounting Features and
        # Delete Access options are not checked.
        if not self.user_has_groups('account.group_account_user') and not access_model.perm_unlink:
            is_delete = False
        session = self.browse(int(session_id))
        session.ensure_one()
        context = dict(session._context)
        balance_type = balance or 'end'
        context['bank_statement_id'] = session.cash_register_id.id
        context['balance'] = balance_type
        context['default_pos_id'] = session.config_id.id
        cashbox_id = None
        if balance_type == 'start':
            cashbox_id = session.cash_register_id.cashbox_start_id.id
        else:
            cashbox_id = session.cash_register_id.cashbox_end_id.id
        cashbox_line = []
        total = 0
        if cashbox_id:
            account_cashbox_line = self.env['account.cashbox.line']
            cashbox = account_cashbox_line.search([
                ('cashbox_id', '=', cashbox_id)
            ])
            if cashbox:
                for line in cashbox:
                    subtotal = line.number * line.coin_value
                    total += subtotal
                    cashbox_line.append({"id": line.id,
                                         "number": line.number,
                                         "coin_value": line.coin_value,
                                         "subtotal": subtotal,
                                         "total": total,
                                         "is_delete": is_delete
                                         })
            else:
                cashbox_line.append({"total": total,
                                     "is_delete": is_delete
                                     })
        else:
            cashbox_line.append({"total": total,
                                 "is_delete": is_delete
                                 })
        return cashbox_line

    def _validate_session(self):
        res = super(PosSession, self)._validate_session()
        if self.move_id and self.pos_branch_id:
            self.env.cr.execute("UPDATE account_move SET pos_branch_id=%s WHERE id=%s" % (
                self.pos_branch_id.id, self.move_id.id))
            self.env.cr.execute("UPDATE account_move_line SET pos_branch_id=%s WHERE move_id=%s" % (
                self.pos_branch_id.id, self.move_id.id))
        vals = {}
        if not self.start_at:
            vals['start_at'] = fields.Datetime.now()
        if not self.stop_at:
            vals['stop_at'] = fields.Datetime.now()
        if vals:
            self.write(vals)
        return res


class AccountBankStmtCashWizard(models.Model):
    """
    Account Bank Statement popup that allows entering cash details.
    """
    _inherit = 'account.bank.statement.cashbox'
    _description = 'Account Bank Statement Cashbox Details'

    description = fields.Char("Description")

    def validate_from_ui(self, session_id, balance, values):
        """ Create , Edit , Delete of Closing Balance Grid

        :param session_id: POS Open Session id .
        :param values: Array records to save

        :return: Array of cashbox line.
        """
        session = self.env['pos.session'].browse(int(session_id))
        bnk_stmt = session.cash_register_id
        if (balance == 'start'):
            self = session.cash_register_id.cashbox_start_id
        else:
            self = session.cash_register_id.cashbox_end_id
        if not self:
            self = self.create({'description': "Created from POS"})
            if self and (balance == 'end'):
                account_bank_statement = session.cash_register_id
                account_bank_statement.write({'cashbox_end_id': self.id})
        for val in values:
            id = val['id']
            number = val.get('number', 0)
            coin_value = val.get('coin_value', 0)
            cashbox_line = self.env['account.cashbox.line']
            if id and number and coin_value:  # Add new Row
                cashbox_line = cashbox_line.browse(id)
                cashbox_line.write({'number': number,
                                    'coin_value': coin_value
                                    })
            elif not id and number and coin_value:  # Add new Row
                cashbox_line.create({'number': number,
                                     'coin_value': coin_value,
                                     'cashbox_id': self.id
                                     })
            elif id and not (number and coin_value):  # Delete Exist Row
                cashbox_line = cashbox_line.browse(id)
                cashbox_line.unlink()

        total = 0.0
        for lines in self.cashbox_lines_ids:
            total += lines.subtotal
        if (balance == 'start'):
            # starting balance
            bnk_stmt.write({'balance_start': total,
                            'cashbox_start_id': self.id})
        else:
            # closing balance
            bnk_stmt.write({'balance_end_real': total,
                            'cashbox_end_id': self.id})
        if (balance == 'end'):
            if bnk_stmt.difference < 0:
                if self.env.user.id == SUPERUSER_ID:
                    return (_('you have to send more %s %s') %
                            (bnk_stmt.currency_id.symbol,
                             abs(bnk_stmt.difference)))
                else:
                    return (_('you have to send more amount'))
            elif bnk_stmt.difference > 0:
                if self.env.user.id == SUPERUSER_ID:
                    return (_('you may be missed some bills equal to %s %s')
                            % (bnk_stmt.currency_id.symbol,
                               abs(bnk_stmt.difference)))
                else:
                    return (_('you may be missed some bills'))
            else:
                return (_('you done a Great Job'))
        else:
            return

    def validate(self):
        """
        TODO: Raise popup for set closing balance in session POS
        """
        res = super(AccountBankStmtCashWizard, self).validate()
        bnk_stmt_id = (self.env.context.get('bank_statement_id', False) or
                       self.env.context.get('active_id', False))
        bnk_stmt = self.env['account.bank.statement'].browse(bnk_stmt_id)
        if bnk_stmt.pos_session_id.state == 'closing_control':
            if bnk_stmt.difference < 0:
                raise UserError(_('you have to send more %s %s') % (
                    bnk_stmt.currency_id.symbol,
                    abs(bnk_stmt.difference)))
            elif bnk_stmt.difference > 0:
                raise UserError(_('you may be missed some '
                                  'bills equal to %s %s') % (
                                    bnk_stmt.currency_id.symbol,
                                    abs(bnk_stmt.difference)))
            else:
                return res
        else:
            return res
