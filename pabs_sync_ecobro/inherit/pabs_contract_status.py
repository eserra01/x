# -*- coding: utf-8 -*-

from odoo import api, fields, models

class PABSContractStatus(models.Model):
  _inherit = 'pabs.contract.status'

  ecobro_code = fields.Integer(string='Estatus Ecobro')

  