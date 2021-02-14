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
        print("cccccc")
        return self.env.ref('xmarts_funeraria.id_payroll_ing_egre').report_action(self, data=data)


class ReportAttendanceRecapINGEGRE(models.AbstractModel):

    _name = "report.xmarts_funeraria.payroll_ing_egre"

    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        payment = self.env['account.payment'].search([
                    ('payment_date', '>=', date_start),
                    ('payment_date', '<=', date_end),

                ])

        docs = []
        docse = []        
        exend = 0
        amount_total = 0        
        exend_e = 0
        amount_total_e = 0
        comisi = []
        do = []        
        if payment:
            c = []
            for p in payment:
                if p.reference == 'surplus':
                    exend += p.amount
                    amount_total += p.amount

                if p.debt_collector_code:
                    c.append(p.debt_collector_code.id)
            cobrador = set(c)
            if cobrador:
                for c in cobrador:
                    cobra = self.env['account.payment'].search([('payment_date', '>=', date_start),('payment_date', '<=', date_end),('debt_collector_code', '=', c)])                   
                    
                    amount = 0
                    if cobra:
                        for co in cobra:                           
                            if co.reference == 'payment':
                                amount_total += co.amount
                                amount += co.amount
                            print("----cobra--------",amount,"-----cobra-----",co.amount,"--------------",co.debt_collector_code.name,"--------------",co.name)
                    cobrador = self.env['account.payment'].search([('payment_date', '>=', date_start),('payment_date', '<=', date_end),('debt_collector_code', '=', c)],limit=1)                   
                    print("------------",amount,"----------",cobrador.name)
                    for pay in cobrador:
                        
                        if pay.reference == 'payment':
                            docs.append({
                                'Ecobro_receipt': pay.debt_collector_code.barcode,
                                'debt_collector_code': pay.debt_collector_code.name,
                                'amount': amount,
                            })

            for com in payment.comission_output_ids:
                if com.actual_commission_paid > 0:
                    if com.job_id.name == 'Fideicomiso':
                        exend_e += com.actual_commission_paid
                        amount_total_e += com.actual_commission_paid

                    if com.job_id.name != 'Fideicomiso':
                        comisi.append(com.comission_agent_id.id)
                        do.append({
                            'Ecobro_receipt': com.comission_agent_id.barcode,
                            'debt_collector_code': com.comission_agent_id.name,
                            'amount': com.actual_commission_paid,
                        })
            
       
     
            comision = set(comisi)
            if comision:
                for c in comision:
                    
                    comm = self.env['pabs.comission.output'].search([('create_date', '>=', date_start),('create_date', '<=', date_end),('comission_agent_id', '=', c),('actual_commission_paid','>', 0)],limit=1)                   
                    
                    for cc in comm:
                        if cc.job_id.name != 'Fideicomiso':
                            amount = 0
                            for comis in do:
                                if comis["Ecobro_receipt"] == cc.comission_agent_id.barcode:
                                    amount_total_e += float(comis["amount"])
                                    amount += float(comis["amount"])
                            docse.append({
                                'Ecobro_receipt': cc.comission_agent_id.barcode,
                                'debt_collector_code': cc.comission_agent_id.name,
                                'amount': amount,})



        
        return {
            'amount_total': amount_total,
            'amount_total_e': amount_total_e,
            'exend': exend,
            'exend_e': exend_e,
            'date_start': date_start,
            'date_end': date_end,
            'docs': docs,
            'docse': docse,
        }