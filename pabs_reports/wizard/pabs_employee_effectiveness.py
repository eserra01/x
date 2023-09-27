# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

from dateutil import tz
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta

LISTA_ESTATUS_ACTIVOS = [
  'ACTIVO',
  'SUSP. TEMPORAL',

  'PAGADO',

  'REALIZADO',
  'REALIZADO PERCAPITA',
  'REALIZADO POR COBRAR',

  'VERIFICACION_TEMP',
  'VERIFICACION'
]

LISTA_ESTATUS_CANCELADOS = [
  'CANCELADO',
  'SUSP. PARA CANCELAR',
  'TRASPASO',
  'VERIFICACION SC',
  'QUEBRANTO'
]

HEADERS = [
  'Codigo',
  'Nombre',
  'Fecha de ingreso',
  'Esquema',
  'Estatus',
  'Oficina',
  'Activos y suspendidos temporales',
  'Pagados',
  'Realizados',
  'Otros estatus activos',
  'Cancelados',
  'Suspendidos por cancelar',
  'Traspasos',
  'Verificacion por cancelar',
  'Cancelacion acumulada',
  'Total de ventas',
  'Efectividad',
  'Porcentaje de bono'
]

class PabsEmployeeEffectiveness(models.TransientModel):
  _name = 'pabs.employee.effectiveness'
  _description = 'Wizard para reporte de efectividad de asistentes'

  ### Mostrar estatus activos y cancelados
  def _get_active_status(self):
      res = ""

      estatus = self.env['pabs.contract.status'].search([
        ('status', 'not in', LISTA_ESTATUS_CANCELADOS)
      ])

      for est in estatus:
        res = res + est.status + ","

      return res

  def _get_cancel_status(self):
      res = ""

      estatus = self.env['pabs.contract.status'].search([
        ('status', 'in', LISTA_ESTATUS_CANCELADOS)
      ])

      for est in estatus:
        res = res + est.status + ","

      return res

  periodo_efectividad = fields.Selection(string="Tipo de periodo", selection = [
    ('m3', 'a 3 meses'),
    ('m4', 'a 4 meses'),
    ('m6', 'a 6 meses'),
    ('libre', 'Personalizado')
  ], required = True, default = 'libre')

  start_date = fields.Date(string='Fecha inicial de contratos', required=True)
  end_date = fields.Date(string='Fecha final de contratos', required=True)

  estatus_activos = fields.Char(string="Estatus que favorecen la efectividad", default= lambda self: self._get_active_status(), readonly=True)
  estatus_cancelados = fields.Char(string="Estatus que perjudican la efectividad", default= lambda self: self._get_cancel_status(), readonly=True)

  ### Al elegir el tipo de periodo asignar las fechas correspondientes
  @api.onchange('periodo_efectividad')
  def definir_fechas(self):
    if self.periodo_efectividad == 'm3':
      fecha_inicial_efectividad = fields.Date.today() + relativedelta(months=-4)
      fecha_inicial_efectividad = fields.Date.start_of(fecha_inicial_efectividad, 'month')

      fecha_final_efectividad = fields.Date.today() + relativedelta(months=-2)
      fecha_final_efectividad = fields.Date.end_of(fecha_final_efectividad, 'month')

      self.start_date = fecha_inicial_efectividad
      self.end_date = fecha_final_efectividad
    if self.periodo_efectividad == 'm4':
      fecha_inicial_efectividad = fields.Date.today() + relativedelta(months=-5)
      fecha_inicial_efectividad = fields.Date.start_of(fecha_inicial_efectividad, 'month')

      fecha_final_efectividad = fields.Date.today() + relativedelta(months=-2)
      fecha_final_efectividad = fields.Date.end_of(fecha_final_efectividad, 'month')

      self.start_date = fecha_inicial_efectividad
      self.end_date = fecha_final_efectividad
    elif self.periodo_efectividad == 'm6':
      fecha_inicial_efectividad = fields.Date.today() + relativedelta(months=-7)
      fecha_inicial_efectividad = fields.Date.start_of(fecha_inicial_efectividad, 'month')

      fecha_final_efectividad = fields.Date.today() + relativedelta(months=-2)
      fecha_final_efectividad = fields.Date.end_of(fecha_final_efectividad, 'month')

      self.start_date = fecha_inicial_efectividad
      self.end_date = fecha_final_efectividad

  ### Consultar
  def consultar_efectividad(self, fecha_inicial, fecha_final):
    ### Validar estatus
    estatus = self.env['pabs.contract.status'].search([])

    est_act = estatus.filtered(lambda x: x.status == 'ACTIVO')
    if not est_act:
      raise ValidationError("No existe el estatus ACTIVO")
    
    est_temp = estatus.filtered(lambda x: x.status == 'SUSP. TEMPORAL')
    if not est_temp:
      raise ValidationError("No existe el estatus SUSP. TEMPORAL")
    
    est_pag = estatus.filtered(lambda x: x.status == 'PAGADO')
    if not est_pag:
      raise ValidationError("No existe el estatus PAGADO")
    
    est_rea = estatus.filtered(lambda x: x.status == 'REALIZADO')
    if not est_rea:
      raise ValidationError("No existe el estatus REALIZADO")

    est_sus = estatus.filtered(lambda x: x.status == 'SUSP. PARA CANCELAR')
    if not est_sus:
      raise ValidationError("No existe el estatus SUSP. PARA CANCELAR")
    
    est_can = estatus.filtered(lambda x: x.status == 'CANCELADO')
    if not est_can:
      raise ValidationError("No existe el estatus CANCELADO")
    
    est_tra = estatus.filtered(lambda x: x.status == 'TRASPASO')
    if not est_tra:
      raise ValidationError("No existe el estatus TRASPASO")
    
    est_ver = estatus.filtered(lambda x: x.status == 'VERIFICACION SC')
    if not est_ver:
      raise ValidationError("No existe el estatus VERIFICACION SC")
    
    est_queb_id = estatus.filtered(lambda x: x.status == 'QUEBRANTO')

    if est_queb_id:
      est_queb_id = est_queb_id.id
    else:
      est_queb_id = 0
    
    otros_activos = estatus.filtered(lambda x: x.id not in (
      est_act.id, est_temp.id, est_pag.id, est_rea.id,
      est_sus.id, est_can.id, est_tra.id, est_ver.id
    ))

    if not otros_activos:
      otros_activos = "(0)"
    else:
      otros_activos = tuple(otros_activos.ids)
    
    company_id = self.env.company.id

    consulta = """
    WITH empleados AS (
      SELECT 
        emp.barcode as codigo,
        COALESCE(emp.name, '') as nombre,
        emp.date_of_admission as fecha_ingreso,
        COALESCE(esq.name, '') as esquema,
        COALESCE(est.name, '') as estatus,
        COALESCE(ofi.name, '') as oficina,
        COALESCE(efe.activos, 0) as activos_y_suspendidos,
        COALESCE(efe.pagados, 0) as pagados,
        COALESCE(efe.realizados, 0) as realizados,
        COALESCE(efe.otros_activos, 0) as otros_activos,
        COALESCE(efe.cancelados, 0) as cancelados,
        COALESCE(efe.suspendidos, 0) as suspendidos,
        COALESCE(efe.traspasos, 0) as traspasos,
        COALESCE(efe.verificaciones_sc, 0) as verificaciones_cancelar,
        COALESCE(efe.cancelaciones, 0) as cancelaciones,
        COALESCE(efe.cantidad_contratos, 0) as afiliacion_total,
        COALESCE(efe.efectividad, 0) as efectividad,
        CASE
          WHEN COALESCE(efe.efectividad, 0) > .90 THEN 1
          WHEN COALESCE(efe.efectividad, 0) > .80 THEN .85
          WHEN COALESCE(efe.efectividad, 0) > .70 THEN .75
          ELSE 0
        END AS porcentaje_bono
      FROM hr_employee AS emp
      INNER JOIN stock_warehouse AS ofi ON emp.warehouse_id = ofi.id
      LEFT JOIN pabs_payment_scheme AS esq ON emp.payment_scheme = esq.id
      LEFT JOIN hr_employee_status AS est ON emp.employee_status = est.id
      INNER JOIN
      (
        /*Calculo de efectividad por asistente*/
        SELECT 
          x.id_empleado,
          x.cantidad_contratos,
          /*Activos*/
          x.activos,
          x.pagados,
          x.realizados,
          x.otros_activos,
          /*Cancelados*/
          x.suspendidos,
          x.cancelados,
          x.traspasos,
          x.verificaciones_sc,
          x.suspendidos + x.cancelados + x.traspasos + x.verificaciones_sc as cancelaciones,
          CAST( 
            CAST(1 AS NUMERIC(10,2)) - CAST(x.suspendidos + x.cancelados + x.traspasos + x.verificaciones_sc AS NUMERIC(10,2)) / CAST(x.cantidad_contratos AS NUMERIC(10,2))
          AS NUMERIC (10,2)) as efectividad 
        FROM
        (
          /*Cantidad de contratos activos, suspendidos y cancelados por asistente*/
          SELECT 
            con.sale_employee_id as id_empleado,
            COUNT(*) as cantidad_contratos,
            SUM(CASE WHEN est.id IN ({act}, {temp}) THEN 1 ELSE 0 END) as activos,
            SUM(CASE WHEN est.id = {pag} THEN 1 ELSE 0 END) as pagados,
            SUM(CASE WHEN est.id = {rea} THEN 1 ELSE 0 END) as realizados,
            SUM(CASE WHEN est.id IN {otros_act} THEN 1 ELSE 0 END) as otros_activos,
            
            SUM(CASE WHEN est.id = {sus} THEN 1 ELSE 0 END) as suspendidos,
            SUM(CASE WHEN est.id IN ({can}, {queb}) THEN 1 ELSE 0 END) as cancelados,
            SUM(CASE WHEN est.id = {tra} THEN 1 ELSE 0 END) as traspasos,
            SUM(CASE WHEN est.id = {ver} THEN 1 ELSE 0 END) as verificaciones_sc
          FROM pabs_contract AS con
          INNER JOIN pabs_contract_status as est ON con.contract_status_item = est.id
            WHERE con.state = 'contract'
            AND con.company_id IN ({com1})
            AND con.invoice_date BETWEEN '{ini}' AND '{fin}'
              GROUP BY sale_employee_id HAVING COUNT(*) > 0
                ORDER BY sale_employee_id
        ) AS x
      ) AS efe ON emp.id = efe.id_empleado
        WHERE emp.company_id IN ({com2})
          ORDER BY emp.barcode
    )
      SELECT 
        *
      FROM empleados
    UNION SELECT 
        'Z_Total' as codigo,
        'Total' as nombre,
        '1900-01-01' as fecha_ingreso,
        '' as esquema,
        '' as estatus,
        '' as oficina,
        SUM(activos_y_suspendidos) as activos_y_suspendidos,
        SUM(pagados) as pagados,
        SUM(realizados) as realizados,
        SUM(otros_activos) as otros_activos,
        SUM(cancelados) as cancelados,
        SUM(suspendidos) as suspendidos,
        SUM(traspasos) as traspasos,
        SUM(verificaciones_cancelar) as verificaciones_cancelar,
        SUM(cancelaciones) as cancelaciones,
        SUM(afiliacion_total) as afiliacion_total,
        ROUND(AVG(efectividad), 2) as efectividad,
        CASE
          WHEN AVG(efectividad) > .90 THEN 1
          WHEN AVG(efectividad) > .80 THEN .85
          WHEN AVG(efectividad) > .70 THEN .75
          ELSE 0
        END AS porcentaje_bono
      FROM empleados
        ORDER BY codigo
    """.format(
      act = est_act.id,
      temp = est_temp.id,
      pag = est_pag.id,
      rea = est_rea.id,
      otros_act = otros_activos,
      sus = est_sus.id,
      can = est_can.id,
      queb = est_queb_id,
      tra = est_tra.id,
      ver = est_ver.id,
      ini = fecha_inicial,
      fin = fecha_final,
      com1 = company_id,
      com2 = company_id
    )
    
    self.env.cr.execute(consulta)

    empleados = []
    for res in self.env.cr.fetchall():
      empleados.append({
        'codigo': res[0],
        'nombre': res[1],
        'fecha_ingreso': res[2],
        'esquema': res[3],
        'estatus': res[4],
        'oficina': res[5],
        'activos_y_suspendidos': res[6],
        'pagados': res[7],
        'realizados': res[8],
        'otros_activos': res[9],
        'cancelados': res[10],
        'suspendidos': res[11],
        'traspasos': res[12],
        'verificaciones_cancelar': res[13],
        'cancelaciones': res[14],
        'afiliacion_total': res[15],
        'efectividad': res[16],
        'porcentaje_bono': res[17]
      })

    if not empleados:
      raise ValidationError("No se encontraron registros")

    return empleados
  
  ### Generar reporte en pdf
  def print_pdf_report(self):

    empleados = self.consultar_efectividad(self.start_date, self.end_date)    

    data = {
      'fecha_inicial': self.start_date,
      'fecha_final': self.end_date,
      'tipo': dict(self._fields['periodo_efectividad'].selection).get(self.periodo_efectividad),
      'registros': empleados
    }

    return self.env.ref("pabs_reports.employee_effectiveness_pdf").report_action(self, data=data)
  
  ### Generar reporte en excel
  def print_xlsx_report(self): 

    data = {
      'fecha_inicial': self.start_date,
      'fecha_final': self.end_date
    }

    return self.env.ref("pabs_reports.employee_effectiveness_xlsx_id").report_action(self, data=data)

class PabsEmployeeEffectivenessXLSXReport(models.AbstractModel):
  _name = 'report.pabs_reports.employee_effectiveness_xlsx_report'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, recs):

    empleados = self.env['pabs.employee.effectiveness'].consultar_efectividad(data['fecha_inicial'], data['fecha_final'])
      
    sheet = workbook.add_worksheet('Efectividad')

    bold_format = workbook.add_format({'bold': True})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    float_format = workbook.add_format({'num_format': '0%'})

    fila = 0
    for index, val in enumerate(HEADERS):
      sheet.write(fila,index,val,bold_format)

    for emp in empleados:
      fila = fila + 1
      
      sheet.write(fila, 0, emp['codigo'])
      sheet.write(fila, 1, emp['nombre'])
      sheet.write(fila, 2, emp['fecha_ingreso'], date_format)
      sheet.write(fila, 3, emp['esquema'])
      sheet.write(fila, 4, emp['estatus'])
      sheet.write(fila, 5, emp['oficina'])
      sheet.write(fila, 6, emp['activos_y_suspendidos'])
      sheet.write(fila, 7, emp['pagados'])
      sheet.write(fila, 8, emp['realizados'])
      sheet.write(fila, 9, emp['otros_activos'])
      sheet.write(fila, 10, emp['cancelados'])
      sheet.write(fila, 11, emp['suspendidos'])
      sheet.write(fila, 12, emp['traspasos'])
      sheet.write(fila, 13, emp['verificaciones_cancelar'])
      sheet.write(fila, 14, emp['cancelaciones'])
      sheet.write(fila, 15, emp['afiliacion_total'])
      sheet.write(fila, 16, emp['efectividad'], float_format)
      sheet.write(fila, 17, emp['porcentaje_bono'], float_format)

