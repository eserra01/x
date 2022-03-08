# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import models, fields


class Company(models.Model):
    _inherit = 'res.company'

    display_address = fields.Text(related='partner_id.display_address')
    display_address_without_company = fields.Text(
        related='partner_id.display_address_without_company')
    display_address_without_company_line = fields.Text(
        related='partner_id.display_address_without_company_line')
    vat_label = fields.Char(related='partner_id.vat_label')
    vat_label_full = fields.Char(related='partner_id.vat_label_full')
    footer_line = fields.Text(related='partner_id.data_line')
    footer_line_break = fields.Text(related='partner_id.data_line_break')
    footer_line_icon = fields.Text(related='partner_id.data_line_icon')
    footer_line_break_icon = fields.Text(related='partner_id.data_line_break_icon')
    footer_line_abbr = fields.Text(related='partner_id.data_line_abbr')
    footer_line_break_abbr = fields.Text(related='partner_id.data_line_break_abbr')
