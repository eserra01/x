from datetime import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import ValidationError

class ReportWizardComisionesPorRecuperar(models.TransientModel):
    _name = 'report.pabs.comisiones.por.recuperar'

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
        
        return self.env.ref('xmarts_funeraria.id_comisiones_por_recuperar').report_action(self, data=data)


class ReportComisionesPorRecuperar(models.AbstractModel):
    _name = "report.xmarts_funeraria.comisiones_por_recuperar"

    @api.model
    def _get_report_values(self, docids, data=None):
        
        # [
        #     {
        #         'codigo_asistente': 'P0001',
        #         'asistente': 'MARIA MORALES',
        #         'estatus_contratos': [
        #             {
        #                 'estatus': 'ACTIVO',
        #                 'total_por_pagar': 1200
        #                 'contratos':[
        #                     {
        #                         'fecha_contrato': '2021-01-01',
        #                         'contrato': '1CJ000001',
        #                         'cliente': 'ANA ARAMBULA',
        #                         'colonia': 'LA SABANA',
        #                         'localidad': 'ACAPULCO',
        #                         'telefono': '3331234567',
        #                         'cobrador': 'ROGELIO RODRIGUEZ',
        #                         'comision_correspondiente': 900,
        #                         'comision_pagada': 600,
        #                         'comision_por_pagar': 300,
        #                         'motivo': 'Activo',
        #                         'cargo': 'ASISTENTE SOCIAL'
        #                     },
        #                     {
        #                         'fecha_contrato' : '...'
        #                     }
        #                 ]
        #             },
        #             {
        #                 'estatus': 'SUSPENSION PARA CANCELAR',
        #                 'total_por_pagar': 3000',
        #                 'contratos':[
        #                     {
        #                         'fecha_contrato': '2021-01-01',
        #                         'contrato': '1CJ000001',
        #                         'cliente': 'ANA ARAMBULA',
        #                         'colonia': 'LA SABANA',
        #                         'localidad': 'ACAPULCO',
        #                         'telefono': '3331234567',
        #                         'cobrador': 'ROGELIO RODRIGUEZ',
        #                         'comision_correspondiente': 900,
        #                         'comision_pagada': 0,
        #                         'comision_por_pagar': 900,
        #                         'motivo': 'NO ABONA',
        #                         'cargo': 'COORDINADOR'
        #                     },
        #                     {
        #                         'fecha_contrato' : '...'
        #                     }
        #                 ]
        #             },
        #             {   'estatus': '...'}
        #         ]
        #     },
        #     {   'codigo_asistente' : '...'}
        # ]

        # Agregar validacion de fechas
        fecha_inicial = data['form']['date_start']
        fecha_final = data['form']['date_end']

        #Si se seleccionaron fechas
        if not fecha_inicial or not fecha_final:
            raise ValidationError("Elige las fechas")        

        #Consultar los contratos entre dos fechas
        contratos = self.env['pabs.contract'].search([
            ('invoice_date', '>=', fecha_inicial),
            ('invoice_date', '<=', fecha_final)
        ])

        #Obtener los asistentes únicos de todos los contratos y ordenar por nombre
        asistentes = contratos.mapped(lambda con: con.sale_employee_id)
        asistentes = asistentes.sorted(key = lambda asi: asi.name)

        lista_asistentes = []

        for asi in asistentes:
            detalle_asistente = {}
            detalle_asistente.update({'codigo_asistente': asi.barcode, 'asistente': asi.name})

            #Filtrar los contratos por código de asistente
            contratos_asistente = contratos.filtered_domain([('sale_employee_id', '=', asi.id)])

            #Obtener los estátus únicos de cada contrato y ordenar por nombre
            estatus_contratos = contratos_asistente.mapped(lambda con: con.contract_status_item)
            estatus_contratos = estatus_contratos.sorted(key = lambda est: est.status)

            lista_estatus = []
            for est in estatus_contratos:
                detalle_estatus = {}
                detalle_estatus.update({'estatus': est.status})

                #Filtrar los contratos por estatus y ordenar por numero de contrato
                contratos_por_estatus = contratos_asistente.filtered_domain([('contract_status_item','=', est.id)])
                contratos_por_estatus = contratos_por_estatus.sorted(key=lambda con: con.name)

                total_por_pagar = 0
                lista_contratos = []
                for con in contratos_por_estatus:
                    #Obtener la linea del arbol de comisiones del empleado
                    comisiones = con.commission_tree.filtered_domain([('comission_agent_id', '=', asi.id)])

                    for comision in comisiones:
                        lista_contratos.append({
                            'fecha_contrato': fields.Date.to_string(con.invoice_date),
                            'contrato': con.name,
                            'cliente': con.full_name,
                            'colonia': con.neighborhood_id.name,
                            'localidad': con.municipality_id.name,
                            'telefono': con.phone,
                            'cobrador': con.debt_collector.name,
                            'comision_correspondiente': comision.corresponding_commission,
                            'comision_pagada': comision.commission_paid,
                            'comision_por_pagar': comision.remaining_commission,
                            'motivo': con.contract_status_reason.reason,
                            'cargo': comision.job_id.name
                        })

                        total_por_pagar = total_por_pagar + comision.remaining_commission
                        #Fin de iteración de comisiones
                    #Fin de iteración de contratos

                detalle_estatus.update({'total_por_pagar': total_por_pagar, 'contratos': lista_contratos})
                lista_estatus.append(detalle_estatus)

                #Fin de iteración de estatus
                
            detalle_asistente.update({'estatus_contratos': lista_estatus})
            lista_asistentes.append(detalle_asistente)
            # Fin de iteración de asistentes

        #raise ValidationError("{}".format(lista_asistentes))

        return{
            'fecha_inicio': fecha_inicial,
            'fecha_final': fecha_final,
            'lista_asistentes': lista_asistentes
        }