# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
  _inherit = 'account.payment'

  ecobro_affect_id = fields.Char(string='Afectación de ecobro ID')

  def generate_output_comission(self):
    comission_tree_obj = self.env['pabs.comission.tree']
    payment_obj = self.env['account.payment']
    payment_ids = payment_obj.search([
      ('ecobro_affect_id','!=',False),
      ('comission_output_ids','=',False)])
    for payment_id in payment_ids:
      IdPago = payment_id.id
      if payment_id.contract:
        NumeroContrato = payment_id.contract.id
      if payment_id.debt_collector_code:
        CodigoCobrador = payment_id.debt_collector_code.barcode
      if payment_id.amount:
        MontoPago = payment_id.amount or 0
      _logger.info("ID: {} contrato: {} code: {} monto: {}".format(IdPago,payment_id.contract.name,CodigoCobrador,MontoPago))
      comission_tree_obj.CrearSalidas(
        IdPago=IdPago, NumeroContrato=NumeroContrato,
        CodigoCobrador=CodigoCobrador, MontoPago=MontoPago,
        EsExcedente=False)