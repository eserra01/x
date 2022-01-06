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

  account_ids = fields.Many2many(comodel_name="account.account", string="Cuentas permitidas")
 