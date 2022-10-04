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

  def transfer_parnters_old(self):
    ### Declaración de objetos:
    contract_obj = self.env['pabs.contract']
    ### Buscamos todos los contratos que tenga asignado el cobrador origen
    contract_ids = contract_obj.search([
      ('debt_collector','=',self.collector_origin_id.id),
      ('contract_status_item', 'in', (15,17,21) ) #Solo activos, suspendidos temporales y realizados por cobrar
    ])
    ### SI no se encuentran contratos
    if not contract_ids:
      ### Enviamos un mensaje de error
      raise ValidationError((
        "El Cobrador {} no tiene ningún contrato asignado".format(self.collector_origin_id.name)))
    for contract_id in contract_ids:
      contract_id.debt_collector = self.collector_dest_id.id
    self._cr.commit()
    raise ValidationError((
      'Se asignaron {} contratos al asistente {}'.format(len(contract_ids),self.collector_dest_id.name)))

  def transfer_parnters(self):  
    #
    qry = """UPDATE pabs_contract SET debt_collector = {destino} WHERE id IN(
    SELECT id FROM pabs_contract WHERE debt_collector = {origen} AND contract_status_item in (
    SELECT id FROM pabs_contract_status WHERE status IN ('REALIZADO POR COBRAR','SUSP. TEMPORAL','ACTIVO')
    ));
    """.format(destino=self.collector_dest_id.id,origen=self.collector_origin_id.id)       
    self.env.cr.execute(qry)
    self._cr.commit()
    raise ValidationError(('Se asignaron los contratos al asistente {}'.format(self.collector_dest_id.name)))
