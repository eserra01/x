# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

HEADERS = [
  'Tipo',
  'Código',
  'Nombre', 
  'Importe']

class ReportWizardINGEGR(models.TransientModel):
  _inherit = 'report.pabs.ing.egre'

  def print_xls_report(self):
    data = {
      'ids': self.ids,
      'model': self._name,
      'form': {
        'date_start': self.date_from,
        'date_end': self.date_to,
      },
    }
    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_reports.ingre_egre_report_xlsx').report_action(self, data=data)

class PabsIngreEgreReportXLSX(models.AbstractModel):
  _name = 'report.pabs_reports.ingresos_egresos_report_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    date_start = data['form']['date_start']
    date_end = data['form']['date_end']

    ### GENERAMOS LA HOJA
    if date_start and date_end:
      sheet = workbook.add_worksheet("Ingresos y Egresos {} - {}".format(date_start,date_end))
    else:
      sheet = workbook.add_worksheet("Ingresos y Egresos {}".format(date_start))

    ### AGREGAMOS FORMATOS
    title_format = workbook.add_format({'bold' : True, 'font_size' : 14, 'center_across' : True})
    subtitle_format = workbook.add_format({'font_size' : 12, 'center_across' : True})
    bold_format = workbook.add_format({'bold' : True})
    header_format = workbook.add_format({'bold' : True,'bg_color': '#2978F8'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})
    subtotal_format = workbook.add_format({'top' : 2, 'bold' : True, 'num_format': '$#,##0.00'})


    ### ESCRIBIMOS EL ENCABEZADO DE LA PAGINA
    sheet.merge_range("A2:D2","Programa de Apoyo en Beneficio Social", title_format)
    sheet.merge_range("A3:D3", "INGRESOS Y EGRESOS", subtitle_format)
    sheet.merge_range("A4:B4", "Periodo de {} al {}".format(date_start, date_end))

    ### ESCRIBIMOS LAS ENCABEZADOS DE INGRESOS
    for index, val in enumerate(HEADERS):
      sheet.write(5,index,val,header_format)

    ### INGRESOS
    sheet.write(6,0,"INGRESOS", bold_format)
    #Consultar todos los pagos realizados entre dos fechas con estatus válido
    pagos = self.env['account.payment'].search([
      ('payment_date', '>=', date_start), ('payment_date', '<=', date_end), 
      ('state', 'in', ['posted','sent','reconciled']), 
      ('reference','in',['payment', 'surplus'])
    ]).filtered(lambda r: r.contract.company_id.id in self.env.company.ids)

    ingresos_lista_cobradores = []
    ingresos_sin_clasificar = []
    total_ingresos = 0
    count = 6

    ### INGRESOS SIN CLASIFICAR (Pagos sin cobrador)
    #Obtener los excedentes y los pagos que no tengan cobrador
    pagos_sin_cobrador = pagos.filtered_domain([('debt_collector_code','=',False)])
    cantidad_surplus = 0
    cantidad_payment = 0

    for pago in pagos_sin_cobrador:
      #Calcular pago por excedente
      if pago.reference == 'surplus':
        cantidad_surplus = cantidad_surplus + pago.amount
      #Calcular pagos normales
      elif pago.reference == 'payment':
        cantidad_payment = cantidad_payment + pago.amount

    ### SI EXISTEN REGISTROS SIN CLASIFICACION
    if cantidad_surplus or cantidad_payment:
      count+=1
      sheet.write(count,0, "01 SIN CLASIFICAR", bold_format)

    ### SI EXISTE REGISTROS DE EXCEDENTE
    if cantidad_surplus > 0:
      count+=1
      total_ingresos = total_ingresos + cantidad_surplus
      sheet.write(count,2, "COBRANZA EXD. INV.")
      sheet.write(count,3, cantidad_surplus, money_format)

    ### SI EXISTEN PAGOS QUE NO TIENEN COBRADOR
    if cantidad_payment > 0:
      count+=1
      total_ingresos = total_ingresos + cantidad_payment
      sheet.write(count,2, "SIN COBRADOR")
      sheet.write(count,3, cantidad_payment, money_format)

    ### INGRESOS CLASIFICADOS (Pagos con cobrador)
    #Obtener el cobrador único todos los pagos y ordenar por nombre
    cobradores = pagos.mapped(lambda pago: pago.debt_collector_code) #Nota: no envia el cobrador Null
    cobradores = cobradores.sorted(key=lambda cob: cob.name)
    ### SI HAY PAGOS CLASIFICADOS
    if cobradores:
      count+=1
      sheet.write(count,0, "02 CLASIFICADOS", bold_format)

    for cobrador in cobradores:
      count+=1
      #Filtrar los pagos, dejar solo los de los empleados en turno
      pagos_cobrador = pagos.filtered_domain([('debt_collector_code','=',cobrador.id), ('reference','=','payment')])

      cantidad_cobrador = 0
      for pago in pagos_cobrador:
        cantidad_cobrador = cantidad_cobrador + pago.amount

      total_ingresos = total_ingresos + cantidad_cobrador

      ### INSERTAMOS LAS LINEAS DE LOS COBRADORES
      sheet.write(count, 1, cobrador.barcode or "")
      sheet.write(count, 2, cobrador.name or "")
      sheet.write(count, 3, cantidad_cobrador or 0, money_format)

    ### ESCRIBIMOS EL TOTAL DE INGRESOS
    count+=1
    sheet.write(count,3,total_ingresos or 0, subtotal_format)

    ### EGRESOS
    count+=2
    sheet.write(count,0,"EGRESOS", bold_format)
    egresos_lista_comisionistas = []
    egresos_sin_clasificar = [] #Fideicomiso e IVA
    total_egresos = 0

    #Consultar id de cargo papeleria
    cargo_papeleria = self.env['hr.job'].search([('name','=','PAPELERIA')])

    #Consultar las salidas entre dos fechas
    salidas = self.env['pabs.comission.output'].search([
      ('payment_date', '>=', date_start), 
      ('payment_date', '<=', date_end),
      ('payment_status', 'in', ['posted','sent','reconciled']),
      ('actual_commission_paid', '!=', 0),
      ('job_id', 'not in', [cargo_papeleria.id])
      ]
    )

    # Validar que todas las salidas tengan un empleado que comisiona
    lista_salidas_error = ""
    for pago in salidas:
      if not pago.comission_agent_id:
        lista_salidas_error = "No se tiene un empleado asignado a la salida de comisiones en el recibo {}\n".format(pago.ecobro_receipt)

    if lista_salidas_error != "":
        raise ValidationError(lista_salidas_error)

    ### EGRESOS SIN CLASIFICAR (Fideicomiso)
    #Filtrar las salidas por cargo de fideicomiso
    cargo_fideicomiso = self.env['hr.job'].search([('name','=','FIDEICOMISO'), ('company_id', '=', self.env.company.id)])
    if not cargo_fideicomiso:
      raise ValidationError("No se encontró el cargo FIDEICOMISO")

    salidas_fideicomiso = salidas.filtered(lambda x: x.job_id.id == cargo_fideicomiso.id and x.actual_commission_paid > 0)

    if salidas_fideicomiso:
      total_fideicomiso = sum(salidas_fideicomiso.mapped('actual_commission_paid'))
      egresos_sin_clasificar.append({
          'codigo_comisionista': '', 
          'nombre_comisionista': 'FIDEICOMISO', 
          'cantidad_egresos': total_fideicomiso
      })

      total_egresos = total_egresos + total_fideicomiso

    aplica_iva = self.env.company.apply_taxes
    cargo_iva = 0
    if aplica_iva:
      # Salidas de fideicomiso que subsidian IVA
      salidas_subsidio = salidas.filtered(lambda x: x.job_id.id == cargo_fideicomiso.id and x.actual_commission_paid < 0)

      if salidas_subsidio:
        subsidio_fideicomiso = sum(salidas_subsidio.mapped('actual_commission_paid'))
        egresos_sin_clasificar.append({
            'codigo_comisionista': '', 
            'nombre_comisionista': 'SUBSIDIO FIDEICOMISO', 
            'cantidad_egresos': subsidio_fideicomiso
        })

        total_egresos = total_egresos + subsidio_fideicomiso

      # Salidas por cargo de IVA
      cargo_iva = self.env['hr.job'].search([('name','=','IVA'), ('company_id', '=', self.env.company.id)])

      if not cargo_iva:
        raise ValidationError("No se encontró el cargo IVA")

      salidas_IVA = salidas.filtered(lambda x: x.job_id.id == cargo_iva.id)

      if salidas_IVA:
        total_iva = sum(salidas_IVA.mapped('actual_commission_paid'))

        egresos_sin_clasificar.append({
            'codigo_comisionista': '', 
            'nombre_comisionista': 'IVA', 
            'cantidad_egresos': total_iva
        })

        total_egresos = total_egresos + total_iva

    ### Escribir Egresos sin clasificar
    count+=1
    sheet.write(count,0, "01 SIN CLASIFICAR", bold_format)

    for egr in egresos_sin_clasificar:
      count+=1
      sheet.write(count,2, egr.get('nombre_comisionista'))
      sheet.write(count,3, egr.get('cantidad_egresos'), money_format)

    ### EGRESOS CLASIFICADOS
    #Quitar el cargo de fideicomiso al recordset de salidas
    salidas_comisionistas = []
    if aplica_iva:
      salidas_comisionistas = salidas.filtered(lambda x: x.job_id.id not in (cargo_fideicomiso.id, cargo_iva.id) )
    else:
      salidas_comisionistas = salidas.filtered(lambda x: x.job_id.id != cargo_fideicomiso.id)

    ### SI HAY SALIDAS DIFERENTES A FIDEICOMISO
    if salidas_comisionistas:
      count+=1
      sheet.write(count,0, "02 CLASIFICADOS", bold_format)

    #Obtener el comisionista único de todas las salidas y ordenar por codigo
    codigos_unicos = salidas_comisionistas.mapped(lambda salida: salida.comission_agent_id)
    codigos_unicos = codigos_unicos.sorted(key=lambda salida: salida.barcode)

    for emp in codigos_unicos:
      count+=1
      # Filtrar las salidas por código de empleado
      salidas_por_codigo = salidas_comisionistas.filtered_domain([('comission_agent_id','=',emp.id)])

      #Obtener los cargos únicos para todas las salidas del empleado
      cargos_de_salidas = salidas_por_codigo.mapped(lambda salida: salida.job_id)

      registro_empleado = {}
      for cargo in cargos_de_salidas:
        sheet.write(count, 1, emp.barcode)
        #Filtrar las salidas por cargo
        salidas_por_cargo = salidas_por_codigo.filtered_domain([('job_id','=',cargo.id)])
        
        nombre_comisionista = "{} - ({})".format(emp.name, cargo.name)
        total_cargo = 0
        for salida in salidas_por_cargo:
            total_cargo = total_cargo + salida.actual_commission_paid

        sheet.write(count, 2, nombre_comisionista)
        sheet.write(count, 3, total_cargo, money_format)
        total_egresos = total_egresos + total_cargo
        count+=1
        #Fin de iteración por cargos de un empleado

    #### INSERTAMOS EL TOTAL DE EGRESOS
    count+=1
    sheet.write(count,3, total_egresos or 0, subtotal_format)
      