# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class res_partner_type(models.Model):
    _name = "res.partner.type"
    _description = "Tipo de socio, filtra por importe total comprado en tus tiendas"

    name = fields.Char('Nombre', required=1)
    from_amount_total_orders = fields.Float('Del monto total', help='Mínimo de la cantidad total comprada en su tienda')
    to_amount_total_orders = fields.Float('A la cantidad total', help='Máximo de la cantidad total comprada en su tienda')

    def get_type_from_total_amount(self, amount):
        types = self.search([])
        type_will_add = None
        for type in types:
            if amount >= type.from_amount_total_orders and amount <= type.to_amount_total_orders:
                type_will_add = type.id
        return type_will_add


class res_partner(models.Model):
    _inherit = "res.partner"

    wallet = fields.Float(
        digits=(16, 4),
        compute='_compute_wallet',
        string='Monto de la tarjeta',
        help='Esta cantidad de billetera del cliente, guarda todo el cambio de dinero cuando se paga el pedido en pos')
    credit = fields.Float(
        digits=(16, 4),
        compute='_compute_debit_credit_balance',
        string='Crédito',
        help='El monto de crédito que este cliente puede usar')
    debit = fields.Float(
        digits=(16, 4),
        compute='_compute_debit_credit_balance',
        string='Débito',
        help='Importe de débito de este cliente')
    balance = fields.Float(
        digits=(16, 4),
        compute='_compute_debit_credit_balance',
        string='Balance',
        help='Cantidad de saldo que el cliente puede usar pagado en POS')
    limit_debit = fields.Float(
        'Límite de débito',
        help='Cantidad de crédito límite que se puede agregar a este cliente')
    credit_history_ids = fields.One2many(
        'res.partner.credit',
        'partner_id',
        'Historial de crédito')
    pos_loyalty_point_import = fields.Float(
        'Importación de puntos de lealtad',
        default=0,
        help='El sistema de administración puede importar puntos para este cliente')
    pos_loyalty_point = fields.Float(
        digits=(16, 4),
        compute="_get_point",
        string='Puntos de lealtad',
        help='El punto total del cliente puede usar el programa de recompensas del sistema pos')
    pos_loyalty_type = fields.Many2one(
        'pos.loyalty.category',
        'Tipo de lealtad',
        help='Tipo de cliente de programa de lealtad')
    pos_loyalty_point_ids = fields.One2many(
        'pos.loyalty.point',
        'partner_id',
        'Historial de puntos')
    discount_id = fields.Many2one(
        'pos.global.discount',
        'POS descuento',
        help='Descuento (%) aplicado automáticamente para este cliente')
    birthday_date = fields.Date('Cumpleaños')
    group_ids = fields.Many2many(
        'res.partner.group',
        'res_partner_group_rel',
        'partner_id',
        'group_id',
        string='Nombre de grupos')
    pos_order_ids = fields.One2many(
        'pos.order',
        'partner_id',
        'POS Orden')
    pos_total_amount = fields.Float(
        'POS monto total',
        help='Cantidad total que el cliente compró en su tienda',
        readonly=1)
    pos_partner_type_id = fields.Many2one(
        'res.partner.type',
        string='POS tipo de Cliente',
        readonly=1)
    pos_branch_id = fields.Many2one(
        'pos.branch',
        'Sucursal')
    special_name = fields.Char('Nombre especial')

    def update_branch_to_partner(self, vals):
        for partner in self:
            if not partner.pos_branch_id:
                partner.write(vals)
        return True

    def add_barcode(self):
        barcode_rules = self.env['barcode.rule'].sudo().search([
            ('type', '=', 'client'),
            ('pattern', '!=', '.*'),
        ])
        if barcode_rules:
            for partner in self:
                format_code = "%s%s%s" % (barcode_rules[0].pattern, partner.id, datetime.now().strftime("%d%m%y%H%M"))
                barcode = self.env['barcode.nomenclature'].sanitize_ean(format_code)
                partner.write({'barcode': barcode})
        return True

    @api.model
    def create_from_ui(self, partner):
        if partner.get('birthday_date', None):
            birthday_date = datetime.strptime(partner.get('birthday_date'), "%d-%m-%Y")
            partner.update({'birthday_date': birthday_date})
        if partner.get('property_product_pricelist', False):
            partner['property_product_pricelist'] = int(partner['property_product_pricelist'])
        for key, value in partner.items():
            if value == "false":
                partner[key] = False
            if value == "true":
                partner[key] = True
        return super(res_partner, self).create_from_ui(partner)

    def _get_point(self):
        for partner in self:
            partner.pos_loyalty_point = partner.pos_loyalty_point_import
            for loyalty_point in partner.pos_loyalty_point_ids:
                if loyalty_point.type == 'redeem':
                    partner.pos_loyalty_point -= loyalty_point.point
                else:
                    partner.pos_loyalty_point += loyalty_point.point

    def _compute_debit_credit_balance(self):
        for partner in self:
            partner.credit = 0
            partner.debit = 0
            partner.balance = 0
            for credit in partner.credit_history_ids:
                if credit.type == 'plus':
                    partner.credit += credit.amount
                if credit.type == 'redeem':
                    partner.debit += credit.amount
            partner.balance = partner.credit + partner.limit_debit - partner.debit
        return True

    def _compute_wallet(self):
        for partner in self:
            partner.wallet = 0
            self.env.cr.execute("""
            SELECT sum(pp.amount)
            FROM 
                pos_payment AS pp,
                pos_payment_method AS ppm,
                pos_order AS po,
                res_partner AS rp,
                account_journal AS aj
            WHERE
                rp.id=%s
                AND rp.id=po.partner_id
                AND pp.pos_order_id=po.id
                AND aj.id=ppm.cash_journal_id
                AND ppm.id=pp.payment_method_id
                AND aj.pos_method_type = 'wallet'""" % partner.id)
            plus_wallet_datas = self.env.cr.fetchall()
            if len(plus_wallet_datas) == 1 and plus_wallet_datas[0] and plus_wallet_datas[0][0]:
                partner.wallet = - (plus_wallet_datas[0][0])

    @api.model
    def create(self, vals):
        if not vals.get('pos_branch_id'):
            vals.update({'pos_branch_id': self.env['pos.branch'].sudo().get_default_branch()})
        partner = super(res_partner, self).create(vals)
        if partner.birthday_date and (partner.birthday_date >= fields.Date.context_today(self)):
            raise UserError('La fecha de nacimiento no podría ser mayor que hoy')
        self.env['pos.cache.database'].insert_data(self._inherit, partner.id)
        return partner

    def write(self, vals):
        res = super(res_partner, self).write(vals)
        for partner in self:
            if partner and partner.id != None and partner.active:
                self.env['pos.cache.database'].insert_data(self._inherit, partner.id)
            if partner.active == False:
                self.env['pos.cache.database'].remove_record(self._inherit, partner.id)
            if partner.birthday_date and (partner.birthday_date >= fields.Date.context_today(self)):
                raise UserError('La fecha de nacimiento no podría ser mayor que la de hoy')
        return res

    def unlink(self):
        for record in self:
            self.env['pos.cache.database'].remove_record(self._inherit, record.id)
        return super(res_partner, self).unlink()
