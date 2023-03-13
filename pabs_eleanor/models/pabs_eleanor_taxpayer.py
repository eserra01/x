# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PabsEleanorTaxpayer(models.Model):
    _name = 'pabs.eleanor.taxpayer'
    _description = 'Contribuyente'
    _rec_name = 'taxpayer'

    taxpayer = fields.Char(string="Contribuyente", required=True)
    rfc = fields.Char(string="RFC", required=True)
    curp = fields.Char(string="CURP", required=True)
    address = fields.Char(string="Domicilio", required=True)
    imss_class = fields.Char(string="Clasificación IMSS", required=True)
    boss_register = fields.Char(string="Registro patronal", required=True)
    register_date = fields.Char(string="Fecha registro", required=True)        
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,) 
