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
    'wizard/pabs_daily_helps_wizard.xml',
    'wizard/pabs_collector_report_wizard.xml',
    'wizard/report_pabs_ing_egre_wizard.xml',
    'wizard/transfer_portfolio_partners_wizard.xml',
    'views/menus.xml',
    'reports/elaborated_contracts.xml',
    'reports/pabs_collector_report_template.xml',
    'security/security.xml',
    'security/ir.model.access.csv',
    
    ],
  'installable': True,
  'auto_install': False,
}