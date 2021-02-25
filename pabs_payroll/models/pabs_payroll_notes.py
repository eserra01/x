# -*- coding: utf-8 -*-
from odoo import fields, models, api

class PabsPayrollNotes(models.Model):
  _name = 'pabs.payroll.notes'
  _description = 'Notas de incidencias de nómina'

  payroll_id = fields.Many2one(comodel_name='pabs.payroll',
    string='Nómina')

  description = fields.Html(string='Notas(Asuntos extraordinarios)',
    required=True)

  employee_id = fields.Many2one(comodel_name='hr.employee',
    required=True,
    string='Empleado')
