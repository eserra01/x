# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
  _inherit = 'account.move'

  contract_id = fields.Many2one(comodel_name='pabs.contract', string='Contrato')

  comission_output_ids = fields.One2many(comodel_name="pabs.comission.output", inverse_name="refund_id", string="Salidas de comisiones")

  def action_post(self):
    comission_tree_obj = self.env['pabs.comission.tree']
    context = self._context
    for line in self.line_ids:
      _logger.warning("los movimientos son: descripcion: {} \n Cuenta: {}".format(line.name, line.account_id.name))
    res = super(StockMove, self).action_post()
    if context.get('investment_bond'):
      NumeroContrato = self.contract_id.name,
      MontoPago = self.amount_total
      comission_tree_obj.CrearSalidasEnganche(
        IdPago=self.id, NumeroContrato=NumeroContrato, 
        MontoPago=MontoPago, TipoPago='Bono')
    return res

  def action_invoice_register_payment(self):
    return self.env['account.payment']\
      .with_context(default_contract=self.contract_id.id,active_ids=self.ids, active_model='account.move', active_id=self.id)\
      .action_register_payment()
      