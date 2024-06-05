# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################
{
  'name' : 'Balanza de comprobación PABS',
  'summary': 'Coded By: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)',
  'author' : 'PABS',
  'category': 'Custom',
  'website': 'https://www.pabsmr.org',
  'depends' : ['account'],
  'data': [
    'security/ir.model.access.csv',
    'views/pabs_trialbalance_view.xml',   
    'wizard/pabs_trialbalance_wizard_view.xml',
    'views/pabs_cash_flow_view.xml',   
    'wizard/pabs_cash_flow_wizard_view.xml'
  ],
  'installable': True,
  'auto_install': False,
}
