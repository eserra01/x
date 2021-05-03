from datetime import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import ValidationError

class ReportWizardINGEGR(models.TransientModel):
    _name = 'report.pabs.ing.egre'

    date_from = fields.Date(
        string='De',
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
        #print("cccccc")
        return self.env.ref('xmarts_funeraria.id_payroll_ing_egre').report_action(self, data=data)


class ReportAttendanceRecapINGEGRE(models.AbstractModel):

    _name = "report.xmarts_funeraria.payroll_ing_egre"

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']

### INGRESOS

        # [
        #     {
        #         'codigo_cobrador': 'C0001',
        #         'cobrador': 'Andres Andrade',
        #         'ingresos': 1500
        #     },
        #     {
        #         'codigo_cobrador': 'C0002',
        #         'cobrador': 'Bernardo Benitez',
        #         'cantidad_ingresos': 3000
        #     },
        # ]

        #Consultar todos los pagos realizados entre dos fechas con estatus válido
        pagos = self.env['account.payment'].search([
            ('payment_date', '>=', date_start), ('payment_date', '<=', date_end), 
            ('state', 'in', ['posted','sent','reconciled']), 
            ('reference','in',['payment', 'surplus'])
        ]).filtered(lambda r: r.contract.company_id.id == self.env.user.company_id.id)

        ingresos_lista_cobradores = []
        ingresos_sin_clasificar = []
        total_ingresos = 0

    ### INGRESOS SIN CLASIFICAR (Pagos sin cobrador)
        #Obtener los excedentes y los pagos que no tengan cobrador
        pagos_sin_cobrador = pagos.filtered_domain([('debt_collector_code','=',False)])

        cantidad_surplus = 0
        cantidad_payment = 0
        for pago in pagos_sin_cobrador:
            #Calcular pago por excedente
            if pago.reference == 'surplus':
                cantidad_surplus = cantidad_surplus + pago.amount
            #Calcular pagos normales
            elif pago.reference == 'payment':
                cantidad_payment = cantidad_payment + pago.amount

        if cantidad_surplus > 0:
            total_ingresos = total_ingresos + cantidad_surplus

            ingresos_sin_clasificar.append({
                'codigo_cobrador':'',
                'cobrador':'COBRANZA EXD. INV.',
                'cantidad_ingresos': cantidad_surplus
            })

        if cantidad_payment > 0:
            total_ingresos = total_ingresos + cantidad_payment

            ingresos_sin_clasificar.append({
                'codigo_cobrador':'',
                'cobrador':'SIN COBRADOR',
                'cantidad_ingresos': cantidad_payment
            })

    ### INGRESOS CLASIFICADOS (Pagos con cobrador)
        #Obtener el cobrador único todos los pagos y ordenar por nombre
        cobradores = pagos.mapped(lambda pago: pago.debt_collector_code) #Nota: no envia el cobrador Null
        cobradores = cobradores.sorted(key=lambda cob: cob.name)

        for cobrador in cobradores:
            #Filtrar los pagos, dejar solo los de los empleados en turno
            pagos_cobrador = pagos.filtered_domain([('debt_collector_code','=',cobrador.id), ('reference','=','payment')])

            cantidad_cobrador = 0
            for pago in pagos_cobrador:
                cantidad_cobrador = cantidad_cobrador + pago.amount

            total_ingresos = total_ingresos + cantidad_cobrador

            ingresos_lista_cobradores.append({
                'codigo_cobrador': cobrador.barcode,
                'cobrador': cobrador.name,
                'cantidad_ingresos': cantidad_cobrador
            })

        #raise ValidationError("{}".format(ingresos_lista_cobradores))

### EGRESOS
        # [
        #     {
        #         'codigo_comisionista': 'P0001',
        #         'cargos': 
        #         [
        #             {
        #                 'nombre_comisionista': 'Maria Morales (Asistente)',
        #                 'cantidad_egresos': 500
        #             },
        #             {
        #                 'nombre_comisionista': 'Maria Morales (Coordinador)',
        #                 'cantidad_egresos': 1000
        #             },
        #         ]
        #     },
        #     { 'codigo_comisionista': 'P0002', ...}
        # ]

        egresos_lista_comisionistas = []
        egresos_sin_clasificar = {} #SOLO FIDEICOMISO
        total_egresos = 0

        #Consultar id de cargo papeleria
        cargo_papeleria = self.env['hr.job'].search([('name','=','PAPELERIA')])

        #Consultar las salidas entre dos fechas
        salidas = self.env['pabs.comission.output'].search([
            ('payment_date', '>=', date_start), 
            ('payment_date', '<=', date_end),
            ('payment_status', 'in', ['posted','sent','reconciled']),
            ('actual_commission_paid', '>', 0),
            ('job_id', 'not in', [cargo_papeleria.id])
            ]
        )

        # Validar que todas las salidas tengan un empleado que comisiona
        lista_salidas_error = ""
        for pago in salidas:
            if not pago.comission_agent_id:
                lista_salidas_error = "No se tiene un empleado asignado a la salida de comisiones en el recibo {}\n".format(pago.ecobro_receipt)

        if lista_salidas_error != "":
            raise ValidationError(lista_salidas_error)

        ### EGRESOS SIN CLASIFICAR (Fideicomiso)
        #Filtrar las salidas por cargo de fideicomiso
        cargo_fideicomiso = self.env['hr.job'].search([('name','=','FIDEICOMISO')])

        salidas_fideicomiso = salidas.filtered_domain([('job_id','=',cargo_fideicomiso.id)])

        total_fideicomiso = 0
        for salida in salidas_fideicomiso:
            total_fideicomiso = total_fideicomiso + salida.actual_commission_paid

        total_egresos = total_egresos + total_fideicomiso
        egresos_sin_clasificar.update({'codigo_comisionista': '', 'nombre_comisionista': 'FIDEICOMISO', 'cantidad_egresos':total_fideicomiso} )

        ### EGRESOS CLASIFICADOS
        #Quitar el cargo de fideicomiso al recordset de salidas
        salidas_comisionistas = salidas.filtered_domain([('job_id', '!=', cargo_fideicomiso.id)])

        #Obtener el comisionista único de todas las salidas y ordenar por codigo
        codigos_unicos = salidas_comisionistas.mapped(lambda salida: salida.comission_agent_id)
        codigos_unicos = codigos_unicos.sorted(key=lambda salida: salida.barcode)

        for emp in codigos_unicos:

            # Filtrar las salidas por código de empleado
            salidas_por_codigo = salidas_comisionistas.filtered_domain([('comission_agent_id','=',emp.id)])

            #Obtener los cargos únicos para todas las salidas del empleado
            cargos_de_salidas = salidas_por_codigo.mapped(lambda salida: salida.job_id)

            registro_empleado = {}
            registro_empleado.update({'codigo_comisionista': emp.barcode})

            cargos = []
            for cargo in cargos_de_salidas:
                #Filtrar las salidas por cargo
                salidas_por_cargo = salidas_por_codigo.filtered_domain([('job_id','=',cargo.id)])
                
                nombre_comisionista = "{} - ({})".format(emp.name, cargo.name)
                total_cargo = 0
                for salida in salidas_por_cargo:
                    total_cargo = total_cargo + salida.actual_commission_paid

                cargos.append({'nombre_comisionista': nombre_comisionista, 'cantidad_egresos':total_cargo})
                total_egresos = total_egresos + total_cargo
                #Fin de iteración por cargos de un empleado

            registro_empleado.update({'cargos': cargos})
            egresos_lista_comisionistas.append(registro_empleado)
            #Fin de iteración por códigos

        #raise ValidationError("{}".format(egresos_lista_comisionistas))

        ### ENVIAR DATOS ###
        return {
            'fecha_inicio':     date_start,
            'fecha_final':      date_end,
            'lista_ingresos_sin_clasificar':   ingresos_sin_clasificar,
            'lista_ingresos':   ingresos_lista_cobradores,
            'total_ingresos':   total_ingresos,
            'lista_egresos':    egresos_lista_comisionistas,
            'egresos_fideicomiso': egresos_sin_clasificar,
            'total_egresos':    total_egresos
        }