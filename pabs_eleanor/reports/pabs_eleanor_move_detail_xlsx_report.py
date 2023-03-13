# -*- encoding: utf-8 -*-
from odoo import models, fields

class EleanorMoveDetail(models.TransientModel):
  _name = 'pabs.eleanor.move.detail'
  _description = 'Detalle de movimientos'

  period_type = fields.Selection([('weekly','Semanal'),('biweekly','Quincenal')], string="Tipo de periodo", required=True)

  def generate_xls_report(self):
    data = {
       'period_type': self.period_type,
       'period_name': dict(self._fields['period_type'].selection).get(self.period_type)
    }

    return self.env.ref('pabs_eleanor.pabs_eleanor_move_detail_xlsx_report_id').report_action(self, data=data)

class PabsEleanorMoveDetailXlsxReport(models.AbstractModel):
    _name = 'report.pabs_eleanor.pabs_eleanor_move_detail_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, recs):
        id_compania = self.env.company.id

        bold = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '$#,##0.00'})

        ### Buscar periodo abierto
        period_type = data['period_type']
        period_id = self.env['pabs.eleanor.move'].get_period(period_type = period_type)

        if not period_id:
            sheet.write(0, 0, 'No se encontró un periodo abierto', bold)
            return
        else:
            period_id = period_id.id

        ### Obtener permisos de acceso del usuario
        ids_departamentos = []
        ids_oficinas = []
        all_employees_allowed = self.env.user.all_employees

        if not all_employees_allowed:
            accesos = self.env['pabs.eleanor.user.access'].search([
                ('company_id', '=', id_compania),
                ('user_id', '=', self.env.user.id)
            ])

            ids_departamentos = accesos.mapped('department_id').ids
            ids_oficinas = accesos.mapped('warehouse_id').ids

        ### Buscar conceptos
        conceptos_enc = self.env['pabs.eleanor.concept'].search([
            ('company_id', '=', id_compania)
        ], order="concept_type desc, order")

        ### Buscar movimientos del periodo
        movimientos_aux = []
        if all_employees_allowed:
            movimientos_aux = self.env['pabs.eleanor.move'].search([
                ['company_id', '=', id_compania],
                ['period_id', '=', period_id],
                ['employee_id.employee_status.name', '=', 'ACTIVO']
            ])
        else:
            movimientos_aux = self.env['pabs.eleanor.move'].search([
                ['company_id', '=', id_compania],
                ['period_id', '=', period_id],
                ['employee_id.employee_status.name', '=', 'ACTIVO'],
                '|', ['employee_id.department_id.id', 'in', ids_departamentos],
                ['employee_id.warehouse_id.id', 'in', ids_oficinas]
            ])

        ### Construir diccionario para la escritura de filas:
        
        # [
        #     {
        #         "codigo": "A0001",
        #         "nombre": "JUAN PEREZ",
        #         "oficina": "GUERREROS",
        #         "estatus": "ACTIVO",
        #         "movimientos":[
        #             {
        #                 "id_concepto": "1",
        #                 "monto": 100
        #             },
        #             {
        #                 "id_concepto": "2",
        #                 "monto": 200
        #             },#...
        #         ]
        #     },#...
        # ]

        empleados = movimientos_aux.mapped('employee_id')
        empleados = empleados.sorted(key=lambda x: x.barcode)

        registros = []
        for emp in empleados:
            reg = {
                "codigo": emp.barcode,
                "nombre": emp.name,
                "oficina": emp.warehouse_id.name if emp.warehouse_id else emp.department_id.name,
                "estatus": emp.employee_status.name
            }

            mov_del_emp = movimientos_aux.filtered(lambda x: x.employee_id.id == emp.id)
                        
            movimientos = []
            for mov in mov_del_emp:
                movimientos.append({
                    "id_concepto": mov.concept_id.id,
                    "monto": mov.amount
                })

            reg.update({"movimientos": movimientos})

            registros.append(reg)
            
        ##############################################################
        ########## HOJA CON TODOS LOS EMPLEADOS Y CONCEPTOS ##########
        sheet = workbook.add_worksheet("Todos los movimientos")
        
        ### Escribir encabezados 
        fila = 0
        sheet.write(fila, 0, "Codigo", bold)
        sheet.write(fila, 1, "Nombre", bold)
        sheet.write(fila, 2, "Oficina", bold)
        sheet.write(fila, 3, "Estatus", bold)

        ### Lista de todos conceptos con número de columna en archivo de Excel
        conceptos_col = []
        col = 4
        for conc in conceptos_enc:
            sheet.write(fila, col, conc.name2, bold)

            conceptos_col.append({
                "id": conc.id,
                "columna": col
            })

            col = col + 1

        ### Consultar empleados (Solo de los que tiene acceso)
        empleados = []
        if all_employees_allowed:
            empleados = self.env['hr.employee'].search([
                ('company_id', '=', id_compania),
                ('period_type', '=', period_type),
                ('employee_status.name', 'in', ['ACTIVO'])
            ], order="barcode")
        else:
            empleados = self.env['hr.employee'].search([
                ('company_id', '=', id_compania),
                ('period_type', '=', period_type),
                ('employee_status.name', 'in', ['ACTIVO']),
                '|', ['department_id.id', 'in', ids_departamentos],
                ['warehouse_id.id', 'in', ids_oficinas]
            ], order="barcode")

        ### Escribir filas
        for emp in empleados:
            fila = fila + 1

            ### Datos del empleado
            sheet.write(fila, 0, emp.barcode)
            sheet.write(fila, 1, emp.name)
            sheet.write(fila, 2, emp.warehouse_id.name if emp.warehouse_id else emp.department_id.name)
            sheet.write(fila, 3, emp.employee_status.name)

            ### Buscar movimentos del empleado
            reg = next((x for x in registros if x['codigo'] == emp.barcode), 0)

            ### Movimientos del empleado
            if reg:
                for mov in reg['movimientos']:
                    ### Encontrar columna correspondiente
                    col = next((x for x in conceptos_col if x['id'] == mov['id_concepto']), 0)

                    if not col:
                        sheet.write(fila, 0, "No se encontró el concepto con id {}".format(mov['id_concepto']))
                        return
                    else:
                        sheet.write(fila, col['columna'], mov['monto'], money_format)

        ############################################################################
        ########## HOJA QUE CONTIENE SOLO EMPLEADOS Y CONCEPTOS CON VALOR ##########
        sheet = workbook.add_worksheet("Solo movimientos con valor")

        ### Escribir encabezados 
        fila = 0
        sheet.write(fila, 0, "Codigo", bold)
        sheet.write(fila, 1, "Nombre", bold)
        sheet.write(fila, 2, "Oficina", bold)
        sheet.write(fila, 3, "Estatus", bold)

        ### Lista de conceptos que tienen movimiento con número de columna en archivo de Excel
        conceptos_con_mov = movimientos_aux.mapped('concept_id')

        conceptos_col = []
        col = 4
        for conc in conceptos_enc:
            if conc.id in conceptos_con_mov.ids:
                sheet.write(fila, col, conc.name2, bold)

                conceptos_col.append({
                    "id": conc.id,
                    "columna": col
                })

                col = col + 1

        ### Escribir filas
        for reg in registros:
            fila = fila + 1

            ### Datos del empleado
            sheet.write(fila, 0, reg['codigo'])
            sheet.write(fila, 1, reg['nombre'])
            sheet.write(fila, 2, reg['oficina'])
            sheet.write(fila, 3, reg['estatus'])
            
            ### Movimientos del empleado
            for mov in reg['movimientos']:
                ### Encontrar columna correspondiente
                col = next((x for x in conceptos_col if x['id'] == mov['id_concepto']), 0)

                if not col:
                    sheet.write(fila, 0, "No se encontró el concepto con id {}".format(mov['id_concepto']))
                    return
                else:
                    sheet.write(fila, col['columna'], mov['monto'], money_format)