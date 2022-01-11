# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################

from odoo import fields, models, _, api
from odoo.exceptions import UserError

class HrEmployee(models.Model):
  _inherit = 'hr.employee'

  use_expense = fields.Boolean(string="Puede usar gastos")
  expense_journal_id = fields.Many2one(string='Diario para gastos', comodel_name='account.journal')
  analytic_account_id = fields.Many2one(string='Cuenta analítica', comodel_name='account.analytic.account')
  account_analytic_tag_ids = fields.Many2many(string='Etiquetas analíticas', comodel_name='account.analytic.tag')
 