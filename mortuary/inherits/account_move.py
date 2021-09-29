# -*- coding: utf-8 -*-

from odoo import api, fields, models

class AccountMove(models.Model):
  _inherit = 'account.move'

  recibo = fields.Char(string="Número de recibo")