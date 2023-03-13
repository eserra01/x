# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PabsEleanorConceptCategory(models.Model):
    _name = 'pabs.eleanor.concept.category'
    _description = 'Categorías de conceptos'    

    name = fields.Char(string="Categoría", required=True)
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,) 

