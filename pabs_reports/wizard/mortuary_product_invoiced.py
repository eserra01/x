# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class MortuaryProductInvoiced(models.TransientModel):
  _name = 'mortuary.product.invoiced'

  start_date = fields.Date(string='Fecha Inicial',
    required=True)

  end_date = fields.Date(string='Fecha Final')

  def print_pdf_report(self):
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

    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_reports.mortuary_product_invoiced_report').report_action(self, data=data)

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
    