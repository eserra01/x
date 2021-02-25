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
    self.empty_window()
    global MY_VAL 
    global MY_VAL2

    lot_obj = self.env['stock.production.lot']
    product_obj = self.env['product.product']
    mov_obj = self.env['stock.move.line']
    pick_obj = self.env['stock.picking']
    loc_obj = self.env['stock.location']
    hr_obj = self.env['hr.employee']
    stkmove_obj = self.env['stock.move']
    cont_obj = self.env['pabs.contract']

    request_id = lot_obj.search([('name','=',self.request.name)], limit=1)

    if request_id:
      prod_id = product_obj.search([('id','=',self.request.product_id.id)], limit = 1)
      for stk in mov_obj.search([('lot_id','=',self.request.product_id.id)], limit = 1):
        MY_VAL = stk.picking_id.id
        MY_VAL2 = stk.location_dest_id.id
        pick_id = pick_obj.search([('id','=',MY_VAL)], limit = 1)
        loc_id = loc_obj.search([('id','=',MY_VAL2)])

      empl_id = hr_obj.search([('id','=',self.request.id)], limit = 1)
      stkmove_id = stkmove_obj.search([('series','=',self.request.name)],limit =1)
      cont_id = cont_obj.search([('lot_id','=',self.request.id)],limit =1)
      if cont_id:
        
        if cont_id.state == "contract" :
            self.status_sol = "No disponible"
        else:
          self.status_sol = "Disponible"
      elif stkmove_id:
          if stkmove_id.origen_solicitud == "cancelada" or stkmove_id.origen_solicitud == "extravio" :
            self.status_sol = "No disponible"
          else:
            self.status_sol="Disponible"
      else:
        self.status_sol = "Disponible"

      if empl_id:
        self.code = empl_id.barcode
        self.promoter = empl_id.name
        self.date_emission = pick_id.date_done
        self.warehouse = loc_id.complete_name
        #status_sol
        self.description = prod_id.name
      else:
        self.promoter = "No asignado"
        self.description = prod_id.name
        self.date_emission = pick_id.date_done
        self.warehouse = loc_id.complete_name
        #self.warehouse = mov_id.date
    

       
        

  def empty_window(self):
    self.date_emission = False
    self.promoter = False
    self.warehouse = False
    self.status_sol = False
    self.description = False
   

  



    