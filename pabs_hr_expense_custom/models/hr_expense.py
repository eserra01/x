# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################

from odoo import fields, models, _, api
from odoo.exceptions import UserError

class HrExpense(models.Model):
  _inherit = 'hr.expense'    

  number = fields.Char(string=u"Número", default='/', required=True, readonly=True, copy=False)

  @api.model
  def create(self, vals):
    res = super(HrExpense,self).create(vals)
    if not res.company_id.expense_sequence_id:
      raise UserError("No se ha especificado la secuencia númerica a utilizar para los gastos, por favor contacte al administrador del sistema.")
    if res.number == '/':
      res.number = res.company_id.expense_sequence_id._next()
    return res

  # 
  @api.onchange('employee_id')
  def _onchange_employee(self):
      for rec in self:
        if self.employee_id:
          if not rec.employee_id.expense_journal_id:
            raise UserError("No se ha especificado un diario de gastos para este empleado, por favor por confugure uno.")
          # Se especifica el diario en el gasto según el configurado
          rec.sheet_id.journal_id = rec.employee_id.expense_journal_id.id
          # Se especifica la cuenta analítica          
          rec.analytic_account_id = rec.employee_id.analytic_account_id.id
          #
          if rec.employee_id.account_analytic_tag_ids:
            rec.analytic_tag_ids = rec.employee_id.account_analytic_tag_ids.ids
          else:
            rec.analytic_tag_ids = False         
        else:
           # Obtenemos los productos permitidos por usuario
          rec.product_id = False
          domain = []
          product_user_id = self.env['user.product.expense'].search([('user_id','=',self.env.user.id)])
          if product_user_id:
            domain = product_user_id.product_expense_ids.ids
          return {'domain': {'product_id': [('id', 'in', domain)]}}

