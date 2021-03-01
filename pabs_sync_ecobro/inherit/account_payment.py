# -*- coding: utf-8 -*-

from odoo import api, fields, models

class AccountPayment(models.Model):
  _inherit = 'account.payment'

  ecobro_affect_id = fields.Char(string='Afectación de ecobro ID')