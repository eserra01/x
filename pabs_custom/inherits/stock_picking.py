# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

OPERATION_TYPE = [
('incoming','Recepción'),
('outgoing','Entrega'),
('internal','Transferencia Interna')]

class StockPicking(models.Model):
  _inherit = 'stock.picking'

  ### Declaración de campos
  operation_type = fields.Selection(selection=OPERATION_TYPE,
    string='Tipo de Operacion calculado',
    related="picking_type_id.code")

  employee_id = fields.Many2one(comodel_name='hr.employee',
    string='A.S')

  salary = fields.Boolean(related='employee_id.payment_scheme.allow_all')

  find_serie = fields.Char(String='Buscar Serie')

  ### Campos XMARTS
  type_transfer = fields.Selection([
    ('ac-ov', 'Almacén Central -> Oficina de Ventas'),
    ('ac-cont', 'Almacén Central -> Contratos'),
    ('cont-ov', 'Contratos -> Oficina de Ventas'),
    ('cont-ac', 'Contratos -> Almacén Central'),
    ('cont-as', 'Contratos -> Asistente'),
    ('ov-cont', 'Oficina de Venta -> Contratos'),
    ('ov-ac', 'Oficina de Venta -> Almacén Central'),
    ('ov-as', 'Oficina de Venta -> Asistente'),
    ('as-ov', 'Asistente -> Oficina de Venta'),
    ('as-cont', 'Asistente -> Contratos'),
    ('as-cont', 'Asistente -> Admon Contratos')],
    string='Tipo de transferencia')
  ### Termina campos XMARTS

  ### Métodos XMARTS
  @api.onchange('type_transfer','employee_id')
  def onchange_type_transfer(self):
    picking_type_obj = self.env['stock.picking.type']
    location_obj = self.env['stock.location']
    if self.type_transfer == 'ov-as' and self.employee_id:
      picking_type_id = picking_type_obj.search([
        ('default_location_src_id','=',self.employee_id.request_location_id.id),
        ('default_location_dest_id','=',self.employee_id.local_location_id.id)])
      if picking_type_id:
        self.picking_type_id = picking_type_id
    """for rec in self:
      if rec.type_transfer == 'sucursal':
        rec.move_ids_without_package.product_uom_qty = 0
        rec.move_ids_without_package.series = ''
      elif rec.type_transfer == 'asistente' or rec.type_transfer == 'ventas':
        rec.move_ids_without_package.product_uom_qty = 1
        rec.move_ids_without_package.series_start = ''
        rec.move_ids_without_package.series_end = ''"""

  @api.onchange('picking_type_id', 'partner_id')
  def onchange_picking_type(self):
    origin = ''
    if self.type_transfer != 'regreso_solicitudes':
      if self.picking_type_id:
        ####### VALIDACIONES RESPECTIVAS PARA LAS UBICACIONES
        if self.picking_type_id.default_location_src_id:
          location_id = self.picking_type_id.default_location_src_id
          ### VALIDANDO UBICACIÓN ORIGEN
          if location_id:
            if location_id.office_location:
              origin+='ov-'
            elif location_id.contract_location and location_id.received_location:
              origin+='cont-'
            elif location_id.consignment_location:
              origin+='as-'
            elif location_id.central_location:
              origin+='ac-'
        elif self.partner_id:
          location_id = self.partner_id.property_stock_supplier
        else:
          customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

        if self.picking_type_id.default_location_dest_id:
          location_dest_id = self.picking_type_id.default_location_dest_id
          ### VALIDANDO UBICACIÓN DESTINO
          if location_dest_id:
            if location_dest_id.office_location:
              origin+='ov'
            elif location_dest_id.contract_location:
              origin+='cont'
            elif location_dest_id.consignment_location:
              origin+='as'
            elif location_dest_id.central_location:
              origin+='ac'
            elif location_dest_id.received_location:
              origin+='ov'
          if origin and (self.picking_type_id.code == 'internal'):
            values = origin.split("-")
            if len(values) == 2:
              try:
                self.type_transfer = origin
              except:
                raise ValidationError((
                  'No se encontró la validación "{}"\n favor de ponerse en contacto con sistemas'.format(origin)))
        elif self.partner_id:
          location_dest_id = self.partner_id.property_stock_customer
        else:
          location_dest_id, supplierloc = self.env['stock.warehouse']._get_partner_locations()
        if self.state == 'draft':
          self.location_id = location_id.id
          self.location_dest_id = location_dest_id.id
    if self.partner_id and self.partner_id.picking_warn:
      if self.partner_id.picking_warn == 'no-message' and self.partner_id.parent_id:
        partner = self.partner_id.parent_id
      elif self.partner_id.picking_warn not in ('no-message', 'block') and self.partner_id.parent_id.picking_warn == 'block':
        partner = self.partner_id.parent_id
      else:
        partner = self.partner_id
        if partner.picking_warn != 'no-message':
          if partner.picking_warn == 'block':
            self.partner_id = False
          return {'warning': {
            'title': ("Warning for %s") % partner.name,
            'message': partner.picking_warn_msg}}

  
  @api.onchange('location_dest_id')
  def onchange_location_dest_id(self):
    employee_obj = self.env['hr.employee']
    if self.location_dest_id:
      if self.location_dest_id.consignment_location:
        employee_id = employee_obj.search([
          ('local_location_id','=',self.location_dest_id.id)],limit=1)
        if employee_id:
          self.employee_id = employee_id.id
        else:
          self.employee_id = False

  @api.onchange('location_id')
  def onchange_location_id(self):
    employee_obj = self.env['hr.employee']
    if self.location_id:
      if self.location_id.consignment_location:
        employee_id = employee_obj.search([
          ('local_location_id','=',self.location_id.id)],limit=1)
        if employee_id:
          self.employee_id = employee_id.id
        else:
          self.employee_id = False

  @api.onchange('find_serie')
  def search_serie(self):
    lot_obj = self.env['stock.production.lot']
    if self.find_serie:
      serie = self.find_serie
      lot_id = lot_obj.search([
        ('name','=',serie)])
      if not lot_id:
        raise ValidationError((
          "No se encontró el número de serie en el sistema"))
      serie_data = {
        'name' : lot_id.product_id.name,
        'product_id' : lot_id.product_id.id,
        'series' : serie,
        'product_uom' : lot_id.product_id.uom_id.id,
        'product_uom_qty' : 1,

      }
      self.move_ids_without_package = [(0, 0, serie_data)]
      self.find_serie = False
      return {
        'move_ids_without_package' : [(0, 0, serie_data)]
      }      
