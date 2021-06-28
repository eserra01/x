# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResCompany(models.Model):
  _inherit = 'res.company'

  contract_location = fields.Many2one(comodel_name='stock.location',
    string='Ubicación de Contratos Recibidos')
  