# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class FixStockMove(models.TransientModel):
  _name = 'fix.stock.move'

  name = fields.Char(string='Número de solicitud',
    size=12,
    required=True)

  fix_move_ids = fields.Many2many(comodel_name='stock.move',
    relation="_request_fixed",
    column1='fix_id',
    column2='move_id',
    string='Solicitudes')

  aplica_iva = fields.Boolean(store=False)

  @api.onchange('name')
  def find_request(self):

    self.aplica_iva = self.env.company.apply_taxes
    
    stock_obj = self.env['stock.move']
    location_obj = self.env['stock.location']
    lot_obj = self.env['stock.production.lot']
    quant_obj = self.env['stock.quant']
    contract_location = location_obj.search([
      ('contract_location','=',True)],limit=1)
    if not contract_location:
      raise ValidationError((
        "No está configurada la ubicación de contratos, favor de contactar a sistemas"))
    recept_contract_location = location_obj.search([
      ('location_id','=',contract_location.location_id.id),
      ('received_location','=',True)],limit=1)
    if not recept_contract_location:
      raise ValidationError((
        "No esta configurada la ubicación de recepción de contratos, favor de contactar a sistemas"))
    data = []
    for rec in self:
      if rec.name:
        lot = rec.name
        lot_id = lot_obj.search([
          ('name','=',lot)],limit=1)
        if not lot_id:
          raise ValidationError((
            "No se encontró el número de serie: {}".format(lot)))
        quant_id = quant_obj.search([
          ('lot_id','=',lot_id.id),
          ('quantity','>',0)], order="id desc",limit=1)
        if not quant_id:
          raise ValidationError((
            "No se encontró ningún movimiento referente al número de serie: {}".format(lot)))
        if quant_id.location_id.id == recept_contract_location.id:
          raise ValidationError((
            "La solicitud se encuentra en el corte, favor de comunicarse con sistemas para abrir el corte nuevamente"))
        today_start = "{} 00:00:00".format(fields.Date.today())
        today_end = "{} 23:59:59".format(fields.Date.today())
        move_id = stock_obj.search([
          ('create_date','>',today_start),
          ('create_date','<',today_end),
          ('series','=',lot),
          ('codigo_de_activacion_valid','!=',False)
        ],order='create_date desc', limit=1)
        if not move_id:
          raise ValidationError((
          "La solicitud no se encuentra recibida el día de hoy"))
        for obj in move_id:
          data.append(obj.id)
        rec.fix_move_ids = [( 6, 0, data)]

  def fix_stock_move(self):
    contract_obj = self.env['pabs.contract']
    lot_obj = self.env['stock.production.lot']
    for rec in self.fix_move_ids:
      lot_id = lot_obj.search([
        ('name','=',rec.series)])
      contract_id = contract_obj.search([
        ('lot_id','=',lot_id.id)])
      if contract_id.state not in ('actived','precontract'):
        raise ValidationError((
          "La solicitud no puede ser modificada por que se encuentra en estado: {}".format(contract_id.state)))
      contract_id.stationery = rec.papeleria
      contract_id.initial_investment = rec.inversion_inicial
      contract_id.comission = rec.toma_comision
      contract_id.amount_received = rec.amount_received
      contract_id.payment_scheme_id = rec.payment_scheme.id
      