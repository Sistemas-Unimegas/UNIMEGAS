# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductBarcode(models.Model):
    _name = 'product.barcode'
    _rec_name = 'barcode'
    _description = "Producto multi Código de Barras"

    product_tmpl_id = fields.Many2one('product.template', 'Plantilla del Producto', required=1)
    product_id = fields.Many2one('product.product', compute='_get_product_id', string='Producto')
    quantity = fields.Float('Cantidad', required=1)
    list_price = fields.Float(
        'Precio de Lista',
        help='Si el cajero escanea este código de barras, este precio se establece automáticamente en línea',
        required=1)
    uom_id = fields.Many2one('uom.uom', string='Unidad de Medida', required=1)  # v12 only
    barcode = fields.Char('Código de Barras', required=1)

    def _get_product_id(self):
        for barcode in self:
            products = self.env['product.product'].search([
                ('product_tmpl_id', '=', barcode.product_tmpl_id.id)
            ])
            if products:
                barcode.product_id = products[0].id
            else:
                barcode.product_id = None