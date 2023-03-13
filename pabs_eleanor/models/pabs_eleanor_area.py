# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PabsEleanorArea(models.Model):
    _name = 'pabs.eleanor.area'
    _description = 'Áreas Eleanor'

    name = fields.Char(string="Área", required=True)
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,) 
