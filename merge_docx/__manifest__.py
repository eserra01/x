# -*- coding: utf-8 -*-

{
    'name': 'Template Report DOCX',
    'description': 'Is Easy an elegant and scalable solution to design reports'
                   'using Microsoft Office.',
    'summary': 'Export data all objects odoo to Microsoft Office output'
                   ' files docx, pdf',
    'category': 'All',
    'version': '1.0',
    'website': 'http://www.build-fish.com/',
    "license": "OPL-1",
    'author': 'BuildFish',
    'depends': [
        'base', 'web'
    ],
    "external_dependencies": {
        "bin": ["unoconv"],
    },
    'data': [
        'data/templates.xml',
        'report.xml',
        'views/webclient_templates.xml',
        'views/report_view.xml'
    ],
    'live_test_url': 'https://youtu.be/919YFe4mtkc',
    'price': 55.00,
    'currency': 'EUR',
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
