# -*- coding: utf-8 -*-

from odoo import fields, models, api

class PabsOffice(models.Model):
  _name = 'pabs.office'

  ### Declaración de campos
  name = fields.Char(string='Nombre de oficina',
    required=True)

  code = fields.Char(string='Código de solicitud',
    required=True)
  