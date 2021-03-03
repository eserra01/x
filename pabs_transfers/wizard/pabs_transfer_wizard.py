# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

ORIGIN = [
  ('cancelada', 'Cancelada'),
  ('extravio', 'Extravio'),
  ('sobrantes', 'Sobrantes')]

class PABSTransfer(models.TransientModel):
  _name = 'pabs.transfer'
  _description = 'Transferencias Canceladas, Extraviadas y Sobrantes'

  transfer_line_ids = fields.One2many(comodel_name='pabs.transfer.line',
    inverse_name='transfer_id',
    string='Detalle la transferencia')

  def generate_transfer(self):
    ### DECLARACIÓN DE OBJETOS
    picking_obj = self.env['stock.picking']
    stock_move_obj = self.env['stock.move']
    stock_move_line_obj = self.env['stock.move.line']
    location_obj = self.env['stock.location']
    picking_type_obj = self.env['stock.picking.type']
    ### VALIDAMOS QUE EXISTAN MOVIMIENTOS
    if self.transfer_line_ids:
      ### RECORREMOS LA LISTA DE MOVIMIENTOS
      for line in self.transfer_line_ids:
        ### CALCULAMOS LA UBICACIÓN ORIGEN
        location_id = line.calc_origin_location()
        ### CALCULAMOS LA UBICACIÓN DESTINO
        location_dest_id = line.calc_dest_location()
        ### BUSCAMOS SI EXISTE UN TIPO DE TRANSFERENCIA DE ESE TIPO
        picking_type_id = picking_type_obj.search([
          ('code','=','internal'),
          ('default_location_src_id','=',location_id),
          ('default_location_dest_id','=',location_dest_id)],limit=1)
        ### SI NO EXISTE
        if not picking_type_id:
          ### TRAEMOS EL NOMBRE DE LA UBICACION ORIGEN
          location_name = location_obj.browse(location_id).name
          ### GENERAMOS LOS DATOS PARA CREAR UN TIPO DE TRANSFERENCIA
          picking_type_data = {
            'name' : "{} -> DEVOLUCION".format(location_name),
            'sequence_code' : "{} - {}".format(location_name, line.origin),
            'warehouse_id' : line.lot_id.warehouse_id.id,
            'code' : 'internal',
            'default_location_src_id' : location_id,
            'default_location_dest_id' : location_dest_id,
          }
          ### CREAMOS EL TIPO DE TRANSFERENCIA
          picking_type_id = picking_type_obj.create(picking_type_data)
        ### GENERANDO LISTA
        pick_lines = []
        ### GENERAMOS LA INFORMACION DEL DETALLE DE LA TRANSFERENCIA
        line_data = {
          'name': line.lot_id.product_id.name,
          'product_id': line.lot_id.product_id.id,
          'product_uom_qty': 1,
          'product_uom': line.lot_id.product_id.uom_id.id,
          'state': 'draft',
          'series' : line.series,
          'origen_solicitud' : line.origin,
        }
        ### AGREGAMOS EL STOCK EN EL ARRAY
        pick_lines.append((0,0,line_data))
        ### GENERAMOS LA INFORMACIÓN PARA CREAR EL PICKING
        picking_data = {
          'picking_type_id' : picking_type_id.id,
          'location_id': location_id,
          'location_dest_id' : location_dest_id,
          'type_transfer' : 'as-ov',
          'employee_id' : line.lot_id.employee_id.id,
          'origin' : line.origin,
          'move_lines':pick_lines,
        }
        ### CREAMOS EL PICKING
        picking_id = picking_obj.create(picking_data)
        ### VALIDAMOS EL PICKING
        picking_id.button_validate()
        self._cr.commit()
    ### SI NO
    else:
      ### ENVIAMOS MENSAJE QUE NO EXISTEN LINEAS
      raise ValidationError((
        "No existen lineas para procesar"))

class PABSTransferLine(models.TransientModel):
  _name = 'pabs.transfer.line'
  _description = 'Detalle de Transferencias Canceladas, Extraviadas y Sobrantes'

  transfer_id = fields.Many2one(comodel_name='pabs.transfer',
    string='ID transferencia')

  lot_id = fields.Many2one(comodel_name='stock.production.lot',
    string='Solicitud')

  series = fields.Char(string='Número de Solicitud',
    required=True)

  location_id = fields.Many2one(comodel_name='stock.location',
    string='Ubicación Origen')

  location_dest_id = fields.Many2one(comodel_name='stock.location',
    string='Ubicación Destino')

  origin = fields.Selection(selection=ORIGIN,
    string='Origen de solicitud', required=True)

  def calc_origin_location(self):
    ### DECLARAMOS LOS OBJECTOS
    quant_obj = self.env['stock.quant']
    ### BUSCAMOS LA UBICACIÓN DE LA SOLICITUD
    quant_id = quant_obj.search([
      ('lot_id','=',self.lot_id.id),
      ('quantity','>',0)], order="in_date desc", limit=1)
    ### SI NO SE ENCUENTRA EL MOVIMIENTO
    if not quant_id:
      ### ENVIAMOS UN MENSAJE DE ERROR
      raise ValidationError((
        "No se encontró el origen de la solicitud"))
    ### GUARDAMOS LA UBICACIÓN
    location_id = False
    if quant_id.location_id.consignment_location:
      location_id = quant_id.location_id.id
    else:
      raise ValidationError((
        "La ubicación origen es: {}, debe ser una ubicación de asistente para poder transferirla".format(
          quant_id.location_id.name)))
    ### RETORNAMOS LA UBICACIÓN O ENVIAMOS UN FALSOO
    return location_id

  def calc_dest_location(self):
    ### SI EXISTE UNA SOLICITUD
    if self.lot_id:
      ### GUARDAMOS EL ALMACÉN AL CUAL ESTA ASIGNADO
      warehouse_id = self.lot_id.warehouse_id
      ### SI N OESTA ASIGNADO
      if not warehouse_id:
        ### ENVIAMOS MENSAJE DE ERROR
        raise ValidationError((
          "la solicitud {} no esta asignada a ningún almacén".format(self.lot_id.name)))
      if self.origin in ('cancelada','extravio'):
        ### GUARDAMOS LA UBICACIÓN DE NO DISPONIBLE
        location_id = warehouse_id.wh_trash_stock_id.id
      elif self.origin == 'sobrantes':
        location_id = warehouse_id.lot_stock_id.id
      ### RETORNAMOS LA UBICACIÓN O ENVIAMOS UN FALSOO
      return location_id or False

  @api.onchange('series','origin')
  def calc_locations(self):
    ### DECLARACIÓN DE OBJECTOS
    lot_obj = self.env['stock.production.lot']
    ### SE RECORRE POR SI HAY MULTIPLES REGISTROS
    for rec in self:
      ### SI SE CAPTURO UNA SERIE
      if rec.series:
        ### SE REALIZA LA BUSQUEDA DE LA SERIE
        lot_id = lot_obj.search([
          ('name','=',rec.series)],limit=1)
        ### SI NO SE ENCUENTRA
        if not lot_id:
          ### ARROJAMOS UN MENSAJE DE ERROR
          raise ValidationError((
            "No se encontró la solicitud: {} en el sistema".format(rec.series)))
        ### ESCRIBIMOS LA SERIE EN EL LOT
        rec.lot_id = lot_id.id
        ### BUSCAMOS LA SOLICITUD
        location_id = rec.calc_origin_location()
        if location_id:
          ### SE ESCRIBE LA UBICACIÓN DONDE ESTÁ UBICADA LA SOLICITUD
          rec.location_id = location_id
      ### SI SELECCIONARON EL TIPO DE TRANSFERENCIA CANCELADA
      if rec.origin:
        ### CALCULAMOS LA UBICACIÓN DE TIPO NO DISPONIBLE
        location_dest_id = self.calc_dest_location()
        ### SI EXISTE LA UBICACIÓN
        if location_dest_id:
          ### GUARDAMOS EL VALOR
          rec.location_dest_id = location_dest_id

  
