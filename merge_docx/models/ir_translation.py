# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import models, fields, api, tools


class IrTranslation(models.Model):
    _inherit = 'ir.translation'

    @api.model
    def _get_source_query_name(self, name, types, lang):
        
        query = """ SELECT src FROM ir_translation
                    WHERE type in %s AND name=%s """
        params = (types, tools.ustr(name))
        return (query, params)

    @tools.ormcache('name', 'types', 'lang')
    def __get_source_name(self, name, types, lang):
        query, params = self._get_source_query_name(name, types, lang)
        self._cr.execute(query, params)
        res = self._cr.fetchone()
        return res and res[0] or u''

    @api.model
    def _get_source_name(self, name, types, lang):
        return self.__get_source_name(name, types, lang)
