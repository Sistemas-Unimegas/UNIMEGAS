# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class pos_sale_extra(models.Model):
    _name = "pos.sale.extra"
    _description = "Venta de artículos adicionales basados ​​en producto principal"

    product_tmpl_id = fields.Many2one('product.template', 'Producto Base', required=1,
                                      domain=[('available_in_pos', '=', True)])
    product_id = fields.Many2one('product.product', 'Producto extra', required=1,
                                 domain=[('available_in_pos', '=', True)])
    quantity = fields.Float('Cantidad predeterminada', default=1, required=1)
    list_price = fields.Float('Precio de Lista', required=1)

    @api.model
    @api.onchange('product_id')
    def onchange_product_id(self):
        self.list_price = self.product_id.list_price


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pos_combo_item_ids = fields.One2many('pos.combo.item', 'product_combo_id', string='Productos de Combo')
    is_combo = fields.Boolean(
        'Paquete de Combo / Paquete',
        help='Actívelo y vea la pestaña Combo / Paquete y agregue elementos para la opción de Combo'
    )
    is_combo_item = fields.Boolean(
        'Elemento de Combo dinámico',
        help='Permitir que este producto se convierta en elemento combinado de otro producto'
    )
    combo_limit = fields.Integer(
        'Límite de artículo de Combo',
        help='Los elementos combinados de límite pueden permitir agregar / combo')
    is_credit = fields.Boolean('Es Crédito', default=False)
    multi_category = fields.Boolean('Multi Categoría')
    pos_categ_ids = fields.Many2many(
        'pos.category',
        string='POS Multi Categoría')
    multi_uom = fields.Boolean('Multi Unidad')
    price_uom_ids = fields.One2many(
        'product.uom.price',
        'product_tmpl_id',
        string='Precio por unidad de venta')
    multi_variant = fields.Boolean('Producto Multi variante')
    pos_variant_ids = fields.One2many(
        'product.variant',
        'product_tmpl_id',
        string='Multi Variantes')
    cross_selling = fields.Boolean('Venta cruzada')
    cross_ids = fields.One2many(
        'product.cross',
        'product_tmpl_id',
        string='Artículos de venta cruzada')
    supplier_barcode = fields.Char(
        'Código de barras del proveedor', copy=False,
        help="Producto de código de barras del proveedor, puede ingresar aquí y escanear en POS")
    barcode_ids = fields.One2many(
        'product.barcode',
        'product_tmpl_id',
        string='Código de barras múltiple')
    pack_ids = fields.One2many(
        'product.quantity.pack',
        'product_tmpl_id',
        string='Paquete de cantidades')
    pos_sequence = fields.Integer('POS Secuencia')
    is_voucher = fields.Boolean('Es Voucher', default=0)
    sale_extra = fields.Boolean(string='Venta activa extra')
    sale_extra_item_ids = fields.One2many(
        'pos.sale.extra',
        'product_tmpl_id',
        'Venta de artículos extra')
    minimum_list_price = fields.Float('Precio de venta mínimo', default=0)
    sale_with_package = fields.Boolean('Venta con empaque')
    price_unit_each_qty = fields.Boolean('Precio de venta activo cada cantidad')
    product_price_quantity_ids = fields.One2many(
        'product.price.quantity',
        'product_tmpl_id',
        'Precio cada cantidad')
    qty_warning_out_stock = fields.Float('Cantidad - Advertencia fuera de stock', default=10)
    combo_price = fields.Float(
        'Precio del producto en Combo',
        help='Este precio reemplazará el precio público e incluirá una línea de venta en el POS'
    )
    combo_limit_ids = fields.One2many(
        'pos.combo.limit',
        'product_tmpl_id',
        'Artículos en Combo limitados por categoría'
    )
    name_second = fields.Char(
        'Segundo Nombre',
        help='Si necesita imprimir recibo POS en árabe, chino ... idioma\n'
             'Ingrese su idioma aquí, y vaya a Pos Segundo lenguaje activo')
    special_name = fields.Char('Nombre Especial')
    uom_ids = fields.Many2many('uom.uom', string='Unidades de la misma categoría', compute='_get_uoms_the_same_category')
    note_ids = fields.Many2many(
        'pos.note',
        'product_template_note_rel',
        'product_tmpl_id',
        'note_id',
        string='Notas fijas'
    )
    tag_ids = fields.Many2many(
        'pos.tag',
        'product_template_tag_rel',
        'product_tmpl_id',
        'tag_id',
        string='Etiquetas'
    )
    pos_branch_id = fields.Many2one('pos.branch', string='Sucursal')
    commission_rate = fields.Float(
        'Porcentaje de comision',
        default=50,
        help='Tasa de comisión (%) para vendedores'
    )
    cycle = fields.Integer(
        'Ciclo',
        help='Tiempos de ciclo totales que el cliente puede usar en Negocios Spa'
    )

    def add_barcode(self):
        for product in self:
            format_code = "%s%s%s" % ('777', product.id, datetime.now().strftime("%d%m%y%H%M"))
            barcode = self.env['barcode.nomenclature'].sanitize_ean(format_code)
            product.write({'barcode': barcode})
        return True

    @api.model
    def create(self, vals):
        if not vals.get('pos_branch_id'):
            vals.update({'pos_branch_id': self.env['pos.branch'].sudo().get_default_branch()})
        product_tmpl = super(ProductTemplate, self).create(vals)
        return product_tmpl

    @api.onchange('uom_id')
    def onchange_uom_id(self):
        if self.uom_id:
            uoms = self.env['uom.uom'].search([('category_id', '=', self.uom_id.category_id.id)])
            self.uom_ids = [(6, 0, [uom.id for uom in uoms])]

    def _get_uoms_the_same_category(self):
        for product in self:
            uoms = self.env['uom.uom'].search([('category_id', '=', product.uom_id.category_id.id)])
            product.uom_ids = [(6, 0, [uom.id for uom in uoms])]

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        for product_temp in self:
            products = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)])
            for product in products:
                if product.sale_ok and product.available_in_pos:
                    self.env['pos.cache.database'].insert_data('product.product', product.id)
                if not product.available_in_pos or not product.active:
                    self.env['pos.cache.database'].remove_record('product.product', product.id)
        return res

    def unlink(self):
        for product_temp in self:
            products = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)])
            for product in products:
                self.env['pos.cache.database'].remove_record('product.product', product.id)
        return super(ProductTemplate, self).unlink()


class product_product(models.Model):
    _inherit = 'product.product'

    def write(self, vals):
        res = super(product_product, self).write(vals)
        for product in self:
            if product.available_in_pos and product.active:
                self.env['pos.cache.database'].insert_data('product.product', product.id)
            if not product.available_in_pos or not product.active:
                self.env['pos.cache.database'].remove_record(self._inherit, product.id)
        return res

    @api.model
    def create(self, vals):
        product = super(product_product, self).create(vals)
        if product.sale_ok and product.available_in_pos:
            self.env['pos.cache.database'].insert_data(self._inherit, product.id)
        return product

    def unlink(self):
        for product in self:
            self.env['pos.cache.database'].remove_record(self._inherit, product.id)
        return super(product_product, self).unlink()

    def add_barcode(self):
        for product in self:
            format_code = "%s%s%s" % ('777', product.id, datetime.now().strftime("%d%m%y%H%M"))
            barcode = self.env['barcode.nomenclature'].sanitize_ean(format_code)
            product.write({'barcode': barcode})
        return True
