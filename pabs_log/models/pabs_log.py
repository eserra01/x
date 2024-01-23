# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError

TOPICS = [
    ('tdc','Transferencia de cartera'),
    ('pay', 'Sincronización de pagos')
]

class PabsLog(models.Model):
    _name = 'pabs.log'
    _decription = 'Logs generales'
    _rec_name = 'topic_id'

    
    topic_id = fields.Selection(TOPICS, string="Funcionalidad", required =True)    
    detail = fields.Char(string="Detalle", required=True)
    user_id = fields.Many2one(string="Usuario", comodel_name="res.users", required =True)    
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True) 
    


