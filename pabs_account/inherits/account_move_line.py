# -*- coding: utf-8 -*-

from odoo import api, models, fields

class AccountMoveLine(models.Model):
  _inherit = 'account.move.line'

  analytic_account_required = fields.Boolean(string='¿Analítica requerida?',
    related="account_id.analytic_account_required")

  # Campos para Flujo de efectivo
  is_a_cash_flow_journal = fields.Boolean(string="El diario aplica para flujo de efectivo", related='journal_id.is_a_cash_flow_journal')
  is_a_cash_flow_account = fields.Boolean(string="La cuenta aplica para flujo de efectivo", related='account_id.cash_flow_analytic_tag_required')
  cash_flow_type = fields.Char(string="Tipo para flujo de efectivo", compute="_calc_cash_flow_type")

  @api.depends('is_a_cash_flow_journal', 'is_a_cash_flow_account', 'debit', 'credit')
  def _calc_cash_flow_type(self):
    for rec in self:
      rec.cash_flow_type = None

      if rec.is_a_cash_flow_journal and rec.is_a_cash_flow_account:
        if rec.debit:
          rec.cash_flow_type = 'debit'
        elif rec.credit:
          rec.cash_flow_type = 'credit'