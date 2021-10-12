# -*- coding: utf-8 -*-

from odoo import api, fields, models

class AccountTax(models.Model):
    _inherit = 'account.tax'

    inverse_tax_account = fields.Many2one(comodel_name='account.account', string='Contra Cuenta de IVA')