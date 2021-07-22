# -*- coding: utf-8 -*-

from odoo import api, fields, models

class AccountAccount(models.Model):
  _inherit = 'account.account'

  analytic_account_required = fields.Boolean(string='¿Cuenta Analítica obligatoria?')
  