# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

STATES = [
  ('presented','Presentada'),
  ('missing','Faltante')]

ACTIVADA = [('True','Si'), ('False','No')]

class PabsArchingLine(models.Model):
  _name = 'pabs.arching.line'

  #Documento de arqueo al que pertenece
  arching_id = fields.Many2one(comodel_name='pabs.arching', string='Arqueo')

  lot_id = fields.Many2one(comodel_name='stock.production.lot', string='Solicitud', required=True)
  scan_date = fields.Datetime(string="Fecha de escaneo")
  activated = fields.Boolean(string="Activada")
  state = fields.Selection(selection = STATES, string='Estatus')
  service_name = fields.Char(related="lot_id.product_id.name", string='Paquete')

  @api.onchange('lot_id')
  def _onchange_lot_id(self):
    #Validar que se escribió una solicitud
    if not self.lot_id.id:
      return

    #Validar si la solicitud existe
    lot_obj = self.env['stock.production.lot'].browse(self.lot_id.id)
    if not lot_obj:
      raise ValidationError("La solicitud {} no existe".format(self.lot_id.name))

    # Validar si la solicitud se encuentra en la ubicación del asistente (Mostrará error si el asistente tiene mas de una ubicación activa)
    stock_quant_obj = self.env['stock.quant'].search([('lot_id','=',self.lot_id.id), ('location_id', '=', self.arching_id.employee_id.local_location_id.id), ('quantity','=','1')])
    if not stock_quant_obj:
      actual_stock_quant_obj = self.env['stock.quant'].search([('lot_id','=',self.lot_id.id), ('quantity','=','1')])
      raise ValidationError("La solicitud {} no se encuentra en la ubicación del asistente. Su ubicación actual es: {}".format(self.lot_id.name, actual_stock_quant_obj.location_id.complete_name))

    #Validar si la solicitud tiene un contrato
    contract_obj = self.env['pabs.contract'].search([('lot_id','=', self.lot_id.id)])
    if contract_obj.state == 'contract':
      raise ValidationError("La solicitud {} ya pertenece al contrato {}".format(self.lot_id.name, contract_obj.name))

    #Consultar si la solicitud está activada
    if contract_obj.activation_code:
      self.activated = True
    else:
      self.activated = False

    self.scan_date = datetime.today()
    self.state = 'presented'
 