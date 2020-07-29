# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class pos_combo_item(models.Model):
    _name = "pos.combo.item"
    _rec_name = "product_id"
    _description = "Gestión de productos de Paquetes/Combo"

    required = fields.Boolean('Es requerido', default=0)
    product_id = fields.Many2one(
        'product.product',
        'Producto',
        required=True,
        domain=[('available_in_pos', '=', True)])
    product_combo_id = fields.Many2one(
        'product.template',
        'Combo',
        required=True,
        domain=[('available_in_pos', '=', True)])
    quantity = fields.Float(
        'Cantidad',
        required=1,
        default=1)
    price_extra = fields.Float(
        'Precio extra',
        help='Este precio se sumará al precio de venta del producto en el combo')
    default = fields.Boolean(
        'Seleccionado por default',
        default=1)
    tracking = fields.Boolean(
        'Rastreo de Lotes/Series',
        help='Permite al cajero establecer series/lotes a los productos del combo')
    uom_id = fields.Many2one(
        'uom.uom', 'Unidad de medida')

    @api.model
    def create(self, vals):
        if vals.get('quantity', 0) < 0:
            raise UserError('La cantidad no debe ser mejor a 0')
        return super(pos_combo_item, self).create(vals)

    def write(self, vals):
        if vals.get('quantity', 0) < 0:
            raise UserError('La cantidad no debe ser menor a 0')
        return super(pos_combo_item, self).write(vals)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id and self.product_id.uom_id:
            self.uom_id = self.product_id.uom_id
