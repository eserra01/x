# -*- coding: utf-8 -*-
from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

class PabsTrialbalance(models.Model):
    _name = 'pabs.trialbalance'    
    _description = "Balanza de comprobación"
    _rec_name = 'account_id'

    
    account_id = fields.Many2one(string="Cuenta", comodel_name='account.account',)    
    account_analytic_account_ids = fields.Many2many(string="Cuentas analíticas", comodel_name='account.analytic.account',)
    account_analytic_tag_ids = fields.Many2many(string="Etiquetas analíticas", comodel_name='account.analytic.tag',)
    credit = fields.Float(string = "Crédito",)
    debit = fields.Float(string = "Débito",)
    icredit = fields.Float(string = "Crédito (inicial)",)
    idebit = fields.Float(string = "Débito (inicial)",)
    tcredit = fields.Float(string = "Crédito (total)",)
    tdebit = fields.Float(string = "Débito (total)",)
    start_date = fields.Date(string="Fecha inicial")
    end_date = fields.Date(string="Fecha final",)

    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True, tracking=True) 

    def general_ledger_action(self):

        # Movimientos del periodo
        if self.account_analytic_account_ids or self.account_analytic_tag_ids:
            #
            account_analytic_account_ids = ""
            for aaa in self.account_analytic_account_ids:
                account_analytic_account_ids+= str(aaa.id) + ","
            account_analytic_account_ids = account_analytic_account_ids[:-1]
            #
            account_analytic_tag_ids = ""
            for aat in self.account_analytic_tag_ids:
                account_analytic_tag_ids += str(aat.id) +  ","
            account_analytic_tag_ids = account_analytic_tag_ids[:-1]
            #
            if self.account_analytic_account_ids and self.account_analytic_tag_ids:
                qry = """
                SELECT B.id FROM 
                account_move_line A 
                INNER JOIN account_move B ON A.move_id = B.id 
                INNER JOIN account_analytic_tag_account_move_line_rel C ON A.id = C.account_move_line_id 
                WHERE A.date BETWEEN '{}' AND '{}' AND A.company_id = {} AND
                A.account_id = {} AND B.state = 'posted' AND 
                A.analytic_account_id IN ({}) AND C.account_analytic_tag_id IN ({});
                """.format(self.start_date, self.end_date, self.company_id.id, self.account_id.id,account_analytic_account_ids,account_analytic_tag_ids)                
            elif self.account_analytic_account_ids:
                qry = """
                SELECT B.id FROM 
                account_move_line A 
                INNER JOIN account_move B ON A.move_id = B.id               
                WHERE A.date BETWEEN '{}' AND '{}' AND A.company_id = {} AND
                A.account_id = {} AND B.state = 'posted' AND 
                A.analytic_account_id IN ({});
                """.format(self.start_date, self.end_date, self.company_id.id, self.account_id.id,account_analytic_account_ids)
            else:
                qry = """
                SELECT B.id FROM 
                account_move_line A 
                INNER JOIN account_move B ON A.move_id = B.id 
                INNER JOIN account_analytic_tag_account_move_line_rel C ON A.id = C.account_move_line_id 
                WHERE A.date BETWEEN '{}' AND '{}' AND A.company_id = {} AND
                A.account_id = {} AND B.state = 'posted' AND 
                C.account_analytic_tag_id IN ({});
                """.format(self.start_date, self.end_date, self.company_id.id , self.account_id.id, account_analytic_tag_ids)                
        else:
            qry = """
            SELECT B.id FROM 
            account_move_line A INNER JOIN account_move B ON A.move_id = B.id 
            WHERE A.date BETWEEN '{}' AND '{}' AND A.company_id = {} AND
            A.account_id = {} AND B.state = 'posted';
            """.format(self.start_date, self.end_date, self.company_id.id, self.account_id.id)                            
        #
        self.env.cr.execute(qry)            
        
        ids = []
        for res in self.env.cr.fetchall():
            if int(res[0]) not in ids:
                ids.append(int(res[0]))
               
        #       
        action_id = self.env["ir.actions.actions"]._for_xml_id("account.action_move_journal_line")        
        action_id.update({'domain':"[('id','=',%s)]"%(str(ids)),'target':'self','context':{}})
        return action_id       
             

    def move_lines_action(self):

        # Movimientos del periodo
        if self.account_analytic_account_ids or self.account_analytic_tag_ids:
            #
            account_analytic_account_ids = ""
            for aaa in self.account_analytic_account_ids:
                account_analytic_account_ids+= str(aaa.id) + ","
            account_analytic_account_ids = account_analytic_account_ids[:-1]
            #
            account_analytic_tag_ids = ""
            for aat in self.account_analytic_tag_ids:
                account_analytic_tag_ids += str(aat.id) +  ","
            account_analytic_tag_ids = account_analytic_tag_ids[:-1]
            #
            if self.account_analytic_account_ids and self.account_analytic_tag_ids:
                qry = """
                SELECT A.id FROM 
                account_move_line A 
                INNER JOIN account_move B ON A.move_id = B.id 
                INNER JOIN account_analytic_tag_account_move_line_rel C ON A.id = C.account_move_line_id 
                WHERE A.date BETWEEN '{}' AND '{}' AND A.company_id = {} AND
                A.account_id = {} AND B.state = 'posted' AND 
                A.analytic_account_id IN ({}) AND C.account_analytic_tag_id IN ({});
                """.format(self.start_date, self.end_date, self.company_id.id, self.account_id.id,account_analytic_account_ids,account_analytic_tag_ids)                
            elif self.account_analytic_account_ids:
                qry = """
                SELECT A.id FROM 
                account_move_line A 
                INNER JOIN account_move B ON A.move_id = B.id               
                WHERE A.date BETWEEN '{}' AND '{}' AND A.company_id = {} AND
                A.account_id = {} AND B.state = 'posted' AND 
                A.analytic_account_id IN ({});
                """.format(self.start_date, self.end_date, self.company_id.id, self.account_id.id,account_analytic_account_ids)
            else:
                qry = """
                SELECT A.id FROM 
                account_move_line A 
                INNER JOIN account_move B ON A.move_id = B.id 
                INNER JOIN account_analytic_tag_account_move_line_rel C ON A.id = C.account_move_line_id 
                WHERE A.date BETWEEN '{}' AND '{}' AND A.company_id = {} AND
                A.account_id = {} AND B.state = 'posted' AND 
                C.account_analytic_tag_id IN ({});
                """.format(self.start_date, self.end_date, self.company_id.id , self.account_id.id, account_analytic_tag_ids)                
        else:
            qry = """
            SELECT A.id FROM 
            account_move_line A INNER JOIN account_move B ON A.move_id = B.id 
            WHERE A.date BETWEEN '{}' AND '{}' AND A.company_id = {} AND
            A.account_id = {} AND B.state = 'posted';
            """.format(self.start_date, self.end_date, self.company_id.id, self.account_id.id)                            
        
        self.env.cr.execute(qry)            
        
        ids = []
        for res in self.env.cr.fetchall():           
            ids.append(int(res[0]))
        
        #       
        action_id = self.env["ir.actions.actions"]._for_xml_id("account.action_account_moves_all")        
        action_id.update({'domain':"[('id','=',%s)]"%(str(ids)),'target':'self','context':{}})
        return action_id   
    
   