# -*- coding: utf-8 -*-
{
    'name': "xmarts_funeraria",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'account', 'hr','pabs_custom','pabs_account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'report/promoter_office.xml',
        #'wizard/payroll_promoter.xml',
        'wizard/account_payment_wizard.xml',
        'report/account_payment_colloctors.xml',
        'wizard/payroll_pabs_ing_egre.xml',
        'report/payroll_ing_egre.xml',
        'wizard/carnet_pago_rango.xml',
        'wizard/carnet_pago_rango_tabla_wizard.xml',
        'report/carnet_pago_sin_tabla_rango.xml',
        'wizard/comisiones_promotores.xml',
        'report/rpt_comisiones_promotores.xml',
        'wizard/historial_ventas.xml',
        'report/rpt_historial_ventas.xml',
        'wizard/comisiones_por_recuperar.xml',
        'report/rpt_comisiones_por_recuperar.xml',
        'views/hr_employee.xml',
        'views/res_company_view.xml',
        'views/stock_picking_view.xml',
        'report/arqueo.xml',
        'report/carnet_pago.xml',
        'report/carnet_pago_sin_tabla.xml',
        'report/estado_cuenta.xml',
        'report/estimado_pago.xml',
        'report/bono500.xml',
        'report/cartera_cobrador.xml',
        'report/activo_moroso.xml',
        'report/detallado_moroso.xml',
        'report/contrato_pagado.xml',
        'report/office_promoter.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
