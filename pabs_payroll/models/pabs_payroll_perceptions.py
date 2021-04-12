# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError

class PabsPayrollConcentrated(models.Model):
  _name = 'pabs.payroll.perceptions'
  _description = 'Percepciones de nómina'

  payroll_id = fields.Many2one(comodel_name='pabs.payroll.management',
    string='Nómina')

  employee_id = fields.Many2one(comodel_name='hr.employee',
    string='Empleado',
    required=True)

  job_id = fields.Many2one(comodel_name='hr.job',
    related="employee_id.job_id",
    string='Puesto Laboral')

  scheme_id = fields.Many2one(comodel_name="pabs.payment.scheme",
    related="employee_id.payment_scheme",
    string='Esquema')

  salary = fields.Float(string='Sueldo')

  seventh_day = fields.Float(string='Septimo Día')

  extra = fields.Float(sting='Horas Extra')

  fest_day = fields.Float(string='Día Festivo')

  commission = fields.Float(string='Comisión')

  retroactive = fields.Float(string='Retroactivo')

  waranty_commission = fields.Float(string='Comision Garantía')

  support_training = fields.Float(string='Apoyo Capacitación')

  bond_tip_sale = fields.Float(string='Bono Tip de Venta')

  salary_assistant = fields.Float(string='Sueldo Asistencia')

  support_period = fields.Float(string='Periodo de Apoyo')

  gratification = fields.Float(string='Gratificación')

  referral_bonus = fields.Float(string='Bono por recomendar')

  inv_investment = fields.Float(string='Bono inv inicial alta')

  effective_bonus = fields.Float(string='Bono por efectividad')

  sunday_premium = fields.Float(string='Prima dominical')

  vacation_pay = fields.Float(string='Prima vacacional')

  productivity_bonus = fields.Float(string='Bono productividad')

  fuel_support = fields.Float(string='Apoyo de gasolina')

  rif_support = fields.Float(string='Apoyo RIF')

  monthly_bouns = fields.Float(string='Bono mensual')

  food_allowances = fields.Float(string='Vales de despensa')

  loan = fields.Float(string='Prestamo Caja de Ahorro')

  loan_company = fields.Float(string='Prestamo empresa')

  change = fields.Float(string='Apoyo cambio de plaza')

  total = fields.Float(String='Total percepciones',
    compute="_calc_total")

  @api.onchange('salary','seventh_day','extra','fest_day','commission'
    'retroactive','waranty_commission','support_training','bond_tip_sale',
    'salary_assistant','support_period','gratification','referral_bonus',
    'inv_investment','effective_bonus','sunday_premium','vacation_pay',
    'productivity_bonus','fuel_support','rif_support','monthly_bouns','food_allowances',
    'loan','change')
  def _calc_total(self):
    for rec in self:
      total = rec.salary + rec.seventh_day + rec.extra + \
      rec.fest_day + rec.commission + rec.retroactive + rec.waranty_commission + \
      rec.support_training + rec.bond_tip_sale + rec.salary_assistant + rec.support_period + \
      rec.gratification + rec.referral_bonus + rec.inv_investment + rec.effective_bonus + \
      rec.sunday_premium + rec.vacation_pay + rec.productivity_bonus + rec.fuel_support + \
      rec.rif_support + rec.monthly_bouns + rec.food_allowances + rec.loan + rec.change
      rec.total = total