# -*- coding: utf-8 -*-
{
    'name': "Colonias",

    'summary': """
        Colonias""",

    'description': """
        Colonias
    """,

    'author': "Xmarts",
    'website': "https://www.xmarts.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '13.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'l10n_mx_edi'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/colonias.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
