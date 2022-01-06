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
    #
    expense_id = self.env['hr.expense'].search([('sheet_id','=',self.id)])
    if expense_id:
      if expense_id.account_id not in self.env.company.account_ids:
        raise UserError("La cuenta seleccionada no está permitida, seleccione otra en su lugar.")  
    res = super(HrExpenseSheet,self).action_sheet_move_create()
    return res

  def action_submit_sheet(self):
    if self.env.user.expense_limit == 0:
      raise UserError("No se ha definido un límite de gastos en el usuario.")    
    if self.total_amount > self.env.user.expense_limit:
      raise UserError("El límite de gastos que tiene autorizado es por $%s"%(self.env.user.expense_limit))    
    res = super(HrExpenseSheet,self).action_submit_sheet()
    return res

# class HrExpense(models.Model):
#   _inherit = 'hr.expense'    

#   def action_view_sheet(self):
          
#     res = super(HrExpense,self).action_view_sheet()
#     return res
