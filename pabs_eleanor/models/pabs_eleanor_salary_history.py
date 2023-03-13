# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PabsEleanorSalaryHistory(models.Model):
    _name = 'pabs.eleanor.salary.history'
    _description = 'HIstórico de sueldos'
   
    period_id = fields.Many2one(comodel_name="pabs.eleanor.period", string="Periodo", required=True)
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Empleado", required=True)
    salary = fields.Float(string="Salario interno total", required=True)
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True) 

    period_type = fields.Selection([('weekly','Semanal'),('biweekly','Quincenal')], string="Tipo periodo", related='period_id.period_type')
    week_number = fields.Integer(string="Número de periodo", related='period_id.week_number')
    date_start = fields.Date(string="Fecha inicio", related='period_id.date_start')

    daily_internal_salary = fields.Float(string="Salario Interno diario", related="employee_id.daily_internal_salary")
    period_internal_salary = fields.Float(string="Salario Interno periodo", related="employee_id.period_internal_salary")

    ### Crea el histórico de sueldos del periodo seleccionado
    def create_salary_history(self, tipo_periodo, company_id):
        
        ### Buscar periodo abierto
        periodo = self.env['pabs.eleanor.period'].search([
            ('company_id', '=', company_id),
            ('period_type', '=', tipo_periodo),
            ('state', '=', 'open')
        ])

        if not periodo:
            raise ValidationError("No existe un periodo {} abierto".format(dict(self._fields['period_type'].selection).get(self.period_type)))
        
        if len(periodo) > 1:
            raise ValidationError("Existe mas de un periodo {} abierto".format(dict(self._fields['period_type'].selection).get(self.period_type)))

        ### Verificar que no existan registros en el periodo
        cant = self.search_count([
            ('company_id', '=', company_id),
            ('period_id', '=', periodo.id)
        ])

        if cant > 0:
            raise ValidationError("Ya existen {} registros en el periodo {} {}".format(cant, periodo.period_type, periodo.week_number))

        ### Consultar sueldos
        empleados = self.env['hr.employee'].search([
            ('company_id', '=', company_id),
            ('period_type', '=', periodo.period_type),
            ('employee_status.name', 'in', ['ACTIVO', 'PERMISO']),
            ('total_internal_salary', '>', 0)
        ])

        nuevos_historicos = []
        for emp in empleados:
            nuevos_historicos.append({
                'company_id': company_id,
                'period_id': periodo.id,
                'employee_id': emp.id,
                'salary': emp.total_internal_salary
            })

        ### Crear registros
        self.create(nuevos_historicos)