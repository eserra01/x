# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class MortuaryProductInvoiced(models.TransientModel):
  _name = 'mortuary.product.invoiced'

  start_date = fields.Date(string='Fecha Inicial',
    required=True)

  end_date = fields.Date(string='Fecha Final')

  def print_report(self):
    ### DECLARACIÓN DE OBJETOS
    invoice_obj = self.env['account.move']
    ### DECLARAMOS VARIABLE DOMINIO
    domain = [('mortuary_id', '!=', False), ('type', '=', 'out_invoice'), ('state','=','posted')]

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

    ### Crear lista con las lineas de las facturas ###
    lista_facturas = invoice_ids.sorted(key=lambda x: x.partner_id.name)
    lista_lineas_factura = []
    total_facturado = 0
    for factura in lista_facturas:
      
      #Buscar bitácora ligada a la factura
      if not factura.partner_id:
        raise ValidationError("No se puede generar el reporte porque la factura {} no tiene una bitácora ligada".format(factura.name))

      numero_de_bitacora = factura.partner_id.name
      bitacora = self.env['mortuary'].search([
        ('name', '=', numero_de_bitacora),
        ('company_id', '=', self.env.company.id)
      ])

      if not bitacora:
        raise ValidationError("No se puede generar el reporte porque la factura {} apunta a la bitácora {} y dicha bitácora no existe".format(factura.name, numero_de_bitacora))

      #Recorrer cada linea de la factura y llenar lista
      for linea in factura.invoice_line_ids:
        nueva_linea = {
          'numero_de_factura': factura.name,
          'bitacora': numero_de_bitacora,
          'fecha': factura.invoice_date,
          'tipo_de_servicio': bitacora.ds_tipo_de_servicio.name,
          'finado': bitacora.ii_finado,
          'producto': linea.product_id.name,
          'cantidad': linea.quantity,
          'subtotal': linea.price_subtotal,
        }

        lista_lineas_factura.append(nueva_linea)
        
        total_facturado = total_facturado + linea.price_subtotal

    ### retornamos los datos
    return {
      'name' : data.get('name'),
      'detail' : details,
      'lineas_de_facturas': lista_lineas_factura,
      'total_facturado' : total_facturado
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

    ############## ENCABEZADO #############
    formato_titulo = workbook.add_format({'bold': True, 'font_size': 14})
    sheet.write(0,0, "INFORME DE FACTURACION FUNERARIA", formato_titulo)
    sheet.write(1,0, data.get('name'), formato_titulo)

    sheet.write(3, 0, "Detallado de facturas", formato_titulo)

    ############## DETALLADO #############
    ### Crear lista con las lineas de las facturas ###
    lista_facturas = invoice_ids.sorted(key=lambda x: x.partner_id.name)
    lista_lineas_factura = []
    total_facturado  = 0

    for factura in lista_facturas:
      
      #Buscar bitácora ligada a la factura
      if not factura.partner_id:
        raise ValidationError("No se puede generar el reporte porque la factura {} no tiene una bitácora ligada".format(factura.name))

      numero_de_bitacora = factura.partner_id.name
      bitacora = self.env['mortuary'].search([
        ('name', '=', numero_de_bitacora),
        ('company_id', '=', self.env.company.id)
      ])

      if not bitacora:
        raise ValidationError("No se puede generar el reporte porque la factura {} apunta a la bitácora {} y dicha bitácora no existe".format(factura.name, numero_de_bitacora))

      #Recorrer cada linea de la factura y llenar lista
      for linea in factura.invoice_line_ids:
        nueva_linea = {
          'numero_de_factura': factura.name,
          'bitacora': numero_de_bitacora,
          'fecha': factura.invoice_date,
          'tipo_de_servicio': bitacora.ds_tipo_de_servicio.name,
          'finado': bitacora.ii_finado,
          'producto': linea.product_id.name,
          'cantidad': linea.quantity,
          'subtotal': linea.price_total,
        }

        lista_lineas_factura.append(nueva_linea)
        
        total_facturado = total_facturado + linea.price_subtotal

    #Escribir nombres de columnas
    formato_header = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#00FFFF'})
    sheet.write(4,0, "Factura", formato_header)
    sheet.write(4,1, "Bitácora", formato_header)
    sheet.write(4,2, "Fecha", formato_header)
    sheet.write(4,3, "Tipo de servicio", formato_header)
    sheet.write(4,4, "Finado", formato_header)
    sheet.write(4,5, "Descripción", formato_header)
    sheet.write(4,6, "Cantidad", formato_header)
    sheet.write(4,7, "Subtotal", formato_header)

    #Escribir detalles
    formato_fecha = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    fila = 5

    for linea in lista_lineas_factura:
      sheet.write(fila, 0, linea.get('numero_de_factura'))
      sheet.write(fila, 1, linea.get('bitacora'))
      sheet.write(fila, 2, linea.get('fecha'), formato_fecha)
      sheet.write(fila, 3, linea.get('tipo_de_servicio'))
      sheet.write(fila, 4, linea.get('finado'))
      sheet.write(fila, 5, linea.get('producto'))
      sheet.write(fila, 6, linea.get('cantidad'))
      sheet.write(fila, 7, linea.get('subtotal'), money_format)

      fila = fila + 1

    sheet.write(fila, 6, "Total:")
    sheet.write(fila, 7, total_facturado, money_format)

    ############## CONCENTRADO #############

    #Escribir nombres de columnas
    fila = fila + 3
    sheet.write(fila, 0, "Resumen de facturas", formato_titulo)
    
    fila = fila + 1
    sheet.write(fila, 0, "Concepto", bold_format)
    sheet.write(fila, 1, "Cantidad", bold_format)
    sheet.write(fila, 2, "Total", bold_format)
    fila = fila + 1

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

      #Escribir detalle
      sheet.write(fila, 0, product_id.name)
      sheet.write(fila, 1, int(qty))
      sheet.write(fila, 2, total, money_format)
      fila = fila + 1
