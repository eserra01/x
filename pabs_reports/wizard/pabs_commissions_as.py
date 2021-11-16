# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz

HEADERS = [
  {'name': 'Código', 'width': 10},
  {'name':'Nombre', 'width': 50},
  {'name':'No. de pago', 'width': 20},
  {'name':'Fecha de pago', 'width': 15},
  {'name':'Contrato', 'width': 15},
  {'name':'Importe', 'width': 15}]

class PabsCommissionAS(models.TransientModel):
  _name = 'pabs.commissions.as'
  _description = 'Reporte de comisiones de asistente social por periodo'

  start_date = fields.Date(string='Fecha Inicial', required=True)
  end_date = fields.Date(string='Fecha Final', required=True)
  all = fields.Boolean(string="Todos los asistentes", default=True)
  agent_id = fields.Many2one(string='Agente', comodel_name='hr.employee')

  def generate_xlsx_report(self):
    data = {
      'ids': self.ids,
      'model': self._name,
      'form': 
      {
        'date_start': self.start_date,
        'date_end': self.end_date,
        'all': self.all,
        'agent_id': self.agent_id.id
      },
    }
    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_reports.pabs_commissions_as_xlsx').report_action(self, data=data)

class PabsCommissionsASReportXLSX(models.AbstractModel):
  _name = 'report.pabs_reports.pabs_commissions_as_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    
    date_start = data['form']['date_start']
    date_end = data['form']['date_end']
    
    # SALIDAS ENTRE DOS FECHAS
    # Consultar id de cargo papeleria
    cargo_papeleria = self.env['hr.job'].search([('name','=','PAPELERIA')])
    cargo_iva = self.env['hr.job'].search([('name','=','IVA')])

    if data['form']['all']:
      agente = "Todos"
      commission_ids = self.env['pabs.comission.output'].search([
        ('payment_date', '>=', date_start), 
        ('payment_date', '<=', date_end),
        ('payment_status', 'in', ['posted','sent','reconciled']),
        ('actual_commission_paid', '!=', 0),
        ('job_id', 'not in', [cargo_papeleria.id, cargo_iva.id])
        ]
      )
    else:     
       agente = '-'     
       commission_ids = self.env['pabs.comission.output'].search([
        ('payment_date', '>=', date_start), 
        ('payment_date', '<=', date_end),
        ('payment_status', 'in', ['posted','sent','reconciled']),
        ('actual_commission_paid', '!=', 0),
        ('job_id', 'not in', [cargo_papeleria.id, cargo_iva.id]),
        ('comission_agent_id','=',data['form']['agent_id'])
        ]
      )

    ### GENERAMOS LA HOJA
    sheet = workbook.add_worksheet("Comisiones de asistente social")

    ### AGREGAMOS FORMATOS
    bold_format = workbook.add_format({'bold': True})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})

      
    sheet.write(0, 1,"Comisiones por agente del %s al %s"%(date_start,date_end))
    sheet.write(1, 1,"Agente: %s"%(agente))
    row = 4
    ### INSERTAMOS LOS ENCABEZADOS PARA EL FORMATO
    for index, val in enumerate(HEADERS):
      sheet.write(row-1, index,val.get('name'), bold_format)
      sheet.set_column(row-1, index, val.get('width'))

    total = 0
    ### INSERTAMOS LA INFORMACIÓN 
    for commission in commission_ids:
      ### GENERAMOS LOS INDEX
      count = 0
      total += commission.actual_commission_paid
      ### ESCRIBIMOS 
      sheet.write(row, 0, commission.comission_agent_id.barcode or "")
      sheet.write(row, 1, commission.comission_agent_id.name or "")
      sheet.write(row, 2, commission.payment_id.name or "")
      sheet.write(row, 3, str(commission.payment_id.payment_date) or "")
      sheet.write(row, 4, commission.payment_id.contract.name or "")
      sheet.write(row, 5, commission.actual_commission_paid or "")
      # count+=1
      row+=1
    
    if not data['form']['all']:
      sheet.write(row, 4, "Total", bold_format)
      sheet.write(row, 5, total or "", )


    


    
