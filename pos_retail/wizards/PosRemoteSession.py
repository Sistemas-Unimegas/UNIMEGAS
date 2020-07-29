# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import json
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class pos_remote_session(models.TransientModel):
    _name = "pos.remote.session"
    _description = "Ayuda a administrar sesiones remotas"

    message = fields.Text('Mensaje')
    config_ids = fields.Many2many('pos.config', 'remote_session_config_rel', 'wiz_id', 'config_id',
                                  'La configuración POS necesita hacer', required=1)
    action = fields.Selection([
        ('reload_session', 'Recargar sesión'),
        ('open_session', 'Abrir sesión'),
        ('validate_and_post_entries', 'Validar y publicar entradas'),
        ('close_session', 'Cerrar sesión'),
        ('lock_session', 'Bloquear sesión'),
        ('unlock_session', 'Desbloquear sesión'),
        ('remove_cache', 'Eliminar caché')
    ], string='Acción a hacer', required=1)

    def send_notifications(self):
        for record in self:
            if not record.config_ids:
                raise UserError(_('Advertencia, agregue pos config primero'))
            vals = {}
            for config in record.config_ids:
                action = record.action
                vals[action] = True
                sessions = self.env['pos.session'].search([('config_id', '=', config.id), ('state', '=', 'opened')])
                if sessions:
                    vals.update({'session_id': sessions[0].id})
                    vals.update({'config_id': config.id})
                    vals.update({'database': self.env.cr.dbname})
                    user = sessions[0].user_id
                    self.env['bus.bus'].sendmany(
                        [[(self.env.cr.dbname, 'pos.remote_sessions', user.id), json.dumps(vals)]])
                else:
                    users = self.env['res.users'].search([('pos_config_id', '=', config.id)])
                    for user in users:
                        self.env['bus.bus'].sendmany(
                            [[(self.env.cr.dbname, 'pos.remote_sessions', user.id), json.dumps(vals)]])
        return True