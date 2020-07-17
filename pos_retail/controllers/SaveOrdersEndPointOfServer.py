# -*- coding: utf-8 -*
from odoo import http, _
from odoo.addons.web.controllers import main as web
import odoo
from odoo import api, fields, models, SUPERUSER_ID

import json
import logging
from odoo.http import request
import time
import platform
import subprocess

_logger = logging.getLogger(__name__)


class SyncController(web.Home):

    def __init__(self):
        _logger.info('Starting SyncController')
        self.auto_push_orders = False

    @http.route('/pos/ping/server', type="json", auth='none', cors='*')
    def ping_odoo_server(self, ip, port):
        _logger.info('ping server ip address %s' % ip)
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', ip]
        return json.dumps({'state': 'succeed', 'values': subprocess.call(command) == 0})

    @http.route('/pos/create_from_ui', type="json", auth='none', csrf=False, cors='*', methods=['POST'])
    def endpoint_save_orders(self):
        datas = json.loads(request.httprequest.data)
        database = datas.get('database')
        username = datas.get('username')
        server_version = datas.get('server_version')
        orders = datas.get('orders')
        order_ids = []
        if len(orders) > 0:
            registry = odoo.registry(database)
            orders = [order[2] for order in orders]
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                order_ids = env['pos.order'].sudo().create_from_ui(orders)
                _logger.info('User %s created order ids: %s - odoo version %s' % (username, order_ids, server_version))
        return order_ids

    @http.route('/pos/automation/paid_orders', type="json", auth='user', cors='*')
    def push_orders(self, message):
        values = []
        if self.auto_push_orders:
            return json.dumps({'status': 'waiting', 'values': []})
        else:
            self.auto_push_orders = True
            orders = request.env['pos.order'].search([
                ('state', '=', 'draft'),
                ('user_id', '=', request.env.user.id)
            ])
            for order in orders:
                is_paid = order._is_pos_order_paid()
                if is_paid:
                    order.action_pos_order_paid()
                    _logger.info('auto paid order id %s' % order.id)
                    values.append(order.name)
                    request.env.cr.commit()
            self.auto_push_orders = False
        return json.dumps({'status': 'succeed', 'values': values})

