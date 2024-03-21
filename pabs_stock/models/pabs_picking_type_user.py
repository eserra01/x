# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PabsPickingTypeUser(models.Model):
    _name = 'pabs.picking.type.user'
    _decription = 'Pernisos de usaurios para operaciones'

    user_id = fields.Many2one(string="Usuario", comodel_name="res.users", required =True)
    going = fields.Boolean(string="Peticiones a AG")
    ret = fields.Boolean(string="Retornos a AG")
    request = fields.Boolean(string="Solicitudes a AG")
    consumption = fields.Boolean(string="Consumos")
    adjust = fields.Boolean(string="Ajuste de consumibles")
    adjust2 = fields.Boolean(string="Ajuste de urnas y ataúdes")
    internal = fields.Boolean(string="Trapasos internos")
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True) 
    
    _sql_constraints = [
    ('user_id', 'unique (user_id)', 'Ya existe un registro para este usuario.'),]


