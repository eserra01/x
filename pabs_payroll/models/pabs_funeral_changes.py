# -*- coding: utf-8 -*-
from odoo import fields, models, api

class PabsFuneralChanges(models.Model):
  _name = 'pabs.funeral.changes'
  _description = 'Cambios de Funeraria'

  payroll_id = fields.Many2one(comodel_name='pabs.payroll',
    string='Nómina')

  contract_id = fields.Many2one(comodel_name='pabs.contract',
    string='Contrato Nuevo')

  partner_name = fields.Char(string='Nombre del cliente')

  employee_id = fields.Many2one(comodel_name='hr.employee',
    string='Nombre de A.S')

  amount = fields.Float(string='Monto')

  funeral_changes = fields.Integer(string='Total de cambios de funeraria',
    default=1)
  