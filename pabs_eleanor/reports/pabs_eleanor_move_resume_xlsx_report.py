# -*- encoding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import ValidationError

class EleanorMoveResume(models.TransientModel):
  _name = 'pabs.eleanor.move.resume'
  _description = 'Detalle de movimientos'

  period_type = fields.Selection([('weekly','Semanal'),('biweekly','Quincenal')], string="Tipo de periodo", required=True)

  def generate_xls_report(self):
    data = {
        'period_type': self.period_type,
        'period_name': dict(self._fields['period_type'].selection).get(self.period_type)
    }

    return self.env.ref('pabs_eleanor.pabs_eleanor_move_resume_xlsx_report_id').report_action(self, data=data)

class PabsEleanorMoveResumeXlsxReport(models.AbstractModel):
    _name = 'report.pabs_eleanor.pabs_eleanor_move_resume_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, recs):

        ### Obtener permisos de acceso del usuario ###
        ids_departamentos = []
        ids_oficinas = []
        all_employees_allowed = self.env.user.all_employees

        if not all_employees_allowed:
            accesos = self.env['pabs.eleanor.user.access'].search([
                ('company_id', '=', self.env.company.id),
                ('user_id', '=', self.env.user.id)
            ])

            ids_departamentos = accesos.mapped('department_id').ids
            ids_oficinas = accesos.mapped('warehouse_id').ids
        
        ### Crear libro
        sheet = workbook.add_worksheet("Resúmen de movimientos")
        bold = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '$#,##0.00'})

        consulta = """
            SELECT 
                x.codigo,
                x.nombre,
                x.oficina,
                x.estatus,
                x.sueldo,
                x.total_percepciones,
                x.total_deducciones,
                x.total_comisiones,
                x.total_com_transferencia,
                (x.sueldo + x.total_percepciones + x.total_comisiones + x.total_com_transferencia - x.total_deducciones) as neto,
                x.id_oficina,
	            x.id_departamento
            FROM
            (
                SELECT 
                    emp.barcode as codigo,
                    emp.name as nombre,
                    COALESCE(ofi.name, dep.name) as oficina,
                    est.name as estatus,
                    COALESCE(sue.sueldo, 0) as sueldo,
                    COALESCE(mov.total_percepciones, 0) as total_percepciones,
                    COALESCE(mov.total_deducciones, 0) as total_deducciones,
                    COALESCE(mov.total_comisiones, 0) as total_comisiones,
                    COALESCE(mov.total_com_transferencia, 0) as total_com_transferencia,
                    COALESCE(emp.warehouse_id, 0) as id_oficina,
		            COALESCE(emp.department_id, 0) as id_departamento
                FROM hr_employee AS emp
                INNER JOIN hr_employee_status AS est ON emp.employee_status = est.id
                LEFT JOIN stock_warehouse AS ofi ON emp.warehouse_id = ofi.id
                LEFT JOIN hr_department AS dep ON emp.department_id = dep.id
                LEFT JOIN
                (
                    SELECT 
                        emp.id as id_empleado,
                        CASE
                            WHEN emp.period_type = 'weekly' THEN ROUND(CAST((emp.total_internal_salary / 30) * 7 AS DECIMAL), 2)
                            WHEN emp.period_type = 'biweekly' THEN ROUND(CAST((emp.total_internal_salary / 30) * 15 AS DECIMAL), 2)
                            ELSE 0
                        END as sueldo
                    FROM hr_employee AS emp
                        WHERE emp.period_type = 'zztipo_periodozz'
                        AND emp.company_id = zzid_companiazz
                ) AS sue ON emp.id = sue.id_empleado
                LEFT JOIN 
                (
                    SELECT 
                        mov.employee_id as id_empleado,
                        SUM(CASE WHEN conc.concept_type = 'perception' AND conc.allow_load = TRUE THEN mov.amount ELSE 0 END) as total_percepciones,
                        SUM(CASE WHEN conc.concept_type = 'deduction' AND conc.allow_load = TRUE THEN mov.amount ELSE 0 END) as total_deducciones,
                        SUM(CASE WHEN conc.concept_type = 'perception' AND conc.name = 'P_COMISIONES' THEN mov.amount ELSE 0 END) as total_comisiones,
                        SUM(CASE WHEN conc.concept_type = 'perception' AND conc.name = 'P_COMISIONES TRANSFERENCIA' THEN mov.amount ELSE 0 END) as total_com_transferencia
                    FROM pabs_eleanor_period AS per
                    INNER JOIN pabs_eleanor_move AS mov ON per.id = mov.period_id
                    INNER JOIN pabs_eleanor_concept AS conc ON mov.concept_id = conc.id
                        WHERE per.state = 'open'
                        AND per.period_type = 'zztipo_periodozz'
                        AND per.company_id = zzid_companiazz
                            GROUP BY mov.employee_id
                ) AS mov ON emp.id = mov.id_empleado
                    WHERE emp.period_type = 'zztipo_periodozz'
                    AND emp.company_id = zzid_companiazz
                    AND est.name IN ('ACTIVO')
            ) AS x
                WHERE (x.sueldo + x.total_percepciones + x.total_comisiones + x.total_com_transferencia + x.total_deducciones) > 0
                    ORDER BY x.codigo
        """

        consulta = consulta.replace('zztipo_periodozz', data['period_type'])
        consulta = consulta.replace('zzid_companiazz', str(self.env.company.id))

        self.env.cr.execute(consulta)
                
        ### Encabezados
        fila = 0
        sheet.write(fila, 0, 'Codigo', bold)
        sheet.write(fila, 1, 'Nombre', bold)
        sheet.write(fila, 2, 'Oficina', bold)
        sheet.write(fila, 3, 'Estatus', bold)
        sheet.write(fila, 4, 'Sueldo', bold)
        sheet.write(fila, 5, 'Total percepciones', bold)
        sheet.write(fila, 6, 'Total deducciones', bold)
        sheet.write(fila, 7, 'Total comisiones', bold)
        sheet.write(fila, 8, 'Total comisiones transferencia', bold)
        sheet.write(fila, 9, 'Neto', bold)

        ### Filas
        for res in self.env.cr.fetchall():            
            ### No enviar empleados a los que no tiene acceso
            if all_employees_allowed:
                fila = fila + 1
            else:
                restringido = True
                if res[10] and res[10] in ids_oficinas:
                        restringido = False
                elif res[11] and res[11] in ids_departamentos:
                        restringido = False
                
                if restringido:
                    continue
                else:
                    fila = fila + 1

            sheet.write(fila, 0, res[0])
            sheet.write(fila, 1, res[1])
            sheet.write(fila, 2, res[2])
            sheet.write(fila, 3, res[3])
            sheet.write(fila, 4, res[4], money_format)
            sheet.write(fila, 5, res[5], money_format)
            sheet.write(fila, 6, res[6], money_format)
            sheet.write(fila, 7, res[7], money_format)
            sheet.write(fila, 8, res[8], money_format)
            sheet.write(fila, 9, res[9], money_format)