# -*- coding: utf-8 -*-

from odoo import api, fields, models

class HREmployee(models.Model):
  _inherit = 'hr.employee'

  ecobro_id = fields.Char(string='Ecobro ID', tracking=True)
  