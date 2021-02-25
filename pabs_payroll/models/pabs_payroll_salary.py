# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError

class PabsPayrollSalary(models.Model):
  _name = 'pabs.payroll.salary'

  payroll_id = fields.Many2one(comodel_name='pabs.payroll.collection',
    string='Nómina')

  employee_id = fields.Many2one(comodel_name='hr.employee',
    string='Asistente Social')

  contract1_id = fields.Many2one(comodel_name='pabs.contract',
    string='Contrato 1',
    required=True)

  contract2_id = fields.Many2one(comodel_name='pabs.contract',
    string='Contrato 2')

  salary = fields.Float(string='Sueldo',
    compute='_calc_salary')

  @api.onchange('contract1_id','contract2_id')
  def _calc_salary(self):
    for rec in self:
      salary = 0
      if rec.contract1_id:
        salary+=550
      if rec.contract2_id:
        salary+=550
      rec.salary = salary