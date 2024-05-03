# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError

class PabsOfficeManager(models.Model):
    _name = 'pabs.office.manager'
    _decription = 'Gerentes de oficina PABS'  
    _inherit = 'mail.thread'      
    
    warehouse_id = fields.Many2one(string="Oficina", comodel_name="stock.warehouse", required =True,tracking=True)       
    employee_id = fields.Many2one(string="Empleado", comodel_name="hr.employee", required =True,tracking=True,)      
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,tracking=True) 

    _sql_constraints = [(
    'unique_office_manager',
    'UNIQUE(warehouse_id, employee_id,company_id)',
    'No se puede crear el registro: ya existe una combinación de Gerente y oficina.'
  )]