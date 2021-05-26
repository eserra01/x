# -*- coding: utf-8 -*-

from odoo import api, fields, models

class PabsContract(models.Model):
  _inherit = 'pabs.contract'

  def _calc_paid_balance(self):
    for rec in self:
      amount_payments = sum(rec.payment_ids.filtered(
        lambda r: r.state in ('posted','reconciled')).mapped(
        'amount'))
      amount_refunds = sum(rec.refund_ids.filtered(
        lambda r: r.state == 'posted' and r.type == 'out_refund').mapped(
        'amount_total'))
      amount_transfers = sum(rec.transfer_balance_ids.filtered(
        lambda r: r.parent_state in ('posted','reconciled')).mapped('balance_signed'))
      rec.paid_balance = amount_payments + amount_refunds + amount_transfers