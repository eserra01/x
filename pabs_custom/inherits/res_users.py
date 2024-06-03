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