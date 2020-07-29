# -*- coding: utf-8 -*-
from odoo import api, models, fields, registry
import logging

_logger = logging.getLogger(__name__)


class PosIoT(models.Model):
    _name = "pos.iot"
    _description = "Pos IoT Equipo"

    name = fields.Char('Nombre', required=1)
    proxy = fields.Char('Proxy', required=1)
    port = fields.Char('Puerto', required=1, default='8069')
    product_ids = fields.Many2many(
        'product.product',
        'iot_product_rel',
        'iot_box_id',
        'product_id',
        string='Productos',
        domain=[('available_in_pos', '=', True)],
        help='Los productos se enviarán a la caja de IoT')
    screen_kitchen = fields.Boolean('Pantalla directa', help='Pantalla IoT de sesión de cocina / bar')
    login_kitchen = fields.Char('Inicio de sesión de pantalla', help='Cuenta de inicio de sesión de cocina / pantalla de bar')
    password_kitchen = fields.Char('Contraseña de pantalla', help='Contraseña de la pantalla de la cocina / barra')
    database = fields.Char('Tu base de datos Odoo')
    odoo_public_proxy = fields.Char('Su proxy público de Odoo',
                                    help='ejemplo: http://192.168.1.7:8069 o tu dominio Odoo')
