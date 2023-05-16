from datetime import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import ValidationError

class CarnetPagoWizard(models.TransientModel):
    _name = 'report.carnet.pago'

    initial_contract = fields.Many2one(comodel_name="pabs.contract", domain="([('state','=','contract')])", string="Contrato inicial")
    final_contract = fields.Many2one(comodel_name="pabs.contract", domain="([('state','=','contract')])", string="Contrato final")

    def filter(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'initial_contract': self.initial_contract.name,
                'final_contract': self.final_contract.name,
            },
        }

        return self.env.ref('xmarts_funeraria.rpt_carnet_pago_sin_tabla_rango').report_action(self, data=data)

#<!-- <div style="page-break-before: always;"></div> -->

class ReportCarnetPagoRango(models.AbstractModel):
    _name = "report.xmarts_funeraria.carnet_pago_por_rango"

    @api.model
    def _get_report_values(self, docids, data=None):
        #Obtener datos de la ventana
        initial_contract = data['form']['initial_contract']
        final_contract = data['form']['final_contract']

        #Si se seleccionaron los contratos
        if initial_contract and final_contract:
            contract_ids = self.env['pabs.contract'].search([
                ('state','=','contract'),
                ('name','>=',initial_contract),
                ('name','<=',final_contract)], 
                    order="name"
            )
        else:
            raise ValidationError("Elige el contrato inicial y el contrato final")

        #Obtener campos de compañia
        compañia = self.env.company
        if not compañia:
            raise ValidationError("No se tiene asignada una compañia")
        if len(compañia) > 1:
            raise ValidationError("Se tiene asignada mas de una compañia")

        nombre_compañia = compañia.name
        telefonos_compañia = compañia.service_phone

        contracts_list = []
        
        for con in contract_ids:

            ### Obtener ultimo abono (dependiendo el tipo de recibo se mostrarán distintos datos)
            last_payment = self.env['account.payment'].search([
                ('contract','=',con.id),
                ('state', 'in', ('posted', 'sent', 'reconciled'))
            ], limit=1, order="payment_date desc")

            fecha_recibo = ""
            if last_payment.reference in ('stationary', 'surplus'):
                fecha_recibo = fields.Date.to_string(con.invoice_date)
            else:
                fecha_recibo = fields.Date.to_string(last_payment.date_receipt)
            
            recibo = ""
            if last_payment.reference in ('stationary', 'surplus'):
                recibo = "Inv. Inicial"
            else:
                if last_payment.ecobro_receipt:
                    recibo = last_payment.ecobro_receipt
                else:
                    recibo = dict(last_payment._fields['reference'].selection).get(last_payment.reference)

            monto = 0
            if last_payment.reference in ('stationary', 'surplus'):
                monto = con.initial_investment
            else:
                monto = last_payment.amount
            
            cobrador = ""
            if last_payment.debt_collector_code:
                cobrador = last_payment.debt_collector_code.name
            else:
                cobrador = ""

            cobrador_contrato = ""
            if con.debt_collector:
                cobrador_contrato = con.debt_collector.name
            else:
                cobrador_contrato = ""

            contracts_list.append({
                "contrato": con.name,
                "solicitud": con.lot_id.name,
                "forma_de_pago": dict(con._fields['way_to_payment'].selection).get(con.way_to_payment),
                "monto_de_pago": con.payment_amount,
                "titular": con.full_name,
                "telefono_cobro": con.phone_toll,
                "calle_cobro": con.street_name_toll,
                "numero_cobro": con.street_number_toll,
                "colonia_cobro": con.toll_colony_id.name,
                "entrecalles_cobro": con.between_streets_toll,
                "fecha_recibo": fecha_recibo,
                "recibo": recibo,
                "monto": monto,
                "cobrador": cobrador,
                "saldo": con.balance,
                "asistente": con.employee_id.name,
                "cobrador_contrato": cobrador_contrato,
                "company_id": self.env.company.id,
                "activation_code": con.activation_code
            })
        
        # #Retornar información
        # info = [{
        #     'docs': contracts_list
        # }]

        #raise ValidationError("{}".format(info))

        return {
            "docs": contracts_list,
            "compañia": nombre_compañia,
            "telefonos_compañia": telefonos_compañia
        }
