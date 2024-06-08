# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    operation_ids = fields.Many2many(
        comodel_name='pabs.changes.format.operation',
        string="Operaciones permitidas",
        relation='user_operation_rel',
        column1='user_id',
        column2='operation_id'
    )
    exclude_pass_reset = fields.Boolean(string="Excluir reseteo password")
    physical_company_id = fields.Many2one(string="Empresa física",comodel_name="pabs.physical.company",tracking=True)