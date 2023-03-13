# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PabsEleanorEba(models.Model):
    _name = 'pabs.eleanor.eba'
    _description = 'EBA'
    _rec_name = 'nss'

    nss = fields.Char(string="NSS", required=True)
    full_name = fields.Char(string="Nombre completo", required=True)
    move_origin = fields.Char(string="Origen movimiento", required=True) 
    move_type = fields.Char(string="Tipo movimiento", required=True)
    move_date = fields.Char(string="Fecha movimiento", required=True)
    days = fields.Char(string="Días", required=True)
    salary = fields.Char(string="Salario", required=True)
    withdrawal = fields.Char(string="Retiro", required=True)
    ceav_boss = fields.Char(string="CEAV Patronal", required=True)
    ceav_worker = fields.Char(string="CEAV Obrero", required=True)
    rcv = fields.Char(string="RCV", required=True)
    boss_input = fields.Char(string="Aportación patronal", required=True)
    discount_type = fields.Char(string="Tipo descuento", required=True)
    discount_value = fields.Char(string="Valor descuento", required=True)
    credit_number = fields.Char(string="Número crédito", required=True)
    amortization = fields.Char(string="Amortización", required=True)
    infonavit = fields.Char(string="No. Crédito INFONAVIT", required=True)    
    total = fields.Char(string="Total", required=True)
    company = fields.Char(string="Empresa", required=True)
    period = fields.Char(string="Periodo", required=True)
    boss_register = fields.Char(string="Registro patronal", required=True)
    eba_id = fields.Char(string="EBA id", required=True)
    branch = fields.Char(string="Plaza", required=True)
    internal_period = fields.Char(string="Periodo interno", required=True)            
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Empleado", required=True)
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,) 
