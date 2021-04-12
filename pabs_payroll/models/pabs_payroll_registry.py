# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.addons.pabs_payroll.models.pabs_payroll import WEEK, STATES

class PabsPayrollRegistry(models.Model):
  _name = 'pabs.payroll.registry'

  week_number = fields.Selection(selection=WEEK,
    string='Semana',
    required=True)

  warehouse_id = fields.Many2one(comodel_name='stock.warehouse',
    string='Oficina de Venta',
    required=True)

  payroll_id = fields.Many2one(comodel_name='pabs.payroll',
    string='Nómina Secretaria')

  secretary = fields.Boolean(string='Secretaria',
    compute="_calc_payrolls")

  payroll_contract_id = fields.Many2one(comodel_name='pabs.payroll.contract',
    string='Nómina Contratos')

  contract = fields.Boolean(string='Contratos',
    compute="_calc_payrolls")

  payroll_collection_id = fields.Many2one(comodel_name='pabs.payroll.collection',
    string='Nómina Cobranza')

  collection = fields.Boolean(string='Cobranza',
    compute="_calc_payrolls")

  def _get_warehouse_ids(self):
    ### DECLARACIÓN DE OBJETOS
    location_obj = self.env['stock.location']
    ### IDS DE LOS ALMACENES
    warehouse_ids = []
    ### BUSCAMOS LAS UBICACIONES DE VENTAS
    location_ids = location_obj.search([
      ('office_location','=',True)])
    if location_ids:
      for location_id in location_ids:
        warehouse_ids.append(location_id.get_warehouse().id)
    return warehouse_ids

  def _calc_payrolls(self):
    for rec in self:
      if rec.payroll_id:
        rec.secretary = True
      else:
        rec.secretary = False
      if rec.payroll_contract_id:
        rec.contract = True
      else:
        rec.contract = False
      if rec.payroll_collection_id:
        rec.collection = True
      else:
        rec.collection = False

  _sql_constraints = [
    ('unique_warehouse_on_week',
      'UNIQUE(week_number, warehouse_id)',
      'No se puede crear el registro: solo puede existir un registro por Semana'),
    ]