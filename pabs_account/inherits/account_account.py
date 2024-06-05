# -*- coding: utf-8 -*-

from odoo import api, fields, models

class AccountAccount(models.Model):
  _inherit = 'account.account'

  analytic_account_required = fields.Boolean(string='¿Cuenta Analítica obligatoria?')
  cash_flow_analytic_tag_required = fields.Boolean(string='¿Etiqueta Analítica obligatoria para flujo de efectivo?')