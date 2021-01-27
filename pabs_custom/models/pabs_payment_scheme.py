# -*- coding: utf-8 -*-

from odoo import fields, models, api

class PABSPaymentScheme(models.Model):
  _name = 'pabs.payment.scheme'
  _description = 'Esquemas de Pago'

  ### Declaración de campos
  name = fields.Char(string='Esquema de Pago',
    required=True)

  description = fields.Text(string='Descripción del esquema')

  allow_all = fields.Boolean(string='¿Es un esquema de sueldo?')
  