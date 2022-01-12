# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################

from odoo import fields, models, _, api
from odoo.exceptions import UserError

class UserProductExpense(models.Model):
  _name = 'user.product.expense'
  _rec_name='user_id'

  user_id = fields.Many2one(string="Usuario", comodel_name='res.users')  
  product_expense_ids = fields.Many2many(string='Productos permitidos', comodel_name='product.product', domain="[('can_be_expensed','=',True)]") 
  company_id = fields.Many2one('res.company', u'Compañía', readonly=True, default=lambda self: self.env.company, required=True)

  @api.model
  def create(self, vals):
    user_id = vals.get('user_id')
    product_expense_ids = self.search([('user_id','=',user_id)])
    if product_expense_ids:
      raise UserError("Ya existe un registro con el usuario especificado.")
    rec = super(UserProductExpense, self).create(vals)
    return rec
