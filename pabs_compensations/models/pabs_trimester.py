# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError

class PabsTrimester(models.Model):
    _name = 'pabs.trimester'
    _decription = 'Trimestres PABS'  
    
    name = fields.Char("Trimestre",readonly=True)
    month = fields.Integer(string="Mes en que se evalua",readonly=True)
    first_month = fields.Integer(string="Primer mes",readonly=True)
    last_month = fields.Integer(string="Último mes",readonly=True)
    last_done_date = fields.Datetime(string="Última evaluación",readonly=True)
    done = fields.Boolean(string="Evaluado",readonly=True)    
