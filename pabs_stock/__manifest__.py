# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################
{
  'name' : 'Control de inventario PABS',
  'summary': 'Coded By: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)',
  'author' : 'PABS',
  'category': 'Custom',
  'website': 'https://www.pabsmr.org',
  'depends' : ['stock','mortuary','pabs_sync_ebita'],
  'data': [
    'security/ir.model.access.csv',
    'security/security.xml',
    'security/groups.xml',
    'views/pabs_stock_picking_view.xml',
    'views/pabs_stock_config_view.xml',
    'views/pabs_sync_ebita_log_view.xml',      
    'views/product_template_view.xml',   
    'views/product_category_view.xml',   
    'views/stock_location_view.xml',   
    'views/pabs_picking_type_user_view.xml',   
    'wizard/set_lots_wizard_view.xml',   
    'wizard/update_stock_wizard_view.xml',   
    'reports/pabs_stock_movs_report.xml',   
    'wizard/create_move_ebita_wizard_view.xml',   
  ],
  'installable': True,
  'auto_install': False,
}
