# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class account_journal(models.Model):
    _inherit = "account.journal"

    pos_method_type = fields.Selection([
        ('default', 'Default'),
        ('rounding', 'Redondeo'),
        ('wallet', 'Billetera'),
        ('voucher', 'Voucher'),
        ('credit', 'Credito/Debito'),
        ('return', 'Orden de devolución')
    ], default='default', string='Método POS', required=1)
    decimal_rounding = fields.Integer(
        'POS redondeo decimal',
        default=1,
        help='Ejemplo: \n'
             'El monto pagado es 1.94, redondeo de 1, El monto a pagar será 1.9 \n'
             'El monto pagado es 1.94, redondeo de 0, El monto a pagar será 2')
