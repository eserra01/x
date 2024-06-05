# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError

class PabsCashFlowWizard(models.TransientModel):
    _name = 'pabs.cash.flow.wizard'
    _description = 'Asistente Flujo de efectivo'

    def _default_date(self):
        return fields.Date.context_today(self)
  
    start_date = fields.Date(string="Fecha inicial", default=_default_date, required=True)
    end_date = fields.Date(string="Fecha final", default=_default_date, required=True)
    info = fields.Char(string="", default="")
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True,) 
    
    def get_cash_flow(self):
        company_id = self.env.company.id

        ### Verificar que no existen asientos con más de una etiqueta analítica
        query = """
            SELECT
                mov.name as move_name,
                mov.ref as move_ref,
                line.id as line_id
            FROM account_move AS mov
            INNER JOIN account_journal AS jou ON mov.journal_id = jou.id
            INNER JOIN account_move_line AS line ON mov.id = line.move_id
            INNER JOIN account_account AS acc ON line.account_id = acc.id
            LEFT JOIN account_analytic_tag_account_move_line_rel AS tag_by_line ON line.id = tag_by_line.account_move_line_id
            LEFT JOIN account_analytic_tag AS tag ON tag_by_line.account_analytic_tag_id = tag.id AND tag.cash_flow_type IS NOT NULL
                WHERE mov.state = 'posted'
                AND jou.is_a_cash_flow_journal = TRUE
                AND acc.cash_flow_analytic_tag_required = TRUE
                AND mov.date BETWEEN '{}' AND '{}'
                AND mov.company_id = {}
                    GROUP BY mov.name, mov.ref, line.id HAVING COUNT(*) > 1
        """.format(self.start_date, self.end_date, company_id)

        self.env.cr.execute(query)

        duplicate_tags = ""
        limit = 10
        for index, res in enumerate(self.env.cr.fetchall(), 1):
            duplicate_tags = duplicate_tags + "{},{},{}\n".format(res[0],res[1],res[2])

            if index == limit:
                break
        
        if duplicate_tags:
            raise ValidationError("Se encontraron asientos con doble etiqueta analítica\n\nAsiento, Referencia, Id asiento\n{}".format(duplicate_tags))

        ### Consultar asientos
        query = """
            SELECT
                'balance' as cash_flow_type,
                '' as tag,
                COALESCE(SUM(COALESCE(line.debit, 0)) - SUM(COALESCE(line.credit, 0)), 0) as debit,
                0 as credit,
                0 as tag_id
            FROM account_move AS mov
            INNER JOIN account_journal AS jou ON mov.journal_id = jou.id
            INNER JOIN account_move_line AS line ON mov.id = line.move_id
            INNER JOIN account_account AS acc ON line.account_id = acc.id
            LEFT JOIN account_analytic_tag_account_move_line_rel AS tag_by_line ON line.id = tag_by_line.account_move_line_id
            LEFT JOIN account_analytic_tag AS tag ON tag_by_line.account_analytic_tag_id = tag.id AND tag.cash_flow_type IS NOT NULL
                WHERE mov.state = 'posted'
                AND jou.is_a_cash_flow_journal = TRUE
                AND acc.cash_flow_analytic_tag_required = TRUE
                AND mov.date < '{}'
                AND mov.company_id = {}
            UNION SELECT
                tag.cash_flow_type, 
                tag.name as tag,
                SUM(line.debit) as debit,
                SUM(line.credit) as credit,
                tag.id as tag_id
            FROM account_move AS mov
            INNER JOIN account_journal AS jou ON mov.journal_id = jou.id
            INNER JOIN account_move_line AS line ON mov.id = line.move_id
            INNER JOIN account_account AS acc ON line.account_id = acc.id
            LEFT JOIN account_analytic_tag_account_move_line_rel AS tag_by_line ON line.id = tag_by_line.account_move_line_id
            LEFT JOIN account_analytic_tag AS tag ON tag_by_line.account_analytic_tag_id = tag.id AND tag.cash_flow_type IS NOT NULL
                WHERE mov.state = 'posted'
                AND jou.is_a_cash_flow_journal = TRUE
                AND acc.cash_flow_analytic_tag_required = TRUE
                AND mov.date BETWEEN '{}' AND '{}'
                AND mov.company_id = {}
                    GROUP BY tag.cash_flow_type, tag.id, tag.name
                        ORDER BY cash_flow_type, tag
        """.format(self.start_date, company_id, self.start_date, self.end_date, company_id)

        self.env.cr.execute(query)
        
        initial_balance = 0
        income = []
        expenses = []
        for res in self.env.cr.fetchall():
            cash_flow_type = res[0]

            if cash_flow_type == 'balance':
                initial_balance = float(res[2])
            elif cash_flow_type == 'debit':
                income.append({
                    'cash_flow_type': cash_flow_type,
                    'tag': res[1],
                    'amount': float(res[2]) - float(res[3]),
                    'tag_id': res[4],
                })
            elif cash_flow_type == 'credit':
                expenses.append({
                    'cash_flow_type': cash_flow_type,
                    'tag': res[1],
                    'amount': float(res[3]) - float(res[2]),
                    'tag_id': res[4],
                })
        
        ### Crear registros de pabs.cash.flow
        cash_flow_obj = self.env['pabs.cash.flow']
        
        cash_flow_ids = cash_flow_obj.search([])
        cash_flow_ids.unlink()

        # 1. Saldo inicial
        cash_flow_obj.create({
            'start_date': self.start_date,
            'end_date': self.end_date,
            'type': 'x1_initial_balance',
            'account_analytic_tag': None,
            'amount': initial_balance
        })

        # 2.1 Ingresos
        total_income = 0
        for inc in income:
            cash_flow_obj.create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'type': 'x21_income',
                'account_analytic_tag': inc['tag_id'],
                'amount': inc['amount']
            })

            total_income = total_income + inc['amount']
            
        # 2.2 Total ingresos
        cash_flow_obj.create({
            'start_date': self.start_date,
            'end_date': self.end_date,
            'type': 'x22_total_income',
            'account_analytic_tag': None,
            'amount': total_income
        })

        # 2.3 Disponible
        cash_flow_obj.create({
            'start_date': self.start_date,
            'end_date': self.end_date,
            'type': 'x3_available',
            'account_analytic_tag': None,
            'amount': initial_balance + total_income
        })

        # 3.1 Egresos
        total_expenses = 0
        for exp in expenses:
            cash_flow_obj.create({
                'start_date': self.start_date,
                'end_date': self.end_date,
                'type': 'x41_expenses',
                'account_analytic_tag': exp['tag_id'],
                'amount': exp['amount']
            })

            total_expenses = total_expenses + exp['amount']

        # 3.2 Total egresos
        cash_flow_obj.create({
            'start_date': self.start_date,
            'end_date': self.end_date,
            'type': 'x42_total_expenses',
            'account_analytic_tag': None,
            'amount': total_expenses
        })

        # 4. Saldo final
        cash_flow_obj.create({
            'start_date': self.start_date,
            'end_date': self.end_date,
            'type': 'x5_final_balance',
            'account_analytic_tag': None,
            'amount': initial_balance + total_income - total_expenses
        })

        ### Mostrar vista de lista
        return {
            'type': 'ir.actions.act_window',
            'name': "Flujo de efectivo del {} al {}".format(self.start_date,self.end_date),
            'res_model': 'pabs.cash.flow',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': self.env.ref('pabs_trialbalance_report.pabs_cash_flow_tree_view').id,
            'target': 'main',
            #'context': {'search_default_group_by_type': True},
            # 'domain': domain
        }