# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################

from odoo import fields, models, _, api
from odoo.exceptions import UserError

class ProductProduct(models.Model):
  _inherit = 'product.product'

  requires_plate = fields.Boolean(string="Requiere placa") 