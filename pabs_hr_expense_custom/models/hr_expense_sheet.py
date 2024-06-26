# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################

from sre_parse import expand_template
from odoo import fields, models, _, api
from odoo.exceptions import UserError
from datetime import date

class HrExpenseSheet(models.Model):
  _inherit = 'hr.expense.sheet'

  amount_residual = fields.Float(string="Monto restante", compute='_compute_amount_resiudal')
  show_payment_button = fields.Boolean(string="Mostrar botón de pago", readonly=True)
  payments_number = fields.Integer(string="Pagos", compute='_compute_payments') 
  state_log = fields.Char(string='Log de estatus', readonly=True)

  def action_get_payments_view(self):
    payment_ids = self.env['account.payment'].search([('expense_sheet_id','=',self.id),('state','in',['posted','reconciled'])])
    ids = []
    for payment in payment_ids:
      ids.append(payment.id)
    return {
      'name': 'Pagos de gasto',
      'type': 'ir.actions.act_window',
      'view_mode': 'tree',
      'view_type': 'form',
      'res_model': 'account.payment',
      'view_id': self.env.ref('account.view_account_supplier_payment_tree').id,
      'domain': [('id','in',ids)],
    }
  
  def _compute_payments(self):
      for rec in self:
        # Buscamos los pagos del gasto
        payment_ids = self.env['account.payment'].search([('expense_sheet_id','=',rec.id),('state','in',['posted','reconciled'])])
        rec.payments_number = len(payment_ids)

  def _compute_amount_resiudal(self):
      for rec in self:
        # Buscamos los pagos del gasto
        payment_ids = self.env['account.payment'].search([('expense_sheet_id','=',rec.id),('state','in',['posted','reconciled'])])
        amount_payments = 0
        for payment in payment_ids:
          amount_payments += payment.amount          
        if rec.total_amount - amount_payments > 0.00:
          rec.show_payment_button = True
        else:
          rec.show_payment_button = False
        rec.amount_residual = rec.total_amount - amount_payments


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

  def approve_expense_sheets(self):
    # 
    if self.company_id.expense_limit == 0:
      raise UserError("No se ha definido un límite de gastos en la compañía.")
    
    # Si se superó el limite de gastos
    if self.total_amount > self.company_id.expense_limit:
      #
      allow = False
      product_user_id = self.env['user.product.expense'].search([('user_id','=',self.env.user.id)])
      if product_user_id:
        if product_user_id.approve_limit_expense:
          allow = True
      if not allow:        
        raise UserError("El límite de gastos que tiene autorizado es por $%s, el gasto solo puede ser aprobado por un usuario autorizado."%(self.company_id.expense_limit))        
    return super(HrExpenseSheet, self).approve_expense_sheets()
  
  def write(self, vals):
    # Obtenmos el status previo si el registró cambio de status
    previous_state = self.state   
    rec = super(HrExpenseSheet, self).write(vals)
    # Si el registro cambia de estatus actualizamos el campo del log
    for k in vals.keys():     
      if k == 'state':        
        states_dic = {'draft':'Borrador','submit':'Enviado','approve':'Aprobado','post':'Publicado','done':'Pagado','cancel':'Rechazado'}        
        today = date.today()    
        if previous_state:          
          if self.state_log:          
            log = str(self.state_log) + ', ' + str(states_dic[previous_state]) + '->' + str(states_dic[vals.get('state')]) + ' (' + str(today.strftime("%d/%m/%Y")) + ')'
          else:          
            log = str(states_dic[previous_state]) + '->' + str(states_dic[vals.get('state')]) + ' (' + str(today.strftime("%d/%m/%Y")) + ')'
          self.state_log = log
          break        
    return rec

class HrExpenseSheetRegisterPaymentWizard(models.TransientModel):
  _inherit = "hr.expense.sheet.register.payment.wizard"

  # Se sobreescribe el le método para tomar el diario especificado en la compañía y asignar gasto al pago
  def _get_payment_vals(self):        
      """ Hook for extension """
      # if not self.company_id.expense_payment_journal_id:
      #     raise UserError("No se ha definido un diario de gastos en la compañia.")  
      # 
      hr_expense_sheet_id = self.env['hr.expense.sheet'].browse(self.env.context.get('active_id'))
      if self.amount > hr_expense_sheet_id.amount_residual:
        raise UserError("El monto del pago no puede ser mayor a %s"%(str(hr_expense_sheet_id.amount_residual)))
      return {
          'partner_type': 'supplier',
          'payment_type': 'outbound',
          'partner_id': self.partner_id.id,
          'partner_bank_account_id': self.partner_bank_account_id.id,
          'journal_id': self.journal_id.id,            
          'company_id': self.company_id.id,
          'payment_method_id': self.payment_method_id.id,
          'expense_sheet_id':  self.env.context.get('active_id'),
          'amount': self.amount,
          'currency_id': self.currency_id.id,
          'payment_date': self.payment_date,
          'communication': self.communication,
          
          'reference': 'payment_expense', 
          'way_to_pay': 'cash'
      }
    
  def expense_post_payment(self):
    res = super(HrExpenseSheetRegisterPaymentWizard, self).expense_post_payment()
    #
    hr_expense_sheet_id = self.env['hr.expense.sheet'].browse(self.env.context.get('active_id'))
    if hr_expense_sheet_id:     
      # Si el monto del pago es mayor o igual que el monto restante del gasto
      if hr_expense_sheet_id.amount_residual <= self.amount:        
        # Se pone como pagado el gasto 
        hr_expense_sheet_id.state = 'done'
        expense_id = self.env['hr.expense'].search([('sheet_id','=',hr_expense_sheet_id.id)])
        if expense_id:
          expense_id.state = 'done'

      ### Actualizar linea de crédito con la etiqueta analítica
      if self.account_analytic_tag_required:
        payment = self.env['account.payment'].search([
          ('expense_sheet_id', '=', hr_expense_sheet_id.id)
        ])

        if not payment:
          raise UserError('No se encontró el pago ligado al reporte de gastos con id {}'.format(hr_expense_sheet_id.id))
        
        credit_lines = payment.move_line_ids.filtered(lambda x: x.credit > 0 and x.account_id.id == self.journal_id.default_debit_account_id.id)

        for line in credit_lines:
          line.write({'analytic_tag_ids': [(4, self.account_analytic_tag_id.id, 0)]})
    return res
