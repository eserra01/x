# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging


_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
  _inherit = 'account.move'

  def invert_refund_invoices(self):
    account_move_obj = self.env['account.move']
    move_ids = account_move_obj.search([
      ('type','=','out_refund'),
      ('state','=','posted'),
      ('invoice_payment_ref','!=',False)])
    move_ids.sorted(key=lambda r: r.partner_id)
    last = False
    for move_id in move_ids:
      _logger.warning("El recibo: {} se esta procesando".format(move_id.invoice_payment_ref))
      if move_id.invoice_payment_ref != last:
        last = move_id.invoice_payment_ref
        continue
      else:
        move_id.button_draft()
        move_id.button_cancel()
