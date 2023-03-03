# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz

HEADERS = [
  'Fecha Corte',
  'Solicitud',
  'Estatus',
  'Cliente',
  'Teléfono',
  'Calle',
  'Exterior',
  'Interior',
  'Colonia',
  'Localidad',
  'Fecha de nacimiento',
  'Plan',
  'Inversión Inicial',
  'Asistente',
  'Oficina',
  'Origen',
  'Fecha de Captura',
  'Clave de Activación',
  'Agente',
  'Comentarios',
  'Referencia']

class CallCenterVerificationReport(models.TransientModel):
  _name = 'pabs.call.center.verification.report'
  _description = 'Reporte Verificación Corte de solicitudes'

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

    return self.env.ref('pabs_reports.verification_report').report_action(self, data=data)

class PabsVerificationReportXLSX(models.AbstractModel):
  _name = 'report.pabs_reports.verification_report_xlsx'
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

    # ### SI NO SE ENCONTRARON REGISTROS COINCIDENTES
    # if not closing_ids:
    #   raise ValidationError((
    #     "No se encontraron registros para procesar"))

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
    for closing_id in closing_ids:
      for line in closing_id.picking_id.move_line_ids_without_package:
        contract_id = contract_obj.search([('lot_id','=',line.lot_id.id)], limit=1)
        move_id = stock_move_obj.search([
          ('series','=',line.lot_id.name),
          ('codigo_de_activacion_valid','!=',False)],order="create_date desc",limit=1)
        ### Fecha Corte
        sheet.write(count, 0, closing_id.date or "", date_format)
        ### Solicitud
        sheet.write(count, 1, line.lot_id.name or "")
        ### Estatus
        sheet.write(count, 2, "RECIBIDO")
        ### Cliente
        sheet.write(count, 3, contract_id.full_name or "")
        ### Teléfono
        sheet.write(count, 4, contract_id.phone or "")
        ### Calle
        sheet.write(count, 5, contract_id.street_name or "")
        ### Exterior
        sheet.write(count, 6, contract_id.street_number or "")
        ### Interior
        sheet.write(count, 7, "")
        ### Colonia
        sheet.write(count, 8, contract_id.neighborhood_id.name or "")
        ### Localidad
        sheet.write(count, 9, contract_id.municipality_id.name or "")
        ### Fecha de nacimiento
        sheet.write(count, 10, contract_id.birthdate or "", date_format)
        ### Plan
        sheet.write(count, 11, line.product_id.name or "")
        ### Inversión inicial
        sheet.write(count, 12, move_id.inversion_inicial or 0, money_format)
        ### Asistente
        sheet.write(count, 13, contract_id.lot_id.employee_id.name or "")
        ### Oficina
        sheet.write(count, 14, line.lot_id.warehouse_id.name or "")
        ### Origen
        sheet.write(count, 15, dict(move_id._fields['origen_solicitud'].selection).get(move_id.origen_solicitud) or "")
        ### Fecha de Captura
        sheet.write(count, 16, contract_id.create_date or "", date_format)
        ### Clave de activación
        sheet.write(count, 17, contract_id.activation_code or "")
        ### Agente que activo
        sheet.write(count, 18, contract_id.agent_id or "")
        ### Comentarios
        sheet.write(count, 19, contract_id.comments or "")
        ### Reference
        sheet.write(count, 20, move_id.referencia or "")
        count+=1