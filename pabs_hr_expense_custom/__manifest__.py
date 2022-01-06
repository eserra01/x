# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################
{
  'name' : 'Customización del módulo hr_expense',
  'summary': 'Coded By: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)',
  'author' : 'PABS',
  'category': 'Custom',
  'website': 'https://www.pabsmr.org',
  'depends' : ['base','hr_expense','hr'],
  'data': [
    'views/res_company_view.xml',
    'views/res_users_view.xml',
    'views/hr_expense_view.xml',
    'views/hr_employee_view.xml',
    'security/security.xml',
  ],
  'installable': True,
  'auto_install': False,
}
