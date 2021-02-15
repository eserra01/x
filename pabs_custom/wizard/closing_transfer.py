# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

MONTHS = {
  'January' : 'Enero',
  'February' : 'Febrero',
  'March' : 'Marzo',
  'April' : 'Abril',
  'May' : 'Mayo',
  'June' : 'Junio',
  'July' : 'Julio',
  'August' : 'Agosto',
  'September' : 'Septiembre',
  'October' : 'Octubre',
  'November' : 'Noviembre',
  'December' : 'Diciembre',
}

class ClosingTransfers(models.TransientModel):
  _name = 'pabs.closing.transfer'
  _description = 'Corte de solicitudes'

  warehouse_id = fields.Many2one(comodel_name='stock.warehouse',
    string='Oficina de Ventas',
    required=True)

  date_closing = fields.Date(string='Fecha de Corte',
    required=True,
    default=fields.Date.today())

  def calc_lines(self, picking_id, previus=False):
    data = []
    move_obj = self.env['stock.move']
    contract_obj = self.env['pabs.contract']
    for line in picking_id.move_line_ids_without_package:
      lot = line.lot_id.name
      move_id = move_obj.search([
        ('series','=',lot),
        ('codigo_de_activacion_valid','!=',False)],limit=1)
      contract_id = contract_obj.search([
        ('activation_code','=',move_id.codigo_de_activacion_valid)])
      data_dict = {
        'code' : move_id.picking_id.employee_id.barcode,
        'employee' : move_id.picking_id.employee_id.name,
        'product' : move_id.product_id.name,
        'lot' : lot,
        'initial' : move_id.inversion_inicial,
        'commission' : move_id.toma_comision or 0,
        'total' : move_id.amount_received or 0,
        'method_payment' : move_id.forma_pago,
        'reference' : move_id.referencia or 'NINGUNA',
        'origin' : move_id.origen_solicitud,
        'scheme' : contract_id.payment_scheme_id.name
      }
      data.append(data_dict)
      if not previus:
        contract_id.initial_investment = move_id.inversion_inicial or 0
        contract_id.stationery = move_id.papeleria or 0
        contract_id.comission = move_id.toma_comision or 0
        contract_id.state = 'precontract'

    return data

  def print_closing_transfer(self):
    ### VARIABLE DE DATOS PARA EL PICKING
    picking_data = {}
    ### DECLARACIÓN DE OBJETOS
    quant_obj = self.env['stock.quant']
    location_obj = self.env['stock.location']
    picking_obj = self.env['stock.picking']
    stock_move_obj = self.env['stock.move']
    stock_move_line_obj = self.env['stock.move.line']
    picking_type_obj = self.env['stock.picking.type']
    transfer_registry_obj = self.env['closing.transfer.registry']
    ### INFORMACIÓN QUE SE ENVIARÁ AL REPORTE
    day = self.date_closing.strftime('%d')
    month = MONTHS.get(self.date_closing.strftime('%B'))
    year = self.date_closing.strftime('%Y')
    data = {
      'logo' : self.warehouse_id.company_id.logo,
      'date' : '{} de {} del {}'.format(day, month, year),
      'warehouse_id' : self.warehouse_id.name}
    ### VERIFICA SI YA EXISTÍA ALGÚN CORTE ANTERIORMENTE
    previus = transfer_registry_obj.search([
      ('warehouse_id','=',self.warehouse_id.id),
      ('date','=',self.date_closing)])
    ### SÍ EXISTE UN REGISTRO, ENVÍA ESE REPORTE
    if previus:
      lines = self.calc_lines(previus.picking_id,previus=True)
      data.update({
        'create_uname' : previus.picking_id.create_uid.name,
        'move_lines' : lines,
        'picking_id': previus.picking_id, 
      })
      ### RETORNA EL REPORTE CON LA INFORMACIÓN QUE YA EXISTÍA PREVIAMENTE
      return self.env.ref('pabs_custom.closing_transfer_print').report_action(self, data=data)
    ### BUSCAR LA UBICACIÓN DE RECIBIDOS DEL ALMACÉN
    """child_id = location_obj.search([
      ('parent_path','like',self.warehouse_id.view_location_id.id),
      ('received_location','=',True)],limit=1)"""
    child_id = self.warehouse_id.wh_receipt_stock_id
    ### SI NO ENCUENTRA LA UBICACIÓN ENVÍA UN ERROR
    if not child_id:
      raise ValidationError((
        "No se encontró ningúna ubicación de recibidos de la oficina {}".format(self.warehouse_id.name)))
    ### GENERANDO PARAMETROS DE BUSQUEDA EN LA FECHA
    start_date = '{} 00:00:00'.format(self.date_closing)
    end_date = '{} 23:59:59'.format(self.date_closing)
    ### BUSCAR TODOS LOS MOVIMIENTOS QUE SE GENERARON EN ESAS FECHAS Y PERTENEZCAN AL ALMACÉN DE RECIBIDOS
    quant_ids = quant_obj.search([
      ('location_id','=',child_id.id),
      ('inventory_quantity','>',0),
      ('create_date','>',start_date),
      ('create_date','<',end_date)])
    ### SI NO ENCUENTRA NADA QUE PROCESAR
    if not quant_ids:
      raise ValidationError((
        "Nada que procesar"))
    ### BUSCANDO LA UBICACIÓN DE CONTRATOS
    contract_location = location_obj.search([
      ('contract_location','=',True)],limit=1)
    ### SE ENCUENTRA LA UBICACIÓN DE DISPONIBLES, PERO NECESITAMOS LA UBICACIÓN DE RECIBIDOS
    ### POR ESO, BUSCAMOS LA OTRA UBICACIÓN
    if contract_location:
      contract_warehouse = contract_location.get_warehouse()
      contract_reception = location_obj.search([
        ('location_id','=',contract_warehouse.view_location_id.id),
        ('received_location','=',True)],limit=1)

      ### SI SE ENCUENTRA UBICACIÓN DE CONTRATOS RECIBIDOS
      if contract_reception:
        picking_type_id = picking_type_obj.search([
          ('code','=','internal'),
          ('default_location_src_id','=',child_id.id),
          ('default_location_dest_id','=',contract_reception.id)],limit=1)
        ### BUSCAMOS EL TIPO DE OPERACIÓN QUE VA ACORDE A LA TRANSACCIÓN

        if not picking_type_id:
          raise ValidationError((
            "No se encontró el tipo de operación, favor de ponerse en contacto con sistemas"))
        ### SI SE ENCUENTRA SE EMPAQUETA TODO EN UN JSON PARA CREAR EL PICKING
        closing = 'Corte {} {}'.format(self.warehouse_id.name, fields.Date.today())
        picking_data.update({
          'picking_type_id' : picking_type_id.id,
          'location_id': child_id.id,
          'location_dest_id' : contract_reception.id,
          'type_transfer' : 'ov-cont',
          'origin' : closing
        })
        ### CREANDO EL PICKING
        picking_id = picking_obj.create(picking_data)
        ### AGREGANDO EL PICKING AL REPORTE
        data.update({
          'create_uname' : picking_id.create_uid.name,
          'picking_id' : picking_id
        })
        ### RECORREMOS LOS PRODUCTOS QUE SE ENCONTRARON PARA CREAR LA TRANSFERENCIA
        for quant in quant_ids:
          ### CREANDO ENCABEZADO DE LA TRANSFERENCIA
          stock_move_data = {
            'name' : quant.product_id.name,
            'picking_id' : picking_id.id,
            'product_id' : quant.product_id.id,
            'product_uom' : quant.product_id.uom_id.id,
            'location_id' : picking_id.location_id.id,
            'location_dest_id' : picking_id.location_dest_id.id,
            'product_uom_qty' : 1,
          }
          ### CREANDO EL MOVIMIENTO DE STOCK
          move_id = stock_move_obj.create(stock_move_data)
          line_data = {
            'picking_id' : picking_id.id,
            'move_id': move_id.id,
            'product_id': quant.product_id.id,
            'product_uom_id' : quant.product_id.uom_id.id,
            'qty_done' : 1,
            'lot_id' : quant.lot_id.id,
            'location_id' : picking_id.location_id.id,
            'location_dest_id' : picking_id.location_dest_id.id,
            'state' : 'assigned',
            'reference' : move_id.reference,
          }
          stock_move_line_obj.create(line_data)
        picking_id.button_validate()
        ### CALCULANDO EL DETALLE
        lines = self.calc_lines(picking_id,previus=False)
        data.update({
          'move_lines' : lines,
        })
        ### Agregar registro de corte
        transfer_registry_obj.create({
          'name' : closing,
          'picking_id' : picking_id.id,
          'warehouse_id' : self.warehouse_id.id,
          'date' : fields.Date.today()
        })
    return self.env.ref('pabs_custom.closing_transfer_print').report_action(self, data=data)

class ClosingTransferReport(models.Model):
  _name = 'report.pabs_custom.closing_transfer_print'

  @api.model
  def _get_report_values(self, docids, data):
    return {
    'create_uname' : data.get('create_uname'),
    'move_lines' : data.get('move_lines'),
    'picking_id' : data.get('picking_id'),
    'warehouse_id' : data.get('warehouse_id'),
    'date' : data.get('date'),
  }
