# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz
import logging

HEADERS = [
  'Feche de Contrato',
  'Contrato',
  'N. Solicitud',
  'Cliente',
  'Domicilio',
  'Colonia',
  'Localidad',
  'Entre Calles',
  'Teléfono',
  'Promotor',
  'Cobrador',
  'Forma de Pago',
  'Fecha Estatus',
  'Estatus',
  'Motivo',
  'Id Contrato',
  'Monto Pago Actual',
  'Servicio',
  'Costo',
  'Saldo',
  'PAPE',
  'Comisión PAPE',
  'Comisión Restante PAPE',
  'PROM',
  'Comisión PROM',
  'Comisión Restante PROM',
  'CORD',
  'Comisión CORD',
  'Comisión Restante CORD',
  'GTE',
  'Comisión GTE',
  'Comisión Restante GTE',
  'FIDE',
  'Comisión FIDE',
  'Comisión Restante FIDE',
  'Ultimo Abono',
  'Recibo',
  'Importe',
  'Estatus',
  'Días sin Abonar',
  'Monto Atrasado']

_logger = logging.getLogger(__name__)

class DailyHelps(models.TransientModel):
  _name = 'pabs.daily.helps'
  _description = 'Wizard para reporte de ayudas diarias'

  start_date = fields.Date(string='Fecha de inicio',
    default=fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General')),
    required=True)

  end_date = fields.Date(string='Fecha de Fin')

  def print_xls_report(self):
    ### ARMANDO LOS PARAMETROS
    data = {
      'start_date' : self.start_date,
      'end_date' : self.end_date,
    }
    ### RETORNAMOS EL REPORTE

    return self.env.ref('pabs_reports.daily_helps_xlsx').report_action(self, data=data)

class PabsReportXLSX(models.AbstractModel):
  _name = 'report.pabs_reports.daily_helps_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    ### DECLARACIÓN DE OBJETOS
    contract_obj = self.env['pabs.contract'].sudo()

    ### GUARDAMOS LOS PARAMETROS
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    ### SI AGREGARON FECHA FINAL
    if end_date:
      contract_ids = contract_obj.search([
        ('state','=','contract'),
        ('invoice_date','>=',start_date),
        ('invoice_date','<=',end_date)],order="invoice_date")
      report_name = "Ayudas Diarias de {} - {}".format(start_date,end_date)
    ### SI SOLAMENTE AGREGA UNA FECHA
    else:
      contract_ids = contract_obj.search([
        ('state','=','contract'),
        ('invoice_date','=',start_date)], order="invoice_date")
      report_name = "Ayudas Diarias de {}".format(start_date)
    ### SI NO SE ENCONTRARÓN CONTRATOS
    if not contract_ids:
      ### MENSAJE DE ERROR
      raise ValidationError((
        "No hay contratos para el día: {}".format(start_date)))
    ### GENERAMOS LA HOJA
    sheet = workbook.add_worksheet(report_name[:31])
    ### AGREGAMOS FORMATOS
    bold_format = workbook.add_format({'bold': True})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    money = workbook.add_format({'num_format': '$#,##0'})
    ### INSERTAMOS LOS ENCABEZADOS PARA EL FORMATO
    for index, val in enumerate(HEADERS):
      sheet.write(0,index,val,bold_format)
    ### INSERTAMOS LA INFORMACIÓN DE LOS CONTRATOS
    for rec_index,contract_id in enumerate(contract_ids):
      rec_index+=1
      count = 0
      sheet.write(rec_index,count,contract_id.invoice_date or "",date_format)
      count+=1
      sheet.write(rec_index,count,contract_id.name or "")
      count+=1
      sheet.write(rec_index,count,contract_id.lot_id.name or "")
      count+=1
      sheet.write(rec_index,count,contract_id.full_name or "")
      count+=1
      street = contract_id.street_name
      number = contract_id.street_number
      address = ""
      if street:
        address = address + street
      if number:
        address = address + " " + number
      sheet.write(rec_index,count,address or "")
      count+=1
      neightborhood = ""
      if contract_id.neighborhood_id:
        neighborhood = contract_id.neighborhood_id.name
      sheet.write(rec_index,count,neighborhood or "")
      count+=1
      sheet.write(rec_index,count,contract_id.municipality_id.name or "")
      count+=1
      sheet.write(rec_index,count,contract_id.between_streets or "")
      count+=1
      sheet.write(rec_index,count,contract_id.phone or "")
      count+=1
      sheet.write(rec_index,count,contract_id.sale_employee_id.name or "")
      count+=1
      sheet.write(rec_index,count,contract_id.debt_collector.name or "")
      count+=1
      sheet.write(rec_index,count,dict(contract_id._fields['way_to_payment'].selection).get(contract_id.way_to_payment) or "")
      count+=1
      sheet.write(rec_index,count,contract_id.date_of_last_status,date_format or "")
      count+=1
      sheet.write(rec_index,count,contract_id.contract_status_item.status or "")
      count+=1
      sheet.write(rec_index,count,contract_id.contract_status_reason.reason or "")
      count+=1
      sheet.write(rec_index,count,contract_id.id or "")
      count+=1
      sheet.write(rec_index,count,contract_id.payment_amount,money or "")
      count+=1
      sheet.write(rec_index,count,contract_id.name_service.name or "")
      count+=1
      sheet.write(rec_index,count,contract_id.product_price,money or "")
      count+=1
      sheet.write(rec_index,count,contract_id.balance,money or "")
      count+=1
      stationery = contract_id.commission_tree.filtered(lambda t: t.job_id.name == "PAPELERIA")
      if stationery:
        sheet.write(rec_index,count,stationery.comission_agent_id.name or "")
        count+=1
        sheet.write(rec_index,count,stationery.corresponding_commission or "",money)
        count+=1
        sheet.write(rec_index,count,stationery.remaining_commission or "",money)
        count+=1
      else:
        sheet.write(rec_index,count,"")
        count+=1
        sheet.write(rec_index,count,"")
        count+=1
        sheet.write(rec_index,count,"")
        count+=1
      asistant_social = contract_id.commission_tree.filtered(lambda t: t.job_id.name == "ASISTENTE SOCIAL")
      if asistant_social:
        sheet.write(rec_index,count,asistant_social.comission_agent_id.name or "")
        count+=1
        sheet.write(rec_index,count,asistant_social.corresponding_commission or "",money)
        count+=1
        sheet.write(rec_index,count,asistant_social.remaining_commission or "",money)
        count+=1
      else:
        sheet.write(rec_index,count,"")
        count+=1
        sheet.write(rec_index,count,"")
        count+=1
        sheet.write(rec_index,count,"")
        count+=1
      coord = contract_id.commission_tree.filtered(lambda t: t.job_id.name == "COORDINADOR")
      if asistant_social:
        sheet.write(rec_index,count,coord.comission_agent_id.name or "")
        count+=1
        sheet.write(rec_index,count,coord.corresponding_commission or "",money)
        count+=1
        sheet.write(rec_index,count,coord.remaining_commission or "",money)
        count+=1
      else:
        sheet.write(rec_index,count,"")
        count+=1
        sheet.write(rec_index,count,"")
        count+=1
        sheet.write(rec_index,count,"")
        count+=1
      manager = contract_id.commission_tree.filtered(lambda t: t.job_id.name == "GERENTE DE OFICINA")
      if manager:
        sheet.write(rec_index,count,manager.comission_agent_id.name or "")
        count+=1
        sheet.write(rec_index,count,manager.corresponding_commission or "",money)
        count+=1
        sheet.write(rec_index,count,manager.remaining_commission or "",money)
        count+=1
      else:
        sheet.write(rec_index,count,"")
        count+=1
        sheet.write(rec_index,count,"")
        count+=1
        sheet.write(rec_index,count,"")
        count+=1
      fide = contract_id.commission_tree.filtered(lambda t: t.job_id.name == "FIDEICOMISO")
      if fide:
        sheet.write(rec_index,count,fide.comission_agent_id.name or "")
        count+=1
        sheet.write(rec_index,count,fide.corresponding_commission or "",money)
        count+=1
        sheet.write(rec_index,count,fide.remaining_commission or "",money)
        count+=1
      else:
        sheet.write(rec_index,count,"")
        count+=1
        sheet.write(rec_index,count,"")
        count+=1
        sheet.write(rec_index,count,"")
        count+=1
      for payment_id in contract_id.payment_ids.sorted(key=lambda r: r.payment_date,reverse=True):
        sheet.write(rec_index,count,payment_id.name or "")
        count+=1
        payment_name = payment_id.Ecobro_receipt or payment_id.name
        sheet.write(rec_index,count,payment_name or "")
        count+=1
        sheet.write(rec_index,count,payment_id.amount or "",money)
        count+=1
        sheet.write(rec_index,count,dict(payment_id._fields['state'].selection).get(payment_id.state) or "")
        count+=1
        break
      sheet.write(rec_index,count,contract_id.days_without_payment or "")
      count+=1
      sheet.write(rec_index,count,contract_id.late_amount or "",money)
      count+=1
    #_logger.warning("lista recibida: {}".format(data))
    ### RECORRER LA INFORMACIÓN RECOPILADA
    """for row_index, row_data in enumerate(data):
      row_index+=1
      for cols_index, cols_data in enumerate(row_data):
        sheet.write(row_index,cols_index,cols_data)"""
