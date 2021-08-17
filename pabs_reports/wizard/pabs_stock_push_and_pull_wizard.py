# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime

HEADERS = [
  'FECHA',
  'REFERENCIA',
  'ENTRADA',
  'SALIDA',
  'EXISTENCIA',
  'COSTO UNITARIO',
  'DEBE',
  'HABER',
  'SALDO']

class StockPushAndPullWizard(models.TransientModel):
  _name = 'pabs.stock.push_and_pull_wizard'
  _description = 'Reporte de Entradas y Salidas de Ataudes y Urnas'

  product_id = fields.Many2one(comodel_name='product.product',
    string='Articulo',
    required=True)

  start_date = fields.Date(string='Fecha Inicio',
    default=fields.Date.today(),
    required=True)

  end_date = fields.Date(string='Fecha Final')

  def print_xls_report(self):
    ### DECLARACIÓN DE OBJETOS
    order_line_obj = self.env['purchase.order.line']
    stock_obj = self.env['stock.move']
    location_obj = self.env['stock.location']

    ### BUSCAMOS LAS UBICACIONES DE CLIENTES
    location_ids = location_obj.search([('usage','=','customer')])

    records = []

    ### ENCONTRAMOS LAS VARIABLES
    product_id = self.product_id
    start_date = self.start_date
    end_date = self.end_date

    ### GENERAMOS EL ULTIMO MOMENTO DEL DÍA
    date_qty = datetime.strptime('{} 23:59:59'.format(start_date),"%Y/%m/%d %H:%M:%S")

    ### LA CANTIDAD QUE HABIA A LA FECHA INGRESADA
    qty_product = product_id.with_context({'to_date': date_qty}).qty_available

    ### GENEERAMOS DOMINIO DE BUSQUEDA
    domain = [
      ('qty_received','>',0),
      ('product_id','=',product_id.id),
      ('date_planned','>=','{} 00:00:00'.format(start_date)),
      ('date_planned','<=','{} 23:59:59'.format(end_date or start_date))]

    ### BUSCAMOS LOS PEDIDOS DE COMPRA DONDE EXISTA ESE PRODUCTO
    line_ids = order_line_obj.search(domain, order="date_planned")

    existants = qty_product
    total = (product_id.standard_price * existants)
    ### RECORREMOS LOS REGISTROS ENCONTRADOS
    for count,line_id in enumerate(line_ids):
      ### CARGAMOS EXISTENCIAS + LO RECIBIDO
      if count == 0:
        existants = qty_product + line_id.qty_received
      ### CAPTURAMOS LOS DEBITOS
      debit = total = (product_id.standard_price * existants)
      ### AGREGAMOS LA INFORMACIÓN A UNA LISTA
      records.append({
        'date' : line_id.date_planned.date(),
        'ref' : line_id.order_id.name,
        'push' : line_id.qty_received,
        'output' : '',
        'exist' : existants,
        'cost' : product_id.standard_price,
        'debit' : debit,
        'credit' : '',
        'saldo' : total
      })
    if not records:
      records.append({
        'date' : '',
        'ref' : '',
        'push' : '',
        'output' : '',
        'exist' : existants,
        'cost' : '',
        'debit' : '',
        'credit' : '',
        'saldo' : total,
      })

    ### GENERAMOS DOMINIO PARA LAS SALIDAS DE INVENTARIO
    domain_out = [
      ('location_dest_id','in',location_ids.ids),
      ('state', '=', 'done'),
      ('product_id','=',product_id.id),
      ('date_expected','>=','{} 00:00:00'.format(start_date)),
      ('date_expected','<=','{} 23:59:59'.format(end_date or start_date))]

    ### BUSCAMOS LAS SALIDAS CON LOS PARAMETROS DE BUSQUEDA
    move_ids = stock_obj.search(domain_out)

    ### RECORREMOS LOS REGISTROS ENCONTRADOS
    for move_id in move_ids:
      existants = (existants - move_id.product_qty)
      credit = (product_id.standard_price * move_id.product_qty)
      total = total - credit
      records.append({
        'date' : move_id.date_expected.date(),
        'ref' : move_id.service_number,
        'push' : '',
        'output' : move_id.product_qty,
        'exist' : existants,
        'cost' : product_id.standard_price,
        'debit' : '',
        'credit' : credit,
        'saldo' : total
      })

    if not records:
      raise ValidationError("No se encontró información para procesar")

    data = {'product_id': product_id.id, 'records' : records}
    return self.env.ref('pabs_reports.stock_push_and_pull_report_xlsx').report_action(self, data=data)

class StockPushAndPullReportXLSX(models.AbstractModel):
  _name = 'report.pabs_reports.push_and_pull_stock_xlsx'
  _inherit = 'report.report_xlsx.abstract'


  def generate_xlsx_report(self, workbook, data, lines):
    product_obj = self.env['product.product']

    product_id = product_obj.browse(data['product_id'])

    ### GENERAMOS LA HOJA
    sheet = workbook.add_worksheet("Entradas y Salidas")

    ### AGREGAMOS FORMATOS
    header_format = workbook.add_format({'bold': True,'bg_color': '#2978F8','align': 'center'})
    bold_format = workbook.add_format({'bold': True,'align': 'center'})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})

    ### ENCABEZADOS
    count = 2
    sheet.write(0,1,'Articulo Seleccionado:', bold_format)
    sheet.write(0,2,product_id.name,bold_format)
    for row, row_data in enumerate(HEADERS):
      sheet.write(count, row, row_data, bold_format)
    count+=1

    for row_data in data['records']:
      sheet.write(count, 0, row_data['date'], date_format)
      sheet.write(count, 1, row_data['ref'])
      sheet.write(count, 2, row_data['push'])
      sheet.write(count, 3, row_data['output'])
      sheet.write(count, 4, row_data['exist'])
      sheet.write(count, 5, row_data['cost'], money_format)
      sheet.write(count, 6, row_data['debit'], money_format)
      sheet.write(count, 7, row_data['credit'], money_format)
      sheet.write(count, 8, row_data['saldo'], money_format)
      count += 1
