# -*- coding: utf-8 -*-
{
    'name': "pabs_eleanor",

    'summary': """ 
    Adaptación de ELEANOR para Odoo
    """,        

    'description': """
        ...
    """,

    'author': "PABS",
    'website': "http://pabsmr.org",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','hr','account','pabs_custom'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'security/groups.xml',
        'views/menus.xml',
        'views/pabs_eleanor_area_view.xml',
        'views/pabs_eleanor_disease_view.xml',
        'views/stock_warehouse_view.xml',
        'views/hr_department_view.xml',
        'views/hr_job_view.xml',
        'views/hr_employee_view.xml',
        'views/res_users_view.xml',
        'views/pabs_eleanor_user_access_view.xml',
        'views/pabs_eleanor_concept_category_view.xml',
        'views/pabs_eleanor_concept_job_view.xml',
        'views/pabs_eleanor_concept_view.xml',
        'views/pabs_eleanor_period_view.xml',
        'views/pabs_eleanor_move_view.xml',
        'views/pabs_eleanor_migration_view.xml',
        'reports/pabs_eleanor_move_detail_xlsx_report_view.xml',
        'reports/pabs_eleanor_move_resume_xlsx_report_view.xml',
        'reports/pabs_eleanor_move_resume_acc_xlsx_report_view.xml',
        'wizard/pabs_eleanor_move_import_xlsx_wizard_view.xml',
        'views/pabs_eleanor_move_binnacle_view.xml',
        'views/pabs_eleanor_salary_history_view.xml',
        'views/pabs_eleanor_taxpayer_view.xml',
        'views/pabs_eleanor_ema_view.xml',
        'views/pabs_eleanor_eba_view.xml',
        'wizard/pabs_eleanor_cofiplem_import_xlsx_wizard_view.xml',
        'wizard/pabs_eleanor_close_period_wizard_view.xml',
        'wizard/pabs_eleanor_move_layout_wizard_view.xml',
    ],        
}
