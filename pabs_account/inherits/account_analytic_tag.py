# -*- coding: utf-8 -*-
from odoo import api, fields, models

class AccountAnalyticTag(models.Model):
  _inherit = 'account.analytic.tag'

  cash_flow_type = fields.Selection(string="Categoria en flujo de efectivo", selection=[('debit', 'Débito'), ('credit', 'Crédito')])