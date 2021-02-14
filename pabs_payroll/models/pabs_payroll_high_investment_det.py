# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.addons.pabs_payroll.models.pabs_payroll_high_investment import VALUES

class PabsPayrollHighInvestmentDet(models.Model):
  _name = 'pabs.payroll.high.investment.det'
  _description = 'Inversión Alta Detalle Cobranza'

  payroll_id = fields.Many2one(comodel_name='pabs.payroll.collection',
    string='Nómina')

  contract_id = fields.Many2one(comodel_name='pabs.contract',
    string='Contrato',
    required=True)

  employee_id = fields.Many2one(comodel_name='hr.employee',
    string='Promotor')

  contract_date = fields.Date(string='Fecha de contrato')

  high_investment = fields.Float(string='Inv Alta',
    required=True)

  high_investment_bonus = fields.Float(string='Bono A.S',
    required=True)

  @api.onchange('contract_id')
  def get_contract_info(self):
    for rec in self:
      if rec.contract_id:
        rec.employee_id = rec.contract_id.employee_id.id
        rec.contract_date = rec.contract_id.invoice_date
        rec.high_investment = rec.contract_id.initial_investment