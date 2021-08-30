# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
  _inherit = 'account.move'

  def print_account(self):
    return self.env.ref('pabs_reports.accounting_policy_report').report_action(self, data={'ids' : self.ids})
    
class AccountingPolicyReport(models.AbstractModel):
  _name = 'report.pabs_reports.accounting_policy_template'

  @api.model
  def _get_report_values(self, docids, data):
    move_obj = self.env[data.get('context').get('active_model')]
    move_ids = move_obj.browse(data.get('context').get('active_ids'))
    return {
      'docs' : move_ids,
    }