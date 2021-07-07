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
      domain.append(('date_of_last_status', '>=', self.start_date))
      domain.append(('date_of_last_status', '<=', self.end_date))
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
    mortuary_obj = self.env['mortuary']

    ### SI HAY IDS DE CONTRATOS
    if data.get('contract_ids'):
      ### INSTANCIAMOS LOS OBJETOS
      contract_ids = contract_obj.browse(data.get('contract_ids'))

    ### GENERAMOS LA HOJA
    sheet = workbook.add_worksheet("Pagos A Contratos Realizados")

    ### AGREGAMOS FORMATOS
    bold_format = workbook.add_format({'bold': True})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})

    row = 1

    ### INSERTAMOS LOS ENCABEZADOS PARA EL FORMATO
    for index, val in enumerate(HEADERS):
      sheet.write(0, index,val, bold_format)

    ### INSERTAMOS LA INFORMACIÓN DE LOS CONTRATOS
    for contract_id in contract_ids:
      ### GENERAMOS LOS INDEX
      count = 0

      ### ESCRIBIMOS EL CONTRATO
      sheet.write(row, count, contract_id.name or "")
      count+=1

      ### BUSCAMOS LA BITACORA RELACIONADA AL CONTRATO.
      mortuary_id = mortuary_obj.search([('tc_no_contrato' , '=', contract_id.name)])

      ### ESCRIBIMOS LA BITACORA
      sheet.write(row, count, mortuary_id.name or 'No se encontró bitacora' or '')
      count+=1

      ### ESCRIBIMOS EL ESTATUS DEL CONTRATO
      sheet.write(row, count, contract_id.contract_status_item.status or '')
      count+=1

      ### ESCRIBIMOS EL MOTIVO DEL CONTRATO
      sheet.write(row, count,  contract_id.contract_status_reason.reason or '')
      count+=1

      ### FECHA DE CAMBIO DE ESTATUS
      date = contract_id.date_of_last_status
      ### ESCRIBIMOS LA FECHA DE CAMBIO DE ESTATUS
      sheet.write(row, count, date or '', date_format)
      count+=1

      ### BUSCAMOS LOS ABONOS A PARTIR DE LA FECHA DE CAMBIO DE ESTATUS
      payment_ids = contract_id.payment_ids.filtered(
        lambda r: (r.payment_date >= date and r.reference == 'payment' and r.state in ('posted','reconciled')))

      ### SI HAY PAGOS
      if payment_ids:
        for payment_id in payment_ids:
          ### ESCRIBIMOS EL MONTO DEL ABONO
          sheet.write(row, count, payment_id.amount or 0, money_format)
          count+=1
          sheet.write(row, count, payment_id.debt_collector_code.name or '')
          count+=1
          sheet.write(row, count, payment_id.payment_date or '', date_format)
          row+=1
      else:
        row+=1


    
