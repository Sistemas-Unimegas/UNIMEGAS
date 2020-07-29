# -*- coding: utf-8 -*-
from odoo import api, models, fields, registry
import logging

_logger = logging.getLogger(__name__)

class pos_category(models.Model):
    _inherit = "pos.category"

    is_category_combo = fields.Boolean(
        'Es una categoría de combo',
        help='Si está seleccionado, \n'
             'Cuando los combos aparecen en la pantalla POS\n'
             'La ventana emergente solo muestra que las categorías de POS tienen marcada la categoría de Combo'
    )
    sale_limit_time = fields.Boolean('Tiempo límite de venta')
    from_time = fields.Float('Hora inicial')
    to_time = fields.Float('Hora final')
    submit_all_pos = fields.Boolean('Enviar a todos los puntos de venta')
    pos_branch_ids = fields.Many2many(
        'pos.branch',
        'pos_category_branch_rel',
        'categ_id',
        'branch_id',
        string='Sucursales aplicadas')
    pos_config_ids = fields.Many2many(
        'pos.config',
        'pos_category_config_rel',
        'categ_id',
        'config_id',
        string='POS aplicados')

    @api.model
    def create(self, vals):
        category = super(pos_category, self).create(vals)
        self.env['pos.cache.database'].insert_data(self._inherit, category.id)
        return category

    def write(self, vals):
        res = super(pos_category, self).write(vals)
        for category in self:
            self.env['pos.cache.database'].insert_data(self._inherit, category.id)
        return res

    def unlink(self):
        for category in self:
            self.env['pos.cache.database'].remove_record(self._inherit, category.id)
        return super(pos_category, self).unlink()
