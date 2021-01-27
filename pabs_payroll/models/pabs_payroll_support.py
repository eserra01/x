# -*- coding: utf-8 -*-
from odoo import fields, models, api

class SupportPayroll(models.Model):
  _name = 'pabs.payroll.support'
  _description = 'Nómina para Apoyo'

  payroll_id = fields.Many2one(comodel_name='pabs.payroll',
    string='Nómina')

  employee_id = fields.Many2one(comodel_name='hr.employee',
    string='Asistente',
    required=True)

  new_entry = fields.Float(string='Apoyo Nuevo Ingreso')

  pantry_support = fields.Float(string='Apoyo para despensa')

  salary = fields.Float(string='Sueldo')

  investment_bonus = fields.Float(string='Bono por Inversión')

  warranty = fields.Float(string='Garantía')
  
  absences = fields.Float(string='Faltas')

  total = fields.Float(string='Total',
    compute="_calc_total")

  @api.onchange('new_entry','pantry_support','salary','investment_bonus','warranty','absences')
  def _calc_total(self):
    for rec in self:
      rec.total = rec.new_entry + rec.pantry_support + rec.salary + rec.investment_bonus + rec.warranty + rec.absences
    