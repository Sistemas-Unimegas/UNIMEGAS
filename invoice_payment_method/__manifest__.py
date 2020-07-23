# -*- coding: utf-8 -*-
{
    'name': "Agregar Método de Pago en la Factura",

    'summary': """
        El usuario puede seleccionar PPD o PUE en lugar del cálculo automático
        que realiza Odoo por default""",

    'description': """
        Agrega el campo Método de Pago en la factura con las opciones PPD o PUE
        y así el usuario puede seleccionar la opción para modificar el flujo
        de la generación de la factura electrónica.
    """,

    'author': "SURSOOM",
    'website': "www.sursoom.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'facturacion',
    'version': '0.1.13',

    # any module necessary for this one to work correctly
    'depends': ['base','l10n_mx_edi','l10n_mx','account','account_accountant'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/view_invoice.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
