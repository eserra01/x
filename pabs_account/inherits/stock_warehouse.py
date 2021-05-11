# -*- coding: utf-8 -*-

from odoo import api, fields, models

class StockWarehouse(models.Model):
  _inherit = 'stock.warehouse'

  analytic_account_id = fields.Many2one(comodel_name='account.analytic.account',
    string='Cuenta analitica')
  
