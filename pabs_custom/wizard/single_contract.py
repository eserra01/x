# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class SingleContract(models.TransientModel):
  _name = 'pabs.single.contract'
  _description = 'Consulta de contratos'

  name = fields.Char(string='Busqueda',
    required=True)

  contract_ids = fields.Many2many(comodel_name='pabs.contract',
    relation="_contracts_search",
    column1="single_id",
    column2="contract_id",
    string='Contratos encontrados')

