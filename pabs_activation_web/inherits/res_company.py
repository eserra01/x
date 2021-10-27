# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ResCompany(models.Model):
  _inherit = 'res.company'

  salary_contract_limit = fields.Integer(string='Limite de Contratos a sueldo')
  visible_activador = fields.Boolean (string = "Visible en el activador", default = False)