# -*- coding: utf-8 -*-

{
  'name' : 'Sincronizador con Ecobro',
  'summary': 'Coded By: Eduardo Serrano(eduardo.serrano@pabsmr.org)',
  'author' : 'PABS',
  'category': 'SYNC',
  'website': 'https://www.pabsmr.org',
  'depends' : [
    'base',
    'base_setup',
    'hr',
    'pabs_custom'],
  'data': [
    'views/ecobro_settings_view.xml',
    'views/hr_employee_view.xml',
    'views/account_payment_view.xml',
    'data/ir_cron.xml',
  ],
  'installable': True,
  'auto_install': False,
}
