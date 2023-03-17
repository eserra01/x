# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PabsEleanorUserAccess(models.Model):
    _name = 'pabs.eleanor.user.access'
    _description = 'Permisos de acceso'
    _rec_name  = 'user_id'

    user_id = fields.Many2one(comodel_name="res.users", string="Usuario", required=True, domain=lambda self: [('company_id.id', '=', self.env.company.id)])
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", string="Oficina")
    department_id = fields.Many2one(comodel_name="hr.department", string="Departamento")
    location_type = fields.Selection([('office','Oficina'),('department','Departamento')], string="Tipo de ubicación", required=True)
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,) 

    _sql_constraints = [
        ('access_department_uniq', 'UNIQUE (user_id,department_id,company_id)',  'Ya existe un registro con el usuario y departamento seleccionados.'),
        ('access_office_uniq', 'UNIQUE (user_id,warehouse_id,company_id)',  'Ya existe un registro con el usuario y oficina seleccionados.')
    ]

