# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ResCompany(models.Model):
  _inherit = 'res.company'

  initial_investment_account_id = fields.Many2one(comodel_name='account.account',
    string='Cuenta de Inversiones iniciales')

  excedent_account_id = fields.Many2one(comodel_name='account.account',
    string='Cuenta de Excedentes')

  bank_account_id = fields.Many2one(comodel_name='account.account',
    string='Cuenta de banco')

  account_journal_id = fields.Many2one(comodel_name='account.journal',
    string='Diario')

  inverse_account = fields.Many2one(comodel_name='account.account',
    string='Contra Cuenta de depositos')

  bank_account_ids = fields.One2many(comodel_name='pabs.bank.account',
    inverse_name='company_id',
    string='Cuentas de Banco')

  deposit_analytic_account_id = fields.Many2one(comodel_name='account.analytic.account',
    string='Cuenta analitica de deposito')

  pabs_account_analytic_tag_id = fields.Many2one(comodel_name='account.analytic.tag',
    string='Etiqueta analitica depósitos PABS')
  
  odoo_account_analytic_tag_id = fields.Many2one(comodel_name='account.analytic.tag',
    string='Etiqueta analitica depósitos ODOO')

  legal_signature = fields.Binary(string='Firma Apoderado Legal')

  apply_taxes = fields.Boolean(string = "Aplicar impuestos", default = False)

class PabsBankAccount(models.Model):
  _name = 'pabs.bank.account'
  _description = 'Cuentas de banco para ecobro'

  name = fields.Char(string='Banco',
    required=True)

  account_id = fields.Many2one(comodel_name='account.account',
    string='Cuenta Contable',
    required=True)

  company_id = fields.Many2one(comodel_name='res.company',
    string='Compañia')
  