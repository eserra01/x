# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ClosingTransferRegistry(models.Model):
  _name = 'closing.transfer.registry'

  name = fields.Char(string='Nombre del registro')

  picking_id = fields.Many2one(comodel_name='stock.picking')

  warehouse_id = fields.Many2one(comodel_name='stock.warehouse',
    string='Oficina de Ventas')
  
  date = fields.Date(string='Fecha de Corte')

  company_id = fields.Many2one(
    'res.company', 'Compañia', required=True,
    default=lambda s: s.env.company.id, index=True)

  def unlink(self):
    picking_obj = self.env['stock.picking']
    return_picking = self.env['stock.return.picking']
    return_line = self.env['stock.return.picking.line']
    for registry in self:
      picking_id = registry.picking_id
      original_location = picking_id.location_id.id
      data = {
        'picking_id' : picking_id.id,
        'parent_location_id' : picking_id.location_id.location_id.id,
        'original_location_id' : original_location,
        'location_id' : original_location,
      }
      wizard_id = return_picking.create(data)
      for line in picking_id.move_ids_without_package:
        line_data = {
          'product_id' : line.product_id.id,
          'quantity' : line.quantity_done,
          'wizard_id' : wizard_id.id,
          'move_id' : line.id,
        }
        return_line.create(line_data)
      action = wizard_id.create_returns()
      picking_return_id = picking_obj.browse(action['res_id'])
      for picking_line in picking_return_id.move_line_ids_without_package:
        picking_line.qty_done = 1
      picking_return_id.button_validate()
    super(ClosingTransferRegistry, self).unlink()