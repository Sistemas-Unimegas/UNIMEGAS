# -*- coding: utf-8 -*-
from odoo import api, models, fields, registry
import logging

_logger = logging.getLogger(__name__)

class PosBranch(models.Model):
    _name = "pos.branch"
    _description = "Sucursales"

    name = fields.Char('Nombre', required=1)
    user_id = fields.Many2one(
        'res.users',
        'Gerente de la sucursal',
        required=1,
        help='Gerente de esta sucursal'
    )
    user_ids = fields.Many2many(
        'res.users',
        'pos_branch_res_users_rel',
        'branch_id',
        'user_id',
        string='Usuarios de la sucursal',
        help='Si los usuarios han agregado aquí, verán cualquier dato que se haya vinculado a esta Sucursal'
    )
    config_ids = fields.One2many(
        'pos.config',
        'pos_branch_id',
        string='POS de esta sucursal',
        readonly=1,
        help='El punto de ventas ha sido asignado a esta sucursal'
    )


    def get_default_branch(self):
        if self.env.user.pos_branch_id:
            return self.env.user.pos_branch_id.id
        else:
            _logger.info('Usuario %s no tiene sucursal' % self.env.user.login)
            return None