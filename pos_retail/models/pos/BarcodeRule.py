# -*- coding: utf-8 -*-
from odoo import api, models, fields

class barcode_rule(models.Model):

    _inherit = "barcode.rule"

    type = fields.Selection(selection_add=[
        ('order', 'Orden de devolución'),
        ('return_products', 'Productos devueltos'),
        ('voucher', 'Voucher'),
        ('login_security', 'inicio de sesión seguro'),
        ('fast_order_number', 'Número de pedido rápido'),
    ])

