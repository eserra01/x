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
        # 1. Codigo del empleado
            # 2. Plan
                # 3. Cobrador que recuperó el abono
                    # 4. Contratos
                # 3z Total cobrador
            # 2z Total plan
        # 1z Total código empleado

        # [
        # {'codigo': 'P0024', 'total_codigo': 200.0, 
        #    'planes': [{
        #     'asistente_plan': 'P0024 - ESTELA MORALES RENDON  - 1CJ',
        #     'subtotal_plan_asistente': 200.0,
        #     'subtotal_plan_cobrador': 0.0,
        #     'cobradores': [{
        #         'cobrador': 'NINGUNO',
        #         'subtotal_asistente': 200.0,
        #         'subtotal_cobrador': 0.0,
        #         'pagos': [{
        #             'fecha_recibo': False,
        #             'fecha_oficina': '2021-02-15',
        #             'contrato': '1CJ005115',
        #             'recibo': False,
        #             'cliente': 'LIZBETH CISNEROS GARCIA',
        #             'importe': 100.0,
        #             'comision_asistente': 100.0,
        #             'comision_cobrador': 0.0,
        #             }, {
        #             'fecha_recibo': False,
        #             'fecha_oficina': '2021-02-15',
        #             'contrato': '1CJ005119',
        #             'recibo': False,
        #             'cliente': 'JAVIER HECTOR BRITO MARTINEZ',
        #             'importe': 900.0,
        #             'comision_asistente': 100.0,
        #             'comision_cobrador': 0.0,
        #             }],
        #         }],
        #     }]},
        # {'codigo': 'P0055', 'total_codigo': 900.0, 
        #   'planes': [{
        #     'asistente_plan': 'P0055 - REINA JIMENEZ CARMONA  - 1CJ',
        #     'subtotal_plan_asistente': 900.0,
        #     'subtotal_plan_cobrador': 0.0,
        #     'cobradores': [{
        #         'cobrador': 'NINGUNO',
        #         'subtotal_asistente': 900.0,
        #         'subtotal_cobrador': 0.0,
        #         'pagos': [{
        #             'fecha_recibo': False,
        #             'fecha_oficina': '2021-02-15',
        #             'contrato': '1CJ005119',
        #             'recibo': False,
        #             'cliente': 'JAVIER HECTOR BRITO MARTINEZ',
        #             'importe': 900.0,
        #             'comision_asistente': 800.0,
        #             'comision_cobrador': 0.0,
        #             }, {
        #             'fecha_recibo': False,
        #             'fecha_oficina': '2021-02-15',
        #             'contrato': '1CJ005126',
        #             'recibo': False,
        #             'cliente': 'ACACIA MENDOZA SALADO',
        #             'importe': 100.0,
        #             'comision_asistente': 100.0,
        #             'comision_cobrador': 0.0,
        #             }],
        #         }],
        #     }]},

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

        #Ordenar por nombre
        salidas = salidas.sorted(key=lambda salida: salida.comission_agent_id.name)

        # Validar que todas las salidas tengan un empleado que comisiona
        lista_salidas_error = ""
        for pago in salidas:
            if not pago.comission_agent_id:
                lista_salidas_error = "No se tiene un empleado asignado a la salida de comisiones en el recibo {}\n".format(pago.Ecobro_receipt)

        if lista_salidas_error != "":
            raise ValidationError(lista_salidas_error)
        
        # Recordset de códigos únicos de todas las salidas
        aux_codigos_unicos = []
        aux_codigos_unicos = salidas.mapped(lambda salida: salida.comission_agent_id)   
        
        lista_codigos = [] # Lista que se enviará al reporte 
        for empleado in aux_codigos_unicos:

            # 1. Filtrar las salidas por código de empleado
            aux_salidas_por_empleado = salidas.filtered(lambda salida: salida.comission_agent_id.barcode == empleado.barcode)

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

                    #Obtener los cobradores de las salidas
                    aux_cobradores_unicos = aux_salidas_por_plan.mapped(lambda salida: salida.payment_id.debt_collector_code.name or "NINGUNO")

                    #Quitar duplicados de la lista de cobradores
                    aux_cobradores_unicos = list(set(aux_cobradores_unicos))

                    for cobrador in aux_cobradores_unicos:
                        # 3. Filtrar las salidas por cobrador
                        aux_salidas_detalle = aux_salidas_por_plan.filtered(lambda salida: salida.payment_id.debt_collector_code.name == cobrador if salida.payment_id.debt_collector_code else True) #'NINGUNO' == 'NINGUNO')
                        
                        subtotal_asistente = 0
                        subtotal_cobrador = 0
                        lista_pagos = []
                        for pago in aux_salidas_detalle:
                            # 4. Contratos
                            subtotal_asistente = subtotal_asistente + pago.commission_paid
                            subtotal_cobrador = subtotal_cobrador + (pago.commission_paid - pago.actual_commission_paid)

                            lista_pagos.append({
                                # Datos de detalle
                                'fecha_recibo': fields.Date.to_string(pago.payment_id.date_receipt),
                                'fecha_oficina': fields.Date.to_string(pago.payment_id.payment_date),
                                'contrato': pago.payment_id.contract.name,
                                'recibo': pago.payment_id.Ecobro_receipt,
                                'cliente': pago.payment_id.contract.full_name,
                                'importe': pago.payment_id.amount,
                                'comision_cobrador': pago.commission_paid - pago.actual_commission_paid,
                                'comision_asistente': pago.actual_commission_paid
                            })
                            # 4. Fin iteración salida de contratos

                        lista_cobradores.append({
                            'cobrador':cobrador,
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
            # Fin iteración codigos unicos

        # Variables a enviar al reporte
        return {
            "fecha_inicio": fecha_inicial,
            "fecha_final": fecha_final,
            "codigos": lista_codigos
        }

        # raise ValidationError("{}".format(lista_pagos))