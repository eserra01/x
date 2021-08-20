# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

HEADERS = [
  'Fecha de Contrato',
  'Número de Contrato',
  'Nombre de Plan',
  'Cobrador',
  'Asistente Social',
  'Forma de Pago',
  'Monto de Pago Esperado',
  'Monto Actual'
]

class DiferenceBetweenAmountContracts(models.TransientModel):
  _name = 'pabs.difference.between.amount.contracts'
  _description = 'Diferencia en monto de pagos de contratos'

  def print_xls_report(self):
    ### CREAMOS UN CURSOS DE BD
    cr = self._cr
    ### BUSCAMOS EL ID DE LA COMPAÑIA QUE ESTA GENERANDO EL REPORTE
    company_id = self.env.company.id

    ### VARIABLE CON EL QUERY
    query = """
      SELECT 
        fecha_contrato,
        contrato,
        nombre_plan,
        cobrador,
        asistente_social,
        forma_pago,
        pago_esperado,
        monto_actual
      FROM(
        SELECT
          pc.invoice_date as "fecha_contrato",
          pc.name as "contrato",
          pt.name as "nombre_plan",
          he.name as "cobrador",
          he2.name as "asistente_social",
          CASE
            WHEN pc.way_to_payment = 'weekly' THEN 'Semanal'
            WHEN pc.way_to_payment = 'biweekly' THEN 'Quincenal'
            WHEN pc.way_to_payment = 'monthly' THEN 'Mensual'
          END AS "forma_pago",
          CASE
            WHEN pc.way_to_payment = 'weekly' THEN pdi.payment_amount
            WHEN pc.way_to_payment = 'biweekly' THEN (pdi.payment_amount * 2)
            WHEN pc.way_to_payment = 'monthly' THEN (pdi.payment_amount * 4)
          END AS "pago_esperado",
          pc.payment_amount AS "monto_actual"
        FROM
          pabs_contract pc
        INNER JOIN
          stock_production_lot spl ON spl.id = pc.lot_id
        INNER JOIN
          product_template pt ON pt.id = spl.product_id
        INNER JOIN
          hr_employee he ON he.id = pc.debt_collector
        INNER JOIN
          hr_employee he2 ON he2.id = spl.employee_id
        INNER JOIN
          product_pricelist_item pdi ON pdi.product_tmpl_id = pt.id
        WHERE
          pc.state = 'contract' AND
          pc.company_id = {}
        ) AS con
      WHERE 
        con.pago_esperado != con.monto_actual
      ORDER BY 
        con.nombre_plan, 
        con.forma_pago, 
        con.contrato""".format(company_id)
    ### EJECUTAMOS EL QUERY
    cr.execute(query)
    ### GUARDAMOS EL RESULTADO DE LA CONSULTA
    res = cr.fetchall()

    ### SI NO SE ENCUENTRA INFORMACIÓN
    if not res:
      raise ValidationError("No se encontraron diferencias entre monto esperado vs monto recibido")

    ### AGREGAMOS LA INFORMACIÓN A UN DICCIONARIO
    data = {
      'query_data' : res
    }

    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_reports.difference_between_amount_contracts_report_xlsx').report_action(self, data=data)

class DifferenceBetweenContractsReports(models.AbstractModel):
  _name = 'report.pabs_reports.diff_amount_contracts_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    ### NOMBRE DE LA HOJA
    report_name = "Fecha Generación: {}".format(fields.Date.today())
    ### GENERAMOS LA HOJA
    sheet = workbook.add_worksheet(report_name)

    ### AGREGAMOS FORMATOS
    bold_format = workbook.add_format({'bold': True,'align': 'center'})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})

    ### CONTADOR DE CELDAS
    count = 0
    ### INSERTAMOS LOS ENCABEZADOS
    for row, row_data in enumerate(HEADERS):
      sheet.write(count, row, row_data, bold_format)
    count+=1

    ### RECORREMOS LA INFORMACIÓN
    for res in data.get('query_data'):
      ### INSERTAMOS FECHA DE CONTRATO
      sheet.write(count, 0, res[0], date_format)
      ### INSERTAMOS NÚMERO DE CONTRATO
      sheet.write(count, 1, res[1])
      ### INSERTAMOS NOMBRE DEL PLAN
      sheet.write(count, 2, res[2])
      ### INSERTAMOS NOMBRE DEL COBRADOR
      sheet.write(count, 3, res[3])
      ### INSERTAMOS ASISTENTE SOCIAL
      sheet.write(count, 4, res[4])
      ### INSERTAMOS FORMA DE PAGO
      sheet.write(count, 5, res[5])
      ### INSERTAMOS MONTO DE PAGO ESPERADO
      sheet.write(count, 6, res[6], money_format)
      ### INSERTAMOS MONTO ACTUAL
      sheet.write(count, 7, res[7], money_format)
      ### AUMENTAMOS CONTADOR
      count+=1
      