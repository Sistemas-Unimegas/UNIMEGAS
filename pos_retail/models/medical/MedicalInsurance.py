# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import UserError
from datetime import datetime


class medical_insurance(models.Model):
    _name = "medical.insurance"
    _description = "Gestión de Seguros Médicos"
    _rec_name = 'employee'

    insurance_company_id = fields.Many2one(
        'res.partner',
        string='Compañía de seguros',
        domain=[('is_company', '=', True)],
        required=1)
    code = fields.Char('Código', copy=False)
    subscriber_id = fields.Many2one(
        'res.partner', 'Suscriptor',
        help='Nombre del Suscriptor, \n'
             'podría ser una empresa o una persona individual')
    patient_name = fields.Char(
        'Nombre del paciente', required=1,
        help='Nombre completo del paciente, \n'
             'se puede encontrar en el formulario de prescripción médica')
    patient_number = fields.Char(
        'Número del paciente',
        required=1,
        index=1,
        help='Número de identificación del paciente, \n'
             'se puede encontrar en el formulario de prescripción médica')
    rate = fields.Float(
        'Cobertura', help='Tasa de porcentaje cubierta por la compañía de seguros, desde 0 a 100%',
        required=1)
    medical_number = fields.Char(
        'Número médico',
        help='Número de formulario, se puede encontrar en el formulario de prescripción médica',
        required=1)
    employee = fields.Char(
        'Empleado',
        help='Nombre completo del empleado, puede ser diferente del nombre del paciente, \n'
             ' se puede encontrar en el formulario de prescripción médica')
    phone = fields.Char(
        'Teléfono',
        help='Número de teléfono de contacto del paciente')
    product_id = fields.Many2one(
        'product.product',
        'Service',
        domain=[('type', '=', 'service')])
    active = fields.Boolean(
        'Activo',
        default=1)
    expired_date = fields.Datetime('Fecha de expiración')

    _sql_constraints = [
        ('patient_number_uniq', 'unique(patient_number)', 'El número de paciente debe ser único por empresa!'),
    ]

    @api.model
    def create(self, vals):
        if vals.get('rate') > 100 or vals.get('rate') <= 0:
            raise UserError(u'La tasa no es menor que 0 ni mayor que 100')
        if not vals.get('product_id', False):
            products = self.env['product.product'].search([('default_code', '=', 'MS')])
            if products:
                vals.update({'product_id': products[0].id})
            else:
                raise UserError(
                    'No encuentra el Servicio médico del producto con el código predeterminado MS. Por favor cree este producto antes de crear un seguro médico')
        insurance = super(medical_insurance, self).create(vals)
        if not insurance.code:
            format_code = "%s%s%s" % ('666', insurance.id, datetime.now().strftime("%d%m%y%H%M"))
            code = self.env['barcode.nomenclature'].sanitize_ean(format_code)
            insurance.write({'code': code})
        return insurance

    def write(self, vals):
        if vals.get('rate', None):
            if vals.get('rate') > 100 or vals.get('rate') <= 0:
                raise UserError(u'La tasa no es menor que 0 ni mayor que 100')
        return super(medical_insurance, self).write(vals)

    def unlink(self):
        for insurance in self:
            pos_orders = self.env['pos.order'].search(
                [('state', '=', 'paid'), ('medical_insurance_id', '=', insurance.id)])
            if pos_orders:
                raise UserError(u'Este seguro se ha vinculado al pedido pos pagado por el estado, no se pudo eliminar')
        return super(medical_insurance, self).unlink()
