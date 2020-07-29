# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosPromotion(models.Model):
    _name = "pos.promotion"
    _description = "Gestión de promociones en el POS"
    _order = "type"

    sequence = fields.Integer(help="Da la promoción de secuencia cuando se muestra una lista de promociones activas")
    name = fields.Char('Nombre', required=1)
    active = fields.Boolean('Activo', default=1)
    start_date = fields.Datetime(
        'Fecha de activación',
        default=fields.Datetime.now(),
        required=1
    )
    end_date = fields.Datetime('Fecha de término', required=1)
    type = fields.Selection([
        ('1_discount_total_order', '1. Descuento de cada cantidad de pedido total'),
        ('2_discount_category', '2. Descuente cada categoría POS'),
        ('3_discount_by_quantity_of_product', '3. Descuento de cada cantidad de producto'),
        ('4_pack_discount', '4. Compre el paquete completo o una parte del paquete. Artículos de descuento'),
        ('5_pack_free_gift', '5. Compre el paquete completo o una parte del paquete. Artículos gratis'),
        ('6_price_filter_quantity', '6. Venta de todos los productos'),
        ('7_special_category', '7. Cada categoría cada descuento'),
        ('8_discount_lowest_price', '8. Descuento precio más bajo'),
        ('9_multi_buy', '9. Producto múltiple - Precio múltiple'),
        ('10_buy_x_get_another_free', '10. Compre 10A obtenga 1A, Compre 15A obtenga 1A, Compre 20A obtenga 2A'),
        ('11_first_order', '11. Descuento % primera orden'),
        ('12_buy_total_items_free_items', '12. Compre artículos totales gratis algunos artículos')
    ], 'Type',
        default='1_discount_total_order',
        equired=1,
        help=
        '1:  Importe total del pedido> = 100 EUR de descuento 10%,> = 200 EUR de descuento 20% ... \n'
        '2:  Descuento de bebida 10%, descuento de comida 20% ... \n'
        '3:  Compre 3A descuento 10%, Compre 6A descuento 20%, Compre 10A descuento 35% ....\n'
        '4:  Compre 10A + 10B de descuento X, Y, Z .. O Compre 10A o 10B de descuento X e Y y Z\n'
        '5:  Compre 10A + 10B gratis X, Y, Z O Compre 10A o 10B gratis X e Y y Z \n'
        '6:  Compre más pequeño que 10A precio 10 EUR, compre más grande que 20A precio 15 EUR ....\n'
        '7:  Descuento o regalo gratis cuando el cliente compra el producto de la categoría seleccionada \n'
        '8:  Establecer descuento en el precio más bajo del producto de la lista de productos que el cliente compra\n'
        '9:  Permitir establecer producto múltiple con cantidad y precio múltiple\n'
        '10: Las cantidades mínimas establecidas son 10, Compre 10A obtenga 1A, Compre 15A obtenga 1A, Compre 20A obtenga 2A\n'
        '11. Descuento primer pedido del cliente \n'
        '12. Si el total de artículos en el carrito es mayor o igual a X (cantidades) se liberarán algunos artículos. Las cantidades mínimas establecidas de ejemplo son 10, liberarán 1A + 2B, si las cantidades son menores o iguales a 20 libres 2A + 4B')
    method = fields.Selection([
        ('only_one', 'OR'),
        ('all', 'AND')
    ],
        default='only_one',
        string='Condición Or / And',
        help='- Solo uno (or) : Compre 10A o 10B gratis 1X \n'
             '- Todos    (and): Compre 10A y 10B gratis 1X')
    discount_first_order = fields.Float('Discount First Order %')
    product_id = fields.Many2one(
        'product.product',
        'Product Service',
        domain=[('available_in_pos', '=', True)])
    discount_order_ids = fields.One2many(
        'pos.promotion.discount.order',
        'promotion_id',
        'Discounts')
    discount_category_ids = fields.One2many(
        'pos.promotion.discount.category',
        'promotion_id',
        'Categories Discounts')
    discount_quantity_ids = fields.One2many(
        'pos.promotion.discount.quantity',
        'promotion_id',
        'Quantities Discounts')
    gift_condition_ids = fields.One2many(
        'pos.promotion.gift.condition',
        'promotion_id',
        'Gifts condition')
    gift_free_ids = fields.One2many(
        'pos.promotion.gift.free',
        'promotion_id',
        'Gifts apply')
    discount_condition_ids = fields.One2many(
        'pos.promotion.discount.condition',
        'promotion_id',
        'Discounts condition')
    discount_apply_ids = fields.One2many(
        'pos.promotion.discount.apply',
        'promotion_id',
        'Discounts Apply')
    price_ids = fields.One2many(
        'pos.promotion.price',
        'promotion_id',
        'Prices')
    special_category_ids = fields.One2many(
        'pos.promotion.special.category',
        'promotion_id',
        'Special Category')
    discount_lowest_price = fields.Float(
        'Discount (%)',
        help='Discount n (%) of product lowest price of order lines')
    multi_buy_ids = fields.One2many(
        'pos.promotion.multi.buy',
        'promotion_id',
        'Multi Buy')
    product_ids = fields.Many2many(
        'product.product',
        'promotion_product_rel',
        'promotion_id',
        'product_id',
        string='Products group',
        domain=[('available_in_pos', '=', True)]
    )
    minimum_items = fields.Integer(
        'Total Qty >=',
        help='Minimum Items have in Cart for apply Promotion'
    )
    special_customer_ids = fields.Many2many(
        'res.partner',
        'promotion_partner_rel',
        'promotion_id',
        'partner_id',
        string='Special customer',
        help='Only customers added will apply promotion'
    )
    promotion_birthday = fields.Boolean('Promotion Birthday Customers')
    promotion_birthday_type = fields.Selection([
        ('day', 'Birthday same Day'),
        ('week', 'Birthday in Week'),
        ('month', 'Birthday in Month')
    ],
        striing='Time apply',
        default='week'
    )
    promotion_group = fields.Boolean('Promotion Groups')
    promotion_group_ids = fields.Many2many(
        'res.partner.group',
        'pos_promotion_partner_group_rel',
        'promotion_id',
        'group_id',
        string='Customer Groups')
    state = fields.Selection([
        ('active', 'Active'),
        ('disable', 'Disable')
    ], string='State', default='active')
    pos_branch_ids = fields.Many2many(
        'pos.branch',
        'promotion_pos_branch_rel',
        'promotion_id',
        'branch_id',
        string='Branches Applied')
    special_days = fields.Boolean('Special Days')
    monday = fields.Boolean('Monday')
    tuesday = fields.Boolean('Tuesday')
    wednesday = fields.Boolean('Wednesday')
    thursday = fields.Boolean('Thursday')
    friday = fields.Boolean('Friday')
    saturday = fields.Boolean('Saturday')
    sunday = fields.Boolean('Sunday')

    special_times = fields.Boolean('Special Times')
    from_time = fields.Float('From Time')
    to_time = fields.Float('To Time')

    def sync_promotion_all_pos_online(self):
        sessions = self.env['pos.session'].sudo().search([
            ('state', '=', 'opened')
        ])
        for session in sessions:
            self.env['bus.bus'].sendmany(
                [[(self.env.cr.dbname, 'pos.sync.promotions', session.user_id.id), {}]])
        return True

    @api.model
    def default_get(self, fields):
        res = super(PosPromotion, self).default_get(fields)
        products = self.env['product.product'].search([('name', '=', 'Promotion service')])
        if products:
            res.update({'product_id': products[0].id})
        return res

    @api.model
    def create(self, vals):
        promotion = super(PosPromotion, self).create(vals)
        if promotion and promotion.product_id and not promotion.product_id.available_in_pos:
            raise UserError('Product service not available in POS. \n'
                            'Please go to product and check to checkbox available in pos / save')
        return promotion

    def write(self, vals):
        res = super(PosPromotion, self).write(vals)
        for promotion in self:
            if promotion and promotion.product_id and not promotion.product_id.available_in_pos:
                raise UserError('Product service not available in POS. \n'
                                'Please go to product and check to checkbox available in pos / save')
        return res

class PosPromotionDiscountOrder(models.Model):
    _name = "pos.promotion.discount.order"
    _order = "minimum_amount"
    _description = "Promotion each total order"

    minimum_amount = fields.Float('Order Amount >=', required=1)
    discount = fields.Float('Discount %', required=1)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion', required=1, ondelete='cascade')


class PosPromotionDiscountCategory(models.Model):
    _name = "pos.promotion.discount.category"
    _order = "category_id, discount"
    _description = "Promotion each product categories"

    category_id = fields.Many2one('pos.category', 'POS Category', required=1)
    discount = fields.Float('Discount %', required=1)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion', required=1, ondelete='cascade')

    _sql_constraints = [
        ('category_id_uniq', 'unique(category_id)', 'one category only one rule!'),
    ]


class PosPromotionDiscountQuantity(models.Model):
    _name = "pos.promotion.discount.quantity"
    _order = "product_id"
    _description = "Promotion discount each product quantities"

    product_id = fields.Many2one('product.product', 'Product', domain=[('available_in_pos', '=', True)], required=1)
    quantity = fields.Float('Qty >=', required=1)
    discount = fields.Float('Discount %', required=1)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion', required=1, ondelete='cascade')

    @api.model
    def create(self, vals):
        record = super(PosPromotionDiscountQuantity, self).create(vals)
        if record and record.product_id and not record.product_id.available_in_pos:
            raise UserError('Product service not available in POS. \n'
                            'Please go to product and check to checkbox available in pos / save')
        return record

    def write(self, vals):
        res = super(PosPromotionDiscountQuantity, self).write(vals)
        for record in self:
            if record and record.product_id and not record.product_id.available_in_pos:
                raise UserError('Product service not available in POS. \n'
                                'Please go to product and check to checkbox available in pos / save')
        return res


class PosPromotionGiftCondition(models.Model):
    _name = "pos.promotion.gift.condition"
    _order = "product_id, minimum_quantity"
    _description = "Promotion gift condition"

    product_id = fields.Many2one(
        'product.product',
        domain=[('available_in_pos', '=', True)],
        string='Product',
        required=1)
    minimum_quantity = fields.Float('Qty >=', required=1, default=1.0)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion', required=1, ondelete='cascade')

    @api.model
    def create(self, vals):
        record = super(PosPromotionGiftCondition, self).create(vals)
        if record and record.product_id and not record.product_id.available_in_pos:
            raise UserError('Product service not available in POS. \n'
                            'Please go to product and check to checkbox available in pos / save')
        return record

    def write(self, vals):
        res = super(PosPromotionGiftCondition, self).write(vals)
        for record in self:
            if record and record.product_id and not record.product_id.available_in_pos:
                raise UserError('Product service not available in POS. \n'
                                'Please go to product and check to checkbox available in pos / save')
        return res


class PosPromotionGiftFree(models.Model):
    _name = "pos.promotion.gift.free"
    _order = "product_id"
    _description = "Promotion give gift to customer"

    product_id = fields.Many2one(
        'product.product',
        domain=[('available_in_pos', '=', True)],
        string='Product gift',
        required=1)
    quantity_free = fields.Float('Qty Free', required=1, default=1.0)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion', required=1, ondelete='cascade')
    type = fields.Selection([
        ('only_one', 'Only free quantity the same with quantity free set'),
        ('multi', 'Multi free, example: buy 3 free 1, buy 6 free 2'),
    ], default='only_one', string='Type Apply', required=1)

    @api.model
    def create(self, vals):
        record = super(PosPromotionGiftFree, self).create(vals)
        if record and record.product_id and not record.product_id.available_in_pos:
            raise UserError('Product service not available in POS. \n'
                            'Please go to product and check to checkbox available in pos / save')
        return record

    def write(self, vals):
        res = super(PosPromotionGiftFree, self).write(vals)
        for record in self:
            if record and record.product_id and not record.product_id.available_in_pos:
                raise UserError('Product service not available in POS. \n'
                                'Please go to product and check to checkbox available in pos / save')
        return res


class PosPromotionDiscountCondition(models.Model):
    _name = "pos.promotion.discount.condition"
    _order = "product_id, minimum_quantity"
    _description = "Promotion discount condition"

    product_id = fields.Many2one(
        'product.product',
        domain=[('available_in_pos', '=', True)],
        string='Product',
        required=1)
    minimum_quantity = fields.Float('Qty >=', required=1, default=1.0)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion', required=1, ondelete='cascade')

    @api.model
    def create(self, vals):
        record = super(PosPromotionDiscountCondition, self).create(vals)
        if record and record.product_id and not record.product_id.available_in_pos:
            raise UserError('Product service not available in POS. \n'
                            'Please go to product and check to checkbox available in pos / save')
        return record

    def write(self, vals):
        res = super(PosPromotionDiscountCondition, self).write(vals)
        for record in self:
            if record and record.product_id and not record.product_id.available_in_pos:
                raise UserError('Product service not available in POS. \n'
                                'Please go to product and check to checkbox available in pos / save')
        return res


class PosPromotionDiscountApply(models.Model):
    _name = "pos.promotion.discount.apply"
    _order = "product_id"
    _description = "Promotion discount apply"

    product_id = fields.Many2one(
        'product.product',
        domain=[('available_in_pos', '=', True)],
        string='Product',
        required=1)
    type = fields.Selection([
        ('one', 'Discount only one quantity'),
        ('all', 'Discount all quantity'),
    ], string='Type', default='one')
    discount = fields.Float('Discount %', required=1, default=1.0)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion', required=1, ondelete='cascade')

    @api.model
    def create(self, vals):
        record = super(PosPromotionDiscountApply, self).create(vals)
        if record and record.product_id and not record.product_id.available_in_pos:
            raise UserError('Product service not available in POS. \n'
                            'Please go to product and check to checkbox available in pos / save')
        return record

    def write(self, vals):
        res = super(PosPromotionDiscountApply, self).write(vals)
        for record in self:
            if record and record.product_id and not record.product_id.available_in_pos:
                raise UserError('Product service not available in POS. \n'
                                'Please go to product and check to checkbox available in pos / save')
        return res


class PosPromotionPrice(models.Model):
    _name = "pos.promotion.price"
    _order = "product_id, minimum_quantity"
    _description = "Promotion sale off"

    product_id = fields.Many2one('product.product', domain=[('available_in_pos', '=', True)], string='Product',
                                 required=1)
    minimum_quantity = fields.Float('Qty >=', required=1, default=1)
    price_down = fields.Float('Price Discount', required=1)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion', required=1, ondelete='cascade')

    @api.model
    def create(self, vals):
        product = self.env['product.product'].browse(vals['product_id'])
        if vals['price_down'] > product.lst_price:
            raise UserError('Price down could not bigger than product price %s' % product.lst_price)
        if not product.available_in_pos:
            raise UserError('Product service not available in POS. \n'
                            'Please go to product and check to checkbox available in pos / save')
        return super(PosPromotionPrice, self).create(vals)

    def write(self, vals):
        for record in self:
            if vals.get('price_down') and (vals.get('price_down') > record.product_id.lst_price):
                raise UserError('Price down could not bigger than product price %s' % record.product_id.lst_price)
            if not record.product_id.available_in_pos:
                raise UserError('Product service not available in POS. \n'
                                'Please go to product and check to checkbox available in pos / save')
        return super(PosPromotionPrice, self).write(vals)


class PosPromotionSpecialCategory(models.Model):
    _name = "pos.promotion.special.category"
    _order = "type"
    _description = "Promotion for special categories"

    category_id = fields.Many2one('pos.category', 'POS Category', required=1)
    type = fields.Selection([
        ('discount', 'Discount'),
        ('free', 'Free gift')
    ], string='Type', required=1, default='discount')
    count = fields.Integer('Count', help='How many product the same category will apply')
    discount = fields.Float('Discount %', required=1)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion', required=1, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product', domain=[('available_in_pos', '=', True)])
    qty_free = fields.Float('Qty Gift', default=1)

    @api.model
    def create(self, vals):
        record = super(PosPromotionSpecialCategory, self).create(vals)
        if record and record.product_id and not record.product_id.available_in_pos:
            raise UserError('Product service not available in POS. \n'
                            'Please go to product and check to checkbox available in pos / save')
        return record

    def write(self, vals):
        res = super(PosPromotionSpecialCategory, self).write(vals)
        for record in self:
            if record and record.product_id and not record.product_id.available_in_pos:
                raise UserError('Product service not available in POS. \n'
                                'Please go to product and check to checkbox available in pos / save')
        return res


class PosPromotionMultiBuy(models.Model):
    _name = "pos.promotion.multi.buy"
    _description = "Promotion for Multi Buy"

    product_ids = fields.Many2many(
        'product.product',
        'promotion_multi_by_product_rel',
        'multi_by_id',
        'product_id',
        domain=[('available_in_pos', '=', True)],
        string='Products',
        required=1
    )
    promotion_id = fields.Many2one(
        'pos.promotion',
        'Promotion',
        required=1,
        ondelete='cascade'
    )
    list_price = fields.Float(
        'Sale Price',
        required=1
    )
    qty_apply = fields.Float(
        'Qty >=',
        required=1,
        default=1
    )

    @api.model
    def create(self, vals):
        res = super(PosPromotionMultiBuy, self).create(vals)
        if vals.get('qty_apply') <= 0 or vals.get('list_price') <= 0:
            raise UserError('Promotion Price could not smaller than or equal 0')
        return res

    def write(self, vals):
        if (vals.get('qty_apply', None) and vals.get('qty_apply') <= 0) or (
                vals.get('list_price', None) and vals.get('list_price') <= 0):
            raise UserError('Promotion Price could not smaller than or equal 0')
        return super(PosPromotionMultiBuy, self).write(vals)
