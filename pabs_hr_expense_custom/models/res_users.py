# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################

from odoo import fields, models, _, api
from odoo.exceptions import UserError

class ResUsers(models.Model):
  _inherit = 'res.users'
  
  product_expense_ids = fields.Many2many(string='Productos permitidos', comodel_name='product.product', domain="[('can_be_expensed','=',True)]")
 