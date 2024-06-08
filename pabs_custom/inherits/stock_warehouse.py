# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class StockWarehouse(models.Model):
  _inherit = 'stock.warehouse'

  ### Se expandió el código de almacén a 6 digitos
  code = fields.Char(size=6)

  wh_trash_stock_id = fields.Many2one(comodel_name='stock.location',
    string='Ubicación de No disponible')

  wh_receipt_stock_id = fields.Many2one(comodel_name='stock.location',
    string='Ubicación de Recibidos')
  
  type_company = fields.Many2one(comodel_name='type.company', string="Tipo de empresa")

  def _get_locations_values(self, vals, code=False):
    res = super(StockWarehouse, self)._get_locations_values(vals, code)
    code = vals.get('code') or code or ''
    code = code.replace(' ', '').upper()
    company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
    res['lot_stock_id'].update({
      'name' : 'Disponible',
      'office_location' : True,
    })
    res.update({
      'wh_trash_stock_id' : {
        'name': 'No Disponible',
        'active': True,
        'usage': 'internal',
        'scrap_location' : True,
        'barcode': self._valid_barcode(code + '-TRASH', company_id)
      },
      'wh_receipt_stock_id' : {
        'name': 'Recibidos',
        'active': True,
        'usage': 'internal',
        'received_location' : True,
        'barcode': self._valid_barcode(code + '-RECEIPT', company_id)
      }
    })
    return res
