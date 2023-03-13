# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PabsEleanorInability(models.Model):
    _name = 'pabs.eleanor.inability'
    _description = 'Incapacidades'
    _rec_name = 'disease_id'
    _order = 'id desc'
    
    disease_id = fields.Many2one(comodel_name="pabs.eleanor.disease", string="Enfermedad", required=True)
    start_date = fields.Date(string="Fecha de inicio", required=True)    
    end_date = fields.Date(string="Fecha de término", required=True)    
    folio = fields.Char(string="Folio", required=True)
    attachment_name = fields.Char(string="Adjunto")
    attachment_file = fields.Binary(string="Adjunto")
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Empleado")
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,) 
