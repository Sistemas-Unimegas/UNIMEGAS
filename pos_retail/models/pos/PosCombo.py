# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosComboLimit(models.Model):
    _name = "pos.combo.limit"
    _description = "Límite de productos en Combo"

    product_tmpl_id = fields.Many2one(
        'product.template',
        'Producto',
        required=True
    )
    pos_categ_id = fields.Many2one(
        'pos.category',
        string='Categoría POS',
        required=True,
    )
    quantity_limited = fields.Integer(
        'Límite de Cantidad',
        default=10,
        required=True,
        help='Cantidad total que los artículos de esta categoría pueden agregar al Combo'
    )
    default_product_ids = fields.Many2many(
        'product.product',
        'pos_combo_limit_product_product_rel',
        'combo_limit_id',
        'product_id',
        string='Artículos default',
        help='Artículos default que se agregarán al combo, cuando el cajero agrega el combo a la orden de venta'
    )

class PosComboItem(models.Model):
    _name = "pos.combo.item"
    _rec_name = "product_id"
    _description = "Gestión de productos Paquete/Combo"

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
        'Rastreo de Lotes/Serie',
        help='Permite al cajero establecer la serie/lote de los productos del combo')
    uom_id = fields.Many2one(
        'uom.uom', 'Unidad de medida')

    @api.model
    def create(self, vals):
        if vals.get('quantity', 0) < 0:
            raise UserError('Cantidad no puede ser menor a 0')
        return super(PosComboItem, self).create(vals)

    def write(self, vals):
        if vals.get('quantity', 0) < 0:
            raise UserError('Cantidad no puede ser menor a 0')
        return super(PosComboItem, self).write(vals)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id and self.product_id.uom_id:
            self.uom_id = self.product_id.uom_id
