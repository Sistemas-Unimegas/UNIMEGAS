# -*- coding: utf-8 -*-
from odoo import api, models, fields, registry
import logging

_logger = logging.getLogger(__name__)

class PosBranch(models.Model):
    _inherit = "hr.employee"

    barcode = fields.Char(string="Gafette ID", help="ID utilizado para la identificación del empleado.", groups="base.group_user", copy=False)