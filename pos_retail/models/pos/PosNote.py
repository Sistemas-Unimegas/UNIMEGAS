# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class pos_note(models.Model):
    _name = "pos.note"
    _description = "Gestión de Notas de la orden"

    name = fields.Text('Notas', required=1)