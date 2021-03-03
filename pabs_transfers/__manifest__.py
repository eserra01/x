# -*- coding: utf-8 -*-

{
  'name' : 'PABS Transferencias',
  'summary': 'Coded By: Eduardo Serrano(eduardo.serrano@pabsmr.org)',
  'author' : 'PABS',
  'category': 'stock',
  'website': 'https://www.pabsmr.org',
  'depends' : [
    'base',
    'base_setup',
    'pabs_custom'],
  'data': [
    'wizard/pabs_transfer_wizard_view.xml',
    'views/menu_views.xml',
    'security/ir.model.access.csv',
  ],
  'installable': True,
  'auto_install': False,
}
