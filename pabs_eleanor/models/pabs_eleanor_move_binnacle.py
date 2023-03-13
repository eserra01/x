# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PabsEleanorMoveBinnacle(models.Model):
    _name = 'pabs.eleanor.move.binnacle'
    _description = 'Bitácora de movimientos' 

           
    period_id = fields.Many2one(comodel_name="pabs.eleanor.period", string="Periodo", required=True, readonly=True )
    period_type = fields.Selection([('weekly','Semanal'),('biweekly','Quincenal')], string="Tipo periodo", related='period_id.period_type', readonly=True)
    state = fields.Selection([('open','Abierto'),('close','Cerrado')], string="Estatus", related='period_id.state', readonly=True)
    move_type = fields.Selection([('perception','Percepcion'),('deduction','Deducción')], string="Tipo movimiento", required=True, readonly=True)
    concept_id = fields.Many2one(comodel_name="pabs.eleanor.concept", string="Concepto", required=True, readonly=True)
    concept_type = fields.Selection([('perception','Percepcion'),('deduction','Deducción')], string="Tipo concepto", related='concept_id.concept_type', readonly=True)
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Empleado", required=True, readonly=True)
    area_id = fields.Many2one(comodel_name="pabs.eleanor.area", string="Área", required=True, readonly=True)
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", string="Oficina", readonly=True )
    department_id = fields.Many2one(comodel_name="hr.department", string="Departamento", readonly=True)
    job_id = fields.Many2one(comodel_name="hr.job", string="Puesto", required=True, readonly=True )
    amount = fields.Float(string="Importe", readonly=True)
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True, readonly=True) 
    action_type = fields.Selection([('create','Creación'),('edit','Edición'),('delete','Eliminación')], string="Tipo acción", required=True, readonly=True)
    mode = fields.Selection([('form','Formulario'),('masive','Carga masiva')], string="Modo", required=True, readonly=True)
    user_id = fields.Many2one(comodel_name="res.users", string="Usuario", required=True, readonly=True )

       



   



