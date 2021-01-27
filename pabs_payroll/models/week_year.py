# -*- coding: utf-8 -*-
from odoo import fields, models, api

class Year(models.Model):
  _name = 'week.year'
  _description = 'Configuración de Año para la configuración de semanas'

  name = fields.Char(string='Año',
    required=True)
  