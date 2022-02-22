# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz

HEADERS = [
  'CONTRATO',
  'CLIENTE',
  'DOMICILIO',
  'COLONIA',
  'LOCALIDAD',
  'F.P',
  'FECHA PRIMER ABONO',
  'ULT F. ABONO',
  'TELÉFONO',
  'ESTATUS']

class PabsDebtCollector(models.TransientModel):
  _name = 'pabs.debt.collector.wizard'
  _description = 'Reporte de cartera de Cobradores'

  debt_collector_id = fields.Many2one(comodel_name='hr.employee',
    string='Cobrador')

  def print_pdf_report(self):
    data = {}
    if self.debt_collector_id:
      data.update({
        'collector_id' : self.debt_collector_id.id,
      })
    return self.env.ref('pabs_reports.debt_collector_pdf_report').report_action(self, data=data)

  def print_xls_report(self):
    data = {}
    if self.debt_collector_id:
      data.update({
        'collector_id' : self.debt_collector_id.id,
      })
    return self.env.ref('pabs_reports.debt_collector_xlsx_report').report_action(self, data=data)

class PabsDebtCollectorReportPDF(models.AbstractModel):
  _name = 'report.pabs_reports.debt_collector_pdf_template'

  @api.model
  def _get_report_values(self, docids, data):
    ### DECLARACIÓN DE OBJETOS
    employee_obj = self.env['hr.employee']
    contract_obj = self.env['pabs.contract']
    status_obj = self.env['pabs.contract.status']
    ### BUSCAMOS LOS ESTATUS
    status_ids = status_obj.search([('status','in',('ACTIVO','SUSP. TEMPORAL'))])
    logo = self.env.user.company_id.logo
    rec_data = {}
    ### SI CAPTURARON EL COBRADOR
    if data.get('collector_id'):
      collector = employee_obj.browse(data.get('collector_id'))
      all_contracts = contract_obj.search([
        ('state','=','contract'),
        ('contract_status_item','in',status_ids.ids),
        ('debt_collector','=',collector.id)])
    ### SI NO SE CAPTURÓ NADA
    else:
      all_contracts = contract_obj.search([
        ('state','=','contract'),
        ('contract_status_item','in',status_ids.ids)])
    ### SI NO HAY CONTRATOS
    if not all_contracts:
      ### MENSAJE DE ERROR
      raise ValidationError("No se encontrarón contratos para procesar")
    ### FILTRAMOS LOS COBRADORES
    debt_collectors = all_contracts.mapped('debt_collector')
    ### RECORREMOS LOS CONTRATOS POR COBRADOR
    for collector_id in debt_collectors:
      ### FILTRAMOS TODOS LOS CONTRATOS QUE PERTENEZCAN A DICHO COBRADOR
      contract_ids = all_contracts.filtered(lambda r: r.debt_collector.id == collector_id.id)
      contracts_data = []
      ### RECORREMOS LOS CONTRATOS
      for contract_id in contract_ids:
        if contract_id.way_to_payment == 'weekly':
          payment_way = 'S'
        elif contract_id.way_to_payment == 'biweekly':
          payment_way = 'Q'
        elif contract_id.way_to_payment == 'monthly':
          payment_way = 'M'
        else:
          payment_way = ''
        last_payment = contract_id.payment_ids.filtered(lambda r: r.state in ('posted','reconciled','sent')).sorted(key=lambda r: r.payment_date)[-1]
        # Formato de dirección
        address = ''
        neightborhood = ''         
        if contract_id.street_name_toll:
          address =  "{} {}".format(contract_id.street_name_toll,'#' + str(contract_id.street_number_toll) if contract_id.street_number_toll else '')
          neightborhood = contract_id.toll_colony_id.name if contract_id.toll_colony_id else ''
        else:
          address =  "{} {}".format(contract_id.street_name,'#' + str(contract_id.street_number) if contract_id.street_number else '')
          neightborhood = contract_id.neighborhood_id.name if contract_id.neighborhood_id else ''
        contracts_data.append({
          'contract' : contract_id.name,
          'partner_name' : contract_id.full_name,
          'address' : address,
          'neightborhood' : contract_id.toll_colony_id.name or '',
          'locality_id' : contract_id.toll_municipallity_id.name or '',
          'payment_way' : payment_way or '',
          'last_payment' : last_payment.date_receipt if last_payment.date_receipt else last_payment.payment_date,
          'phone' : contract_id.phone_toll or contract_id.phone or '',
          'status' : 'Activo' if contract_id.contract_status_item.status == 'ACTIVO' else 'Inactivo',
        })
      rec_data.update({
        collector_id.name : contracts_data
      })
    return {
      'logo' : logo,
      'count_contracts' : len(all_contracts),
      'data' : rec_data
    }

class PabsDebtCollectorReportXLSX(models.AbstractModel):
  _name = 'report.pabs_reports.debt_collector_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    ### DECLARACIÓN DE OBJETOS
    employee_obj = self.env['hr.employee']
    contract_obj = self.env['pabs.contract']
    status_obj = self.env['pabs.contract.status']
    ### BUSCAMOS LOS ESTATUS
    status_ids = status_obj.search([('status','in',('ACTIVO','SUSP. TEMPORAL'))])
    logo = self.env.user.company_id.logo
    rec_data = {}
    ### SI CAPTURARON EL COBRADOR
    if data.get('collector_id'):
      collector = employee_obj.browse(data.get('collector_id'))
      all_contracts = contract_obj.search([
        ('state','=','contract'),
        ('contract_status_item','in',status_ids.ids),
        ('debt_collector','=',collector.id)])
    ### SI NO SE CAPTURÓ NADA
    else:
      all_contracts = contract_obj.search([
        ('state','=','contract'),
        ('contract_status_item','in',status_ids.ids)])
    if not all_contracts:
      raise ValidationError("No se encontrarón contratos para procesar")

    ### GENERAMOS LA HOJA
    sheet = workbook.add_worksheet("Reporte de Cartera de Cobradores")

    ### AGREGAMOS FORMATOS
    header_format = workbook.add_format({'bold': True,'bg_color': '#2978F8','align': 'center'})
    bold_format = workbook.add_format({'bold': True,'align': 'center'})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})

    sheet.merge_range('A1:I1', "REPORTE DE CARTERA DE COBRADORES", header_format)

    ### FILTRAMOS LOS COBRADORES
    debt_collectors = all_contracts.mapped('debt_collector')

    count = 2
    ### RECORREMOS LOS CONTRATOS POR COBRADOR
    for collector_id in debt_collectors:
      ### FILTRAMOS TODOS LOS CONTRATOS QUE PERTENEZCAN A DICHO COBRADOR
      contract_ids = all_contracts.filtered(lambda r: r.debt_collector.id == collector_id.id)
      ### ENCABEZADOS DE COBRADORES
      sheet.write(count, 1, "Cobrador: {}".format(collector_id.name), bold_format)
      sheet.write(count, 2, "Contratos: {}".format(len(contract_ids)), bold_format)
      count += 1
      ### ENCABEZADOS
      for row, row_data in enumerate(HEADERS):
        sheet.write(count, row, row_data, bold_format)
      ### RECORREMOS LOS CONTRATOS
      for contract_id in contract_ids:
        if contract_id.way_to_payment == 'weekly':
          payment_way = 'S'
        elif contract_id.way_to_payment == 'biweekly':
          payment_way = 'Q'
        elif contract_id.way_to_payment == 'monthly':
          payment_way = 'M'
        else:
          payment_way = ''
        last_payment = contract_id.payment_ids.filtered(lambda r: r.state in ('posted','reconciled','sent')).sorted(key=lambda r: r.payment_date)[-1]
        ### ESTADOS
        state = 'Activo' if contract_id.contract_status_item.status == 'ACTIVO' else 'Inactivo'
        count+= 1
        ### CONTRATOS
        sheet.write(count, 0, contract_id.name or '')
        ### CLIENTES
        sheet.write(count, 1, contract_id.full_name or '')
        ### DOMICILIO
        street = ''
        if contract_id.street_name_toll:
          if contract_id.street_number_toll:
            street = "{} #{}".format(contract_id.street_name_toll, contract_id.street_number_toll)
          else:
            street = contract_id.street_name_toll
        elif contract_id.street_name:
          if contract_id.street_number:
            street = "{} #{}".format(contract_id.street_name, contract_id.street_number)
          else:
            street = contract_id.street_name
        sheet.write(count, 2, street)
        ### COLONIA
        sheet.write(count, 3, contract_id.toll_colony_id.name or '')
        ### LOCALIDAD
        sheet.write(count, 4, contract_id.toll_municipallity_id.name or '')
        ### F.P
        sheet.write(count, 5, payment_way or '')
        ### FECHA DE PRIMER ABONO
        sheet.write(count, 6, contract_id.date_first_payment or '', date_format)
        ### ULT F. ABONO
        sheet.write(count, 7, last_payment.date_receipt if last_payment.date_receipt else last_payment.payment_date, date_format)
        ### TELEFONO
        sheet.write(count, 8, contract_id.phone_toll or contract_id.phone or '')
        ### ESTATUS
        sheet.write(count, 9, state or '')
      count += 4
