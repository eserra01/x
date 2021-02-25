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
      IdPago = self.id
      if self.contract:
        NumeroContrato = self.contract.id
      if self.debt_collector_code:
        CodigoCobrador = self.debt_collector_code.barcode
      if self.amount:
        MontoPago = self.amount or 0
      _logger.info("ID: {} contrato: {} code: {} monto: {}".format(IdPago,NumeroContrato,CodigoCobrador,MontoPago))
      comission_tree_obj.CrearSalidas(
        IdPago=IdPago, NumeroContrato=NumeroContrato,
        CodigoCobrador=CodigoCobrador, MontoPago=MontoPago,
        EsExcedente=False)