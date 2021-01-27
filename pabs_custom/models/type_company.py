# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TypeCompany(models.Model):
  _name = 'type.company'

  name = fields.Char(string='Nombre de la compañia',
    required=True)

  code = fields.Char(string='Código',
    required=True,
    size=2)
  