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

  expense_sequence_id = fields.Many2one(comodel_name="ir.sequence", string="Secuencia numérica")
  expense_payment_journal_id = fields.Many2one(comodel_name="account.journal", string="Diario de pago")
 