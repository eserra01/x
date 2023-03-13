# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PabsEleanorDisease(models.Model):
    _name = 'pabs.eleanor.disease'
    _description = 'Enfermedades'

    name = fields.Char(string="Enfermedad", required=True)
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,) 
