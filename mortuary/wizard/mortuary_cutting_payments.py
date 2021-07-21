# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import ValidationError
from dateutil import tz

HEADERS = [
  'Número de pago',
  'Fecha de Pago',
  'Contrato / Bitacora',
  'Tipo de Servicio',
  'Nombre',
  'Efectivo',
  'Transferencia',
  'T.Crédito',
  'Total']

class CuttingMortuaryPayments(models.TransientModel):
  _name = 'mortuary.cutting.payments'
  _description = 'Corte de pagos de funeraria'

  start_date = fields.Date(string='Fecha Inicial',
    default=fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General')),
    required=True)

  end_date = fields.Date(string='Fecha Final')

  def print_report(self):
    ### BUSCAMOS PAGOS DE FUNERARIA
    payment_obj = self.env['account.payment']
    ### GENERAMOS DOMINIO
    domain = [('state','=','posted'),
      ('reference','=','payment_mortuary')]
    ### SI TIENE FECHA FINAL
    if self.end_date:
      ### AGREGAMOS RANGO DE FECHAS
      domain.append(('payment_date','>=',self.start_date))
      domain.append(('payment_date','<=',self.end_date))
      name = 'del {} al {}'.format(self.start_date, self.end_date)
    ### SI NO
    else:
      ### AGREGAMOS LA UNICA FECHA EN EL DOMINIO
      domain.append(('payment_date','=',self.start_date))
      name = 'del {}'.format(self.start_date)
    ### BUSCAMOS LOS PAGOS CON LOS PARAMETROS DE BUSQUEDA GENERADOS
    payment_ids = payment_obj.search(domain)
    ### SI NO SE ENCONTRÓ NINGÚN PAGO
    if not payment_ids:
      ### MENSAJE DE ERROR
      raise ValidationError("No existen pagos para procesar")
    ### AGREGAMOS PARAMETROS AL DATA
    data = {
      'name' : name,
      'start_date' : self.start_date,
      'end_date' : self.end_date,
      'payment_ids' : payment_ids.ids
    }
    ### verificamos el tipo de reporte que va a traer
    if self._context.get('type_report') == 'pdf':
      ### RETORNAMOS EL REPORTE
      return self.env.ref('mortuary.report_mortuary_payments').report_action(self, data=data)
    ### SI EL TIPO DE REPORTE ES EN XLSX
    elif self._context.get('type_report') == 'xlsx':
      ### RETORNAMOS EL REPORTE EN EXCEL
      return self.env.ref('mortuary.report_mortuary_payments_xlsx').report_action(self, data=data)
    else:
      raise ValidationError("No se encontró plantilla de reporte, favor de verificar con sistemas")


class CuttingMortuaryPDFReport(models.AbstractModel):
  _name = 'report.mortuary.mortuary_payment_report'

  @api.model
  def _get_report_values(self, docids, data):
    ### DECALRAMOS OBJETOS
    payment_obj = self.env['account.payment']
    ### SI VIENEN PAGOS
    if data.get('payment_ids'):
      ### OBTENEMOS LOS OBJETOS DE LOS PAGOS
      payment_ids = payment_obj.browse(data.get('payment_ids'))
    return {
      'data' : data,
      'payment_ids' : payment_ids
    }

class CuttingMortuaryXLSXReport(models.AbstractModel):
  _name = 'report.mortuary.mortuary_payment_report_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    ### DECALRAMOS OBJETOS
    payment_obj = self.env['account.payment']
    ### SI VIENEN PAGOS
    if data.get('payment_ids'):
      ### OBTENEMOS LOS OBJETOS DE LOS PAGOS
      payment_ids = payment_obj.browse(data.get('payment_ids'))

    ### GENERAMOS LA HOJA
    sheet = workbook.add_worksheet(data.get('name'))

    ### AGREGAMOS FORMATOS
    bold_format = workbook.add_format({'bold': True,'bg_color': '#2978F8'})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})

     ### INSERTAMOS LOS ENCABEZADOS
    for row, row_data in enumerate(HEADERS):
      sheet.write(0,row,row_data,bold_format)

    ### VARIABLES DE CONTROL
    count = 1
    cash = 0
    transfer = 0
    credit_card = 0
    total = 0

    ### RECORREMOS TODOS LOS PAGOS
    for payment_id in payment_ids:
      ### ESCRIBIMOS EL NÚMERO DE PAGO
      sheet.write(count, 0, payment_id.name or '')
      ### ESCRIBIMOS LA FECHA DEL PAGO
      sheet.write(count, 1, payment_id.payment_date or '', date_format)
      ### ESCRIBIMOS EL CONTRATO / BITACORA
      sheet.write(count, 2, payment_id..binnacle.name or '')
      ### ESCRIBIMOS EL TIPO DE SERVICIO
      sheet.write(count, 3, payment_id.binnacle.ds_tipo_de_servicio.name or '')
      ### ESCRIBIMOS EL NOMBRE (FINADO)
      sheet.write(count, 4, payment_id.binnacle.ii_finado or '')
      ### ESCRIBIMOS SI EL PAGO FUE EN EFECTIVO
      if payment_id.way_to_pay == 'cash':
        sheet.write(count, 5, payment_id.amount or 0, money_format)
        cash = cash + payment_id.amount
      else:
        sheet.write(count, 5, 0, money_format)
      ### ESCRIBIMOS SI EL PAGO FUE EN TRANSFERENCIA
      if payment_id.way_to_pay == 'transfer':
        sheet.write(count, 6, payment_id.amount or 0, money_format)
        transfer = transfer + payment_id.amount
      else:
        sheet.write(count, 6, 0, money_format)
      ### ESCRIBIMOS SI EL PAGO FUE POR TARJETA DE CRÉDITO
      if payment_id.way_to_pay == 'credit_card':
        sheet.write(count, 7, payment_id.amount or 0, money_format)
        credit_card = credit_card + payment_id.amount
      else:
        sheet.write(count, 7, 0, money_format)
      ### ESCRIBIMOS EL TOTAL DEL REGISTRO
      sheet.write(count, 8, payment_id.amount or 0, money_format)
      total = total + payment_id.amount
      ### INCREMENTAMOS VARIABLE DE CONTROL
      count += 1
    ### ESCRIBIMOS LAS VARIABLES ACUMULADAS
    sheet.write(count, 5, cash, money_format)
    sheet.write(count, 6, transfer, money_format)
    sheet.write(count, 7, credit_card, money_format)
    sheet.write(count, 8, total, money_format)
