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
    'report_xlsx',
    'pabs_custom'],
  'data': [
    'security/ir.model.access.csv',
    'views/week_number_view.xml',
    'views/pabs_payroll_view.xml',
    'views/pabs_payroll_contract_view.xml',
    'views/pabs_payroll_collection_view.xml',
    'views/pabs_payroll_management_view.xml',
    'views/hr_employee_view.xml',
    'views/pabs_contract_view.xml',
    'wizard/pabs_payroll_generate_year_wizard.xml',
    'views/menu_items.xml',
    'reports/payroll_report.xml',
    ],
  'installable': True,
  'auto_install': False,
}