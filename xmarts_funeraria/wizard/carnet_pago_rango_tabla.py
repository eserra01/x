from datetime import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import ValidationError

class CarnetPagoWizard(models.TransientModel):
    _name = 'report.carnet.pago.tabla'

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

        return self.env.ref('xmarts_funeraria.id_carnet_pago').report_action(self, data=data)

#<!-- <div style="page-break-before: always;"></div> -->

class ReportCarnetPagoRango(models.AbstractModel):
    _name = "report.xmarts_funeraria.carnet_pago"

    @api.model
    def _get_report_values(self, docids, data=None):
        if docids:
            return {
             "docs" : self.env['pabs.contract'].browse(docids)
            }
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

        contracts_list = []
        #Ingresar cada contrato a la lista
        for con in contract_ids:
            #Obtener dato del ultimo abono
            last_payment = self.env['account.payment'].search([('contract','=',con.id),('state','in',('posted','reconciled'))], limit=1, order="id desc")

            fecha_recibo = ""
            if last_payment.date_receipt:
                fecha_recibo = fields.Date.to_string(last_payment.date_receipt)
            else:
                fecha_recibo = fields.Date.to_string(last_payment.payment_date)
            
            if last_payment.ecobro_receipt:
                recibo = last_payment.ecobro_receipt
            else:
                recibo = ""

            if last_payment.amount:
                monto = last_payment.amount
            else:
                monto = 0
            
            if last_payment.debt_collector_code:
                cobrador = last_payment.debt_collector_code.name
            else:
                cobrador = ""

            if con.debt_collector:
                cobrador_contrato = con.debt_collector.name
            else:
                cobrador_contrato = ""

            contracts_list.append(con)
        
        # #Retornar información
        # info = [{
        #     'docs': contracts_list
        # }]

        #raise ValidationError("{}".format(info))

        return {
            "docs": contracts_list
        }
