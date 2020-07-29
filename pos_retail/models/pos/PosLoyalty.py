# -*- coding: utf-8 -*-
from odoo import fields, api, models, api, _
from datetime import timedelta

class pos_loyalty_category(models.Model):
    _name = "pos.loyalty.category"
    _description = "Tipo de fidelización del cliente"

    name = fields.Char('Nombre', required=1)
    code = fields.Char('Código', required=1)
    active = fields.Boolean('Activo', default=1)
    from_point = fields.Float('Puntos desde', required=1)
    to_point = fields.Float('Puntos hasta', required=1)


class pos_loyalty(models.Model):
    _name = "pos.loyalty"
    _description = "Programa de lealtades, en este objeto definimos el programa de lealtad, incluye reglas de puntos positivos y reglas de canje de puntos"

    name = fields.Char('Nombre', required=1)
    rule_ids = fields.One2many('pos.loyalty.rule', 'loyalty_id', 'Reglas', help='Reglas para puntos positivos para el cliente')
    reward_ids = fields.One2many('pos.loyalty.reward', 'loyalty_id', 'Recompensas', help='Reglas para canjear puntos cuando el cliente usa puntos en el pedido')
    state = fields.Selection([
        ('running', 'Activo'),
        ('stop', 'Detenido')
    ], string='Estado', default='running')
    product_loyalty_id = fields.Many2one('product.product', string='Servicio de Producto',
                                         domain=[('available_in_pos', '=', True)], required=1)
    rounding = fields.Float(string='Puntos de redondeo', default=1,
                            help="Esta es la relación de redondeo para redondear más puntos cuando el cliente compra productos, calcula como redondeo de moneda")
    rounding_down = fields.Boolean(string='Redondeando hacia abajo Total', default=0,
                            help="Redondeando los puntos totales más, por ejemplo, cuando la orden de compra del cliente,\n"
                                 "El total de puntos más es 7,9 pos redondeando a 7 puntos, y si 7,1 puntos se convierten en 7")
    config_ids = fields.One2many('pos.config', 'loyalty_id', string='Configuración pos aplicada')
    period_expired = fields.Integer('Período Tiempo vencido (día)', help='Todos los puntos provenientes de este programa expirarán si no están actualizados en este período. \n'
                                                                      'Ejemplo: si establece 30 días, cualquier punto positivo tendrá una vida útil de 30 días\n'
                                                                      'Y en 30 días, los puntos caducaron automáticamente y reducen los puntos del cliente',
                                    default=30)

    @api.model
    def default_get(self, default_fields):
        res = super(pos_loyalty, self).default_get(default_fields)
        products = self.env['product.product'].search([('default_code', '=', 'Rs')])
        if products:
            res.update({'product_loyalty_id': products[0].id})
        return res

    def active_all_pos(self):
        configs = self.env['pos.config'].search([])
        for loyalty in self:
            configs.write({'loyalty_id': loyalty.id})
        return True


class pos_loyalty_rule(models.Model):
    _name = "pos.loyalty.rule"
    _rec_name = 'loyalty_id'
    _description = "Reglas de Lealtad puntos plus"

    name = fields.Char('Nombre', required=1)
    active = fields.Boolean('Activo', default=1)
    loyalty_id = fields.Many2one('pos.loyalty', 'Lealtad', required=1)
    coefficient = fields.Float('Coeficiente', required=1,
                               help=' 10 USD convertidos a 1 punto el valor de entrada es 0.1,\n'
                                    ' 100 USD convertidos a un valor de entrada de 1 punto es 0.01\n'
                                    ' 1000 USD convertidos a un valor de entrada de 1 punto es 0.001.',
                               default=1, digits=(16, 6))
    type = fields.Selection([
        ('products', 'Productos'),
        ('categories', 'Categorias'),
        ('order_amount', 'Total de la orden')
    ], string='Tipo', required=1, default='products')
    product_ids = fields.Many2many('product.product', 'loyalty_rule_product_rel', 'rule_id', 'product_id',
                                   string='Productos', domain=[('available_in_pos', '=', True)])
    category_ids = fields.Many2many('pos.category', 'loyalty_rule_pos_categ_rel', 'rule_id', 'categ_id',
                                    string='Categorias')
    min_amount = fields.Float('Monto mínimo', required=1, help='Esta condición mínima cantidad de orden puede aplicar la regla')
    coefficient_note = fields.Text(compute='_get_coefficient_note', string='Nota de coeficiente')
    state = fields.Selection([
        ('running', 'Activo'),
        ('stop', 'Detenido')
    ], string='Estado', default='running')

    def _get_coefficient_note(self):
        for rule in self:
            rule.coefficient_note = '1 %s cubrirá a %s punto y con condición cantidad total pedido mayor que [Min Amount] %s' % (self.env.user.company_id.currency_id.name, rule.coefficient, rule.min_amount)

class pos_loyalty_reward(models.Model):
    _name = "pos.loyalty.reward"
    _description = "Reglas de lealtad canjear los puntos"

    name = fields.Char('Nombre', required=1)
    active = fields.Boolean('Activo', default=1)
    loyalty_id = fields.Many2one('pos.loyalty', 'Lealtad', required=1)
    redeem_point = fields.Float('Canjear punto', help='Este es el punto total obtenido del cliente cuando la recompensa del cajero')
    type = fields.Selection([
        ('discount_products', 'Productos de descuento'),
        ('discount_categories', "Categorías de descuento"),
        ('gift', 'Regalo'),
        ('resale', "Venta de descuento para obtener puntos"),
        ('use_point_payment', "Use el pago de puntos una parte del total del pedido"),
    ], string='Tipo de recompensa', required=1, help="""
        Productos con descuento: los productos de la lista de descuentos filtrarán por productos\n
        Categorías de descuento: los productos con descuento se filtrarán por categorías \n
        Regalo: obsequiará productos de regalo a los clientes \n
        Venta fuera de punto: venta de productos fuera de la lista y obtener puntos de clientes \n
        Use el punto de pago: punto encubierto al precio de descuento \n
    """)
    coefficient = fields.Float('Coeficiente', required=1,
                               help=' 1 punto convertido a 1 USD el valor de entrada es 1,\n'
                                    ' 10 puntos convertidos a 1 USD el valor de entrada es 0.1\n'
                                    ' 1000 puntos convertidos a 1 USD el valor de entrada es 0.001.',
                               default=1, digits=(16, 6))
    discount = fields.Float('Descuento %', required=1, help='Descuento %')
    discount_product_ids = fields.Many2many('product.product', 'reward_product_rel', 'reward_id', 'product_id',
                                            string='Productos', domain=[('available_in_pos', '=', True)])
    discount_category_ids = fields.Many2many('pos.category', 'reward_pos_categ_rel', 'reward_id', 'categ_id',
                                             string='POS Categorias')
    min_amount = fields.Float('Importe mínimo', required=1, help='Cantidad requerida Total del pedido mayor o igual para aplicar esta recompensa')
    gift_product_ids = fields.Many2many('product.product', 'reward_gift_product_product_rel', 'reward_id',
                                        'gift_product_id',
                                        string='Regalos', domain=[('available_in_pos', '=', True)])
    resale_product_ids = fields.Many2many('product.product', 'reward_resale_product_product_rel', 'reward_id',
                                          'resale_product_id',
                                          string='Productos de reventa', domain=[('available_in_pos', '=', True)])
    gift_quantity = fields.Float('Cantidad de regalo', default=1)
    price_resale = fields.Float('Precio de reventa')
    coefficient_note = fields.Text(compute='_get_coefficient_note', string='Nota de coeficiente')
    state = fields.Selection([
        ('running', 'Activo'),
        ('stop', 'Detenido')
    ], string='Estado', default='running')
    line_ids = fields.One2many('pos.order.line', 'reward_id', 'Líneas de pedido de POS')

    def _get_coefficient_note(self):
        for rule in self:
            rule.coefficient_note = '1 punto cubrirá hasta %s %s con condición cantidad mínima orden total mayor que: %s' % (
                rule.coefficient,self.env.user.company_id.currency_id.name, rule.min_amount)

class PosLoyaltyPoint(models.Model):
    _name = "pos.loyalty.point"
    _rec_name = 'partner_id'
    _description = "Modelo de gestión de todos los puntos adicionales o canje de cliente"

    create_uid = fields.Many2one('res.users', string='Creado por', readonly=1)
    is_return = fields.Boolean('Es una devolución', readonly=1)
    create_date = fields.Datetime('Fecha de creación', readonly=1)
    loyalty_id = fields.Many2one('pos.loyalty', 'Programa de Lealtad')
    order_id = fields.Many2one('pos.order', 'Orden', index=1, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', 'Cliente', required=1, index=1)
    end_date = fields.Datetime('Fecha de término')
    point = fields.Float('Punto')
    type = fields.Selection([
        ('import', 'Importación manual'),
        ('plus', 'Plus'),
        ('redeem', 'Redimir')
    ], string='Tipo', default='import', required=1)
    state = fields.Selection([
        ('ready', 'Listo para usar'),
        ('expired', 'Periodo vencido')
    ], string='Estado', default='ready')

    @api.model
    def create(self, vals):
        loyalty_program = self.env['pos.loyalty'].browse(vals.get('loyalty_id'))
        if loyalty_program.period_expired >= 0:
            end_date = fields.datetime.now() + timedelta(days=loyalty_program.period_expired)
            vals.update({'end_date': end_date})
        loyalty_point = super(PosLoyaltyPoint, self).create(vals)
        self.env['pos.cache.database'].insert_data('res.partner', loyalty_point.partner_id.id)
        return loyalty_point

    def cron_expired_points(self):
        loyalty_points = self.search([('end_date', '<=', fields.Datetime.now()), ('type', 'in', ['plus', 'import'])])
        if loyalty_points:
            loyalty_points.write({'state': 'expired'})
        return True

    def set_expired(self):
        return self.write({'state': 'expired'})

    def set_ready(self):
        return self.write({'state': 'ready'})

    def write(self, vals):
        res = super(PosLoyaltyPoint, self).write(vals)
        for loyalty_point in self:
            self.env['pos.cache.database'].insert_data('res.partner', loyalty_point.partner_id.id)
        return res

    def unlink(self):
        res = super(PosLoyaltyPoint, self).unlink()
        for loyalty_point in self:
            self.env['pos.cache.database'].remove_record('res.partner', loyalty_point.partner_id.id)
        return res






