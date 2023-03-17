# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PabsEleanorPeriod(models.Model):
    _name = 'pabs.eleanor.period'
    _description = 'Periodos'    
    _rec_name = 'week_number'

    week_number = fields.Integer(string="Número de periodo", required=True)
    date_start = fields.Date(string="Fecha inicio", required=True)
    date_end = fields.Date(string="Fecha fin", required=True)
    period_type = fields.Selection([('weekly','Semanal'),('biweekly','Quincenal')], string="Tipo", required=True)
    state = fields.Selection([('open','Abierto'),('close','Cerrado')], string="Estatus", required=True, default='open')
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,)

    @api.constrains('state')
    def _check_order(self):       
        for record in self:  
            period_id = self.search([
                ('period_type','=',record.period_type),
                ('state','=','open'),
                ('company_id','=',self.env.company.id)
            ])
                    
            if len(period_id) > 1:
                raise ValidationError("Ya existe un periodo abierto con el tipo seleccionado, por favor cierre el periodo para poder crear uno nuevo.") 

    def close_period(self):
        vals = {'info': 'Esta acción cerrará el periodo seleccionado, de click en Aceptar para continuar...'}
        wizard_id = self.env['pabs.eleanor.close.period.wizard'].create(vals)
        return {
            'name':"Cerrar periodo",
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'pabs.eleanor.close.period.wizard',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': wizard_id.id,
        }  
        return True

    def CargarComisiones(self, id_compania = False):

        # DICCIONARIO DE PARAMETROS PARA CARGA DE COMISIONES
        EMPRESAS = [
            ### PRODUCCION ###
            {
                'empresa': 'GUADALAJARA',
                'version': 14,
                'id_compania': 1,
                'id_compania_viejo_esquema': 0
            },
            {
                'empresa': 'TOLUCA',
                'version': 14,
                'id_compania': 1,
                'id_compania_viejo_esquema': 0
            },
            {
                'empresa': 'PUEBLA',
                'version': 14,
                'id_compania': 1,
                'id_compania_viejo_esquema': 0
            },
            {
                'empresa': 'MERIDA',
                'version': 14,
                'id_compania': 2,
                'id_compania_viejo_esquema': 0
            },
            {
                'empresa': 'CANCUN',
                'version': 14,
                'id_compania': 3,
                'id_compania_viejo_esquema': 0
            },
            {
                'empresa': 'SALTILLO NUEVO E',
                'version': 13,
                'id_compania': 12,
                'id_compania_viejo_esquema': 18
            },
            {
                'empresa': 'CUERNAVACA',
                'version': 13,
                'id_compania': 7,
                'id_compania_viejo_esquema': 0
            },
            {
                'empresa': 'TAMPICO NUEVO E',
                'version': 13,
                'id_compania': 16,
                'id_compania_viejo_esquema': 17
            },
            {
                'empresa': 'ACAPULCO NUEVO E',
                'version': 13,
                'id_compania': 15,
                'id_compania_viejo_esquema': 1
            },
            {
                'empresa': 'MONCLOVA NUEVO E',
                'version': 13,
                'id_compania': 13,
                'id_compania_viejo_esquema': 19
            },
            {
                'empresa': 'NUEVO LAREDO NUEVO E',
                'version': 13,
                'id_compania': 14,
                'id_compania_viejo_esquema': 20
            },
            {
                'empresa': 'TUXTLA GUTIERREZ',
                'version': 13,
                'id_compania': 6,
                'id_compania_viejo_esquema': 0
            },
            {
                'empresa': 'VILLAHERMOSA',
                'version': 13,
                'id_compania': 8,
                'id_compania_viejo_esquema': 0
            },

            ### TEST
            {
                'empresa': 'SALTILLO',
                'version': 13,
                'id_compania': 12,
                'id_compania_viejo_esquema': 0
            },
            {
                'empresa': 'MONCLOVA',
                'version': 13,
                'id_compania': 13,
                'id_compania_viejo_esquema': 0
            },
            {
                'empresa': 'NUEVO LAREDO',
                'version': 13,
                'id_compania': 14,
                'id_compania_viejo_esquema': 0
            }
            ### FIN TEST
        ]

        if not id_compania:
            id_compania = self.env.company.id

        company = self.env['res.company'].browse(id_compania)

        ### Obtener parametros de carga
        param = next((x for x in EMPRESAS if x['empresa'] == company.name), 0)

        if not param:
            raise ValidationError("No se encontraron parámetros de carga para la empresa {}".format(company.name))
        
        ### Obtener conceptos
        id_concepto_comisiones = self.env['pabs.eleanor.concept'].search([
            ('company_id', '=', company.id),
            ('name', '=', 'P_COMISIONES')
        ])

        if not id_concepto_comisiones:
            raise ValidationError("No se encontró el concepto P_COMISIONES")
        
        id_concepto_comisiones = id_concepto_comisiones.id

        id_concepto_transferencia = self.env['pabs.eleanor.concept'].search([
            ('company_id', '=', company.id),
            ('name', '=', 'P_COMISIONES TRANSFERENCIA')
        ])

        if not id_concepto_transferencia:
            raise ValidationError("No se encontró el concepto P_COMISIONES TRANSFERENCIA")
        
        id_concepto_transferencia = id_concepto_transferencia.id

        ### Validar que no existan comisiones en el periodo a cargar
        move_obj = self.env['pabs.eleanor.move']
        periodo = self

        cant = move_obj.search_count([
            ('company_id', '=', company.id),
            ('period_id', '=', periodo.id),
            ('concept_id', 'in', (id_concepto_comisiones, id_concepto_transferencia))
        ])

        if cant > 0:
            raise ValidationError("Ya existen {} comisiones para el periodo {} del {} al {}".format(cant, periodo.week_number, periodo.date_start, periodo.date_end))
        
        ### Sin viejo esquema ###
        if param['id_compania_viejo_esquema'] == 0:
            consulta = ""

            ### Version 14 ###
            if param['version'] == 14:
                consulta = """
                    SELECT
                        emp.barcode as codigo,
                        emp.id as employee_id,
                        CASE
                            WHEN ofi.id IS NOT NULL THEN ofi.pabs_eleanor_area_id
                            WHEN dep.id IS NOT NULL THEN dep.pabs_eleanor_area_id
                            ELSE 0
                        END as area_id,
                        car.id as job_id,
                        COALESCE(ofi.id, 0) as warehouse_id,
                        COALESCE(dep.id, 0) as department_id,
                        ROUND(CAST(com.comision AS DECIMAL), 2) as comision
                    FROM hr_employee AS emp
                    LEFT JOIN hr_job AS car ON emp.job_id = car.id
                    LEFT JOIN stock_warehouse AS ofi ON emp.warehouse_id = ofi.id
                    LEFT JOIN hr_department AS dep ON emp.department_id = dep.id
                    INNER JOIN 
                    (
                        SELECT 
                            com.comission_agent_id as id_empleado,
                            SUM(com.actual_commission_paid) as comision
                        FROM account_payment AS abo
                        INNER JOIN account_move AS mov ON abo.move_id = mov.id
                        INNER JOIN pabs_comission_output AS com ON abo.id = com.payment_id
                            WHERE mov.state = 'posted' 
                            AND abo.reference in ('payment', 'surplus')
                            AND com.company_id = {}
                            AND abo.payment_date BETWEEN '{}' AND '{}' 
                                GROUP BY com.comission_agent_id
                    ) AS com ON emp.id = com.id_empleado
                        WHERE car.name NOT IN ('FIDEICOMISO', 'PAPELERIA', 'IVA')
                        AND com.comision > 0
                            ORDER BY emp.barcode
                """.format(company.id, periodo.date_start, periodo.date_end)
            
            ### Version 13 ###
            elif param['version'] == 13:
                consulta = """
                    SELECT
                        emp.barcode as codigo,
                        emp.id as employee_id,
                        CASE
                            WHEN ofi.id IS NOT NULL THEN ofi.pabs_eleanor_area_id
                            WHEN dep.id IS NOT NULL THEN dep.pabs_eleanor_area_id
                            ELSE 0
                        END as area_id,
                        car.id as job_id,
                        COALESCE(ofi.id, 0) as warehouse_id,
                        COALESCE(dep.id, 0) as department_id,
                        ROUND(CAST(com.comision AS DECIMAL), 2) as comision
                    FROM hr_employee AS emp
                    LEFT JOIN hr_job AS car ON emp.job_id = car.id
                    LEFT JOIN stock_warehouse AS ofi ON emp.warehouse_id = ofi.id
                    LEFT JOIN hr_department AS dep ON emp.department_id = dep.id
                    INNER JOIN 
                    (
                        SELECT 
                            com.comission_agent_id as id_empleado,
                            SUM(com.actual_commission_paid) as comision
                        FROM account_payment AS abo
                        INNER JOIN pabs_comission_output AS com ON abo.id = com.payment_id
                            WHERE abo.state = 'posted' 
                            AND abo.reference in ('payment', 'surplus')
                            AND com.company_id = {}
                            AND abo.payment_date BETWEEN '{}' AND '{}' 
                                GROUP BY com.comission_agent_id
                    ) AS com ON emp.id = com.id_empleado
                        WHERE car.name NOT IN ('FIDEICOMISO', 'PAPELERIA', 'IVA')
                        AND com.comision > 0
                            ORDER BY emp.barcode
                """.format(company.id, periodo.date_start, periodo.date_end)

            ### Cargar comisiones ###
            self.env.cr.execute(consulta)

            comisiones = []
            for res in self.env.cr.fetchall():
                codigo = res[0]
                
                area_id = res[2]
                if not area_id:
                    raise ValidationError("El empleado {} no tiene una area".format(codigo))
                    

                job_id = res[3]
                if not job_id:
                    raise ValidationError("El empleado {} no tiene un puesto".format(codigo))
                
                warehouse_id = res[4]
                department_id = res[5]

                if not warehouse_id and not department_id:
                    raise ValidationError("El empleado {} no tiene ni oficina ni departamento".format(codigo))

                comisiones.append({
                    'period_id':        periodo.id,
                    'move_type':        'perception',
                    'concept_id':       id_concepto_comisiones,
                    'employee_id':      res[1],
                    'area_id':          area_id,
                    'job_id':           job_id,
                    'warehouse_id':     warehouse_id if warehouse_id else None,
                    'department_id':    department_id if department_id else None,
                    'amount':           res[6],
                    'company_id':       company.id
                })

            if comisiones:
                move_obj.with_context(migration=True).create(comisiones)
                self.env['pabs.eleanor.migration.log'].create([{
                    'tabla': 'Carga de comisiones', 
                    'registro': 'Semana {} del {} al {}'.format(periodo.week_number, periodo.date_start, periodo.date_end),
                    'mensaje': 'Se crearon {} registros'.format(len(comisiones))
                }])
            else:
                raise ValidationError("No se encontraron comisiones")

        ### Con viejo esquema ###
        else:
            ### Version 13 ###
            
            ### Cobradores ###
            consulta_cobradores = """
                SELECT
                    emp.barcode,
                    emp.id as employee_id,
                    CASE
                        WHEN ofi.id IS NOT NULL THEN ofi.pabs_eleanor_area_id
                        WHEN dep.id IS NOT NULL THEN dep.pabs_eleanor_area_id
                        ELSE NULL
                    END as area_id,
                    car.id as job_id,
                    ofi.id as warehouse_id,
                    dep.id as department_id,
                    ROUND(CAST(com.comision AS DECIMAL), 2) as comision
                FROM hr_employee AS emp
                LEFT JOIN hr_job AS car ON emp.job_id = car.id
                LEFT JOIN stock_warehouse AS ofi ON emp.warehouse_id = ofi.id
                LEFT JOIN hr_department AS dep ON emp.department_id = dep.id
                INNER JOIN 
                (
                    SELECT 
                        emp.barcode as codigo_empleado,
                        ROUND(SUM(CAST(com.actual_commission_paid AS DECIMAL)), 2) as comision
                    FROM account_payment AS abo
                    INNER JOIN pabs_comission_output AS com ON abo.id = com.payment_id
                    INNER JOIN hr_employee AS emp ON com.comission_agent_id = emp.id
                        WHERE abo.state = 'posted' 
                        AND abo.reference in ('payment', 'surplus')
                        AND com.company_id IN ({}, {})
                        AND abo.payment_date BETWEEN '{}' AND '{}' 
                            GROUP BY emp.barcode
                ) AS com ON emp.barcode = com.codigo_empleado
                    WHERE car.name LIKE '%COBRA%'
                    AND emp.company_id = {}
                    AND com.comision > 0
                        ORDER BY emp.barcode
            """.format(param['id_compania_viejo_esquema'], company.id, '2022-01-01', '2022-01-10', company.id)#periodo.date_start, periodo.date_end, company.id)

            self.env.cr.execute(consulta_cobradores)

            comisiones = []
            for res in self.env.cr.fetchall():
                codigo = res[0]
                    
                area_id = res[2]
                if not area_id:
                    raise ValidationError("El empleado {} no tiene una area".format(codigo))
                    

                job_id = res[3]
                if not job_id:
                    raise ValidationError("El empleado {} no tiene un puesto".format(codigo))
                
                warehouse_id = res[4]
                department_id = res[5]

                if not warehouse_id and not department_id:
                    raise ValidationError("El empleado {} no tiene ni oficina ni departamento".format(codigo))

                comisiones.append({
                    'period_id':        periodo.id,
                    'move_type':        'perception',
                    'concept_id':       id_concepto_comisiones,
                    'employee_id':      res[1],
                    'area_id':          area_id,
                    'job_id':           job_id,
                    'warehouse_id':     warehouse_id if warehouse_id else None,
                    'department_id':    department_id if department_id else None,
                    'amount':           res[6],
                    'company_id':       company.id
                })
            
            ### Asistentes ###
            consulta_asistentes = """
                SELECT
                    emp.barcode,
                    emp.id as employee_id,
                    CASE
                        WHEN ofi.id IS NOT NULL THEN ofi.pabs_eleanor_area_id
                        WHEN dep.id IS NOT NULL THEN dep.pabs_eleanor_area_id
                        ELSE NULL
                    END as area_id,
                    car.id as job_id,
                    ofi.id as warehouse_id,
                    dep.id as department_id,
                    ROUND(CAST(com.comision AS DECIMAL), 2) as comision,
                    ROUND(CAST(com.transferencia AS DECIMAL), 2) as transferencia
                FROM hr_employee AS emp
                LEFT JOIN hr_job AS car ON emp.job_id = car.id
                LEFT JOIN stock_warehouse AS ofi ON emp.warehouse_id = ofi.id
                LEFT JOIN hr_department AS dep ON emp.department_id = dep.id
                INNER JOIN 
                (
                    SELECT 
                        emp.barcode as codigo_empleado,
                        SUM(CASE
                            WHEN com.company_id = {} THEN com.actual_commission_paid
                            ELSE 0
                        END) as comision,
                        SUM(CASE
                            WHEN com.company_id = {} THEN com.actual_commission_paid
                            ELSE 0
                        END) as transferencia
                    FROM account_payment AS abo
                    INNER JOIN pabs_comission_output AS com ON abo.id = com.payment_id
                    INNER JOIN hr_employee AS emp ON com.comission_agent_id = emp.id
                        WHERE abo.state = 'posted' 
                        AND abo.reference in ('payment', 'surplus')
                        AND com.company_id IN ({}, {})
                        AND abo.payment_date BETWEEN '{}' AND '{}' 
                            GROUP BY emp.barcode
                ) AS com ON emp.barcode = com.codigo_empleado 
                    WHERE car.name NOT IN ('FIDEICOMISO', 'PAPELERIA', 'IVA')
                    AND car.name NOT LIKE '%COBRA%'
                    AND emp.warehouse_id IS NOT NULL
                    AND emp.company_id = {}
                    AND (com.comision > 0 or com.transferencia > 0)
                        ORDER BY emp.barcode
            """.format(param['id_compania_viejo_esquema'], company.id, param['id_compania_viejo_esquema'], company.id, periodo.date_start, periodo.date_end, company.id)

            self.env.cr.execute(consulta_asistentes)

            for res in self.env.cr.fetchall():
                codigo = res[0]
                    
                area_id = res[2]
                if not area_id:
                    raise ValidationError("El empleado {} no tiene una area".format(codigo))
                    

                job_id = res[3]
                if not job_id:
                    raise ValidationError("El empleado {} no tiene un puesto".format(codigo))
                
                warehouse_id = res[4]
                department_id = res[5]

                if not warehouse_id and not department_id:
                    raise ValidationError("El empleado {} no tiene ni oficina ni departamento".format(codigo))

                if res[6] > 0:
                    comisiones.append({
                        'period_id':        periodo.id,
                        'move_type':        'perception',
                        'concept_id':       id_concepto_comisiones,
                        'employee_id':      res[1],
                        'area_id':          area_id,
                        'job_id':           job_id,
                        'warehouse_id':     warehouse_id if warehouse_id else None,
                        'department_id':    department_id if department_id else None,
                        'amount':           res[6],
                        'company_id':       company.id
                    })

                if res[7] > 0:
                    comisiones.append({
                        'period_id':        periodo.id,
                        'move_type':        'perception',
                        'concept_id':       id_concepto_transferencia,
                        'employee_id':      res[1],
                        'area_id':          area_id,
                        'job_id':           job_id,
                        'warehouse_id':     warehouse_id if warehouse_id else None,
                        'department_id':    department_id if department_id else None,
                        'amount':           res[7],
                        'company_id':       company.id
                    })

            ### Cargar comisiones ###
            if comisiones:
                move_obj.with_context(migration=True).create(comisiones)
                self.env['pabs.eleanor.migration.log'].create([{
                    'tabla': 'Carga de comisiones', 
                    'registro': 'Semana {} del {} al {}'.format(periodo.week_number, periodo.date_start, periodo.date_end),
                    'mensaje': 'Se crearon {} registros'.format(len(comisiones))
                }])
            else:
                raise ValidationError("No se encontraron comisiones")