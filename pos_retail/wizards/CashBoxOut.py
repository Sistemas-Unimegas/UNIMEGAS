from odoo.exceptions import UserError
from odoo import api, fields, models, _

from odoo.addons.point_of_sale.wizard.pos_box import PosBox


class CashBoxOut(PosBox):
    _inherit = 'cash.box.out'

    product_id = fields.Many2one('product.product', string='Razón')
    name = fields.Char('Descripción', required=1)

    @api.model
    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name

    def _calculate_values_for_statement_line(self, record):
        values = super(CashBoxOut, self)._calculate_values_for_statement_line(record)
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', [])
        if active_model == 'pos.session' and active_ids:
            session = self.env[active_model].browse(active_ids)[0]
            if not session.cash_journal_id:
                raise UserError(_("No hay caja registradora para esta sesión de PoS"))
            if session.state == 'closed':
                raise UserError(_("No permitir la entrada / salida de dinero cuando se cierra la sesión"))
            if self.product_id:
                product = self.product_id
                account_id = None
                if self.amount >= 0:
                    account_id = product.property_account_income_id.id or \
                                 product.categ_id.property_account_income_categ_id.id
                    if not account_id:
                        raise UserError(_(
                            "Tiene que definir una cuenta de ingresos en el producto"
                            " relacionado %s") % (product.name))
                else:
                    account_id = product.property_account_expense_id.id or \
                                 product.categ_id.property_account_expense_categ_id.id
                    if not account_id:
                        raise UserError(_(
                            "Tiene que definir una cuenta de gastos en el producto"
                            " relacionado %s") % (product.name))
                values['account_id'] = account_id
            values['ref'] = session.name
            values['journal_id'] = session.cash_journal_id.id
        return values

    def cash_input_from_pos(self, values):
        active_model = 'pos.session'
        active_ids = values['session_id']
        reason = values['reason']
        amount = values['amount']
        context = {'active_model': active_model, 'active_ids': active_ids, 'active_id': values['session_id']}
        if reason and float(amount):
            self = self.create({
                'name': reason,
                'amount': amount,
            })
            if values.get('product_id'):
                values['product_id'] = values['product_id']
            bank_statements = [session.cash_register_id for session in
                               self.env[active_model].browse(active_ids)
                               if session.cash_register_id]
            if not bank_statements:
                return ("No hay caja registradora para esta sesión de PoS")
            self.with_context(context)._run(bank_statements)
            return ("Registro Efectivo con éxito Monto %s" % amount)
        else:
            return ("Motivo y cantidad son campos obligatorios ")
