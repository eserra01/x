# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
  _inherit = 'stock.picking'

  def print_ticket(self):
    if self.type_transfer == 'as-ov':
      return self.env.ref('xmarts_funeraria.id_promoter_office').report_action(self, data={})
    if self.type_transfer == 'ov-as':
      return self.env.ref('xmarts_funeraria.id_office_promoter').report_action(self, data={})
    if self.type_transfer == 'cont-ov':
      return self.env.ref('xmarts_funeraria.id_contract_office').report_action(self, data={})