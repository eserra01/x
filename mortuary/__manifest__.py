# -*- coding: utf-8 -*-
{
    'name': "mortuary",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr', 'pabs_custom'],

    # always loaded
    'data': [
        'data/data_group.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/ii_servicio.xml',
        'views/ii_servicio2.xml',
        'views/ii_causa_fallecim.xml',
        'views/ds_atiende_servicio.xml',
        'views/ds_sucursal_velacion.xml',
        'views/ds_tipo_servicio.xml',
        'views/ds_capilla.xml',
        'views/ds_origen.xml',
        'views/ds_sucursal_qentreg_cenizas.xml',
        'views/ds_ataud.xml',
        'views/ds_urna.xml',
        'views/relacion_confinad.xml',
        'views/podp_calle_ynumber.xml',
        'views/iv_lugar_velacion.xml',
        'views/iv_nombre_capilla.xml',
        'views/dc_forma_pago.xml',
        'views/ir_operativo.xml',
        'views/carroza.xml',
        'views/ig_proveedor_embalsama.xml',
        'views/ig_templo.xml',
        'views/ig_panteon.xml',
        'views/menus.xml',
        'data/data.xml',
        'report/report_bsf.xml',
        'report/report_cgs.xml',
        'report/report_agreement.xml',
        'report/carnet_pago.xml',
        'report/estado_cuenta.xml',
        'wizard/wizard_convenio_bitacora.xml',
    ],
    'istallable': True,
    'aplication': True,
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
