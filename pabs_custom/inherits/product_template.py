# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ProductTemplate(models.Model):
  _inherit = 'product.template'

  company_id = fields.Many2one(comodel_name='product.template',
    default=lambda s: s.env.company.id, index=True) 