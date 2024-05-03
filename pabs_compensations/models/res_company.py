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

  update_templates = fields.Boolean(string="Actualizar plantillas de AS") 