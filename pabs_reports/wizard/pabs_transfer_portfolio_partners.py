# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class TransferPortfolioPartners(models.Model):
  _name = 'pabs.transfer.portfolio.partners'
  _description = 'Traspaso de Cartera de Clientes'

  collector_origin_id = fields.Many2one(comodel_name= 'hr.employee',
    string='Cobrador Origen',
    required=True)

  collector_dest_id = fields.Many2one(comodel_name='hr.employee',
    string='Cobrador Destino',
    required=True)

  def transfer_parnters(self):
    ### Declaración de objetos:
    contract_obj = self.env['pabs.contract']
    ### Buscamos todos los contratos que tenga asignado el cobrador origen
    contract_ids = contract_obj.search([
      ('debt_collector','=',self.collector_origin_id.id)])
    ### SI no se encuentran contratos
    if not contract_ids:
      ### Enviamos un mensaje de error
      raise ValidationError((
        "El Cobrador {} no tiene ningún contrato asignado".format(collector_origin_id.name)))
    for contract_id in contract_ids:
      contract_id.debt_collector = self.collector_dest_id.id
    self._cr.commit()
    raise ValidationError((
      'Se asignaron {} contratos al asistente {}'.format(len(contract_ids),self.collector_dest_id.name)))
