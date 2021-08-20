# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

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

    raise ValidationError(res)

    return True
