# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################
{
  'name' : 'Logs generales PABS',
  'summary': 'Coded By: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)',
  'author' : 'PABS',
  'category': 'Custom',
  'website': 'https://www.pabsmr.org',
  'depends' : ['base'],
  'data': [
    'security/ir.model.access.csv',
    'security/security.xml',  
    'views/pabs_log_view.xml',   
  ],
  'installable': True,
  'auto_install': False,
}
