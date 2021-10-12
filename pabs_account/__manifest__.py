# -*- coding: utf-8 -*-

{
  'name' : 'Contabilidad PABS',
  'summary': 'Coded By: Eduardo Serrano(eduardo.serrano@pabsmr.org)',
  'author' : 'PABS',
  'category': 'web',
  'website': 'https://www.pabsmr.org',
  'depends' : [
    'base',
    'account',
    'account_accountant',
    'pabs_sync_ecobro',
    'pabs_custom'],
  'data': [
  'wizard/pabs_investment_surplus_wizard.xml',
  'wizard/pabs_bank_deposits_wizard.xml',
  'wizard/pabs_balanace_transfer_wizard.xml',
  'security/ir.model.access.csv',
  'views/res_company_view.xml',
  'views/stock_warehouse_view.xml',
  'views/account_account_view.xml',
  'views/account_move_view.xml',
  'views/account_tax_view.xml',
  'security/security.xml',
  ],
  'installable': True,
  'auto_install': False,
}
