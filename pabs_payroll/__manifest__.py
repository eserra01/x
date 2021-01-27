# -*- coding: utf-8 -*-

{
  'name' : 'Nominas PABS',
  'summary': 'Coded By: Eduardo Serrano(eduardo.serrano@pabsmr.org)',
  'author' : 'PABS',
  'category': 'Nómina',
  'website': 'https://www.pabsmr.org',
  'depends' : [
    'base',
    'hr',
    'pabs_custom'],
  'data': [
    'data/ir_sequence.xml',
    'security/ir.model.access.csv',
    'views/week_number_view.xml',
    'views/pabs_payroll_view.xml',
    'views/menu_items.xml',
    ],
  'installable': True,
  'auto_install': False,
}