# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

STATES = [
  ('draft','Borrador'),
  ('done','Hecho')]



class Stock(models.TransientModel):
  _name = 'pabs.status.stock'

  #contract_request = fields.Many2one(comodel_name ="stock.production_lot",
   # string ="Número de serie")
  request = fields.Many2one(comodel_name='stock.production.lot',
    string = "Número Solicitud",
    tracking=True,
    required=True)

  date_emission = fields.Char(string = "Fecha de admision")

  promoter = fields.Char(string="Promotor")

  warehouse = fields.Char( string = "Almacen")

  status_sol = fields.Char(string ="Estado")

  description = fields.Char(string = "Descripcion del artículo")

  code = fields.Char(string ="Código Promotor")

    
  @api.onchange('request')
  def calc_estatus(self):
    ### LIMPIAMOS LA VENTANA
    self.empty_window()
    ### DECLARACIÓN DE OBJETOS
    quant_obj = self.env['stock.quant']

    ### SI SE ESCRIBIO UNA SOLICITUD
    if self.request:
      ### BUSCAMOS LA SOLICITUD
      quant_id = quant_obj.search([
        ('lot_id', '=', self.request.id)]).filtered(lambda r: r.quantity >= 1)

      ### UBICACIÓN
      location_id = quant_id.location_id

      ### SI EXISTE EN ALGUNA UBICACIÓN
      if quant_id: 
        ### Fecha
        self.date_emission = quant_id.in_date.date()
        ### Promotor
        self.promoter = quant_id.lot_id.employee_id.name or 'N/A'
        ### Almacén
        self.warehouse = location_id.location_id.get_warehouse().name or ''
        ### DESCRIPCIÓN DE LA SOLICITUD
        self.description = quant_id.lot_id.product_id.name or ''
        ### INSERTAMOS EL CÓDIGO DEL ASISTENTE
        self.code = quant_id.lot_id.employee_id.barcode or 'No asignada'

        ### VALIDANDO ESTATUS DE SOLICITUD
        ### SI ES UNA UBICACIÓN CENTRAL
        if location_id.central_location:
          ### INSERTAMOS LA INFORMACIÓN
          self.status_sol = 'Sin Asignar a Oficina'
        ### SI ES UNA UBICACIÓN DE CONTRATOS Y RECEPCIÓN
        if location_id.contract_location and location_id.received_location:
          ### INSERTAMOS LA INFORMACIÓN
          self.status_sol = 'Recepción de Contratos'
        ### SI ES UNA UBICACIÓN DE OFICINA Y ES UNA UBICACIÓN DE CONTRATOS
        if location_id.office_location and location_id.contract_location:
          ### INSERTAMOS LA INFORMACIÓN
          self.status_sol = 'Disponible Contratos'
        ### SI ES UNA UBICACIÓN DE OFICINAS
        if location_id.office_location:
          self.status_sol = 'Disponible'
        ### SI ES UNA UBICACIÓN DE CHATARRA
        if location_id.scrap_location:
          self.status_sol = 'Cancelada'
        ### SI ES UNA UBICACIÓN DE CONSIGNACIÓN
        if location_id.consignment_location:
          self.status_sol = 'Asignada'
        ### SI ES UNA UBICACIÓN DE RECEPCIÓN
        if location_id.received_location:
          self.status_sol = 'Recepción de Oficina'
    
  def empty_window(self):
    self.date_emission = False
    self.promoter = False
    self.warehouse = False
    self.status_sol = False
    self.description = False
   

  



    