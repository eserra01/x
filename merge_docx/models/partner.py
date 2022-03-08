# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def partner_data(self, line_break=False, abbreviation=False):
        footer = []
        if abbreviation:
            if self.phone:
                footer.append(_('Tel: ') + self.phone)
            if self.mobile:
                footer.append(_('Mob: ') + self.mobile)
            if self.email:
                footer.append(_('Mail: ') + self.email)
            if self.website:
                footer.append(_('Web: ') + self.website)
        else:
            if self.phone:
                footer.append(_('P. ') + self.phone)
            if self.mobile:
                footer.append(_('M. ') + self.mobile)
            if self.email:
                footer.append(_('E. ') + self.email)
            if self.website:
                footer.append(_('W. ') + self.website)
        if self.vat:
            footer.append((self.country_id.vat_label or 'TIN') + ': ' + self.vat)
        if line_break:
            return '\n'.join(footer)
        else:
            return '\t'.join(footer)

    def partner_data_icon(self, line_break=False):
        footer = []
        if self.phone:
            footer.append('\U0001F4DE' + ' ' + self.phone)
        if self.mobile:
            footer.append('\U0001F4F1' + ' ' + self.mobile)
        if self.email:
            footer.append('\u2709' + ' ' + self.email)
        if self.website:
            footer.append('\U0001f310' + ' ' + self.website)
        if self.vat:
            footer.append((self.country_id.vat_label or 'TIN') + ': ' + self.vat)
        if line_break:
            return '\n'.join(footer)
        else:
            return '\t'.join(footer)

    display_address = fields.Text(string='Display addres', compute="_compute_display_address")
    display_address_without_company = fields.Text(string='Display addres', compute="_compute_display_address")
    display_address_without_company_line = fields.Text(string='Display addres', compute="_compute_display_address")
    vat_label = fields.Char(string='Vat label', compute="_compute_vat_label")
    vat_label_full = fields.Char(string='Vat label full', compute="_compute_vat_label")
    data_line = fields.Text(string='Data line', compute="_data_partner")
    data_line_break = fields.Text(string='Data line break', compute="_data_partner")
    data_line_icon = fields.Text(string='Data line icon', compute="_data_partner")
    data_line_break_icon = fields.Text(string='Data line break icon', compute="_data_partner")
    data_line_abbr = fields.Text(string='Data line abbreviation', compute="_data_partner")
    data_line_break_abbr = fields.Text(string='Data line break abbreviation', compute="_data_partner")

    def _data_partner(self):
        for partner in self:
            partner.data_line = partner.partner_data()
            partner.data_line_break = partner.partner_data(line_break=True)
            partner.data_line_icon = partner.partner_data_icon()
            partner.data_line_break_icon = partner.partner_data_icon(line_break=True)
            partner.data_line_abbr = partner.partner_data(abbreviation=True)
            partner.data_line_break_abbr = partner.partner_data(line_break=True, abbreviation=True)

    def _compute_display_address(self):
        for partner in self:
            partner.display_address = partner._display_address()
            partner.display_address_without_company = partner._display_address(without_company=True)
            partner.display_address_without_company_line = partner.with_context(line_break=True)._display_address(without_company=True)
    
    def _compute_vat_label(self):
        for partner in self:
            partner.vat_label = partner.company_id.country_id.vat_label or 'TIN'
            partner.vat_label_full = '%s: %s' % (partner.vat_label, partner.vat) if partner.vat else ''

    def _display_address(self, without_company=False):
        res = super(ResPartner, self)._display_address(
            without_company=without_company)
        if self._context.get('line_break', False):
            while "\n\n" in res:
                res = res.replace('\n\n', ' | ')
                res = res.replace('\n', ' | ')
        else:
            while "\n\n" in res:
                res = res.replace('\n\n', '\n')
        return res
