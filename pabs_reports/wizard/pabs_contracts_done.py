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
    ### ARMANDO LOS PARAMETROS
    data = {
      'start_date' : self.start_date,
      'end_date' : self.end_date,
    }
    ### RETORNAMOS EL REPORTE

    return self.env.ref('pabs_reports.pabs_contracts_done_xlsx').report_action(self, data=data)

class PabsContractsDoneReportXLSX(models.AbstractModel):
  _name = 'report.pabs_reports.pabs_contracts_done_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    raise ValidationError("Si entra")
