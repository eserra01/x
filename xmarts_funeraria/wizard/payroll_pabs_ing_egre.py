from datetime import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

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

        #Consultar todos los pagos realizados entre dos fechas
        payment = self.env['account.payment'].search([
                    ('payment_date', '>=', date_start),
                    ('payment_date', '<=', date_end),
                ])

        docs = [] #Lista de registro de ingresos
        docse = [] #Lista de registro de egresos
        exend = 0 #Total de ingresos por excedente
        amount_total = 0 #Total de ingresos
        exend_e = 0 #Total de egresos por fideicomiso
        amount_total_e = 0 #Total de egresos
        comisi = [] #Lista de id de comisionistas
        do = [] #Lista de información del comisionista

        if payment:
            c = []
        ### INGRESOS
            for p in payment:
                #Si el pago es de tipo Excedente sumar el monto a la variable de Total de ingresos por excedente y a la variable de Total de ingresos
                if p.reference == 'surplus':
                    exend += p.amount
                    amount_total += p.amount

                #Si el pago pertenece a un cobrador (que tenga código) añadirlo a una lista
                if p.debt_collector_code:
                    c.append(p.debt_collector_code.id)

            cobrador = set(c)
            if cobrador:
                #Iterar en la lista de cobradores
                for c in cobrador:
                    #Consultar los pagos de un cobrador
                    cobra = self.env['account.payment'].search([('payment_date', '>=', date_start),('payment_date', '<=', date_end),('debt_collector_code', '=', c)])                   
                    
                    amount = 0
                    if cobra:
                        #Iterar en cada pago
                        for co in cobra:
                            #Si el pago es de tipo Abono sumar el monto a la variable de Total del cobrador y a la variable de Total de ingresos
                            if co.reference == 'payment':
                                amount_total += co.amount
                                amount += co.amount
                            print("----cobra--------",amount,"-----cobra-----",co.amount,"--------------",co.debt_collector_code.name,"--------------",co.name)
                    
                    #Consultar los datos del cobrador
                    cobrador = self.env['account.payment'].search([('payment_date', '>=', date_start),('payment_date', '<=', date_end),('debt_collector_code', '=', c)],limit=1)                   

                    print("------------",amount,"----------",cobrador.name)
                    for pay in cobrador:
                        if pay.reference == 'payment':
                            #Agregar el código, nombre y monto del primer recibo del cobrador a una lista
                            docs.append({
                                'Ecobro_receipt': pay.debt_collector_code.barcode,
                                'debt_collector_code': pay.debt_collector_code.name,
                                'amount': amount,
                            })
        ### EGRESOS
            #Iterar en las salidas de comisiones de cada pago
            for com in payment.comission_output_ids:
                if com.actual_commission_paid > 0:
                    #Si la salida le corresponde a Fideicomiso sumar el monto a la variable Total de egresos por fideicomiso y a la variable Total de egresos
                    if com.job_id.name == 'FIDEICOMISO':
                        exend_e += com.actual_commission_paid
                        amount_total_e += com.actual_commission_paid

                    if com.job_id.name != 'FIDEICOMISO':
                        #Ingresar el id del comisionista a una lista
                        comisi.append(com.comission_agent_id.id)

                        #Agregar el código, nombre y comisión real pagada del comisionista a una lista
                        do.append({
                            'Ecobro_receipt': com.comission_agent_id.barcode,
                            'debt_collector_code': com.comission_agent_id.name,
                            'amount': com.actual_commission_paid,
                        })
     
            comision = set(comisi)
            if comision:
                #Iterar en la lista de ids de comisionistas
                for c in comision:
                    
                    #Consultar todas las salidas de comisión generadas para el empleado
                    comm = self.env['pabs.comission.output'].search([('create_date', '>=', date_start),('create_date', '<=', date_end),('comission_agent_id', '=', c),('actual_commission_paid','>', 0)],limit=1)                   
                    
                    #Iterar en cada salida de comisión
                    for cc in comm:
                        if cc.job_id.name != 'FIDEICOMISO':
                            amount = 0

                            #Iterar en cada comisionista de la lista y sumar el monto a la variable Total de egresos del comisionista y la variable Total de egresos
                            for comis in do:
                                if comis["Ecobro_receipt"] == cc.comission_agent_id.barcode:
                                    amount_total_e += float(comis["amount"])
                                    amount += float(comis["amount"])

                            #Ingresar los datos del comisionista a la lista de Egresos
                            docse.append({
                                'Ecobro_receipt': cc.comission_agent_id.barcode,
                                'debt_collector_code': cc.comission_agent_id.name,
                                'amount': amount,})

        #Retornar datos
        return {
            'amount_total': amount_total,       #Total de ingresos
            'amount_total_e': amount_total_e,   #Total de egresos
            'exend': exend,                     #Total de ingresos por Excedente de inversión inicial
            'exend_e': exend_e,                 #Total de egresos por Excedente de inversión inicial???
            'date_start': date_start,           #Fecha inicial
            'date_end': date_end,               #Fecha final
            'docs': docs,                       #Registros de ingreso
            'docse': docse,                     #Registros de egreso
        }