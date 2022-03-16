# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################

from odoo import fields, models, _, api
from odoo.exceptions import UserError

class AccountPayment(models.Model):
  _inherit = 'account.payment'

  expense_sheet_id = fields.Many2one(comodel_name="hr.expense.sheet", string="Gasto")

  
  def cancel(self):    
    res = super(AccountPayment, self).cancel()
    # Si el pago está sociado a un gasto
    if self.expense_sheet_id:
      # Si el monto del pago es mayor o igual al gasto
      if self.amount >= self.expense_sheet_id.total_amount:
        # Se cancela el gasto
        self.expense_sheet_id.state = 'cancel'
        expense_id = self.env['hr.expense'].search([('sheet_id','=',self.expense_sheet_id.id)])
        if expense_id:
          expense_id.state = 'refused'
    return res
      