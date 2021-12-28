# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################

from odoo import fields, models, _, api
from odoo.exceptions import UserError

class ResCompany(models.Model):
  _inherit = 'res.company'

  expense_journal_id = fields.Many2one(string='Diario para gastos', comodel_name='account.journal')
  account_ids = fields.Many2many(comodel_name="account.account", string="Cuenta permitidas")
 