# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    code_pabs = fields.Char(
        string='Codigo',
    )