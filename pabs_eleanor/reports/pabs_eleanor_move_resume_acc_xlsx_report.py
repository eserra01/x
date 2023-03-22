# -*- encoding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import ValidationError

class EleanorMoveResumeAcc(models.TransientModel):
  _name = 'pabs.eleanor.move.resume.acc'
  _description = 'Detalle de movimientos'

  period_type = fields.Selection([('weekly','Semanal'),('biweekly','Quincenal')], string="Tipo de periodo", required=True)

  def generate_xls_report(self):
    data = {
        'period_type': self.period_type,
        'period_name': dict(self._fields['period_type'].selection).get(self.period_type)
    }

    return self.env.ref('pabs_eleanor.pabs_eleanor_move_resume_acc_xlsx_report_id').report_action(self, data=data)

class PabsEleanorMoveResumAcctXlsxReport(models.AbstractModel):
    _name = 'report.pabs_eleanor.pabs_eleanor_move_resume_acc_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, recs):
            ### Crear libro
            sheet = workbook.add_worksheet("Resúmen de cuentas")
            bold = workbook.add_format({'bold': True})
            money_format = workbook.add_format({'num_format': '$#,##0.00'})

            consulta = """
                SELECT 
                    CONCAT('Provisión ', per.tipo_periodo, ' ', per.numero_periodo, ' Periodo ', per.fecha_inicial, ' al ', per.fecha_final) as ref,
                    CAST(per.fecha_final AS VARCHAR(10)) as date,
                    'Diario' as journal_id,
                    x.cuenta as "line_ids/account_id",
                    '' as "line_ids/partner_id",
                    CONCAT('Provisión ', per.tipo_periodo, ' ', per.numero_periodo, ' Periodo ', per.fecha_inicial, ' al ', per.fecha_final) as "line_ids/name",
                    x.analitica as "line_ids/analytic_account_id",
                    x.forma_pago as "line_ids/analytic_tag_ids",
                    x.total_percepciones as "line_ids/debit",
                    x.total_deducciones as "line_ids/credit"
                FROM
                (
                    SELECT 
                        week_number as numero_periodo,
                        CASE
                            WHEN period_type = 'weekly' THEN 'semana'
                            ELSE 'quincena'
                        END as tipo_periodo,
                        date_start as fecha_inicial,
                        date_end as fecha_final
                    FROM pabs_eleanor_period
                        WHERE state = 'open'
                        AND period_type = 'zztipo_periodozz'
                        AND company_id = zzid_companiazz
                ) AS per
                INNER JOIN
                (
                    /* Movimientos */
                    SELECT 
                        COALESCE(cue.name, '') as cuenta,
                        COALESCE(ana.name, '') as analitica,
                        CASE
                            WHEN emp.way_to_pay = 'rif' THEN 'RIF'
                            WHEN emp.way_to_pay = 'resico' THEN 'RESICO'
                            WHEN emp.way_to_pay = 'salary' THEN 'ASALARIADO'
                            ELSE ''
                        END as forma_pago,
                        SUM(CASE WHEN conc.concept_type = 'perception' THEN mov.amount ELSE 0 END) as total_percepciones,
                        SUM(CASE WHEN conc.concept_type = 'deduction' THEN mov.amount ELSE 0 END) as total_deducciones,
                        conc.concept_type as tipo_concepto
                    FROM pabs_eleanor_period AS per
                    INNER JOIN pabs_eleanor_move AS mov ON per.id = mov.period_id
                    LEFT JOIN stock_warehouse AS ofi ON mov.warehouse_id = ofi.id
                    LEFT JOIN hr_department AS dep ON mov.department_id = dep.id
                    LEFT JOIN account_analytic_account AS ana ON COALESCE(ofi.analytic_account_id, dep.account_analytic_id) = ana.id
                    INNER JOIN pabs_eleanor_concept AS conc ON mov.concept_id = conc.id
                    LEFT JOIN account_account AS cue ON conc.account_id = cue.id
                    INNER JOIN hr_employee AS emp ON mov.employee_id = emp.id
                    INNER JOIN hr_employee_status AS est ON emp.employee_status = est.id
                        WHERE per.state = 'open'
                        AND per.period_type = 'zztipo_periodozz'
                        AND per.company_id = zzid_companiazz
                            GROUP BY cue.name, ana.name, emp.way_to_pay, conc.concept_type
                    UNION 
                    /* Sueldos: Solo entregar sueldo a empleados activos */
                    SELECT
                        'Sueldos' as cuenta,
                        COALESCE(ana.name, '') as analitica,
                        CASE
                            WHEN emp.way_to_pay = 'rif' THEN 'RIF'
                            WHEN emp.way_to_pay = 'resico' THEN 'RESICO'
                            WHEN emp.way_to_pay = 'salary' THEN 'ASALARIADO'
                            ELSE ''
                        END as forma_pago,
                        CASE
                            WHEN emp.period_type = 'weekly' THEN SUM(ROUND(CAST((emp.total_internal_salary / 30) * 7 AS DECIMAL), 2))
                            WHEN emp.period_type = 'biweekly' THEN SUM(ROUND(CAST((emp.total_internal_salary / 30) * 15 AS DECIMAL), 2))
                            ELSE 0
                        END as total_percepciones,
                        0 as total_deducciones,
                        'perception' as tipo_concepto
                    FROM hr_employee AS emp
                    INNER JOIN hr_employee_status AS est ON emp.employee_status = est.id
                    LEFT JOIN stock_warehouse AS ofi ON emp.warehouse_id = ofi.id
                    LEFT JOIN hr_department AS dep ON emp.department_id = dep.id
                    LEFT JOIN account_analytic_account AS ana ON COALESCE(ofi.analytic_account_id, dep.account_analytic_id) = ana.id
                        WHERE est.name IN ('ACTIVO')
                        AND emp.period_type = 'zztipo_periodozz'
                        AND emp.company_id = zzid_companiazz
                        AND emp.total_internal_salary > 0
                            GROUP BY ana.name, emp.way_to_pay, emp.period_type
                ) AS x ON 1 = 1
                    ORDER BY x.tipo_concepto DESC, x.cuenta, x.analitica, x.forma_pago
            """

            consulta = consulta.replace('zztipo_periodozz', data['period_type'])
            consulta = consulta.replace('zzid_companiazz', str(self.env.company.id))

            self.env.cr.execute(consulta)
                    
            ### Encabezados
            fila = 0
            sheet.write(fila, 0, 'ref', bold)
            sheet.write(fila, 1, 'date', bold)
            sheet.write(fila, 2, 'journal_id', bold)
            sheet.write(fila, 3, 'line_ids/account_id', bold)
            sheet.write(fila, 4, 'line_ids/partner_id', bold)
            sheet.write(fila, 5, 'line_ids/name', bold)
            sheet.write(fila, 6, 'line_ids/analytic_account_id', bold)
            sheet.write(fila, 7, 'line_ids/analytic_tag_ids', bold)
            sheet.write(fila, 8, 'line_ids/debit', bold)
            sheet.write(fila, 9, 'line_ids/credit', bold)

            ### Filas
            for res in self.env.cr.fetchall():
                fila = fila + 1
                sheet.write(fila, 0, res[0])
                sheet.write(fila, 1, res[1])
                sheet.write(fila, 2, res[2])
                sheet.write(fila, 3, res[3])
                sheet.write(fila, 4, res[4])
                sheet.write(fila, 5, res[5])
                sheet.write(fila, 6, res[6])
                sheet.write(fila, 7, res[7])
                sheet.write(fila, 8, res[8], money_format)
                sheet.write(fila, 9, res[9], money_format)