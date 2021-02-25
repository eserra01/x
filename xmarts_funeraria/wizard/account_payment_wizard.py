from datetime import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

class ReportWizard(models.TransientModel):
    _name = 'report.pabs'

    date_from = fields.Date(
        string='De',
        required=True,
    )
    date_to = fields.Date(
        string='Hasta',
        required=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Cobrador',
    )


    def filter(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.date_from,
                'date_end': self.date_to,
                'employee': self.employee_id.id,
                'employee_name': self.employee_id.name,
            },
        }
        return self.env.ref('xmarts_funeraria.id_collectors').report_action(self, data=data)


class ReportAttendanceRecap(models.AbstractModel):

    _name = "report.xmarts_funeraria.collectors"

    @api.model
    def _get_report_values(self, docids, data=None):
        
        #Obtener datos de la ventana
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        employee = data['form']['employee']
        employee_name = data['form']['employee_name']

        #Si se seleccionó un cobrador
        if employee:
            #Consultar los pagos del cobrador entre dos fechas
            payment = self.env['account.payment'].search([
                    ('debt_collector_code', '=', employee),
                    ('payment_date', '>=', date_start),
                    ('payment_date', '<=', date_end),
                ])

            total_amount = 0 #Total cobrado por el cobrador
            total_item = 0 #Número de recibos cobrados por el cobrador

            docs = [] #Listado de recibos del cobrador

            #Ingresar cada recibo a la lista
            for pay in payment:
                total_amount += pay.amount
                total_item += 1
                docs.append({
                    'date_receipt': pay.date_receipt,
                    'payment_date': pay.payment_date,
                    'contract': pay.contract.name,
                    'Ecobro_receipt': pay.Ecobro_receipt,
                    'partner': pay.contract.full_name,
                    'amount': pay.amount,
                })

            #Retornar información con totales
            reg = [{'report': 1,
                    'collectors': employee_name,
                    'date_start': date_start,
                    'date_end': date_end,
                    'total_amount': total_amount,
                    'total_item': total_item,
                    'docs': docs,}]
            return {
                'reg': reg,
            }
        else: #Todos los cobradores

            #Consultar todos los pagos entre dos fechas
            payment = self.env['account.payment'].search([
                    ('payment_date', '>=', date_start),
                    ('payment_date', '<=', date_end),
                ])
            
            if payment:
                reg = []
                combr = []
                #Por cada pago
                for p in payment:
                    if p.debt_collector_code.name:

                        #Asignar el nombre del cobrador a una lista
                        if not p.debt_collector_code.name in combr:
                            combr.append(p.debt_collector_code.name)

                            #Consultar los recibos del cobrador
                            pp = self.env['account.payment'].search([
                                    ('debt_collector_code', '=', p.debt_collector_code.name),
                                    ('payment_date', '>=', date_start),
                                    ('payment_date', '<=', date_end),
                                ])

                            docs = [] #Listado de recibos del cobrador
                            total_amount = 0 #Total cobrado por el cobrador
                            total_item = 0 #Número de recibos cobrados por el cobrador
                            
                            #Ingresar cada recibo a la lista
                            for pay in pp:
                                total_amount += pay.amount
                                total_item += 1
                                docs.append({
                                    'date_receipt': pay.date_receipt,
                                    'payment_date': pay.payment_date,
                                    'contract': pay.contract.name,
                                    'Ecobro_receipt': pay.Ecobro_receipt,
                                    'partner': pay.contract.full_name,
                                    'amount': pay.amount,
                                })

                            #Ingresar información con totales a la lista de documentos del reporte
                            reg.append({'report': 2,
                                    'collectors': p.debt_collector_code.name,
                                    'date_start': date_start,
                                    'date_end': date_end,
                                    'total_amount': total_amount,
                                    'total_item': total_item,
                                    'docs': docs,})

                #Retornar todos los documentos
                return {
                    'reg': reg,
                }