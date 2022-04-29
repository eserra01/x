# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz

HEADERS = [
  'Fecha Corte',
  'Codigo',
  'Asociado',
  'Oficina',
  'Empresa',
  'Plan',
  'Folio',
  'Estatus',
  'Inv. Inicial',
  'Toma Comision',
  'Importe',
  'Costo',
  'Forma Pago',
  'Referencia',
  'Origen Solicitud',
  #'Valor origen',
  #'Comentarios',
  'Esquema de pago',
  'Calle',
  'Número',
  'Colonia',
  'Municipio',
  'Telefono',
  'Nombre Titular']

class AccumulatedReport(models.TransientModel):
  _name = 'pabs.accumulated.report'
  _description = 'Reporte de Acumulados'

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
    return self.env.ref('pabs_reports.acumulated_report_xlsx').report_action(self, data=data)

class PabsAcumulatedReportXLSX(models.AbstractModel):
  _name = 'report.pabs_reports.acumulated_report_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    ### DECLARACIÓN DE OBJETOS
    closing_obj = self.env['closing.transfer.registry']
    contract_obj = self.env['pabs.contract']
    stock_move_obj = self.env['stock.move']
    picking_obj = self.env['stock.picking']

    ### GUARDAMOS LOS PARAMETROS
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    ### SI AGREGARON FECHA FINAL
    if end_date:
      closing_ids = closing_obj.search([
        ('date','>=',start_date),
        ('date','<=',end_date)],order="date")
      picking_ids = picking_obj.search([
        ('state','=','done'),
        ('origin','in',('cancelada','extravio')),
        ('date_done','>=',start_date),
        ('date_done','<=',end_date)],order="date_done")
      report_name = "Reporte de Acumulados {} - {}".format(start_date,end_date)

    ### SI SOLAMENTE AGREGA UNA FECHA
    else:
      closing_ids = closing_obj.search([
        ('date','=',start_date)], order="date")
      picking_ids = picking_obj.search([
        ('state','=','done'),
        ('origin','in',('cancelada','extravio')),
        ('date_done','=',start_date)],order="date_done")
      report_name = "Reporte de Acumulados de {}".format(start_date)

    ### GENERAMOS LA HOJA
    sheet = workbook.add_worksheet(report_name[:31])

    ### AGREGAMOS FORMATOS
    bold_format = workbook.add_format({'bold': True,'bg_color': '#2978F8'})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})

    ### INGRESAMOS LOS ENCABEZADOS
    for row, row_data in enumerate(HEADERS):
      sheet.write(0,row,row_data,bold_format)

    count = 1
    for picking_id in picking_ids:
      for line in picking_id.move_line_ids_without_package:
        sheet.write(count, 0, picking_id.date_done or "", date_format)
        sheet.write(count, 1, line.lot_id.employee_id.barcode or "")
        sheet.write(count, 2, line.lot_id.employee_id.name or "")
        sheet.write(count, 3, picking_id.location_dest_id.get_warehouse().name)
        sheet.write(count, 4, "COOPERATIVA PABS")
        sheet.write(count, 5, line.product_id.name or "")
        #sheet.write(count, 6, int(line.lot_id.name[6:]) or "")
        sheet.write(count, 6, line.lot_id.name or "")
        if picking_id.origin == 'cancelada':
          status = 'C'
        elif picking_id.origin == 'extravio':
          status = 'E'
        sheet.write(count, 7, status or "")
        sheet.write(count, 8, 0, money_format)
        sheet.write(count, 9, 0, money_format)
        sheet.write(count, 10, 0, money_format)
        sheet.write(count, 11, 0, money_format)
        sheet.write(count, 12, "")
        sheet.write(count, 13, "")
        sheet.write(count, 14, "")
        sheet.write(count, 15, "")
        count+=1
    for closing_id in closing_ids:
      for line in closing_id.picking_id.move_line_ids_without_package:
        sheet.write(count, 0, closing_id.date or "", date_format)
        sheet.write(count, 1, line.lot_id.employee_id.barcode or "")
        sheet.write(count, 2, line.lot_id.employee_id.name or "")
        sheet.write(count, 3, closing_id.warehouse_id.name or "")
        sheet.write(count, 4, "COOPERATIVA PABS")
        sheet.write(count, 5, line.product_id.name or "")
        #sheet.write(count, 6, int(line.lot_id.name[6:]) or "")
        sheet.write(count, 6, line.lot_id.name or "")
        contract_id = contract_obj.search([('lot_id','=',line.lot_id.id)], limit=1)
        if contract_id.state == 'precontract':
          status = 'F'
        elif contract_id.state == 'contract':
          status = 'V'
        sheet.write(count, 7, status or "")
        move_id = stock_move_obj.search([
          ('series','=',line.lot_id.name),
          ('codigo_de_activacion_valid','!=',False)],order="create_date desc",limit=1)
        sheet.write(count, 8, move_id.inversion_inicial or 0, money_format)
        sheet.write(count, 9, move_id.toma_comision or 0, money_format)
        sheet.write(count, 10, move_id.amount_received or 0, money_format)
        sheet.write(count, 11, contract_id.product_price or 0, money_format)
        sheet.write(count, 12, dict(move_id._fields['forma_pago'].selection).get(move_id.forma_pago) or "")
        sheet.write(count, 13, move_id.referencia or "")
        sheet.write(count, 14, dict(move_id._fields['origen_solicitud'].selection).get(move_id.origen_solicitud) or "")
        sheet.write(count, 15, contract_id.payment_scheme_id.name or "")
        sheet.write(count, 16, contract_id.street_name or "")
        sheet.write(count, 17, contract_id.street_number or "")
        sheet.write(count, 18, contract_id.neighborhood_id.name or "")
        sheet.write(count, 19, contract_id.municipality_id.name or "")
        sheet.write(count, 20, contract_id.phone or "")
        sheet.write(count, 21, contract_id.full_name or "")
        count+=1
        
    ### AFILIACIONES ELECTRÓNICAS ###
    afiliaciones = self.env['pabs.econtract.move'].sudo().search([
      ('company_id', '=', self.env.company.id),
      ('fecha_hora_cierre', '>=', '{} 00:00:00'.format(start_date) ),
      ('fecha_hora_cierre', '<=', '{} 23:59:59'.format(end_date) ),
      ('estatus', 'in', ('cerrado','confirmado'))
    ])

    for afi in afiliaciones:
      sheet.write(count, 0, afi.fecha_hora_cierre or "", date_format)
      sheet.write(count, 1, afi.id_asistente.barcode or "")
      sheet.write(count, 2, afi.id_asistente.name or "")
      sheet.write(count, 3, afi.id_contrato.lot_id.warehouse_id.name or "")
      sheet.write(count, 4, "AFILIACIONES ELECTRONICAS")
      sheet.write(count, 5, afi.id_contrato.name_service.name or "")
      sheet.write(count, 6, afi.id_contrato.lot_id.name or "")

      if afi.estatus == 'cerrado':
        status = 'F'
      elif afi.estatus == 'confirmado':
        status = 'V'
      sheet.write(count, 7, status or "")

      sheet.write(count, 8, afi.id_contrato.stationery or 0, money_format)
      sheet.write(count, 9, 0, money_format)
      sheet.write(count, 10, afi.id_contrato.initial_investment or 0, money_format)
      sheet.write(count, 11, afi.id_contrato.product_price or 0, money_format)
      sheet.write(count, 12, "")
      sheet.write(count, 13, "")
      sheet.write(count, 14, "")
      sheet.write(count, 15, "")
      sheet.write(count, 16, afi.id_contrato.street_name or "")
      sheet.write(count, 17, afi.id_contrato.street_number or "")
      sheet.write(count, 18, afi.id_contrato.neighborhood_id.name or "")
      sheet.write(count, 19, afi.id_contrato.municipality_id.name or "")
      sheet.write(count, 20, afi.id_contrato.phone or "")
      sheet.write(count, 21, afi.id_contrato.full_name or "")
      count+=1