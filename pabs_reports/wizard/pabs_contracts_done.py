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
    return True


