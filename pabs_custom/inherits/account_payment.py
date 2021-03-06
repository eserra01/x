# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

WAY_TO_PAY = [
  ('cash','Efectivo'),
  ('transfer', 'Transferencia'),
  ('credit_card','Tarjeta de Crédito/Débito')]

REFERENCE =[('payment','Abono'),
  ('stationary','Papelería'),
  ('surplus','Excedente'),
  ('transfer','Traspaso'),
  ('payment_mortuary','Cobro Funeraria')]

TYPE_CARD =[('tdc','Tarjeta de Crédito'),
  ('tdd','Tarjeta Débito')]
class account_Payment(models.Model):
    _inherit = 'account.payment'

    date_receipt = fields.Date(string="Fecha Recibo")

    reference = fields.Selection(selection  = REFERENCE, string="Referencia",required = True)

    Ecobro_receipt = fields.Char(string="Recibo Ecobro")

    debt_collector_code = fields.Many2one(comodel_name = 'hr.employee' ,string="Cobrador")

    contract = fields.Many2one(comodel_name = 'pabs.contract',string= "Contrato")

    way_to_pay =  fields.Selection(selection=WAY_TO_PAY,
      string = 'Forma de pago',
      required = True)

    payment_date = fields.Date(string="Fecha Cobranza")

    type_card_payment = fields.Selection(selection = TYPE_CARD,
      string= "Tipo de tarjeta")

    card_number = fields.Char(string = "Número de tarjeta", size = 4)

    card_expiration_date = fields.Date(string='Fecha de expiración')

    card_expiration_month = fields.Char(string = "Mes de vencimiento", size = 2)
    card_expiration_year = fields.Char(string = "Año de vencimiento", size = 4)

    number_phone = fields.Char(string = "Número de teléfono")

    authorization_number = fields.Char(string = "Número de autorización")

    transfer_date = fields.Date(string = "Fecha de transferencia")

    transfer_reference = fields.Char(string = "Referencia")

    comission_output_ids = fields.One2many(comodel_name="pabs.comission.output", inverse_name="payment_id", string="Salidas de comisiones")

    def post(self):
      comission_tree_obj = self.env['pabs.comission.tree']
      res = super(account_Payment, self).post()
      context = self._context
      IdPago = self.id
      if self.contract:
        CodigoCobrador = self.debt_collector_code.barcode
        NumeroContrato = self.contract.id
        MontoPago = self.amount or 0
        if context.get('stationery'):
          comission_tree_obj.CrearSalidasEnganche(
            IdPago=IdPago, NumeroContrato=NumeroContrato, 
            MontoPago=MontoPago, TipoPago='Papeleria')
        elif context.get('excedent'):
          comission_tree_obj.CrearSalidas(
            IdPago=IdPago, NumeroContrato=NumeroContrato,
            CodigoCobrador=CodigoCobrador, MontoPago=MontoPago,
            EsExcedente=True)
        else:
          comission_tree_obj.CrearSalidas(
            IdPago=IdPago, NumeroContrato=NumeroContrato,
            CodigoCobrador=CodigoCobrador, MontoPago=MontoPago,
            EsExcedente=False)
      return res

    def disassociate_payment(self):
      reconcile_model = self.env['account.partial.reconcile'].sudo()
      if self.move_line_ids:
        for obj in self.move_line_ids:
          if obj.credit > 0:
            reconcile_id = reconcile_model.search([
              ('credit_move_id','=',obj.id)])
            if reconcile_id:
              reconcile_id.unlink()

    def cancel(self):
      comission_tree_obj = self.env['pabs.comission.tree']
      self.disassociate_payment()
      res = super(account_Payment, self).cancel()
      IdPago = self.id
      if self.contract:
        NumeroContrato = self.contract.id
        comission_tree_obj.RevertirSalidas(
          IdPago=IdPago,NumeroContrato=NumeroContrato)
      return res 

    #Fields mortuary

    binnacle =fields.Many2one(comodel_name = 'pabs.mortuary',string= "Número de bitácora")

    user_create_payment = fields.Many2one(comodel_name = 'hr.employee' ,string="Persona que crea pago")
    
    balance_binnacle = fields.Float(string = "Saldo")

    date_of_death = fields.Date(string ="Fecha de defunción")

    place_of_death = fields.Char(string = "Lugar de fallecimiento")

    additional = fields.Char(string ="Adicionales")

    payment_person = fields.Char(string='Cliente que realizó el pago')

    @api.onchange('contract')
    def _onchange_contract(self):
      for rec in self:
        if rec.contract:
          rec.partner_id = rec.contract_id.partner_id.id
        