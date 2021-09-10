# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class AcccountMove(models.Model):
  _inherit = 'account.move'

  contract_id = fields.Many2one(comodel_name='pabs.contract', string='Contrato')

  comission_output_ids = fields.One2many(comodel_name="pabs.comission.output", inverse_name="refund_id", string="Salidas de comisiones")

  def action_post(self):
    comission_tree_obj = self.env['pabs.comission.tree']
    context = self._context
    res = super(AcccountMove, self).action_post()
    if context.get('investment_bond') or (self.type in ('out_refund','entry') and self.contract_id):
      NumeroContrato = self.contract_id.id,
      MontoPago = self.amount_total
      if self.contract_id.company_id != 9:
        comission_tree_obj.CrearSalidasEnganche(IdPago=self.id, NumeroContrato=NumeroContrato, MontoPago=MontoPago, TipoPago='Bono')
    return res

  def action_invoice_register_payment(self):
    return self.env['account.payment']\
      .with_context(default_contract=self.contract_id.id,active_ids=self.ids, active_model='account.move', active_id=self.id)\
      .action_register_payment()

  def button_cancel(self):
    comission_tree_obj = self.env['pabs.comission.tree']
    res = super(AcccountMove, self).button_cancel()
    if self.type in ('out_refund','entry'):
      if self.contract_id and self.contract_id.company_id != 9:
        NumeroContrato = self.contract_id.id,
        comission_tree_obj.RevertirSalidas(
          IdPago=False,RefundID=self.id,NumeroContrato=NumeroContrato)
    return res

class AccountMoveLine(models.Model):
  _inherit = 'account.move.line'

  contract_id = fields.Many2one(comodel_name='pabs.contract',
    string='Contrato')

  balance_signed = fields.Float(string='Importe Con signo',
    compute='_calc_balance_signed')

  def _calc_balance_signed(self):
    for rec in self:
      if rec.debit or rec.credit:
        rec.balance_signed = (rec.balance * - 1)
  