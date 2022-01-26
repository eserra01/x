# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class OutputPaymentWizard(models.TransientModel):
  _name = 'output.payment.wizard'
  _description = 'Salidas de comisiones'
  
  def _get_domain(self):
    payments_ids = self.env['account.payment'].search([('contract','=',self.env.context.get('active_id'))],order= 'create_date desc')   
    payments = []
    for payment in payments_ids:
      payments.append(payment.id)   
    return "[('id','in',[" + ','.join(map(str, list(payments))) + "])]"    

  payment_id = fields.Many2one(string="Pago", comodel_name="account.payment", domain=_get_domain)  
  comission_output_ids = fields.One2many(comodel_name="pabs.comission.output", inverse_name="payment_id", string="Salidas de comisiones", readonly=True)

  @api.onchange('payment_id')
  def _onchange_payment_id(self):
        res = {}
        if self.payment_id:
          output_ids = self.env['pabs.comission.output'].search([('payment_id','=',self.payment_id.id)])
          outputs = []
          for output in output_ids:
            outputs.append(output.id)
          self.comission_output_ids = [(6, 0, outputs)]
        return res

