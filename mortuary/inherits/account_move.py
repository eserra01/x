# -*- coding: utf-8 -*-

from odoo import api, fields, models

class AccountMove(models.Model):
  _inherit = 'account.move'

  recibo = fields.Char(string="Número de recibo")
  create_person_id = fields.Many2one(comodel_name='invoice.create.person',string='Persona que crea', tracking=True)