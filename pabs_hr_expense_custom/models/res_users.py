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

  expense_limit = fields.Float(string='Límite de gastos', help="Determina el límite que un usuario puede solicitar en gastos.")
 