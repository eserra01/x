# -*- coding: utf-8 -*-

from odoo import fields, models, api

class StockProductionLot(models.Model):
  _inherit = 'stock.production.lot'

  ### Declaración de campos
  active = fields.Boolean(string='Estado',
    default=True)

  employee_id = fields.Many2one(comodel_name='hr.employee',
    string='Asistente')

  ### Cancelación de solicitudes (borrado lógico)
  def action_cancel(self):
    self.active = False

  ### Reactivar las solicitudes
  def action_active(self):
    self.active = True

  