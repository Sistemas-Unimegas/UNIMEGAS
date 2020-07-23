# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Datos_facturas(models.Model):

	_inherit = 'account.move'

	tipo_factura=fields.Selection([('PUE','PUE - Pago en una sola exhibición'),
	                           ('PPD','PPD - Pago en parcialidades o diferido')])