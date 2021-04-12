# -*- coding: utf-8 -*-

from odoo import api, fields, models

class HrEmployee(models.Model):
  _inherit = 'hr.employee'

  salary_base = fields.Float(string='Sueldo base')
  
  own_contracts = fields.One2many(comodel_name='pabs.contract',
    inverse_name='owner_id',
    string='Contratos Propios')