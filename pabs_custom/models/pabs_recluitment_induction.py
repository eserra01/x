# -*- coding: utf-8 -*-

from odoo import fields, models, api

class PABSInductions(models.Model):
  _name = 'pabs.recluitment.induction'
  _description = 'Inducciones Impartidas Por'

  ### Declaración de campos
  name = fields.Char(string='Inducción Impartida Por',
    required=True)  
