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

  date_of_admission = fields.Date(string='Fecha de ingreso',
    related='employee_id.date_of_admission')

  payment_scheme = fields.Many2one(comodel_name='pabs.payment.scheme',
    string='Esquema de pago',
    related='employee_id.payment_scheme')

  productivity_bonus = fields.Float(string='Afiliaciones bono por productividad')

  five_hundred_support = fields.Float(string='Apoyo de $500')

  permanence_bonus = fields.Float(string='Bono por permanencia')
