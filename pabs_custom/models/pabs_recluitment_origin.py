# -*- coding: utf-8 -*-

from odoo import fields, models, api

class PABSRecluitmentOrigin(models.Model):
  _name = 'pabs.recluitment.origin'
  _description = 'Origen de reclutamiento'

  ### Declaración de campos
  name = fields.Char(string='Nombre del Origen',
    required=True)

  description = fields.Text(string='Descripción del origen')
  