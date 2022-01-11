# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################

from odoo import fields, models, _, api
from odoo.exceptions import UserError

class HrExpenseSheet(models.Model):
  _inherit = 'hr.expense.sheet'

  def action_sheet_move_create(self):
    if self.employee_id.expense_journal_id:
      self.journal_id = self.employee_id.expense_journal_id.id
    else:
      raise UserError("No se ha definido un diario de gastos para el empleado seleccionado.")    
    res = super(HrExpenseSheet,self).action_sheet_move_create()
    # Se modifican las cuentas de la póliza de provisión
    account_move_line_ids = self.env['account.move.line'].search([('move_id','=',self.account_move_id.id)])
    for aml in account_move_line_ids:
      if aml.debit == 0:
        aml.account_id = self.employee_id.expense_journal_id.default_debit_account_id.id  
    return res

  # def action_submit_sheet(self):
  #   if self.env.user.expense_limit == 0:
  #     raise UserError("No se ha definido un límite de gastos en el usuario.")    
  #   if self.total_amount > self.env.user.expense_limit:
  #     raise UserError("El límite de gastos que tiene autorizado es por $%s"%(self.env.user.expense_limit))    
  #   res = super(HrExpenseSheet,self).action_submit_sheet()
  #   return res

class HrExpenseSheetRegisterPaymentWizard(models.TransientModel):
    _inherit = "hr.expense.sheet.register.payment.wizard"

    # Se sobreescribe el le método para tomar el diario especificado en la compañía
    def _get_payment_vals(self):        
        """ Hook for extension """
        if not self.company_id.expense_payment_journal_id:
           raise UserError("No se ha definido un diario de gastos en la compañia.")  
        return {
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'partner_id': self.partner_id.id,
            'partner_bank_account_id': self.partner_bank_account_id.id,
            'journal_id': self.company_id.expense_payment_journal_id.id,
            'company_id': self.company_id.id,
            'payment_method_id': self.payment_method_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication
        }
