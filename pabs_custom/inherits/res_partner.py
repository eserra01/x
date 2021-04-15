# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
  _inherit = 'res.partner'

  company_id = fields.Many2one(
    'res.company', 'Compañia', index=True)