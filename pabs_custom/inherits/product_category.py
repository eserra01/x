# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ProductCategory(models.Model):
  _inherit = 'product.category'

  company_id = fields.Many2one(
    'res.company', 'Compañia',
    default=lambda s: s.env.company.id, index=True)