# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz

HEADERS = [
  'Fecha de Contrato',
  'Contrato',
  'Cliente',
  'Domicilio',
  'Colonia',
  'Localidad',
  'Entre Calles',
  'Teléfono',
  'Promotor',
  'Cobrador',
  'Forma de Pago',
  'Fecha de Estatus',
  'Estatus',
  'Motivo',
  'Monto de Pago',
  'Servicio',
  'Costo',
  'Saldo',
  'Fecha de Ultimo Abono',
  'Estatus Moroso']

class DelinquentCustomer(models.TransientModel):
  _name = 'pabs.delinquent.customer'
  _description = 'Reporte Detallado de Morosos'

  def generate_pdf_report(self):
    ### ARMANDO LOS PARAMETROS
    data = {
      'date' : fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General'))
    }

    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_reports.delinquent_customer_report').report_action(self, data=data)

  def generate_xls_report(self):
    ### ARMANDO LOS PARAMETROS
    data = {
      'date' : fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General'))
    }

    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_reports.delinquent_customer_xlsx_report').report_action(self, data=data)

class DelinquentCustomerPDFReport(models.AbstractModel):
  _name = 'report.pabs_reports.delinquent_customer_report_template'

  @api.model
  def _get_report_values(self, docids, data):
    ### DECLARACIÓN DE OBJETOS
    contract_obj = self.env['pabs.contract']
    ### BUSCANDO PARAMETROS DE ENCABEZADO
    logo = self.env.user.company_id.logo
    date = data.get('data') or fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General'))

    ### BUSCAMOS TODOS LOS CONTRATOS
    all_contracts = contract_obj.search([
      ('state','=','contract')])

    ### BUSCAMOS LOS CONTRATOS SEMANALES QUE TENGAN MAS DE 14 DÍAS SIN ABONAR
    contract_week_ids = all_contracts.filtered(
      lambda k: k.way_to_payment == 'weekly').filtered(
      lambda k : k.days_without_payment >= 14)

    ### BUSCAMOS LOS CONTRATOS QUINCENALES QUE TENGAN MÁS DE 30 DÍAS SIN ABONAR
    contract_biweekly_ids = all_contracts.filtered(
      lambda k: k.way_to_payment == 'biweekly').filtered(
      lambda k: k.days_without_payment >= 30)

    ### BUSCAMOS LOS CONTRATOS MENSUALES QUE TENGAN MÁS DE 60 DÍAS SIN ABONAR
    contract_monthly_ids = all_contracts.filtered(
      lambda k: k.way_to_payment == 'monthly').filtered(
      lambda k: k.days_without_payment >= 60)

    ### JUNTAMOS TODOS LOS REGISTROS DE MOROSOS
    contract_ids = contract_week_ids + contract_biweekly_ids + contract_monthly_ids

    ### OBTENEMOS TODOS LOS COBRADORES DE LOS CONTRATOS
    collector_ids = contract_ids.mapped('debt_collector')

    ### DICCIONARIO QUE CONTENDRÁ TODA LA INFORMACIÓN DEL REPORTE
    data = {}

    ### RECORREMOS LA LISTA DE COBRADORES
    for collector_id in collector_ids:
      ### FILTRAMOS TODOS LOS CONTRATOS PERTENECIENTES AL COBRADOR
      collector_contract_ids = contract_ids.filtered(lambda k: k.debt_collector.id == collector_id.id)
      ### GENERAMOS EL ARRAY CON LA INFORMACIÓN
      info = []
      ### RECORREMOS TODOS LOS CONTRATOS
      for contract_id in collector_contract_ids:
        ### OBTENEMOS EL ULTIMO PAGO DEL CONTRATO
        last_payment = contract_id.payment_ids.filtered(
          lambda k: k.reference == 'payment').sorted(
          lambda k: k.payment_date).mapped('payment_date')
        ### SI EXISTEN PAGOS DEL TIPO ABONO
        if last_payment:
          ### TRAEMOS EL ULTIMO
          last_payment = last_payment[-1]
        ### SI NO
        else:
          ### ENVIAMOS VACIO
          last_payment = ' '
        ### VERIFICAMOS LA PERIODICIDAD
        ### SI ES SEMANAL
        if contract_id.way_to_payment == 'weekly':
          period = 'S'
        ### SI ES QUINCENAL
        elif contract_id.way_to_payment == 'biweekly':
          period = 'Q'
        ### SI ES MENSUAL
        elif contract_id.way_to_payment == 'monthly':
          period == 'M'
        ### SI NO ENCUENTRA EL MÉTODO
        else:
          period = ''
        ### GENERAMOS EL DICCIONARIO CON TODA LA INFORMACIÓN DEL CONTRATO
        detail = {
          'contract_name' : contract_id.name,
          'partner_name' : contract_id.full_name,
          'address' : "{} {}".format(contract_id.street_name_toll, contract_id.street_number_toll),
          'colony' : contract_id.toll_colony_id.name or '',
          'municipality' : contract_id.toll_municipallity_id.name or '',
          'last_payment' : last_payment,
          'period' : period or '',
        }
        ### AGREGAMOS LA INFORMACIÓN DEL CONTRATO A LA LISTA
        info.append(detail)
      ### AGREGAMOS LA LISTA DE CONTRATOS POR COBRADOR
      data.update({
        collector_id.name : info,
      })
    ### RETORNAMOS LA INFORMACIÓN
    return {
      'logo' : logo,
      'date' : date,
      'data' : data
    }

class DelinquentCustomerXLSXReport(models.AbstractModel):
  _name = 'report.pabs_reports.delinquent_customer_xls'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    ### DECLARACIÓN DE OBJETOS
    contract_obj = self.env['pabs.contract']
    ### BUSCANDO PARAMETROS DE ENCABEZADO
    logo = self.env.user.company_id.logo
    date = data.get('data') or fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General'))

    ### BUSCAMOS TODOS LOS CONTRATOS QUE TIENEN MÁS DE 14 DÍAS SIN ABONAR
    contract_week_ids = contract_obj.search([
      ('state','=','contract'),
      ('way_to_payment','=','weekly'),
      ('days_without_payment','>=',14)])

    contract_biweekly_ids = contract_obj.search([
      ('state','=','contract'),
      ('way_to_payment','=','biweekly'),
      ('days_without_payment','>=',30)])

    contract_monthly_ids = contract_obj.search([
      ('state','=','contract'),
      ('way_to_payment','=','monthly'),
      ('days_without_payment','>=',60)])

    contract_ids = contract_week_ids + contract_biweekly_ids + contract_monthly_ids

    ### OBTENEMOS TODOS LOS COBRADORES DE LOS CONTRATOS
    collector_ids = contract_ids.mapped('debt_collector')

    ### GENERAMOS LA HOJA
    sheet = workbook.add_worksheet("Reporte de Morosos {}".format(date))

    ### AGREGAMOS FORMATOS
    bold_format = workbook.add_format({'bold': True,'bg_color': '#2978F8'})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    money_format = workbook.add_format({'num_format': '$#,##0'})

    ### DICCIONARIO QUE CONTENDRÁ TODA LA INFORMACIÓN DEL REPORTE
    data = {}

    ### INSERTAMOS LOS ENCABEZADOS
    for row, row_data in enumerate(HEADERS):
      sheet.write(0,row,row_data,bold_format)


    ### RECORREMOS LA LISTA DE COBRADORES
    for collector_id in collector_ids:
      ### FILTRAMOS TODOS LOS CONTRATOS PERTENECIENTES AL COBRADOR
      collector_contract_ids = contract_ids.filtered(lambda k: k.debt_collector.id == collector_id.id)
      ### GENERAMOS EL ARRAY CON LA INFORMACIÓN
      info = []
      ### RECORREMOS TODOS LOS CONTRATOS
      count = 1
      for contract_id in collector_contract_ids:
        ### OBTENEMOS EL ULTIMO PAGO DEL CONTRATO
        last_payment = contract_id.payment_ids.filtered(
          lambda k: k.reference == 'payment').sorted(
          lambda k: k.payment_date).mapped('payment_date')
        ### SI EXISTEN PAGOS DEL TIPO ABONO
        if last_payment:
          ### TRAEMOS EL ULTIMO
          last_payment = last_payment[-1]
        ### SI NO
        else:
          ### ENVIAMOS VACIO
          last_payment = ' '
        ### VERIFICAMOS LA PERIODICIDAD
        ### SI ES SEMANAL
        if contract_id.way_to_payment == 'weekly':
          period = 'S'
        ### SI ES QUINCENAL
        elif contract_id.way_to_payment == 'biweekly':
          period = 'Q'
        ### SI ES MENSUAL
        elif contract_id.way_to_payment == 'monthly':
          period == 'M'
        ### SI NO ENCUENTRA EL MÉTODO
        else:
          period = ''
        ### SE EMPIEZA A ESCRIBIR EL DATO
        sheet.write(count, 0, contract_id.invoice_date or "", date_format)
        sheet.write(count, 1, contract_id.name or "")
        sheet.write(count, 2, contract_id.full_name or "")
        sheet.write(count, 3, "{} {}".format(contract_id.street_name_toll or "", contract_id.street_number_toll or ""))
        sheet.write(count, 4, contract_id.toll_colony_id.name or "")
        sheet.write(count, 5, contract_id.toll_municipallity_id.name or "")
        sheet.write(count, 6, contract_id.between_streets_toll or "")
        sheet.write(count, 7, contract_id.phone_toll or "")
        sheet.write(count, 8, contract_id.sale_employee_id.name or "")
        sheet.write(count, 9, contract_id.debt_collector.name or "")
        sheet.write(count, 10, period or "")
        sheet.write(count, 11, contract_id.date_of_last_status or "", date_format)
        sheet.write(count, 12, contract_id.contract_status_item.status or "")
        sheet.write(count, 13, contract_id.contract_status_reason.reason or "")
        sheet.write(count, 14, contract_id.payment_amount or "")
        sheet.write(count, 15, contract_id.name_service.name or "")
        sheet.write(count, 16, contract_id.product_price or "")
        sheet.write(count, 17, contract_id.balance or "")
        sheet.write(count, 18, last_payment or "", date_format)
        sheet.write(count, 19, "MOROSO")
        count += 1