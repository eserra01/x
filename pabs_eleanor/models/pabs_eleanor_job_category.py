# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PabsEleanorJobCategory(models.Model):
    _name = 'pabs.eleanor.job.category'
    _description = 'Categorías de cargos'    

    name = fields.Char(string="Categoría", required=True)
    identifier = fields.Char(string="Identificador")
    dependence = fields.Char(string="Dependencia")
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,)