# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

HEADERS = [
  'Concepto',
  'Cantidad',
  'Total']

class MortuaryProductInvoiced(models.TransientModel):
  _name = 'mortuary.product.invoiced'

  start_date = fields.Date(string='Fecha Inicial',
    required=True)

  end_date = fields.Date(string='Fecha Final')

  def print_report(self):
    ### DECLARACIÓN DE OBJETOS
    invoice_obj = self.env['account.move']
    ### DECLARAMOS VARIABLE DOMINIO
    domain = [('mortuary_id', '!=', False),('type', '=', 'out_invoice')]

    ### GENERAMOS EL DOMINIO
    if self.end_date:
      domain.append(('invoice_date', '>=', self.start_date))
      domain.append(('invoice_date', '<=', self.end_date))
      name = 'del {} al {}'.format(self.start_date, self.end_date)
    else:
      domain.append(('invoice_date', '=', self.start_date))
      name = 'del {}'.format(self.start_date)


    ### BUSCAMOS QUE EXISTAN FACTURAS EN ESAS FECHAS...
    invoice_ids = invoice_obj.search(domain)

    ### SI NO
    if not invoice_ids:
      ### MENSAJE DE ERROR
      raise ValidationError("No hay facturas para procesar!")

    ### SI SE ENCONTRARON FACTURAS LAS AGREGAMOS A UN DICCIONARIO
    data = {
      'name' : name,
      'invoice_ids' : invoice_ids.ids}

    if self._context.get('type_report') == 'pdf':
      ### RETORNAMOS EL REPORTE EN PDF
      return self.env.ref('pabs_reports.mortuary_product_invoiced_report').report_action(self, data=data)
    elif self._context.get('type_report') == 'xlsx':
      return self.env.ref('pabs_reports.mortuary_product_invoiced_report_xlsx').report_action(self, data=data)

class MortuaryProductInvoicedPDFReport(models.AbstractModel):
  ### TEMPLATE
  _name = 'report.pabs_reports.mortuary_product_invoiced_pdf'

  @api.model
  def _get_report_values(self, docids, data):
    ### INSTANCIACIÓN DE OBJETOS
    invoice_obj = self.env['account.move']

    ### MENSAJE DE ERROR
    if not data.get('invoice_ids'):
      raise ValidationError("Error!")

    ### INSTANCIAMOS LAS FACTURAS GENERADAS
    invoice_ids = invoice_obj.browse(data.get('invoice_ids'))

    ### ARRAY DE LA INFO
    details = []

    ### TRAEMOS TODAS LAS LINEAS DE LAS FACTURAS
    lines = invoice_ids.mapped('invoice_line_ids')
    ### LISTAMOS TODOS LOS PRODUCTOS FACTURADOS
    product_ids =  lines.mapped('product_id')

    ### RECORREMOS LA LISTA DE PRODUCTOS
    for product_id in product_ids:
      ### FILTRAMOS TODAS LAS LINEAS QUE VIENE EL PRODUCTO
      product_lines = lines.filtered(lambda r: r.product_id.id == product_id.id)
      ### SUAMMOS TODAS LAS CANTIDADES DE ESE PRODUCTO
      qty = sum(product_lines.mapped('quantity'))
      ### SUMAMOS EL TOTAL FACTURADO POR ESE PRODUCTO
      total = sum(product_lines.mapped('price_total'))

      ### LOS AGREGAMOS AL ARRAY
      details.append({
        'name' : product_id.name,
        'qty' : int(qty),
        'total' : "${:,.2f}".format(total)
      })

    ### retornamos los datos
    return {
      'name' : data.get('name'),
      'detail' : details,
    }

class MortuaryProductInvoicedPDFReport(models.AbstractModel):
  _name = 'report.pabs_reports.mortuary_product_invoiced_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    ### INSTANCIACIÓN DE OBJETOS
    invoice_obj = self.env['account.move']

    ### MENSAJE DE ERROR
    if not data.get('invoice_ids'):
      raise ValidationError("Error!")

    ### INSTANCIAMOS LAS FACTURAS GENERADAS
    invoice_ids = invoice_obj.browse(data.get('invoice_ids'))

    ### GENERAMOS LA HOJA
    sheet = workbook.add_worksheet(data.get('name'))

    ### AGREGAMOS FORMATOS
    bold_format = workbook.add_format({'bold': True,'bg_color': '#2978F8'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})

     ### INSERTAMOS LOS ENCABEZADOS
    for row, row_data in enumerate(HEADERS):
      sheet.write(0,row,row_data,bold_format)

    ### TRAEMOS TODAS LAS LINEAS DE LAS FACTURAS
    lines = invoice_ids.mapped('invoice_line_ids')
    ### LISTAMOS TODOS LOS PRODUCTOS FACTURADOS
    product_ids =  lines.mapped('product_id')

    ### CONTADOR DE REGISTROS
    count = 1

    ### RECORREMOS LA LISTA DE PRODUCTOS
    for product_id in product_ids:
      ### FILTRAMOS TODAS LAS LINEAS QUE VIENE EL PRODUCTO
      product_lines = lines.filtered(lambda r: r.product_id.id == product_id.id)
      ### SUAMMOS TODAS LAS CANTIDADES DE ESE PRODUCTO
      qty = sum(product_lines.mapped('quantity'))
      ### SUMAMOS EL TOTAL FACTURADO POR ESE PRODUCTO
      total = sum(product_lines.mapped('price_total'))

      sheet.write(count, 0, product.name)
      sheet.write(count, 1, int(qty))
      sheet.write(count, 2, total, money_format)
      count+= 1
