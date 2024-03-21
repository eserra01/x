# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PabsStockConfig(models.Model):
    _name = 'pabs.stock.config'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Pabs picking config"
    _order = 'config_type asc'
    _rec_name = 'company_id'

    central_location_id = fields.Many2one(string="Ubicación almacén consumibles", comodel_name='stock.location', )
    request_location_id = fields.Many2one(string="Ubicación almacén solicitudes", comodel_name='stock.location', )
    scrap_location_id = fields.Many2one(string="Ubicación de consumo", comodel_name='stock.location', )    
    transit_location_id = fields.Many2one(string="Ubicación de tránsito", comodel_name='stock.location', )      
    config_type = fields.Selection([('primary','Primaria'),('secondary','Secundaria')], required=True)    
    consumable_journal_id = fields.Many2one(string="Diario pólizas consumibles", comodel_name="account.journal")
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True)
    



