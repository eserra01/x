# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class StockLocation(models.Model):
  _inherit = 'stock.location'

  ### Declaración de campos
  office_location = fields.Boolean(string='¿Es una Ubicación de oficina de ventas?')

  contract_location = fields.Boolean(string='¿Es una Ubiación de contratos?')

  consignment_location = fields.Boolean(string='¿Es una ubicación de consignación?')

  central_location = fields.Boolean(string='¿Es ubicación central?')

  received_location = fields.Boolean(string='¿Es una ubicación de recepción?')

  ### Desactivar una ubicación
  def inactivate_location(self):
    picking_type_obj = self.env['stock.picking.type']
    operation_ids = picking_type_obj.search([
      ('default_location_src_id', '=', self.id),
      '|',
      ('default_location_dest_id','=',self.id)])
    self.active = False
    for operation in operation_ids:
      operation.active = False



  @api.model
  def create(self, vals):
    res = super(StockLocation, self).create(vals)
    picking_type_obj = self.env['stock.picking.type']
    location_obj = self.env['stock.location']
    warehouse_obj = self.env['stock.warehouse']
    picking_data = {
      'code' : 'internal',
      'use_create_lots' : True,
      'use_existing_lots' : True
    }
    if vals.get('consignment_location'):
      request_location = location_obj.search([
        ('location_id','=',res.location_id.id),
        ('office_location','=',True)], limit=1)
      return_location = location_obj.search([
        ('location_id','=',res.location_id.id),
        ('received_location','=',True)],limit=1)
      warehouse_id = request_location.get_warehouse()
      if request_location and return_location:
        picking_data.update({
          'name' : '{} -> {}'.format(warehouse_id.name,res.name),
          'warehouse_id' : warehouse_id.id,
          'sequence_code': '{} - {}'.format(request_location.name, res.name),
          'default_location_src_id' : request_location.id,
          'default_location_dest_id' : res.id,
        })
        return_picking_data = {
          'code' : 'internal',
          'use_create_lots' : True,
          'use_existing_lots' : True,
          'name' : '{} -> {}'.format(res.name, warehouse_id.name),
          'warehouse_id' : warehouse_id.id,
          'sequence_code': '{} - {}'.format(res.name,request_location.name),
          'default_location_src_id' : res.id,
          'default_location_dest_id' : return_location.id,
        }
      ### Creando Ubicación de ida
      picking_type_obj.create(picking_data)
      ### Creando Ubicación de regreso
      picking_type_obj.create(return_picking_data)
    return res
