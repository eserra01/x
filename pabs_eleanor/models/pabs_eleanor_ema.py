# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PabsEleanorEma(models.Model):
    _name = 'pabs.eleanor.ema'
    _description = 'EMA'
    _rec_name = 'nss'

    nss = fields.Char(string="NSS", required=True)
    full_name = fields.Char(string="Nombre completo", required=True)    
    move_origin = fields.Char(string="Origen movimiento", required=True) 
    move_type = fields.Char(string="Tipo movimiento", required=True)
    move_date = fields.Char(string="Fecha movimiento", required=True)
    days = fields.Char(string="Días", required=True)
    salary = fields.Char(string="Salario", required=True)
    fixed_fee = fields.Char(string="Cuota fija", required=True)
    exce_boss = fields.Char(string="Exce. Patronal", required=True)
    exce_worker = fields.Char(string="Exce. Obrero", required=True)
    pres_money_boss = fields.Char(string="Pres. Dinero patronal", required=True)
    pres_money_worker = fields.Char(string="Pres. Dinero obrero", required=True)
    gmp_boss = fields.Char(string="Gmp.Patronal", required=True)
    gmp_worker = fields.Char(string="Gmp. Obrero", required=True)
    work_risk = fields.Char(string="Riesgo trabajo", required=True)
    i_boss_life = fields.Char(string="Vida patronal", required=True)
    i_worker_life = fields.Char(string="Vida obrero", required=True)
    social_benefits = fields.Char(string="Prestaciones sociales", required=True)
    total = fields.Char(string="Total", required=True)
    company = fields.Char(string="Empresa", required=True)
    period = fields.Char(string="Periodo", required=True)
    boss_register = fields.Char(string="Registro patronal", required=True)    
    ema_id = fields.Char(string="EMA id", required=True)
    branch = fields.Char(string="Plaza", required=True)
    internal_period = fields.Char(string="Periodo interno", required=True)    
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Empleado")
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True) 
