# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date
import calendar

class PabsContract(models.Model):
    _inherit = "pabs.contract"

    def get_credits(self):
        credits = []
        for payment_id in self.payment_ids:
            if payment_id.state in ('posted','send','reconciled'):
                if payment_id.reference == 'stationary':
                    description = 'INVERSION INICIAL'
                    collector = self.employee_id.name
                    order = 1
                elif payment_id.reference == 'surplus':
                    description = 'EXCEDENTE INVERSIÓN INICIAL'
                    collector = self.employee_id.name
                    order = 2
                elif payment_id.reference == 'payment':
                    description = 'ABONO'
                    collector = payment_id.debt_collector_code.name
                    order = 1000
                elif payment_id.reference == 'mortuary':
                    description = 'COBRO FUNERARIA'
                    if payment_id.debt_collector_code:
                        collector = payment_id.debt_collector_code.name
                    else:
                        collector = False
                    order = 2000
                elif payment_id.reference == 'transfer':
                    description = 'TRASPASO'
                    collector = 'TRASPASO'
                    order = 3000
                else:
                    description = ''
                    collector = False
                    order = 4000
                credits.append({
                    'date' : payment_id.date_receipt if payment_id.date_receipt else payment_id.payment_date,
                    'name' : payment_id.ecobro_receipt,
                    'amount' : payment_id.amount,
                    'collector' : collector,
                    'description' : description,
                    'order': order,
                })
        for refund_id in self.refund_ids:
            if refund_id.type == 'out_refund' and refund_id.state == "posted":
                credits.append({
                    'date' : refund_id.invoice_date,
                    'name' : "",
                    'amount' : refund_id.amount_total,
                    'collector' : self.employee_id.name,
                    'description' : refund_id.ref.upper(),
                    'order': 3
                })
        for transfers_id in self.transfer_balance_ids:
            if transfers_id.parent_state == "posted":
                credits.append({
                    'date' : transfers_id.date,
                    'name' : "",
                    'amount' : transfers_id.balance_signed,
                    'collector' : "",
                    'description' : 'TRASPASO',
                    'order': 5000
                })
        credits = sorted(credits, key=lambda r: r['date'])
        credits = sorted(credits, key=lambda r: r['order'])
        return credits

    def payments(self, ids):
        for rec in self:
            payment = self.env['account.payment'].search([('contract','=', ids),('reference','=', 'payment'),('state','in',('posted','reconciled'))])
            if payment:
                pay = []
                for p in payment:
                    vals = {
                        'payment_date' :  p.payment_date,
                        'ecobro_receipt' :  p.ecobro_receipt,
                        'amount' :  p.amount,
                        'debt_collector_code' :  p.debt_collector_code.name,
                        'reference' :  p.reference,

                    }
                    pay.append(vals)

                print("------------", pay)
                return pay

    def estimated_payment_date(self, pay):
        return pay[-1]["date"]

    def late_amount_from_table(self, pay):
        late_amount = 0
        for rec in pay:
            today = date.today()
            if rec["date"] <= today:
                late_amount = late_amount + rec['amount_p']
                
        return late_amount

    def calcular_saldo_a_plazos(self):
        # total facturado
        total_facturado = self.product_price

        #Obtener cantidad entregada en bono de inversión inicial
        total_bono = sum(self.refund_ids.filtered(lambda r: r.type == 'out_refund' and r.state == 'posted').mapped('amount_total'))

        #Obtener cantidad por traspasos
        traspasos = self.transfer_balance_ids.filtered(lambda x: x.move_id.state == 'posted')
        total_traspasos = 0
        if len(traspasos) > 0:
            total_traspasos = sum(traspasos.mapped('debit'))

        #Cantidad a programar (no se toma en cuenta traspasos ni recibos de enganche: inversion, excedente y bono)
        saldo_a_plazos = total_facturado - self.initial_investment - total_bono - total_traspasos

        return saldo_a_plazos
            
    ### GENERAR ESTIMADO DE PAGOS ###
    def estimated_payment(self):
        for rec in self:

            #Total facturado
            total_facturado = rec.product_price

            #Obtener cantidad entregada en bono de inversión inicial
            total_bono = sum(rec.refund_ids.filtered(lambda r: r.type == 'out_refund' and r.state == 'posted').mapped('amount_total'))

            #Obtener cantidad por traspasos
            traspasos = rec.transfer_balance_ids.filtered(lambda x: x.move_id.state == 'posted')
            total_traspasos = 0
            if len(traspasos) > 0:
                total_traspasos = sum(traspasos.mapped('debit'))

            #Cantidad a programar (no se toma en cuenta traspasos ni recibos de enganche: inversion, excedente y bono)
            saldo_a_plazos = total_facturado - rec.initial_investment - total_bono - total_traspasos

            #Obtener monto abonado
            abonado = rec.paid_balance - rec.initial_investment - total_bono #- total_traspasos Se quita total de traspasos porque ya se aplica en rec.paid_balance
            
            ### Forma de pago: SEMANAL
            if rec.way_to_payment == 'weekly':
                cont = 0
                siguiente_fecha = rec.date_first_payment
                pay = []

                while saldo_a_plazos > 0:
                    cont += 1
                    saldo_a_plazos = saldo_a_plazos - rec.payment_amount

                    #Si hay saldo por programar
                    if saldo_a_plazos > 0:
                        
                        #Si hay monto abonado
                        if abonado > 0:
                            #Si el monto abonado es mayor al monto programado
                            if abonado >= rec.payment_amount:
                                vals = {
                                    'item': cont,
                                    'date': siguiente_fecha,
                                    'saldo': saldo_a_plazos,
                                    'amount': rec.payment_amount,
                                    'amount_p': 0.00,
                                }
                                pay.append(vals)
                                abonado = abonado - rec.payment_amount
                            #Si el monto abonado es menor o igual al monto programado
                            else:
                                vals = {
                                    'item': cont,
                                    'date': siguiente_fecha,
                                    'saldo': saldo_a_plazos - abonado,
                                    'amount': rec.payment_amount,
                                    'amount_p': rec.payment_amount - abonado,
                                }
                                pay.append(vals)
                                abonado = 0
                        #Si ya no hay monto abonado
                        else:
                            vals = {
                                'item': cont,
                                'date': siguiente_fecha,
                                'saldo': saldo_a_plazos,
                                'amount': rec.payment_amount,
                                'amount_p': rec.payment_amount,
                            }
                            pay.append(vals)
                    #Si ya no hay saldo a programar colocar último pago
                    else:
                        vals = {
                            'item': cont,
                            'date': siguiente_fecha,
                            'saldo': 0,
                            'amount': rec.payment_amount + saldo_a_plazos,
                            'amount_p': rec.payment_amount + saldo_a_plazos,
                        }
                        pay.append(vals)

                    siguiente_fecha = siguiente_fecha + relativedelta(days=7)
                return pay

            ### Forma de pago: QUINCENAL
            elif rec.way_to_payment == 'biweekly':
                cont = 0
                siguiente_fecha = rec.date_first_payment
                pay = []

                while saldo_a_plazos > 0:
                    cont += 1
                    saldo_a_plazos = saldo_a_plazos - rec.payment_amount

                    #Si hay saldo por programar
                    if saldo_a_plazos > 0:
                        
                        #Si hay monto abonado
                        if abonado > 0:
                            #Si el monto abonado es mayor al monto programado
                            if abonado >= rec.payment_amount:
                                vals = {
                                    'item': cont,
                                    'date': siguiente_fecha,
                                    'saldo': saldo_a_plazos,
                                    'amount': rec.payment_amount,
                                    'amount_p': 0.00,
                                }
                                pay.append(vals)
                                abonado = abonado - rec.payment_amount
                            #Si el monto abonado es menor o igual al monto programado
                            else:
                                vals = {
                                    'item': cont,
                                    'date': siguiente_fecha,
                                    'saldo': saldo_a_plazos - abonado,
                                    'amount': rec.payment_amount,
                                    'amount_p': rec.payment_amount - abonado,
                                }
                                pay.append(vals)
                                abonado = 0
                        #Si ya no hay monto abonado
                        else:
                            vals = {
                                'item': cont,
                                'date': siguiente_fecha,
                                'saldo': saldo_a_plazos,
                                'amount': rec.payment_amount,
                                'amount_p': rec.payment_amount,
                            }
                            pay.append(vals)
                    #Si ya no hay saldo a programar colocar último pago
                    else:
                        vals = {
                            'item': cont,
                            'date': siguiente_fecha,
                            'saldo': 0,
                            'amount': rec.payment_amount + saldo_a_plazos,
                            'amount_p': rec.payment_amount + saldo_a_plazos,
                        }
                        pay.append(vals)

                    #siguiente_fecha = siguiente_fecha + relativedelta(days=15)
                    siguiente_fecha = self.add_one_biweek(siguiente_fecha, siguiente_fecha.day)
                return pay

            ### Forma de pago: MENSUAL
            elif rec.way_to_payment == 'monthly':
                cont = 0
                siguiente_fecha = rec.date_first_payment
                pay = []

                while saldo_a_plazos > 0:
                    cont += 1
                    saldo_a_plazos = saldo_a_plazos - rec.payment_amount

                    #Si hay saldo por programar
                    if saldo_a_plazos > 0:

                        #Si hay monto abonado
                        if abonado > 0:
                            #Si el monto abonado es mayor al monto programado
                            if abonado >= rec.payment_amount:
                                vals = {
                                    'item': cont,
                                    'date': siguiente_fecha,
                                    'saldo': saldo_a_plazos,
                                    'amount': rec.payment_amount,
                                    'amount_p': 0.00,
                                }
                                pay.append(vals)
                                abonado = abonado - rec.payment_amount
                            #Si el monto abonado es menor o igual al monto programado
                            else:
                                vals = {
                                    'item': cont,
                                    'date': siguiente_fecha,
                                    'saldo': saldo_a_plazos - abonado,
                                    'amount': rec.payment_amount,
                                    'amount_p': rec.payment_amount - abonado,
                                }
                                pay.append(vals)
                                abonado = 0
                        #Si ya no hay monto abonado
                        else:
                            vals = {
                                'item': cont,
                                'date': siguiente_fecha,
                                'saldo': saldo_a_plazos,
                                'amount': rec.payment_amount,
                                'amount_p': rec.payment_amount,
                            }
                            pay.append(vals)
                    #Si ya no hay saldo a programar colocar último pago
                    else:
                        vals = {
                                'item': cont,
                                'date': siguiente_fecha,
                                'saldo': 0,
                                'amount': rec.payment_amount + saldo_a_plazos,
                                'amount_p': rec.payment_amount + saldo_a_plazos,
                        }
                        pay.append(vals)

                    #siguiente_fecha = siguiente_fecha + relativedelta(days=30)
                    siguiente_fecha = self.add_one_month(siguiente_fecha, siguiente_fecha.day)               
                return pay

    def add_one_biweek(self, orig_date, dia_primer_abono):
        #Si el dia es menor o igual a 14 se calculará en el mes actual (ejemplo si la quincena uno cae en dia 2, la quincena dos caerá en dia 16)
        if orig_date.day <= 14:
            new_year = orig_date.year
            new_month = orig_date.month
            new_day = orig_date.day + 14

            if dia_primer_abono >= 28:
                last_day_of_month = calendar.monthrange(new_year, new_month)[1]
                new_day = min(dia_primer_abono, last_day_of_month) #Para mantener el día mas próximo al día del primer abono

            return orig_date.replace(year=new_year, month=new_month, day=new_day)

        #Si el día es mayor o igual a 15 se calculará con el mes siguiente (ejemplo si la quincena uno cae en dia 31, la quincena dos caerá en dia 14)
        if orig_date.day >= 15:
            ### Validar cambio de año ###
            # advance year and month by one month
            new_year = orig_date.year
            new_month = orig_date.month + 1

            # note: in datetime.date, months go from 1 to 12
            if new_month > 12:
                new_year = new_year + 1
                new_month = new_month - 12

            if orig_date.day >= 28:
                new_day = 14
            else:
                new_day = orig_date.day - 14

            return orig_date.replace(year=new_year, month=new_month, day=new_day)

    def add_one_month(self, orig_date, dia_primer_abono):
        ### Validar cambio de año ###
        # advance year and month by one month
        new_year = orig_date.year
        new_month = orig_date.month + 1
        # note: in datetime.date, months go from 1 to 12
        if new_month > 12:
            new_year = new_year + 1
            new_month = new_month - 12

        last_day_of_month = calendar.monthrange(new_year, new_month)[1]
        #new_day = min(orig_date.day, last_day_of_month) #Linea original

        new_day = min(dia_primer_abono, last_day_of_month) #Para mantener el día mas próximo al día del primer abono

        return orig_date.replace(year=new_year, month=new_month, day=new_day)

                