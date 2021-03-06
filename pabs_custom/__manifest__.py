# -*- coding: utf-8 -*-
{
  'name' : 'Customizacion PABS',
  'summary': 'Coded By: Eduardo Serrano(eduardo.serrano@pabsmr.org)',
  'author' : 'PABS',
  'category': 'Custom',
  'website': 'https://www.pabsmr.org',
  'depends' : [
    'base', 
    'stock',
    'sale_management',
    'account_accountant',
    'account',
    'product',
    'purchase',
    'contacts',
    'hr'],
  'data': [
    'data/ir_sequence.xml',
    'reports/closing_transfer_report.xml',
    'reports/arching_report.xml',
    'views/pabs_office_view.xml',
    'views/hr_employee_view.xml',
    'views/payment_scheme_view.xml',
    'views/recluitment_origin_view.xml',
    'views/recluitment_induction_view.xml',
    'views/contract_view.xml',
    'views/product_pricelist_view.xml',
    'views/stock_location_view.xml',
    'views/stock_picking_view.xml',
    'views/stock_production_lot_view.xml',
    'views/purchase_order_view.xml',
    'views/closing_transfer_view.xml',
    'views/account_move_view.xml',
    'views/res_locality.xml',
    'views/colonias.xml',
    'views/pabs_comission_template_of_templates_view.xml',
    'views/pabs_comission_template_view.xml',
    'views/pabs_comission_tree_view.xml',
    'views/pabs_comission_debt_collector.xml',
    'views/pabs_comission_output.xml',
    'views/account_payment_view.xml',
    'views/pabs_bonus_view.xml',
    'wizard/pabs_status_stock_view.xml',
    'views/pabs_contract_status_view.xml',
    'views/pabs_contract_status_reason_view.xml',
    'wizard/pabs_closing_transfer_wizard_view.xml',
    'wizard/fix_stock_move_wizard_view.xml',
    'wizard/pabs_single_contract_wizard_view.xml',
    'wizard/pabs_arching_view.xml',
    'security/security.xml',
    'views/menu_views.xml',
    'security/ir.model.access.csv',
    ],
  'installable': True,
  'auto_install': False,
}
