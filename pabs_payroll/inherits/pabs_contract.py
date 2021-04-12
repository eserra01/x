# -*- coding: utf-8 -*-

from odoo import api, fields, models

class PabsContract(models.Model):
  _inherit = 'pabs.contract'

  warehouse_id = fields.Many2one(comodel_name='stock.warehouse',
    related='lot_id.warehouse_id',
    string='Almacén Perteneciente')

  owner_id = fields.Many2one(comodel_name='hr.employee',
    string='Propietario')

  payroll_discount = fields.Boolean(string='¿Descuento Vía Nómina?')
