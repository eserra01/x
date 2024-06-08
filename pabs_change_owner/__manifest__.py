# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################
{
  'name' : 'Permite cambiar el titular de un contrato ',
  'summary': 'Coded By: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)',
  'author' : 'PABS',
  'category': 'Custom',
  'website': 'https://www.pabsmr.org',
  'depends' : ['base','pabs_custom'],
  'data': [
    'security/ir.model.access.csv',
    'security/security.xml',  
    'security/groups.xml',  
    'views/pabs_change_owner_request_view.xml',
    'views/pabs_contract_view.xml',
  ],
  'installable': True,
  'auto_install': False,
}
