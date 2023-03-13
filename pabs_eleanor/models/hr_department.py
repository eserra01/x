# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrDepartment(models.Model):
    _inherit = 'hr.department'    

    pabs_eleanor_area_id = fields.Many2one(comodel_name="pabs.eleanor.area", string="Área")
    account_analytic_id = fields.Many2one(comodel_name="account.analytic.account", string="Cuenta analítica")
