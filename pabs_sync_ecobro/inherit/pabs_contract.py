# -*- coding: utf-8 -*-

from odoo import api, fields, models

class PABSContract(models.Model):
  _inherit = 'pabs.contract'

  ecobro_id = fields.Char(string='Ecobro ID')
