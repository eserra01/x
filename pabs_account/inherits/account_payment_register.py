# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from werkzeug import url_encode

### La etiqueta analítica obligatoria para el wizard "Registrar pagos" solo aplica cuando se llama desde el formulario de reporte de gastos
class HrExpenseSheetRegisterPaymentWizard(models.TransientModel):
  _inherit = 'hr.expense.sheet.register.payment.wizard'

  account_analytic_tag_id = fields.Many2one(string="Etiqueta analítica", comodel_name='account.analytic.tag')
  account_analytic_tag_required = fields.Boolean(string="Etiqueta analítica obligatoria", compute="_calc_analytic_tag_required")

  @api.depends('journal_id')
  def _calc_analytic_tag_required(self):
    for rec in self:
      rec.account_analytic_tag_required = False

      if rec.journal_id.is_a_cash_flow_journal:
        rec.account_analytic_tag_required = True