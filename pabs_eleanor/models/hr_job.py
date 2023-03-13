# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrJob(models.Model):
    _inherit = 'hr.job'    

    job_category_id = fields.Many2one(comodel_name="pabs.eleanor.job.category", string="Categoria")