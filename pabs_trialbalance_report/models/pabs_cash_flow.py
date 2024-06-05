# -*- coding: utf-8 -*-
from odoo import _, models, fields, api
from odoo.exceptions import ValidationError

TYPES = [
    ('x1_initial_balance', '1. Saldo inicial'),
    ('x21_income', '2.1 Ingresos'),
    ('x22_total_income', '2.2 Total ingresos'),
    ('x3_available', '3 Disponible'),
    ('x41_expenses', '4.1 Egresos'),
    ('x42_total_expenses', '4.2 Total egresos'),
    ('x5_final_balance', '5. Saldo final')
]

class PabsCashFlow(models.Model):
    _name = 'pabs.cash.flow'
    _description = "Flujo de efectivo"
    _rec_name = 'type'
    
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True, tracking=True)

    start_date = fields.Date(string="Fecha inicial")
    end_date = fields.Date(string="Fecha final")
    type = fields.Selection(string="Categoria", selection=TYPES, required=True)
    account_analytic_tag = fields.Many2one(string="Etiqueta analítica", comodel_name='account.analytic.tag')
    amount = fields.Float(string="Movimientos y Saldos")

    ### Mostrar Asientos contables
    def general_ledger_action(self):
        query = """
            SELECT
                mov.id
            FROM account_move AS mov
            INNER JOIN account_journal AS jou ON mov.journal_id = jou.id
            INNER JOIN account_move_line AS line ON mov.id = line.move_id
            INNER JOIN account_account AS acc ON line.account_id = acc.id
            LEFT JOIN account_analytic_tag_account_move_line_rel AS tag_by_line ON line.id = tag_by_line.account_move_line_id
            LEFT JOIN account_analytic_tag AS tag ON tag_by_line.account_analytic_tag_id = tag.id AND tag.cash_flow_type IS NOT NULL
                WHERE mov.state = 'posted'
                AND jou.is_a_cash_flow_journal = TRUE
                AND acc.cash_flow_analytic_tag_required = TRUE
                AND tag.id = {}
                AND mov.date BETWEEN '{}' AND '{}'
                AND mov.company_id = {}
        """.format(self.account_analytic_tag.id, self.start_date, self.end_date, self.company_id.id)

        self.env.cr.execute(query)
        
        ids = []
        for res in self.env.cr.fetchall():
            if int(res[0]) not in ids:
                ids.append(int(res[0]))
               
        action_id = self.env["ir.actions.act_window"].for_xml_id("account", "action_move_journal_line")
        action_id.update({'domain':"[('id','=',%s)]"%(str(ids)), 'target':'self','context':{}})
        return action_id
             
    ### Mostrar Apuntes contables
    def move_lines_action(self):
        query = """
            SELECT
                line.id
            FROM account_move AS mov
            INNER JOIN account_journal AS jou ON mov.journal_id = jou.id
            INNER JOIN account_move_line AS line ON mov.id = line.move_id
            INNER JOIN account_account AS acc ON line.account_id = acc.id
            LEFT JOIN account_analytic_tag_account_move_line_rel AS tag_by_line ON line.id = tag_by_line.account_move_line_id
            LEFT JOIN account_analytic_tag AS tag ON tag_by_line.account_analytic_tag_id = tag.id AND tag.cash_flow_type IS NOT NULL
                WHERE mov.state = 'posted'
                AND jou.is_a_cash_flow_journal = TRUE
                AND acc.cash_flow_analytic_tag_required = TRUE
                AND tag.id = {}
                AND mov.date BETWEEN '{}' AND '{}'
                AND mov.company_id = {}
        """.format(self.account_analytic_tag.id, self.start_date, self.end_date, self.company_id.id)
        
        self.env.cr.execute(query)
        
        ids = []
        for res in self.env.cr.fetchall():
            ids.append(int(res[0]))
        
        action_id = self.env["ir.actions.act_window"].for_xml_id("account", "action_account_moves_all")
        action_id.update({'domain':"[('id','=',%s)]"%(str(ids)),'target':'self','context':{}})
        return action_id
    
   