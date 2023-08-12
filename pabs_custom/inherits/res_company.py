# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResCompany(models.Model):
  _inherit = 'res.company'

  bonus_as = fields.Boolean(string="Aplica bono de AS")
  