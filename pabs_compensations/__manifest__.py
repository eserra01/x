# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################
{
  'name' : 'Compensasiones para coordinadores y generentes PABS',
  'summary': 'Coded By: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)',
  'author' : 'PABS',
  'category': 'Custom',
  'website': 'https://www.pabsmr.org',
  'depends' : ['base','pabs_custom','pabs_log'],
  'data': [
    'security/ir.model.access.csv',
    'security/security.xml',  
    'security/groups.xml',      
    'views/res_company_view.xml',       
    'views/pabs_compensation_amount_view.xml',       
    'views/pabs_office_manager_view.xml',       
    'views/pabs_compensation_view.xml',   
    'views/pabs_trimestral_commission_view.xml',   
    'views/pabs_trimester_view.xml',  
    'reports/pabs_bonus_xlsx_report.xml',
    'wizard/bonus_report_xlsx_wizard_view.xml',
    # 'data/pabs.compensation.amount.csv',
    'data/pabs.trimester.csv',
  ],
  'installable': True,
  'auto_install': False,
}
