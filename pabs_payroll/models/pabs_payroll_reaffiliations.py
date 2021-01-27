# -*- coding: utf-8 -*-
from odoo import fields, models, api

class PabsPayrollReaffiliations(models.Model):
  _name = 'pabs.payroll.reaffiliations'
  _description = 'Reafiliaciones en la nómina'

  payroll_id = fields.Many2one(comodel_name='pabs.payroll',
    string='Nómina')

  last_contract_id = fields.Many2one(comodel_name='pabs.contract',
    string='Contrato anterior')

  contract_id = fields.Many2one(comodel_name='pabs.contract',
    string='Contrato Nuevo',
    required=True)

  partner_name = fields.Char(string='Nombre del cliente')

  employee_id = fields.Many2one(comodel_name='hr.employee',
    string='Asistente',
    required=True)

  amount = fields.Float(string='Monto',
    required=True)

  number_reaffiliations = fields.Integer(string='Reafiliaciones semanales')
  
  @api.onchange('contract_id')
  def calc_partner_name(self):
    for rec in self:
      if rec.contract_id:
        rec.partner_name = rec.contract_id.full_name
