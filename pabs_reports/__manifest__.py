# -*- coding: utf-8 -*-
{
  'name' : 'REPORTES PABS',
  'summary': 'Coded By: Luis (luis.lopez@pabsmr.org)',
  'author' : 'PABS',
  'category': 'Reports',
  'website': 'https://www.pabsmr.org',
  'depends' : [
    'xmarts_funeraria',
    'report_xlsx',
    'pabs_custom'],
  'data': [
    'wizard/production_contract.xml',
    'wizard/pabs_daily_helps_wizard.xml',
    'wizard/pabs_acumulated_report_wizard.xml',
    'views/menus.xml',
    'reports/elaborated_contracts.xml'
    
    ],
  'installable': True,
  'auto_install': False,
}