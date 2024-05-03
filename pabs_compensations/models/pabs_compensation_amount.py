# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError
from . import selections

class PabsCompensationAmount(models.Model):
    _name = 'pabs.compensation.amount'
    _decription = 'Montos de compesaciones PABS'  
    _inherit = 'mail.thread'  
    _rec_name = 'type'   
    
    min_production = fields.Integer(string="Producción mínima",tracking=True,default=1,)
    max_production = fields.Integer(string="Producción máxima",tracking=True,default=1,)
    amount = fields.Float(string="Monto",tracking=True)
    type = fields.Selection(selections.TYPES, string="Tipo", required =True,tracking=True)
    compensation_type = fields.Selection(selections.COMPENSATIONS, string="Tipo compensación", required =True,tracking=True)
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,tracking=True) 
