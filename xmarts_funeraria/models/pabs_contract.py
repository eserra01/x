# -*- coding: utf-8 -*-
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class PabsContract(models.Model):
    _inherit = "pabs.contract"

    def payments(self, ids):
        for rec in self:
            payment = self.env['account.payment'].search([('contract','=', ids),('reference','=', 'payment'),('state','in',('posted','reconciled'))])
            if payment:
                pay = []
                for p in payment:
                    vals = {
                        'payment_date' :  p.payment_date,
                        'Ecobro_receipt' :  p.Ecobro_receipt,
                        'amount' :  p.amount,
                        'debt_collector_code' :  p.debt_collector_code.name,
                        'reference' :  p.reference,

                    }
                    pay.append(vals)

                print("------------", pay)
                return pay

    def estimated_payment_date(self, pay):
        date_term = ""
        for rec in pay:
            date_term = rec["date"]

        
        return date_term
            

    def estimated_payment(self, ids):
        for rec in self:

            if rec.way_to_payment == 'weekly':
                
                payment = self.env['account.payment'].search([('contract','=', ids),('reference','=', 'payment'),('state','in',('posted','reconciled'))])
                paid = 0
                if payment:
                    for p in payment:
                        paid += p.amount
                print("---------",paid)
                i = rec.balance
                cont = 0
                date = rec.date_first_payment
                pay = []
                while i > 0:
                    i -= rec.payment_amount
                    cont += 1
                    date_new = fields.Datetime.from_string(date) + relativedelta(days=7)
                    date = date_new
                    print("c vale", i)
                    if i > 0:
                        if paid > 0:
                            if paid > rec.payment_amount:
                                vals = {
                                    'item': cont,
                                    'date': date_new,
                                    'amount': rec.payment_amount,
                                    'amount_p': 0.00,
                                }
                                pay.append(vals)
                                paid -= rec.payment_amount
                            else:
                                vals = {
                                    'item': cont,
                                    'date': date_new,
                                    'amount': rec.payment_amount,
                                    'amount_p': rec.payment_amount - paid,
                                }
                                pay.append(vals)
                                paid -= rec.payment_amount
                        else:
                            vals = {
                                'item': cont,
                                'date': date_new,
                                'amount': rec.payment_amount,
                                'amount_p': rec.payment_amount,
                            }
                            pay.append(vals)
                    else:
                        vals = {
                                'item': cont,
                                'date': date_new,
                                'amount': rec.payment_amount + i,
                                'amount_p': rec.payment_amount + i,
                        }
                        pay.append(vals)

                               
                return pay

            elif rec.way_to_payment == 'biweekly':

            
                payment = self.env['account.payment'].search([('contract','=', ids),('reference','=', 'payment'),('state','in',('posted','reconciled'))])
                paid = 0
                if payment:
                    for p in payment:
                        paid += p.amount
                print("---------",paid)
                i = rec.balance
                cont = 0
                date = rec.date_first_payment
                pay = []
                dates = 0
                month = 0
                while i > 0:
                    if dates == 0:
                        dates = 1
                        i -= rec.payment_amount
                        cont += 1
                        date_new = fields.Datetime.from_string(date) + relativedelta(days=15)
                        date = date_new
                        print("c vale", i, "dates", dates)
                        if i > 0:
                            if paid > 0:
                                if paid > rec.payment_amount:
                                    vals = {
                                        'item': cont,
                                        'date': date_new,
                                        'amount': rec.payment_amount,
                                        'amount_p': 0.00,
                                    }
                                    pay.append(vals)
                                    paid -= rec.payment_amount
                                else:
                                    vals = {
                                        'item': cont,
                                        'date': date_new,
                                        'amount': rec.payment_amount,
                                        'amount_p': rec.payment_amount - paid,
                                    }
                                    pay.append(vals)
                                    paid -= rec.payment_amount
                            else:
                                vals = {
                                    'item': cont,
                                    'date': date_new,
                                    'amount': rec.payment_amount,
                                    'amount_p': rec.payment_amount,
                                }
                                pay.append(vals)
                        else:
                            vals = {
                                    'item': cont,
                                    'date': date_new,
                                    'amount': rec.payment_amount + i,
                                    'amount_p': rec.payment_amount + i,
                            }
                            pay.append(vals)
                    else:
                        dates = 0
                        i -= rec.payment_amount
                        cont += 1
                        month += 1
                        date_new = fields.Datetime.from_string(rec.date_first_payment) + relativedelta(months=month)
                        date = date_new
                        print("c vale", i, "dates", dates)
                        if i > 0:
                            if paid > 0:
                                if paid > rec.payment_amount:
                                    vals = {
                                        'item': cont,
                                        'date': date_new,
                                        'amount': rec.payment_amount,
                                        'amount_p': 0.00,
                                    }
                                    pay.append(vals)
                                    paid -= rec.payment_amount
                                else:
                                    vals = {
                                        'item': cont,
                                        'date': date_new,
                                        'amount': rec.payment_amount,
                                        'amount_p': rec.payment_amount - paid,
                                    }
                                    pay.append(vals)
                                    paid -= rec.payment_amount
                            else:
                                vals = {
                                    'item': cont,
                                    'date': date_new,
                                    'amount': rec.payment_amount,
                                    'amount_p': rec.payment_amount,
                                }
                                pay.append(vals)
                        else:
                            vals = {
                                    'item': cont,
                                    'date': date_new,
                                    'amount': rec.payment_amount + i,
                                    'amount_p': rec.payment_amount + i,
                            }
                            pay.append(vals)
                               
                return pay

            elif rec.way_to_payment == 'monthly':

            
                payment = self.env['account.payment'].search([('contract','=', ids),('reference','=', 'payment'),('state','in',('posted','reconciled'))])
                paid = 0
                if payment:
                    for p in payment:
                        paid += p.amount
                print("---------",paid)
                i = rec.balance
                cont = 0
                date = rec.date_first_payment
                pay = []
                while i > 0:
                    i -= rec.payment_amount
                    cont += 1
                    date_new = fields.Datetime.from_string(date) + relativedelta(months=1)
                    date = date_new
                    print("c vale", i)
                    if i > 0:
                        if paid > 0:
                            if paid > rec.payment_amount:
                                vals = {
                                    'item': cont,
                                    'date': date_new,
                                    'amount': rec.payment_amount,
                                    'amount_p': 0.00,
                                }
                                pay.append(vals)
                                paid -= rec.payment_amount
                            else:
                                vals = {
                                    'item': cont,
                                    'date': date_new,
                                    'amount': rec.payment_amount,
                                    'amount_p': rec.payment_amount - paid,
                                }
                                pay.append(vals)
                                paid -= rec.payment_amount
                        else:
                            vals = {
                                'item': cont,
                                'date': date_new,
                                'amount': rec.payment_amount,
                                'amount_p': rec.payment_amount,
                            }
                            pay.append(vals)
                    else:
                        vals = {
                                'item': cont,
                                'date': date_new,
                                'amount': rec.payment_amount + i,
                                'amount_p': rec.payment_amount + i,
                        }
                        pay.append(vals)

                               
                return pay

                