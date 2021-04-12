# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError

VALUES = {
  '500' : 150,
  '1000' : 250,
}

class PabsPayrollHighInvestment(models.Model):
  _name = 'pabs.payroll.high.investment'
  _description = 'Inversión Alta Asistentes'

  payroll_id = fields.Many2one(comodel_name='pabs.payroll',
    string='Nómina')
  
  employee_id = fields.Many2one(comodel_name='hr.employee',
    string='Asistente',
    required=True)

  five_hundred_investment =  fields.Integer(string='Inversión $500')

  one_thousand_investment = fields.Integer(string='Inversión $1000')

  five_hundred_bonus = fields.Float(string='Bono 500',
    compute="_compute_bonus")

  one_thousand_bonus = fields.Float(string='Bono 1000',
    compute="_compute_bonus")

  total = fields.Float(string='Total',
    compute="_calc_total")

  @api.onchange('five_hundred_investment','one_thousand_investment')
  def _compute_bonus(self):
    for rec in self:
      if rec.five_hundred_investment > 0:
        rec.five_hundred_bonus = float(rec.five_hundred_investment * VALUES['500'])
      else:
        rec.five_hundred_bonus = 0
      if rec.one_thousand_investment > 0:
        rec.one_thousand_bonus = float(rec.one_thousand_investment * VALUES['1000'])
      else:
        rec.one_thousand_bonus = 0

  @api.depends('five_hundred_bonus','one_thousand_bonus')
  def _calc_total(self):
    for rec in self:
      rec.total = rec.five_hundred_bonus + rec.one_thousand_bonus