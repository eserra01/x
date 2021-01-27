# -*- coding: utf-8 -*-

from odoo import fields, models, api

OPTIONS = [
  ('support','Apoyo'),
  ('cooperative','Cooperativa')]

class PabsArchingLine(models.Model):
  _name = 'pabs.arching.line'

  company = fields.Selection(selection=OPTIONS,
    string='Empresa',
    required=True)

  product_id = fields.Many2one(comodel_name='product.product',
    string='Plan',
    required=True)

  lot_id = fields.Many2one(comodel_name='stock.production.lot',
    string='Solicitud',
    required=True)

  arching_id = fields.Many2one(comodel_name='pabs.arching',
    string='Arqueo')
  