# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'    

    eleanor_id = fields.Integer(string="Id de Eleanor")
    birth_place = fields.Many2one(comodel_name="res.country.state", string="Lugar de nacimiento", domain="[('country_id','=',156)]", tracking=True)
    fathers_name = fields.Char(string="Nombre completo del padre", tracking=True)
    mothers_name = fields.Char(string="Nombre completo de la madre", tracking=True)
    infonavit_credit = fields.Char(string="INFONAVIT", tracking=True)
    pabs_eleanor_area_id = fields.Many2one(comodel_name="pabs.eleanor.area", string="Área", compute='_calc_area')
    boss = fields.Char(string="Patrón", tracking=True)
    total_internal_salary = fields.Float(string="Salario Interno total", tracking=True)
    daily_internal_salary = fields.Float(string="Salario Interno diario", compute="_calc_daily_internal_salary")
    period_internal_salary = fields.Float(string="Salario Interno periodo", compute="_calc_period_internal_salary")
    daily_salary = fields.Float(string="Salario diario", tracking=True)
    integrated_daily_salary = fields.Float(string="Salario diario integrado", tracking=True)
    personal_file_name = fields.Char(string="Expediente", tracking=True)
    personal_file_file = fields.Binary(string="Expediente")  
    constancy_up_name = fields.Char(string="Constancia de alta", tracking=True)
    constancy_up_file = fields.Binary(string="Constancia de alta")
    infonavit_credit_amortization = fields.Selection(
        [('vsm','Veces salario'),('fd','Factor de descuento'),('cf','Cuota fija')], 
        string="Amortización crédito INFONAVIT", tracking=True)
    discount_value = fields.Float(string="Valor descuento", tracking=True)
    interest_conflict = fields.Char(string="Conflicto de interés", tracking=True)
    relationship = fields.Char(string="Parentesco", tracking=True)
    period_type = fields.Selection(
        [('weekly','Semanal'),('biweekly','Quincenal')], 
        string="Tipo de periodo", tracking=True)
    way_to_pay = fields.Selection(
        [('rif','RIF'),('resico','RESICO'),('salary','Asalariado'),('none','Ninguno')], 
        string="Forma de pago", tracking=True)
    status_log_ids = fields.One2many(comodel_name='pabs.eleanor.status.log', inverse_name='employee_id')
    inability_ids = fields.One2many(comodel_name='pabs.eleanor.inability', inverse_name='employee_id')
    ema_ids = fields.One2many(comodel_name='pabs.eleanor.ema', inverse_name='employee_id')
    eba_ids = fields.One2many(comodel_name='pabs.eleanor.eba', inverse_name='employee_id')

    def _calc_area(self):
        for rec in self:
            area_obj = self.env['pabs.eleanor.area']

            if rec.warehouse_id or rec.department_id.name == "VENTAS":
                rec.pabs_eleanor_area_id = area_obj.search([
                    ('company_id', '=', rec.company_id.id),
                    ('name', '=', 'ASISTENCIA SOCIAL')
                ])
            else:
                rec.pabs_eleanor_area_id = rec.department_id.pabs_eleanor_area_id.id

    def _calc_daily_internal_salary(self):
        for rec in self:
            if rec.total_internal_salary:
                rec.daily_internal_salary = round(rec.total_internal_salary / float(30), 2)
            else:
                rec.daily_internal_salary = 0

    def _calc_period_internal_salary(self):
        for rec in self:
            if rec.total_internal_salary and rec.period_type:
                if rec.period_type == "weekly":
                    rec.period_internal_salary = round(rec.total_internal_salary / float(30) * float(7), 2)
                elif rec.period_type == "biweekly":
                    rec.period_internal_salary = round(rec.total_internal_salary / float(30) * float(15), 2)
                else:
                    rec.period_internal_salary = 0
            else:
                rec.period_internal_salary = 0