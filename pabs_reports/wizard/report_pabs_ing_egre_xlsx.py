# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

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
    return self.env.ref('pabs_reports.pabs_ing_egre_xlsx').report_action(self, data=data)

class PabsIngreEgreReportXLSX(models.AbstractModel):
  _name = 'report.pabs_reports.ingre_egre_report_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    date_start = data['form']['date_start']
    date_end = data['form']['date_end']
    ### INGRESOS
    #Consultar todos los pagos realizados entre dos fechas con estatus válido
    pagos = self.env['account.payment'].search([
      ('payment_date', '>=', date_start), ('payment_date', '<=', date_end), 
      ('state', 'in', ['posted','sent','reconciled']), 
      ('reference','in',['payment', 'surplus'])
    ])

    ingresos_lista_cobradores = []
    ingresos_sin_clasificar = []
    total_ingresos = 0

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

    if cantidad_surplus > 0:
      total_ingresos = total_ingresos + cantidad_surplus

      ingresos_sin_clasificar.append({
        'codigo_cobrador':'',
        'cobrador':'COBRANZA EXD. INV.',
        'cantidad_ingresos': cantidad_surplus
      })

      if cantidad_payment > 0:
        total_ingresos = total_ingresos + cantidad_payment

      ingresos_sin_clasificar.append({
        'codigo_cobrador':'',
        'cobrador':'SIN COBRADOR',
        'cantidad_ingresos': cantidad_payment
      })

      if cantidad_payment > 0:
        total_ingresos = total_ingresos + cantidad_payment

        ingresos_sin_clasificar.append({
          'codigo_cobrador':'',
          'cobrador':'SIN COBRADOR',
          'cantidad_ingresos': cantidad_payment
        })

      ### INGRESOS CLASIFICADOS (Pagos con cobrador)
      #Obtener el cobrador único todos los pagos y ordenar por nombre
      cobradores = pagos.mapped(lambda pago: pago.debt_collector_code) #Nota: no envia el cobrador Null
      cobradores = cobradores.sorted(key=lambda cob: cob.name)

      for cobrador in cobradores:
        #Filtrar los pagos, dejar solo los de los empleados en turno
        pagos_cobrador = pagos.filtered_domain([('debt_collector_code','=',cobrador.id), ('reference','=','payment')])

        cantidad_cobrador = 0
        for pago in pagos_cobrador:
          cantidad_cobrador = cantidad_cobrador + pago.amount

        total_ingresos = total_ingresos + cantidad_cobrador

        ingresos_lista_cobradores.append({
          'codigo_cobrador': cobrador.barcode,
          'cobrador': cobrador.name,
          'cantidad_ingresos': cantidad_cobrador
        })