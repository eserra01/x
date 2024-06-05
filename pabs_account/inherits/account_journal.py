# -*- coding: utf-8 -*-
from odoo import api, fields, models

class AccountJournal(models.Model):
  _inherit = 'account.journal'

  is_a_cash_flow_journal = fields.Boolean(string='Diario para flujo de efectivo')