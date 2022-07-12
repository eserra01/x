# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz

TIPO_DE_REPORTE = [
  ('mensual', 'Mensual: Contratos realizados (fechas en que los contratos fueron realizados)'),
  ('anual', 'Anual: Contratos no realizados (fechas de oficina de cobranza)'),
  ('cancelados', 'Cancelados: Contratos cancelados (fechas en que los contratos fueron cancelados)'),
  ('cobranza', 'Cobranza de contratos nueva empresa sin realizados')
]

HEADERS = [
  'Fecha de registro',
  'Contrato',
  'Fecha de estatus',
  'Estatus',
  'Motivo',
  'Costo',
  'Abonado',
  'IVA',
  'ISR'
]

class PabsTaxesWizard(models.TransientModel):
  _name = 'pabs.taxes.wizard'
  _description = 'Wizard para reporte de impuestos'

  report_type = fields.Selection(selection=TIPO_DE_REPORTE, string="Tipo de reporte", default='mensual')

  start_date = fields.Date(string='Fecha inicial', default = fields.date.today(),required=True)
  end_date = fields.Date(string='Fecha final', default = fields.date.today(), required=True)

  def print_xls_report(self):
    ### ARMANDO LOS PARAMETROS ###
    data = {
      'start_date' : self.start_date,
      'end_date' : self.end_date,
      'report_type': self.report_type
    }

    ### REPORTE DE COBRANZA MENSUAL DE CONTRATOS QUE APLICA REPORTE DE IMPUESTOS, DIFERENCIANDO ENTRE REALIZADOS Y NO REALIZADOS
    if data['report_type'] == 'cobranza':
      
      company_id = self.env.company.id

      #HARCODED !!!
      fecha_minima_creacion = '1900-01-01'
      if company_id == 12: #SALTILLO
        fecha_minima_creacion = '2021-11-01' #PROD
      elif company_id  == 13: #MONCLOVA
        fecha_minima_creacion = '2021-12-01'
      elif company_id  == 15: #ACAPULCO
        fecha_minima_creacion = '2022-01-01'
      elif company_id  == 16: #TAMPICO
        fecha_minima_creacion = '2022-02-01'
      else:
        raise ValidationError("La compañia no aplica para el reporte de impuestos")

      cobranza = self.env['account.payment'].sudo().search([
        ('contract.company_id', '=', company_id),
        ('state', 'in', ('posted', 'sent', 'reconciled')),
        ('contract.invoice_date', '>=', fecha_minima_creacion),
        ('payment_date', '>=', self.start_date),
        ('payment_date', '<=', self.end_date)
      ])
      
      cantidad_cobranza_realizados = 0
      cantidad_cobranza_no_realizados = 0

      for cob in cobranza:
        if cob.contract.contract_status_item.status == 'REALIZADO' or cob.contract.contract_status_reason.reason == 'REALIZADO POR COBRAR':
          cantidad_cobranza_realizados = cantidad_cobranza_realizados + cob.amount
        else:
          cantidad_cobranza_no_realizados = cantidad_cobranza_no_realizados + cob.amount

      raise ValidationError("Cantidad de cobranza: ${} \n Cantidad de cobranza de realizados: ${} \n Cantidad de cobranza sin contratos realizados: ${}".format(
        cantidad_cobranza_no_realizados,
        cantidad_cobranza_realizados,
        cantidad_cobranza_no_realizados - cantidad_cobranza_realizados
      ))

    ### RETORNAMOS EL REPORTE ###
    return self.env.ref("pabs_account.pabs_taxes_xlsx").report_action(self, data=data)

class PabsTaxesXLSX(models.AbstractModel):
  _name = 'report.pabs_account.pabs_taxes_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    
    
    id_registros = []
    if data['report_type'] == 'mensual':
      id_registros = self.env['pabs.taxes'].search([
        ('company_id', '=', self.env.company.id),
        ('fecha_estatus', '>=', data['start_date']),
        ('fecha_estatus', '<=', data['end_date']),
        '|', ('id_estatus.status', '=', 'REALIZADO'),
        ('id_motivo.reason', '=', 'REALIZADO POR COBRAR')
      ])
    elif data['report_type'] == 'anual':
      id_registros = self.env['pabs.taxes'].search([
        ('company_id', '=', self.env.company.id),
        ('fecha_estatus', '>=', data['start_date']),
        ('fecha_estatus', '<=', data['end_date']),
        ('id_estatus.status', 'not in', ('REALIZADO','CANCELADO')),
        ('id_motivo.reason', '!=', 'REALIZADO POR COBRAR')
      ])
    elif data['report_type'] == 'cancelados':
      id_registros = self.env['pabs.taxes'].search([
        ('company_id', '=', self.env.company.id),
        ('fecha_estatus', '>=', data['start_date']),
        ('fecha_estatus', '<=', data['end_date']),
        ('id_estatus.status', '=', 'CANCELADO')
      ])
    
    ### GENERAMOS LA HOJA
    sheet = workbook.add_worksheet('Contratos')

    ### AGREGAMOS FORMATOS
    bold_format = workbook.add_format({'bold': True})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})
    
    ### INSERTAMOS LOS ENCABEZADOS PARA EL FORMATO
    for index, val in enumerate(HEADERS):
      sheet.write(0,index,val,bold_format)

    fila = 0
    ### INSERTAMOS LA INFORMACIÓN DE LOS CONTRATOS
    for reg in id_registros:
      fila = fila + 1
      
      sheet.write(fila, 0, reg.create_date, date_format)    #'Fecha de registro'
      sheet.write(fila, 1, reg.id_contrato.name)            #'Contrato'
      sheet.write(fila, 2, reg.fecha_estatus, date_format)  #'Fecha de estatus'
      sheet.write(fila, 3, reg.id_estatus.status)           #'Estatus'
      sheet.write(fila, 4, reg.id_motivo.reason)            #'Motivo'
      sheet.write(fila, 5, reg.costo, money_format)         #'Costo'
      sheet.write(fila, 6, reg.abonado, money_format)       #'Abonado'
      sheet.write(fila, 7, reg.iva, money_format)           #'IVA'
      sheet.write(fila, 8, reg.isr, money_format)           #'ISR'
