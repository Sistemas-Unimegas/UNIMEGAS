# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
import odoo
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging

_logger = logging.getLogger(__name__)


class sale_order(models.Model):
    _inherit = "sale.order"

    signature = fields.Binary('Signature', readonly=1)
    book_order = fields.Boolean('Book order')
    ean13 = fields.Char('Ean13', readonly=1)
    pos_location_id = fields.Many2one('stock.location', 'POS Location')
    delivery_date = fields.Datetime('POS Delivery Date ')
    delivered_date = fields.Datetime('POS Delivered Date ')
    delivery_address = fields.Char('POS Delivery Address')
    delivery_phone = fields.Char('POS Delivery Phone', help='Phone of customer for delivery')
    payment_partial_amount = fields.Float('Payment Amount Partial', track_visibility='onchange')
    payment_partial_method_id = fields.Many2one('pos.payment.method', string='Account Payment Method Partial', track_visibility='onchange')
    insert = fields.Boolean('Insert', default=0)
    state = fields.Selection(selection_add=[
        ('booked', 'Converted to POS Order')
    ])
    pos_branch_id = fields.Many2one('pos.branch', string='Branch', track_visibility='onchange')
    pos_order_id = fields.Many2one('pos.order', 'POS Order', readonly=1, track_visibility='onchange')

    def action_validate_picking(self):
        picking_name = ''
        for sale in self:
            for picking in sale.picking_ids:
                if picking.state in ['assigned', 'waiting', 'confirmed']:
                    for move_line in picking.move_line_ids:
                        move_line.write({'qty_done': move_line.product_uom_qty})
                    for move_line in picking.move_lines:
                        move_line.write({'quantity_done': move_line.product_uom_qty})
                    picking.button_validate()
                    picking_name = picking.name
        return picking_name

    @api.model
    def pos_create_sale_order(self, vals, sale_order_auto_confirm, sale_order_auto_invoice, sale_order_auto_delivery):
        sale = self.create(vals)
        sale.order_line._compute_tax_id()
        if sale_order_auto_confirm:
            sale.action_confirm()
            sale.action_done()
        if sale_order_auto_delivery and sale.picking_ids:
            for picking in sale.picking_ids:
                for move_line in picking.move_line_ids:
                    move_line.write({'qty_done': move_line.product_uom_qty})
                for move_line in picking.move_lines:
                    move_line.write({'quantity_done': move_line.product_uom_qty})
                picking.button_validate()
        if sale_order_auto_confirm and sale_order_auto_invoice:
            ctx = {'active_ids': [sale.id]}
            payment = self.env['sale.advance.payment.inv'].with_context(ctx).create({
                'advance_payment_method': 'fixed',
                'fixed_amount': sale.amount_total,
            })
            payment.create_invoices()
        return {'name': sale.name, 'id': sale.id}

    @api.model
    def booking_order(self, vals):
        so = self.create(vals)
        return {'name': so.name, 'id': so.id}

    @api.model
    def create(self, vals):
        if not vals.get('pos_branch_id'):
            vals.update({'pos_branch_id': self.env['pos.branch'].sudo().get_default_branch()})
        sale = super(sale_order, self).create(vals)
        self.env['pos.cache.database'].insert_data(self._inherit, sale.id)
        if not sale.delivery_address:
            if sale.partner_shipping_id:
                sale.delivery_address = sale.partner_shipping_id.contact_address
            else:
                sale.delivery_address = sale.partner_id.contact_address
        return sale

    def write(self, vals):
        res = super(sale_order, self).write(vals)
        for sale in self:
            if not sale.delivery_address:
                if sale.partner_shipping_id:
                    sale.delivery_address = sale.partner_shipping_id.contact_address
                else:
                    sale.delivery_address = sale.partner_id.contact_address
            self.env['pos.cache.database'].insert_data(self._inherit, sale.id)
        return res

    def unlink(self):
        for record in self:
            self.env['pos.cache.database'].remove_record(self._inherit, record.id)
        return super(sale_order, self).unlink()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    insert = fields.Boolean('Insert', default=0)
    parent_id = fields.Many2one('sale.order.line', 'Parent')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    variant_ids = fields.Many2many('product.variant',
                                   'sale_line_variant_rel',
                                   'sale_line_id',
                                   'variant_id',
                                   string='Variants')
    pos_note = fields.Text('Booking Note')
    pos_branch_id = fields.Many2one('pos.branch', string='Branch')

    @api.model
    def create(self, vals):
        if not vals.get('pos_branch_id'):
            vals.update({'pos_branch_id': self.env['pos.branch'].sudo().get_default_branch()})
        line = super(SaleOrderLine, self).create(vals)
        if line.insert:
            line.order_id.write({'insert': True})
        self.env['pos.cache.database'].insert_data('sale.order', line.order_id.id)
        self.env['pos.cache.database'].insert_data(self._inherit, line.id)
        return line

    def unlink(self):
        for record in self:
            self.env['pos.cache.database'].remove_record(self._inherit, record.id)
        return super(SaleOrderLine, self).unlink()

    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        for line in self:
            self.env['pos.cache.database'].insert_data(self._inherit, line.id)
        return res

    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        if self.order_id.pos_location_id:
            values.update({'location_id': self.order_id.pos_location_id.id})
        return values
