# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class PabsContractComments(models.Model):
  _name = 'pabs.contract.comments'

  user_id = fields.Many2one(comodel_name='res.users',
    string='Usuario')

  date = fields.Datetime(string='Fecha y hora')

  comment = fields.Html(string='Comentario')

  contract_id = fields.Many2one(comodel_name='pabs.contract',
    string='Contrato')
