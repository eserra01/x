# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError

class PABSPayrollDeductions(models.Model):
  _name = 'pabs.payroll.deductions'
  _description = 'Deducciones de Nómina'

  payroll_id = fields.Many2one(comodel_name='pabs.payroll.management',
    string='Nómina')

  employee_id = fields.Many2one(comodel_name='hr.employee',
    string='Empleado')

  imss = fields.Float(string='IMSS')

  discount_tip_sale = fields.Float(string='Descuento por tip de venta')

  saving_bank = fields.Float(string='Caja de ahorro')

  sparkasse_loan = fields.Float(string='Prestamo caja de ahorro')

  probenso_loan = fields.Float(string='Prestamo PROBENSO')

  company_loan = fields.Float(string='Prestamo empresa')

  saving_fund = fields.Float(string='Fondo de ahorro')

  infonavit = fields.Float(string='INFONAVIT')

  funeral_package = fields.Float(string='Paquete Funerario')

  anticipated_sales_comission = fields.Float(string='Comisiones anticipadas')

  total = fields.Float(string='Total',
    compute="_calc_total")

  @api.onchange('imss','discount_tip_sale','saving_bank',
    'sparkasse_loan','probenso_loan','company_loan',
    'saving_fund','infonavit','funeral_package','anticipated_sales_comission')
  def _calc_total(self):
    for rec in self:
      total = rec.imss + rec.discount_tip_sale + rec.saving_bank + \
      rec.sparkasse_loan + rec.probenso_loan + rec.company_loan + \
      rec.saving_fund + rec.infonavit + rec.funeral_package + rec.anticipated_sales_comission
      rec.total = total
