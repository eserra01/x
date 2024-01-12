from datetime import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import ValidationError

class ReportWizardComisionesPromotores(models.TransientModel):
    _name = 'report.pabs.comisiones.promotores'

    date_from = fields.Date(
        string='Desde',
    )
    date_to = fields.Date(
        string='Hasta',
    )

    def filter(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.date_from,
                'date_end': self.date_to,
            },
        }
        
        return self.env.ref('xmarts_funeraria.id_comisiones_promotores').report_action(self, data=data)


class ReportComisionesPromotores(models.AbstractModel):
    _name = "report.xmarts_funeraria.comisiones_promotores"

    @api.model
    def _get_report_values(self, docids, data=None):

        # NIVELES
        # 0. Oficina        
        #   1. Codigo del empleado
                # 2. Plan
                    # 3. Cobrador que recuperó el abono
                        # 4. Contratos
                    # 3z Total cobrador
                # 2z Total plan
        #   1z Total código empleado
        # 0z Oficina

        rep = [
            {'nombre_oficina':'JAGUARES', 'codigos':[
                {'codigo': 'P0024', 'total_codigo': 200.0, 
                    'planes': [{
                        'asistente_plan': 'P0024 - ESTELA MORALES RENDON  - 1CJ',
                        'subtotal_plan_asistente': 200.0,
                        'subtotal_plan_cobrador': 0.0,
                        'cobradores': [{
                            'cobrador': 'NINGUNO',
                            'subtotal_asistente': 200.0,
                            'subtotal_cobrador': 0.0,
                            'pagos': [{
                                'fecha_recibo': False,
                                'fecha_oficina': '2021-02-15',
                                'contrato': '1CJ005115',
                                'recibo': False,
                                'cliente': 'LIZBETH CISNEROS GARCIA',
                                'importe': 100.0,
                                'comision_asistente': 100.0,
                                'comision_cobrador': 0.0,
                                }, {
                                'fecha_recibo': False,
                                'fecha_oficina': '2021-02-15',
                                'contrato': '1CJ005119',
                                'recibo': False,
                                'cliente': 'JAVIER HECTOR BRITO MARTINEZ',
                                'importe': 900.0,
                                'comision_asistente': 100.0,
                                'comision_cobrador': 0.0,
                                }
                            ],
                        }],
                    }]
                },
                {'codigo': '...',}
            ]},
            {'oficina':'JAGUARES', 'empleados':['...']}
        ]
                

        # Agregar validacion de fechas
        fecha_inicial = data['form']['date_start']
        fecha_final = data['form']['date_end']

        #Si se seleccionaron fechas
        if not fecha_inicial or not fecha_final:
            raise ValidationError("Elige las fechas")        

        #Consultar id de cargo papeleria, cobrador y fideicomiso
        cargo_papeleria = self.env['hr.job'].search([('name','=','PAPELERIA')])
        cargo_cobrador = self.env['hr.job'].search([('name','=','COBRADOR')])
        cargo_fideicomiso = self.env['hr.job'].search([('name','=','FIDEICOMISO')])

        # Consultar todas las salidas de comisiones entre las fechas elegidas y que estén validadas o posterior
        # (El modelo de salida de comisiones tiene un campo related con la fecha de oficina del pago)
        salidas = self.env['pabs.comission.output'].search([
            ('payment_date', '>=', fecha_inicial), 
            ('payment_date', '<=', fecha_final),
            ('payment_status', 'in', ['posted','sent','reconciled']),
            ('job_id', 'not in', [cargo_papeleria.id, cargo_cobrador.id, cargo_fideicomiso.id])
            ]
        )

        # Validar que todas las salidas tengan un empleado que comisiona
        lista_salidas_error = ""
        for pago in salidas:
            if not pago.comission_agent_id:
                lista_salidas_error = "No se tiene un empleado asignado a la salida de comisiones en el recibo {}\n".format(pago.ecobro_receipt)

        if lista_salidas_error != "":
            raise ValidationError(lista_salidas_error)

        #raise ValidationError("{}".format(aux_oficinas_unicas))
        # Recordset de oficinas únicas de todas las salidas y ordenar por nombre
        aux_oficinas_unicas = salidas.mapped(lambda salida: salida.comission_agent_id.warehouse_id)
        aux_oficinas_unicas = aux_oficinas_unicas.sorted(key=lambda ofi: ofi.name)
        
        #Iterar en cada oficina
        lista_oficinas = [] # Lista que se enviará al reporte
        total_comisiones_asistentes = 0

        for ofi in aux_oficinas_unicas:
            #0. Filtrar las salidas por oficina
            aux_salidas_por_oficina = salidas.filtered(lambda salida: salida.comission_agent_id.warehouse_id.id == ofi.id)

            # Recordset de códigos únicos de los empleados que pertenecen a una oficina y ordenar por nombre
            aux_codigos_unicos = []
            aux_codigos_unicos = aux_salidas_por_oficina.mapped(lambda salida: salida.comission_agent_id)
            aux_codigos_unicos = aux_codigos_unicos.sorted(key=lambda emp: emp.name)


            lista_codigos = [] 

            for empleado in aux_codigos_unicos:
                # 1. Filtrar las salidas por código de empleado
                aux_salidas_por_empleado = aux_salidas_por_oficina.filtered(lambda salida: salida.comission_agent_id.barcode == empleado.barcode)

                for codigo in aux_salidas_por_empleado:
                    
                    #Obtener los planes de las salidas
                    aux_planes_unicos = aux_salidas_por_empleado.mapped(lambda salida: salida.payment_id.contract.name_service)
                    
                    lista_planes = []

                    total_codigo = 0
                    for plan in aux_planes_unicos:
                        subtotal_plan_asistente = 0
                        subtotal_plan_cobrador = 0
                        lista_cobradores = []

                        # 2. Filtrar las salidas por tipo de plan
                        aux_salidas_por_plan = aux_salidas_por_empleado.filtered(lambda salida: salida.payment_id.contract.name_service.id == plan.id) #<<< PLAN 1CJ FORZADO = 62

                        ### Primero: Anexar las salidas de los pagos sin cobrador
                        # Filtrar las salidas que no tiene cobrador
                        aux_salidas_sin_cobrador = aux_salidas_por_plan.filtered(lambda salida: salida.payment_id.debt_collector_code.id == False)

                        subtotal_asistente_ninguno = 0
                        subtotal_cobrador_ninguno = 0
                        lista_pagos_ninguno = []
                        for pago in aux_salidas_sin_cobrador:

                            lista_pagos_ninguno.append({
                                # Datos de detalle
                                'fecha_recibo': fields.Date.to_string(pago.payment_id.date_receipt),
                                'fecha_oficina': fields.Date.to_string(pago.payment_id.payment_date),
                                'contrato': pago.payment_id.contract.name,
                                'recibo': pago.payment_id.ecobro_receipt,
                                'cliente': pago.payment_id.contract.full_name,
                                'importe': pago.payment_id.amount,
                                'comision_cobrador': pago.commission_paid - pago.actual_commission_paid,
                                'comision_asistente': pago.actual_commission_paid,
                                'cargo': pago.job_id.name[0:6]
                            })

                            subtotal_asistente_ninguno = subtotal_asistente_ninguno + pago.actual_commission_paid
                            subtotal_cobrador_ninguno = subtotal_cobrador_ninguno + (pago.commission_paid - pago.actual_commission_paid)
                            #Fin de iteración de pagos sin cobrador


                        if lista_pagos_ninguno:
                            lista_cobradores.append({
                                'cobrador': 'NINGUNO',
                                'subtotal_asistente': subtotal_asistente_ninguno,
                                'subtotal_cobrador': subtotal_cobrador_ninguno,
                                'pagos': lista_pagos_ninguno
                            })

                            # Sumar al acumulado por plan
                            subtotal_plan_asistente = subtotal_plan_asistente + subtotal_asistente_ninguno
                            subtotal_plan_cobrador = subtotal_plan_cobrador + subtotal_cobrador_ninguno

                        ### Segundo: Anexar las salidas de los pagos con cobrador
                        #Obtener los cobradores de las salidas que si tienen cobrador
                        aux_cobradores_unicos = aux_salidas_por_plan.mapped(lambda salida: salida.payment_id.debt_collector_code) #Nota: No incluye los pagos sin cobrador

                        for cobrador in aux_cobradores_unicos:
                            # 3. Filtrar las salidas por cobrador
                            aux_salidas_detalle = aux_salidas_por_plan.filtered(lambda salida: salida.payment_id.debt_collector_code.id == cobrador.id)
                            
                            subtotal_asistente = 0
                            subtotal_cobrador = 0
                            lista_pagos = []
                            for pago in aux_salidas_detalle:
                                # 4. Contratos
                                lista_pagos.append({
                                    # Datos de detalle
                                    'fecha_recibo': fields.Date.to_string(pago.payment_id.date_receipt),
                                    'fecha_oficina': fields.Date.to_string(pago.payment_id.payment_date),
                                    'contrato': pago.payment_id.contract.name,
                                    'recibo': pago.payment_id.ecobro_receipt,
                                    'cliente': pago.payment_id.contract.full_name[0:26],
                                    'importe': pago.payment_id.amount,
                                    'comision_cobrador': pago.commission_paid - pago.actual_commission_paid,
                                    'comision_asistente': pago.actual_commission_paid,
                                    'cargo': pago.job_id.name[0:6]
                                })

                                subtotal_asistente = subtotal_asistente + pago.actual_commission_paid
                                subtotal_cobrador = subtotal_cobrador + (pago.commission_paid - pago.actual_commission_paid)
                                # 4. Fin iteración salida de contratos

                            lista_cobradores.append({
                                'cobrador': cobrador.name,
                                'subtotal_asistente': subtotal_asistente,
                                'subtotal_cobrador': subtotal_cobrador,
                                'pagos': lista_pagos
                            })

                            # Sumar al acumulado por plan
                            subtotal_plan_asistente = subtotal_plan_asistente + subtotal_asistente
                            subtotal_plan_cobrador = subtotal_plan_cobrador + subtotal_cobrador

                            # 3. Fin iteración salidas por cobradores

                        # Buscar el prefijo del plan
                        tarifa = self.env['product.pricelist.item'].search([('product_id','=',plan.id)])

                        lista_planes.append({
                            'asistente_plan': "{} - {} - {}".format(codigo.comission_agent_id.barcode, codigo.comission_agent_id.name, tarifa.prefix_contract),
                            'subtotal_plan_asistente': subtotal_plan_asistente,
                            'subtotal_plan_cobrador': subtotal_plan_cobrador,
                            'cobradores': lista_cobradores
                        })

                        total_codigo = total_codigo + subtotal_plan_asistente
                        # 2. Fin iteración salidas por planes
                    # 1. Fin iteración salidas por código

                lista_codigos.append({
                    'codigo': empleado.barcode,
                    'total_codigo': total_codigo,
                    'planes' : lista_planes
                })
                
                total_comisiones_asistentes = total_comisiones_asistentes + total_codigo
                # Fin iteración codigos unicos

            lista_oficinas.append({
                'nombre_oficina': ofi.name,
                'codigos': lista_codigos
            })
            #Fin iteración oficinas

        #raise ValidationError("{}".format(lista_oficinas))

        # Variables a enviar al reporte
        return {
            "fecha_inicio": fecha_inicial,
            "fecha_final": fecha_final,
            "oficinas": lista_oficinas,
            "total_asistentes": total_comisiones_asistentes
        }
        # raise ValidationError("{}".format(lista_pagos))