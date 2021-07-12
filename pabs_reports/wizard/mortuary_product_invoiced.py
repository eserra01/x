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
      domain.append(('invoice_date', '>=', self.date))
      domain.append(('invoice_date', '<=', self.end_date))
    else:
      domain.append(('invoice_date', '=', self.start_date))


    ### BUSCAMOS QUE EXISTAN FACTURAS EN ESAS FECHAS...
    invoice_ids = invoice_obj.search(domain)

    ### SI NO
    if not mortuary_ids:
      ### MENSAJE DE ERROR
      raise ValidationError("No hay facturas para procesar!")

    ### SI SE ENCONTRARON FACTURAS LAS AGREGAMOS A UN DICCIONARIO
    data = {'invoice_ids' : invoice_ids.ids}

    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_reports.mortuary_product_invoiced_report').report_action(self, data=data)

class MortuaryProductInvoicedPDFReport(models.AbstractModel):
  ### TEMPLATE
  _name = 'report.pabs_reports.mortuary_product_invoiced_pdf'

  @api.model
  def _get_report_values(self, docids, data):
    if data.get('invoice_ids'):
      raise ValidationError("Error!")
    return {
      'data' : data
    }