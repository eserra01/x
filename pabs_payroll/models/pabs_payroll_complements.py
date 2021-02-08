# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError

class PabsPayrollComplements(models.Model):
  _name = 'pabs.payroll.complements'
  _description = 'Complementos de nómina'

  payroll_id = fields.Many2one(comodel_name='pabs.payroll.collection',
    string='Nómina')

  contract_id = fields.Many2one(comodel_name='pabs.contract',
    string='Contrato',
    required=True)

  date_contract = fields.Date(string='Fecha de contrato',
    related='contract_id.invoice_date')

  partner_name = fields.Char(string='Cliente',
    compute="_get_contract_info")

  employee_id = fields.Many2one(comodel_name='hr.employee',
    string='Promotor',
    required=True)

  initial_investment = fields.Float(string='Inv. Inicial',
    required=True)

  complement = fields.Float(string='Complemento')

  apply_amount = fields.Float(string='Importe a aplicar',
    required=True)

  amount_bonus = fields.Float(string='Bono A.S')

  comment = fields.Text(string='Observaciones')

  @api.onchange('contract_id')
  def _get_contract_info(self):
    for rec in self:
      if rec.contract_id:
        rec.partner_name = rec.contract_id.full_name
        rec.employee_id = rec.contract_id.employee_id.id
        rec.initial_investment = rec.contract_id.initial_investment

  @api.onchange('employee_id')
  def _calc_contract_domain(self):
    for rec in self:
      domain = [('state','=','contract')]
      if rec.employee_id:
        domain.append(('employee_id','=',rec.employee_id.id))
      return {
        'domain' : {
          'contract_id' : domain
        }
      }
