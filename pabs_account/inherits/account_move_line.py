# -*- coding: utf-8 -*-

from odoo import api, models, fields

class AccountMoveLine(models.Model):
  _inherit = 'account.move.line'

  analytic_account_required = fields.Boolean(string='¿Analítica requerida?',
    related="account_id.analytic_account_required")
