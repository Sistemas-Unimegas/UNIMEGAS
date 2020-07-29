# -*- coding: utf-8 -*-
from odoo import api, fields, models

class pos_discount(models.Model):

    _name = "pos.global.discount"
    _description = "Gestión de descuento global"

    name = fields.Char('Nombre', required=1)
    amount = fields.Float('Importe de descuento', required=1)
    product_id = fields.Many2one(
        'product.product',
        'Descuento global',
        domain=[
            ('sale_ok', '=', True),
            ('available_in_pos', '=', True)
        ],
        required=1)
    reason = fields.Char('Razón', required=1)
    type = fields.Selection([
        ('percent', '%'),
        ('fixed', 'Cantidad fija')
    ],
        string='Tipo',
        default='percent',
        required=1
    )
    branch_ids = fields.Many2many(
        'pos.branch',
        'pos_global_discount_branch_rel',
        'discount_id',
        'branch_id',
        string='Sucursal'
    )

    @api.model
    def default_get(self, default_fields):
        res = super(pos_discount, self).default_get(default_fields)
        products = self.env['product.product'].search([('name', '=', 'Discount')])
        if products:
            res.update({'product_id': products[0].id})
        return res
