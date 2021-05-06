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

  def write(self, vals):
    res = super(StockLocation, self).write(vals)
    picking_type_obj = self.env['stock.picking.type']
    location_obj = self.env['stock.location']
    type_location = vals.get('consignment_location') or self.consignment_location or False
    if type_location and vals.get('location_id'):
      warehouse_id = location_obj.browse(vals.get('location_id')).get_warehouse()
      picking_type_ids = picking_type_obj.search(['|',
        ('default_location_dest_id','=',self.id),
        ('default_location_src_id','=',self.id)])
      for picking_type_id in picking_type_ids:
        ### SI LA UBICACIÓN ES LA RECEPCIÓN
        if picking_type_id.default_location_dest_id.id == self.id:
          ### SI VIENE DE OFICINA
          if picking_type_id.default_location_src_id.office_location:
            picking_type_id.write({
              'name' : "{} -> {}".format(warehouse_id.name, self.name),
              'warehouse_id' : warehouse_id.id,
              'default_location_src_id' : warehouse_id.lot_stock_id.id})
            ### SOBREESCRIBIMOS LA SECUENCIA OFICINA - ASISTENTE
            picking_type_id.sequence_id.write({
              'name' : "{} Secuencia {} - {}".format(warehouse_id.name, warehouse_id.lot_stock_id.name, self.name),
              'prefix' : "{}/{} - {}".format(warehouse_id.view_location_id.name, warehouse_id.lot_stock_id.name, self.name)
            })
        ### SI LA UBICACIÓN ES DE ORIGEN
        if picking_type_id.default_location_src_id.id == self.id:
          ### SI VA PARA RECIBIDOS
          if picking_type_id.default_location_dest_id.received_location:
            picking_type_id.write({
              'name' : "{} -> {}".format(self.name, warehouse_id.name),
              'warehouse_id' : warehouse_id.id,
              'default_location_dest_id' : warehouse_id.wh_receipt_stock_id.id})
            ### SOBREESCRIBIMOS LA SECUENCIA ASISTENTE A RECIBIDOS
            picking_type_id.sequence_id.write({
              'name' : "{} Secuencia {} - {}".format(warehouse_id.name, self.name, warehouse_id.wh_receipt_stock_id.name),
              'prefix' : "{}/{} - {}".format(warehouse_id.view_location_id.name, self.name, warehouse_id.wh_receipt_stock_id.name)
            })
          ### SI VA PARA NO DISPONIBLE (CANCELADA O EXTRAVIADA)
          if picking_type_id.default_location_dest_id.scrap_location:
            picking_type_id.write({
              'warehouse_id' : warehouse_id.id,
              'default_location_dest_id' : warehouse_id.wh_trash_stock_id.id})
            ### SOBREESCRIBIMOS LA SECUENCIA
            picking_type_id.sequence_id.write({
              'name' : "{} Secuencia {} - {}".format(warehouse_id.name, self.name, warehouse_id.wh_trash_stock_id.name),
              'prefix' : "{}/{} - {}".format(warehouse_id.view_location_id.name, self.name, warehouse_id.wh_trash_stock_id.name)
            })
    return res