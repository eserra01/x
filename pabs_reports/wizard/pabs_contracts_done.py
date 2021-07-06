# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz

HEADERS = [
'CONTRATO',
'BITACORA',
'ESTATUS',
'MOTIVO',
'FECHA CAMB. EST.',
'ABONO',
'COBRADOR',
'FECHA ABONO',
]

class ContractsDone(models.TransientModel):
  _name = 'pabs.contracts.done'
  _description = 'Reporte de Servicios Realizados y pagados'

  start_date = fields.Date(string='Fecha Inicial',
    required=True)

  end_date = fields.Date(string='Fecha Final')

  def generate_xlsx_report(self):
    ### DECLARACIÓN DE OBJETOS
    contract_obj = self.env['pabs.contract']

    ### GENERAMOS LE DOMINIO DE BUSQUEDA
    domain = [
      ('state', '=', 'contract'),
      ('contract_status_reason', 'in', ('REALIZADO POR COBRAR','PAGADO','REALIZADO'))]

    ### SI HAY FECHA FINAL SE AGREGABA LA FECHA
    if self.end_date:
      domain.append(('date_of_last_status', '>=', self.start_date),('date_of_last_status', '<=', self.end_date))
    ### SI NO
    else:
      domain.append(('date_of_last_status' , '=', self.start_date))

    ### BUSCAMOS LOS CONTRATOS CON LOS PARAMETROS DE BUSQUEDA
    contract_ids = contract_obj.search(domain)

    ### SI NO HAY CONTRATOS
    if not contract_ids:
      raise ValidationError("No se encontró ningún contrato para procesar")

    ### AGREGAMOS LOS IDS A LOS PARAMETROS
    data = {'contract_ids' : contract_ids.ids}

    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_reports.pabs_contracts_done_xlsx').report_action(self, data=data)

class PabsContractsDoneReportXLSX(models.AbstractModel):
  _name = 'report.pabs_reports.pabs_contracts_done_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    ### DECLARACIÓN DE OBJETOS
    contract_obj = self.env['pabs.contract']

    if data.get('contract_ids'):
      contract_ids = contract_obj.browse(data.get('contract_ids'))

    raise ValidationError("Contratos: {}".format(contract_ids))
