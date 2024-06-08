# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError

class PabsChangesFormatOperation(models.Model):
  _name = 'pabs.changes.format.operation'  
  _description = 'Operaciones de cambio de formato'
  _order = 'name asc'  

  name = fields.Char(string="Nombre", required=True )    
  code = fields.Char(string="Código", required=True)
  active = fields.Boolean(string="Activo")
  company_id = fields.Many2one(comodel_name='res.company', string='Compañia', required=True, default=lambda s: s.env.company.id,tracking=True)
