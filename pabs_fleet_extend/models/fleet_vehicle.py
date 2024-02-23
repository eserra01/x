# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Mauricio Ruiz (mauricio.ruiz@pabsmr.org)
#
###########################################################################################

from odoo import fields, models, _, api
from odoo.exceptions import UserError

ACQUIRED = [('NUEVO','NUEVO'),('SEMINUEVO','SEMINUEVO')]

VEHICLE_TYPE = [
  ('CARROZA','CARROZA'),
  ('AUTOMOVIL','AUTOMOVIL'),
  ('MOTOCICLETA','MOTOCICLETA'),
  ('VAN DE PASAJEROS','VAN DE PASAJEROS'),
  ('PICKUP','PICKUP'),
  ('AUTOBUS','AUTOBUS'),
]

VEHICLE_USE = [
  ('COBRANZA','COBRANZA'),
  ('COMPRAS','COMPRAS'),
  ('CORTEJO E INSTALACION','CORTEJO E INSTALACION'),
  ('DILIGENCIAS','DILIGENCIAS'),
  ('TOLDOS','TOLDOS'),
  ('TRASLADOS DOLIENTES','TRASLADOS DOLIENTES'),
  ('TRASLADOS DE PERSOANAL','TRASLADOS DE PERSOANAL'),  
]

class FleetVehicle(models.Model):
  _inherit = 'fleet.vehicle'
 
  sale_office = fields.Char(string="Oficina de ventas", tracking=True)
  acquired = fields.Selection(ACQUIRED, string="Se adquiere")
  endorsement_payment_date = fields.Date(string='Fecha pago refrendo', tracking=True)
  owner = fields.Char(string="Unidad a nombre de", tracking=True)
  pabs_vehicle_type = fields.Selection(VEHICLE_TYPE, string="Tipo")
  vehicle_use = fields.Selection(VEHICLE_USE, string="Uso")
  conversion = fields.Char(string="Conversión", tracking=True)
  supplier_conversion = fields.Char(string="Proveedor conversión", tracking=True) 

 