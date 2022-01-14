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