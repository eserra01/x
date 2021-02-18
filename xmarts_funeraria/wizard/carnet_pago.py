from datetime import datetime
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

class CarnetPagoWizard(models.TransientModel):
    _name = 'report.carnet.pago'

    initial_contract = fields.Many2one(comodel_name="pabs.contract", domain="([('state','=','contract')])", string="Contrato inicial")
    final_contract = fields.Many2one(comodel_name="pabs.contract", domain="([('state','=','contract')])", string="Contrato final")

    def filter(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.date_from,
                'date_end': self.date_to,
            },
        }
        return self.env.ref('xmarts_funeraria.id_carnet_pago').report_action(self, data=data)

#<!-- <div style="page-break-before: always;"></div> -->

class ReportAttendanceRecap(models.AbstractModel):
    _name = "report.xmarts_funeraria.id_carnet_pago"

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
                ('name','<=',final_contract)
            ])

        contracts_list = []
        #Ingresar cada contrato a la lista
        for con in contract_ids:
            contracts_list.append({
                "name": con.name
            })
        
        #Retornar información
        info = [{
            "break":1,
            'docs': contracts_list
        }]

        return {
            "docs": info
        }
