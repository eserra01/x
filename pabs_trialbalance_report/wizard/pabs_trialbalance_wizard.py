# -*- coding: utf-8 -*-

from xml.dom import ValidationErr
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta

class PabsTrialbalanceWizard(models.TransientModel):
    _name = 'pabs.trialbalance.wizard'
    _description = 'Asistente Balanza de comprobación'

    def _default_date(self):
        return fields.Date.context_today(self)
  
    start_date = fields.Date(string="Fecha inicial", default=_default_date, required=True)
    end_date = fields.Date(string="Fecha final", default=_default_date, required=True)
    account_ids = fields.Many2many(string="Cuentas", comodel_name='account.account', required=True)
    account_analytic_account_ids = fields.Many2many(string="Cuentas analíticas", comodel_name='account.analytic.account',)
    account_analytic_tag_ids = fields.Many2many(string="Etiquetas analíticas", comodel_name='account.analytic.tag',)
    info = fields.Char(string="", default="")
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,) 
    
    def get_trialbalance(self):      
        company_id = self.env.company.id
        # Borrar registros
        trialbalance_ids = self.env['pabs.trialbalance'].search([])
        trialbalance_ids.unlink()

        tinidebit = 0
        tinicredit = 0
        tmovdebit = 0
        tmovcredit = 0
        tdebit = 0
        tcredit = 0
        init_date = date(self.start_date.year, 1, 1)
        #
        analytic_account_ids = ""            
        for aa in self.account_analytic_account_ids:
            analytic_account_ids += str(aa.id) + ","
        analytic_account_ids = analytic_account_ids[:-1]
        #
        analytic_tag_ids = ""
        for at in self.account_analytic_tag_ids:
            analytic_tag_ids += str(at.id) + ","
        analytic_tag_ids = analytic_tag_ids[:-1]      
        #
        for account in self.account_ids:
                      
            # SALDO INICIAL
            if self.account_analytic_account_ids or self.account_analytic_tag_ids:               
                #
                if self.account_analytic_account_ids and self.account_analytic_tag_ids:
                    #
                    qry = """
                    SELECT A.debit,A.credit FROM 
                    account_move_line A 
                    INNER JOIN account_move B ON A.move_id = B.id 
                    INNER JOIN account_analytic_tag_account_move_line_rel C ON A.id = C.account_move_line_id 
                    WHERE A.date < '{}' AND A.company_id = {} AND
                    A.account_id = {} AND B.state = 'posted' AND 
                    A.analytic_account_id IN ({}) AND C.account_analytic_tag_id IN ({});
                    """.format(self.start_date, company_id, account.id, analytic_account_ids, analytic_tag_ids)
                #
                elif self.account_analytic_account_ids:
                    #
                    qry = """
                    SELECT A.debit,A.credit FROM 
                    account_move_line A 
                    INNER JOIN account_move B ON A.move_id = B.id 
                    WHERE A.date < '{}' AND A.company_id = {} AND
                    A.account_id = {} AND B.state = 'posted' AND 
                    A.analytic_account_id IN ({});
                    """.format(self.start_date, company_id, account.id, analytic_account_ids)
                #
                else:
                    #
                    qry = """
                    SELECT A.debit,A.credit FROM 
                    account_move_line A 
                    INNER JOIN account_move B ON A.move_id = B.id 
                    INNER JOIN account_analytic_tag_account_move_line_rel C ON A.id = C.account_move_line_id 
                    WHERE A.date < '{}' AND A.company_id = {} AND
                    A.account_id = {} AND B.state = 'posted' AND C.account_analytic_tag_id IN ({});
                    """.format(self.start_date, company_id, account.id, analytic_tag_ids)
            #    
            else:
                qry = """
                SELECT A.debit,A.credit FROM 
                account_move_line A INNER JOIN account_move B ON A.move_id = B.id 
                WHERE A.date < '{}' AND A.company_id = {} AND
                A.account_id = {} AND B.state = 'posted';
                """.format(self.start_date, company_id, account.id)  
            #
            self.env.cr.execute(qry)

            debit = 0
            credit = 0
            initial_debit = 0
            initial_credit = 0
            for res in self.env.cr.fetchall():
                debit += float(res[0])
                credit += float(res[1])           
            #
            initial_debit = debit - credit if debit >= credit else 0
            initial_credit = credit - debit if credit >= debit else 0            
            tinidebit += initial_debit
            tinicredit += initial_credit

            # MOVIMIENTOS DEL PERIODO
            if self.account_analytic_account_ids or self.account_analytic_tag_ids:               
                #
                if self.account_analytic_account_ids and self.account_analytic_tag_ids:
                    qry = """
                    SELECT A.debit,A.credit FROM 
                    account_move_line A 
                    INNER JOIN account_move B ON A.move_id = B.id 
                    INNER JOIN account_analytic_tag_account_move_line_rel C ON A.id = C.account_move_line_id 
                    WHERE A.date BETWEEN '{}' AND '{}' AND A.company_id = {} AND
                    A.account_id = {} AND B.state = 'posted' AND
                    A.analytic_account_id IN ({}) AND C.account_analytic_tag_id IN ({});
                    """.format(self.start_date, self.end_date, company_id, account.id, analytic_account_ids, analytic_tag_ids)    
                #
                elif self.account_analytic_account_ids:
                    qry = """
                    SELECT A.debit,A.credit FROM 
                    account_move_line A 
                    INNER JOIN account_move B ON A.move_id = B.id                     
                    WHERE A.date BETWEEN '{}' AND '{}' AND A.company_id = {} AND
                    A.account_id = {} AND B.state = 'posted' AND
                    A.analytic_account_id IN ({});
                    """.format(self.start_date, self.end_date, company_id, account.id, analytic_account_ids)                    
                else:
                    qry = """
                    SELECT A.debit,A.credit FROM 
                    account_move_line A 
                    INNER JOIN account_move B ON A.move_id = B.id 
                    INNER JOIN account_analytic_tag_account_move_line_rel C ON A.id = C.account_move_line_id 
                    WHERE A.date BETWEEN '{}' AND '{}' AND A.company_id = {} AND
                    A.account_id = {} AND B.state = 'posted' AND C.account_analytic_tag_id IN ({});
                    """.format(self.start_date, self.end_date, company_id, account.id, analytic_tag_ids)    

            else:
                qry = """
                SELECT A.debit,A.credit FROM 
                account_move_line A INNER JOIN account_move B ON A.move_id = B.id 
                WHERE A.date BETWEEN '{}' AND '{}' AND A.company_id = {} AND
                A.account_id = {} AND B.state = 'posted';
                """.format(self.start_date, self.end_date, company_id, account.id)                            
            #
            self.env.cr.execute(qry)            
            
            debit = 0
            credit = 0
            for res in self.env.cr.fetchall():
                debit += float(res[0])
                credit += float(res[1])
             #
            tmovdebit += debit
            tmovcredit += credit   

            # Totales
            total_debit = initial_debit + debit
            total_credit = initial_credit + credit
            tdebit += total_debit - total_credit if total_debit > total_credit else 0
            tcredit += total_credit - total_debit if total_credit > total_debit else 0
                     
            account_analytic_account_ids = []
            for aaa in self.account_analytic_account_ids:
                account_analytic_account_ids.append(aaa.id)
            account_analytic_tag_ids = []
            for aat in self.account_analytic_tag_ids:
                account_analytic_tag_ids.append(aat.id)
        
            # Crear registro 
            vals = {
                'company_id': company_id,
                'account_id': account.id,
                'debit': debit,
                'credit': credit,
                'idebit': initial_debit if initial_debit > 0 else 0,
                'icredit': initial_credit if initial_credit > 0 else 0,
                'tdebit': total_debit - total_credit if total_debit > total_credit else 0,
                'tcredit': total_credit - total_debit if total_credit > total_debit else 0,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'account_analytic_account_ids': account_analytic_account_ids,
                'account_analytic_tag_ids': account_analytic_tag_ids,
            }
            print(vals)
            self.env['pabs.trialbalance'].create(vals)

        return {
            'type': 'ir.actions.act_window',
            'name': "Balanza del {} al {}".format(self.start_date,self.end_date),        
            'res_model': 'pabs.trialbalance',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': self.env.ref('pabs_trialbalance_report.pabs_trialbalance_tree_view').id,
            'target': 'main',
            'context': {'period_type': 'weekly'},
            # 'domain': domain
        }  
        
        

    
    
    