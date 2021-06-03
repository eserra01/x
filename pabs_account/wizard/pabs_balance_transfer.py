# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError

STATES = [
  ('draft','Borrador'),
  ('done', 'Hecho'),
  ('cancel','Cancelado')]

class PabsBalanceTransfer(models.Model):
  _name = 'pabs.balance.transfer'
  _description = 'Transferencia de Abonos'

  name = fields.Char(string='Referencia',
    default="TRASPASO ENTRE CONTRATOS")
  
  contract_origin_id = fields.Many2one(comodel_name='pabs.contract',
    string='Contrato Origen',
    required=True)

  origin_titular_name = fields.Char(string='Titular Origen',
    related="contract_origin_id.full_name")

  contract_dest_id = fields.Many2one(comodel_name='pabs.contract',
    string='Contrato Destino',
    required=True)

  dest_titular_name = fields.Char(string='Titular Destino',
    related="contract_dest_id.full_name")

  contract_origin_amount = fields.Float(string='Monto Máximo de Traspaso',
    compute="_calc_origin_amount")

  contract_dest_amount = fields.Float(string='Saldo Restante',
    compute="_calc_dest_amount")

  amount_transfer = fields.Float(string='Monto a Transferir',
    required=True)

  move_id = fields.Many2one(comodel_name='account.move',
    string='Asiento Contable')

  state = fields.Selection(selection=STATES,
    string='Estado',
    default='draft')
  
  company_id = fields.Many2one(
    'res.company', 'Compañia', required=True,
    default=lambda s: s.env.company.id, index=True)

  @api.depends('contract_origin_id')
  def _calc_origin_amount(self):
    for rec in self:
      balance = 0
      if rec.contract_origin_id:
        payments_amount = sum(rec.contract_origin_id.payment_ids.filtered(
          lambda r: r.state in ('posted','reconciled') and r.reference != 'stationary').mapped("amount"))
        refunds_amount = sum(rec.contract_origin_id.refund_ids.filtered(
          lambda r: r.state in ('posted','reconciled') and r.type != 'out_invoice').mapped("amount_total"))
        trasfers_amount = sum(rec.contract_origin_id.transfer_balance_ids.filtered(
          lambda r: r.parent_state in ('posted','reconciled')).mapped("balance_signed"))
        balance = (payments_amount + refunds_amount) + trasfers_amount
      rec.contract_origin_amount = balance

  @api.depends('contract_dest_id')
  def _calc_dest_amount(self):
    for rec in self:
      balance = 0
      if rec.contract_dest_id:
        balance = sum(rec.contract_origin_id.refund_ids.filtered(
          lambda r: r.type == 'out_invoice' and r.state in ('posted','reconciled')).mapped(
          'amount_residual'))
      rec.contract_dest_amount = balance

  def set_balance(self):
    ### DECLARACIÓN DE OBJETOS
    account_obj = self.env['account.move']
    ### VAR DE RECONCILIACIÓN
    reconcile = {}
    ### SI HAY ALGÚN MONTO
    if self.amount_transfer:
      ### VALIDAMOS QUE EL MONTO A TRANSFERIR NO SEA MAYOR QUE EL PERMITIDO DEL CONTRATO
      if self.amount_transfer > self.contract_origin_amount:
        ### MENSAJE DE ERROR
        raise ValidationError("No puedes traspasar más de ${:0,.0f} del contrato origen".format(self.contract_origin_amount))
      ### SI EL MONTO A TRANSFERIR ES MAYOR QUE EL SALDO DEL CONTRATO DESTINO
      if self.amount_transfer > self.contract_dest_amount:
        ### MENSAJE DE ERROR
        raise ValidationError("No puedes traspasar un monto mayor al permitido")
      ### BUSCAMOS LA COMPAÑIA
      company_id = self.env.company
      ### CUENTAS CONTABLES
      origin_partner = self.contract_origin_id.partner_id
      dest_partner = self.contract_dest_id.partner_id
      ### SACAMOS LA LINEA A CONCILIAR DE LA FACTURA
      invoice_conciled_line = self.contract_dest_id.refund_ids.filtered(
        lambda r: r.type == 'out_invoice' and r.state in ('posted','reconciled')).line_ids.filtered(
        lambda r: r.debit > 0).id
      reconcile.update({'debit_move_id' : invoice_conciled_line})
      ### GENERAMOS LA INFORMACIÓN
      lines = []
      ### AGREGAMOS LINEA DE ORIGEN
      lines.append((0,0,{
        'account_id' : origin_partner.property_account_receivable_id.id,
        'partner_id' : origin_partner.id,
        'name' : "Traspaso al contrato {}".format(self.contract_dest_id.name),
        'contract_id' : self.contract_origin_id.id,
        'debit' : self.amount_transfer,
      }))
      ### AGREGAMOS LINEA DESTNO
      lines.append((0,0,{
        'account_id' : dest_partner.property_account_receivable_id.id,
        'partner_id' : dest_partner.id,
        'name' : "Traspaso del contrato {}".format(self.contract_origin_id.name),
        'contract_id' : self.contract_dest_id.id,
        'credit' : self.amount_transfer,
      }))
      ### AGREGAMOS EL CUERPO DE LA PÓLIZA
      data = {
        'ref' : 'TRASPASO ENTRE CONTRATOS',
        'contract_id' : self.contract_dest_id.id,
        'date' : fields.Date.today(),
        'journal_id' : company_id.account_journal_id.id,
        'company_id' : company_id.id,
        'line_ids' : lines,
      }
      ### CREAMOS LA PÓLIZA
      move_id = account_obj.create(data)
      ### VALIDAMOS LA PÓLIZA
      move_id.with_context({'investment_bond' : True}).action_post()
      move_id.write({'contract_id' : False})
      ### SACAMOS LA LINEA DE LA PÓLIZA PARA CONCILIARLA CON EL DOCUMENTO DESTINO
      reconciled_line = move_id.line_ids.filtered(lambda r: r.credit > 0).id
      reconcile.update({'excedent' : reconciled_line})
      ### HACEMOS LA CONCILIACIÓN DEL DOCUMENTO
      self.set_trasfer_column(contract_id=self.contract_origin_id)
      self.contract_dest_id.reconcile_all(reconcile)
      self.move_id = move_id.id
      self.state = 'done'
      return {
        'name': "{}".format(self.contract_dest_id.name),
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'pabs.contract',
        'res_id' : self.contract_dest_id.id,
        'target': 'current'
      }

    ### SI NO HAY ALGÚN MONTO
    else:
      ### MENSAJE DE ERROR
      raise ValidationError("El monto a transferir debe de ser mayor que $0")

  def set_trasfer_column(self, contract_id=None):
    ### SI HAY UN CONTRATO
    if contract_id:
      ### BUSCAMOS EL PUESTO DE TRABAJO DE TRASP
      job_id = self.env['hr.job'].search([('name', '=', "TRASPASO")]).id
      ### SI NO HAY PUESTO DE TRABAJO
      if not job_id:
        ### ENVIAMOS MENSAJE DE ERROR
        raise ValidationError('No se encontró el puesto de "TRASPASO"')
      ### BUSCAMOS AL COMISIONISTA DE TRASPASO
      commission_agent = self.env['hr.employee'].search([('job_id','=',job_id)]).id
      ### SI NO HAY COMISIONISTA
      if not commission_agent:
        ### ENVIAMOS MENSAJE DE ERROR
        raise ValidationError('No se encontró el comisionista de "TRASPASO"')
      ### TRAEMOS EL ARBOL DE COMISIONES DEL CONTRATO
      comission_tree = contract_id.commission_tree.sorted(key=lambda r: r.pay_order)
      ### BUSCAMOS SI EL CONTRATO YA TIENE EL CONCEPTO DE TRASPASO
      comission_line = comission_tree.filtered(lambda r: r.job_id.id == job_id and r.comission_agent_id.id == commission_agent)
      ### SUMAMOS LOS TRASPASOS
      amount = sum(contract_id.transfer_balance_ids.mapped("balance_signed"))
      ### SI EXISTE LA LINEA LA MODIFICAMOS, SI NO, LA CREAMOS
      if comission_line:
        comission_line.write({
          'corresponding_commission' : amount,
          'remaining_commission' : 0,
          'commission_paid' : amount,
          'actual_commission_paid' : amount,
        })
      else:
        contract_id.commission_tree = [(0, 0, {
          'pay_order' : comission_tree[-1].pay_order + 1,
          'job_id' : job_id,
          'comission_agent_id' : commission_agent,
          'corresponding_commission' : amount,
          'remaining_commission' : 0,
          'commission_paid' : amount,
          'actual_commission_paid' : amount,
        })]

  def cancel_transfer(self):
    ### DECLARACIÓN DE OBJETOS
    comission_tree_obj = self.env['pabs.comission.tree']
    ### SÍ EXISTE MOVIMIENTO CONTABLE
    if self.move_id:
      ### SI HAY CONTRATO ORIGEN
      if self.contract_origin_id:
        ### BUSCAMOS EL PUESTO DE TRABAJO DE TRASP
        job_id = self.env['hr.job'].search([('name', '=', "TRASPASO")]).id
        ### SI NO HAY PUESTO DE TRABAJO
        if not job_id:
          ### ENVIAMOS MENSAJE DE ERROR
          raise ValidationError('No se encontró el puesto de "TRASPASO"')
        ### BUSCAMOS AL COMISIONISTA DE TRASPASO
        commission_agent = self.env['hr.employee'].search([('job_id','=',job_id)]).id
        ### SI NO HAY COMISIONISTA
        if not commission_agent:
          ### ENVIAMOS MENSAJE DE ERROR
          raise ValidationError('No se encontró el comisionista de "TRASPASO"')
        ### TRAEMOS EL ARBOL DE COMISIONES
        commission_tree = self.contract_origin_id.commission_tree.sorted(
          key=lambda r: r.pay_order)
        ### BUSCAMOS SI EL CONTRATO YA TIENE EL CONCEPTO DE TRASPASO
        comission_line = commission_tree.filtered(
          lambda r: r.job_id.id == job_id and r.comission_agent_id.id == commission_agent)
        ### MONTO DE TRASFERENCIA
        amount = self.amount_transfer
        ### SI EL MONTO ES IGUAL
        if comission_line.corresponding_commission == (amount * - 1 ):
          ### ELIMINAMOS LA LINEA
          comission_line.unlink()
        ### SI NO
        else:
          ### REDUCIMOS LOS VALORES DEL MONTO DE TRANSFERENCIA
          comission_line.write({
            'corresponding_commission' : comission_line.corresponding_commission - amount,
            'commission_paid' : comission_line.commission_paid - amount,
            'actual_commission_paid' : comission_line.actual_commission_paid - amount
          })
      if self.contract_dest_id:
        comission_tree_obj.RevertirSalidas(
          IdPago=False,RefundID=self.move_id.id,NumeroContrato=self.contract_dest_id.id)
      self.move_id.button_cancel()
      self.state = 'cancel'

