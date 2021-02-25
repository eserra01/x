from datetime import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import ValidationError

class ReportWizardHistorialVentas(models.TransientModel):
    _name = 'report.pabs.historial.ventas'

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
        
        return self.env.ref('xmarts_funeraria.id_historial_ventas').report_action(self, data=data)


class ReportHistorialVentas(models.AbstractModel):
    _name = "report.xmarts_funeraria.historial_ventas"

    @api.model
    def _get_report_values(self, docids, data=None):
        
        # [
        #     {
        #     'empleado': 'P0062 - EVENICE MENDOZA TADEO ',
        #     'total': 2,
        #     'ACTIVO': 0,
        #     'SUSP. PARA CANCELAR': 1,
        #     'SUSP. TEMPORAL': 1,
        #     },
        #     {
        #         'empleado': 'P0127 - HECTOR SERRANO ISABEL ',
        #         'total': 2,
        #         'ACTIVO': 1,
        #         'SUSP. PARA CANCELAR': 1,
        #         'SUSP. TEMPORAL': 0,
        #         },
        #     {
        #         'empleado': 'P0015 - HOGUER BERDEJA CARBAJAL ',
        #         'total': 3,
        #         'ACTIVO': 3,
        #         'SUSP. PARA CANCELAR': 0,
        #         'SUSP. TEMPORAL': 0,
        #     }
        # ]
    
    ### OBTENER CONTRATOS ###
        # Obtener fechas elegidas en el formulario
        fecha_inicial = data['form']['date_start']
        fecha_final = data['form']['date_end']

        if not fecha_inicial or not fecha_final:
            raise ValidationError("Elige las fechas")

        #Obtener contratos elaborados entre las fechas elegidas
        contratos = self.env['pabs.contract'].search([('state','=','contract'), ('invoice_date', '>=', fecha_inicial), ('invoice_date', '<=', fecha_final)])

        #Obtener los estatus únicos de los contratos y ordenar por nombre
        lista_estatus = contratos.mapped('contract_status_item') #Nota: no incluye el empleado Null
        lista_estatus = lista_estatus.sorted(key=lambda est: est.status)

        #Obtener los empleados únicos de los contratos y ordenar por nombre
        lista_empleados = contratos.mapped(lambda emp: emp.sale_employee_id)
        lista_empleados = lista_empleados.sorted(key=lambda emp: emp.name)

        #Construir la lista con nombres de estatus
        nombre_estatus = []
        for est in lista_estatus: 
            nombre_estatus.append(est.status)
    
    ### CONSTRUIR FILA DE CONTRATOS CON EMPLEADO ASIGNADO ###
        lista_totales_empleado = []

        for emp in lista_empleados:
            #Filtrar los contratos, dejar solo los del empleado en turno
            contratos_empleado = contratos.filtered_domain([('sale_employee_id','=',emp.id)])
            
            detalle_empleado = {}
            #Obtener el nombre del empleado y el total de contratos
            nombre = "{} - {}".format(emp.barcode, emp.name)
            detalle_empleado.update({'empleado': nombre, 'total':len(contratos_empleado)})
        
            #Calcular la cantidad de contratos por estatus
            for est in lista_estatus:
                contratos_por_estatus = contratos_empleado.filtered_domain([('sale_employee_id','=',emp.id),('contract_status_item','=',est.id)])
                detalle_empleado.update({ est.status: len(contratos_por_estatus)})
            
            #Agregar datos a la lista_totales_empleado
            lista_totales_empleado.append(detalle_empleado)

    ### CONSTRUIR FILA DE CONTRATOS SIN EMPLEADO ASIGNADO ###
        ### Filtrar los contratos, dejar los que no tienen empleado asignado
        contratos_ninguno = contratos.filtered_domain([('sale_employee_id', '=', False)])
        if contratos_ninguno:
            detalle_empleado = {}
            detalle_empleado.update({'empleado': 'NINGUNO', 'total': len(contratos_ninguno)})

            #Calcular la cantidad de contratos por estatus
            for est in lista_estatus:
                contratos_por_estatus = contratos_ninguno.filtered_domain([('sale_employee_id', '=', False),('contract_status_item', '=', est.id)])
                detalle_empleado.update({est.status: len(contratos_por_estatus)})

            lista_totales_empleado.append(detalle_empleado)
    
    ### CONSTRUIR FILA DE TOTALES ###
        totales_por_estatus = {}
        totales_por_estatus.update({'empleado':'Todos', 'total': len(contratos)})

        #Calcular la cantidad de contratos por estatus
        for est in lista_estatus:
            contratos_por_estatus = contratos.filtered_domain([('contract_status_item','=',est.id)])
            totales_por_estatus.update({est.status: len(contratos_por_estatus)})

    ### ENVIAR DATOS ###
        return {
            'fecha_inicio':     fecha_inicial,
            'fecha_final':      fecha_final,
            'lista_estatus':    nombre_estatus,
            'lista_empleados':  lista_totales_empleado,
            'total_por_estatus': totales_por_estatus
        }
        
        #raise ValidationError("{}".format(lista_totales_empleado))
