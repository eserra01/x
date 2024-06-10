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
  
  ### Override de todo el método
  def _get_payment_vals(self):
    ### Actualizar diccionario "vals" del pago con los valores que no se encuentran en el formulario
    """ Hook for extension """

    return {
      'partner_type': 'supplier',
      'payment_type': 'outbound',
      'partner_id': self.partner_id.id,
      'partner_bank_account_id': self.partner_bank_account_id.id,
      'journal_id': self.journal_id.id,
      'company_id': self.company_id.id,
      'payment_method_id': self.payment_method_id.id,
      'amount': self.amount,
      'currency_id': self.currency_id.id,
      'payment_date': self.payment_date,
      'communication': self.communication,
      
      ### Añadido al método original
      'reference': 'payment_expense', 
      'way_to_pay': 'cash'
    }
  
  ### Override de todo el método
  def expense_post_payment(self):
    self.ensure_one()
    company = self.company_id
    self = self.with_context(force_company=company.id, company_id=company.id)
    context = dict(self._context or {})
    active_ids = context.get('active_ids', [])
    expense_sheet = self.env['hr.expense.sheet'].browse(active_ids)

    # Create payment and post it
    payment = self.env['account.payment'].create(self._get_payment_vals())
    payment.post()

    ### Añadido al método original: Actualizar linea de crédito con la etiqueta analítica
    if self.account_analytic_tag_required:
      credit_lines = payment.move_line_ids.filtered(lambda x: x.credit > 0 and x.account_id.id == self.journal_id.default_credit_account_id.id)

      for line in credit_lines:
        line.write({'analytic_tag_ids': [(4, self.account_analytic_tag_id.id, 0)]})

    # Log the payment in the chatter
    body = (_("A payment of %s %s with the reference <a href='/mail/view?%s'>%s</a> related to your expense %s has been made.") % (payment.amount, payment.currency_id.symbol, url_encode({'model': 'account.payment', 'res_id': payment.id}), payment.name, expense_sheet.name))
    expense_sheet.message_post(body=body)

    # Reconcile the payment and the expense, i.e. lookup on the payable account move lines
    account_move_lines_to_reconcile = self._prepare_lines_to_reconcile(payment.move_line_ids + expense_sheet.account_move_id.line_ids)
    account_move_lines_to_reconcile.reconcile()

    return {'type': 'ir.actions.act_window_close'}