# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, models, fields
from odoo.exceptions import ValidationError
import pytz
tz = pytz.timezone('America/Mexico_City')

STATUS = [
  ('generated','Ya Existe una Póliza prevía'),
  ('not_generated','No Existe Póliza Creada')
]

class PabsAccountMove(models.TransientModel):
  _name = 'pabs.investment.surplus'
  _descripcion = 'Generador de Polizas de Inversiones y Excedentes PABS'

  ecobro_date = fields.Date(string='Fecha de elaboración',
    required=True, default=datetime.now(tz))

  count_contract = fields.Integer(string='Contratos')

  initial_investment = fields.Float(string='Monto de inversiones iniciales')

  excedent = fields.Float(string='Excedentes')

  total = fields.Float(string='Total')

  status = fields.Selection(selection=STATUS,
    compute="calc_data",
    string='Estado de póliza')

  hide = fields.Boolean(string='Hide',
    default=True,
    compute="_calc_hide")

  @api.onchange('count_contract','initial_investment','excedent','total')
  def _calc_hide(self):
    for rec in self:
      if rec.count_contract or rec.initial_investment or rec.excedent:
        rec.hide = False
      else:
        rec.hide = True

  @api.onchange("ecobro_date")
  def calc_data(self):
    ### DECLARAMOS OBJETOS
    contract_obj = self.env['pabs.contract']
    ### guardamos el dato
    date = self.ecobro_date
    ### buscamos los contratos por día
    contract_ids = contract_obj.search([
      ('state','=','contract'),
      ('invoice_date','=',date)])

    ### Quitar los contratos de tipo Afiliación electrónica
    contract_ids = contract_ids.filtered(lambda x: x.name != x.lot_id.name)

    ### Sí no hay contratos
    if not contract_ids:
      self.count_contract = 0
      self.initial_investment = 0
      self.excedent = 0
      self.total = 0
    ### Rellenamos el dato de los contratos por día
    self.count_contract = len(contract_ids)
    ### traemos todos los pagos
    payment_ids = contract_ids.mapped('payment_ids')
    ### Filtramos y sumamos todos los que son por inversión inicial
    initial_investment = sum(payment_ids.filtered(lambda r: r.reference == 'stationary').mapped('amount'))
    self.initial_investment = initial_investment
    ### Filtramos y sumamos todos los que son por excedentes
    excedent = sum(payment_ids.filtered(lambda r: r.reference == 'surplus').mapped('amount'))
    self.excedent = excedent
    ### Sumamos los totales de inversión inicial y excedente
    total = initial_investment + excedent
    self.total = total
    ### Buscamos que no exista una póliza generada previamente
    name = "INVERSIONES INICIALES Y EXCEDENTES {}".format(date)
    
    res = self.validate_account_move(name)
    if res:
      self.status = 'generated'
    else:
      self.status = 'not_generated'

    return {
      'initial_investment' : initial_investment,
      'excedent' : excedent,
      'total' : total
    }

  def validate_account_move(self,name):
    ### Generación de objetos.
    move_obj = self.env['account.move']
    message = ""
    ### Buscamos si ya se generó la póliza de este concepto
    move_id = move_obj.search([('ref','=',name)])
    ### Si la poliza se encuentra en borrador o validada la retornamos
    if move_id.state in ('posted','draft'):
      return move_id
    else:
      return False

  def get_lines(self):
    ### DECLARAMOS OBJETOS
    contract_obj = self.env['pabs.contract']
    ### guardamos el dato
    date = self.ecobro_date
    ### Nombre de la poliza
    name = "INVERSIONES INICIALES Y EXCEDENTES {}".format(date)
    ### Buscamos las cuentas
    company_id = self.env.user.company_id
    initial_investment = company_id.initial_investment_account_id.id
    excedent = company_id.excedent_account_id.id
    bank = company_id.bank_account_id.id
    journal_id = company_id.account_journal_id.id
    ### Validamos que existan todos los parametros necesarios.
    if not initial_investment:
      raise ValidationError(("No se puede generar la póliza porque no se encontra la cuenta de inversiones iniciales configurada"))
    if not excedent:
      raise ValidationError(("No se puede generar la póliza porque no se encontra la cuenta de excedentes configurada"))
    if not bank:
      raise ValidationError(("No se puede generar la póliza porque no se encontra la cuenta banco configurada"))
    if not journal_id:
      raise ValidationError(("No se puede generar la póliza porque no se encontró el diario configurado"))        
    lines = []
    ### buscamos los contratos por día
    contract_ids = contract_obj.search([
      ('state','=','contract'),
      ('invoice_date','=',date)])
    warehouse_ids = contract_ids.mapped('warehouse_id')
    for warehouse_id in warehouse_ids:
      if not warehouse_id.analytic_account_id:
        raise ValidationError(("El almacén {} no tiene configurada una cuenta analitica".format(warehouse_id.name)))
      contracts = contract_ids.filtered(lambda r: r.warehouse_id.id == warehouse_id.id)

      # Si es fiscal
      if self.env.company.apply_taxes:
        # Buscar impuesto de IVA
        impuesto_IVA = self.env['account.tax'].search([('name','=','IVA'), ('company_id','=', self.env.company.id)])
        if not impuesto_IVA:
            raise ValidationError("No se encontró el impuesto con nombre IVA")

        # Buscar contra cuenta de IVA
        if not impuesto_IVA.inverse_tax_account:
          raise ValidationError("No se ha definido la contra cuenta de IVA en el impuesto IVA")

        factor_iva = 1 + (impuesto_IVA.amount / 100)

        #Linea de Inversiones iniciales
        monto_inversion = sum(contracts.payment_ids.filtered(lambda r : r.reference == 'stationary').mapped('amount'))
        lines.append([0,0,{
          'account_id' : initial_investment,
          'name' : name,
          'debit' : 0,
          'credit' : round( monto_inversion / factor_iva, 2),
          'analytic_account_id' : warehouse_id.analytic_account_id.id or False,
        }])

        #Linea de Excedentes
        monto_excedente = sum(contracts.payment_ids.filtered(lambda r: r.reference == 'surplus').mapped('amount'))
        lines.append([0,0,{
          'account_id' : excedent,
          'name' : name,
          'debit' : 0,
          'credit' : round( monto_excedente / factor_iva, 2),
          'analytic_account_id' : warehouse_id.analytic_account_id.id or False,
        }])

        #Linea de IVA (Una linea sumando inversiones y excedentes)
        lines.append([0,0,{
          'account_id' : impuesto_IVA.inverse_tax_account.id,
          'name' : "IVA",
          'debit' : 0,
          'credit' : round( (monto_inversion + monto_excedente) - (round( monto_inversion / factor_iva, 2) + round( monto_excedente / factor_iva, 2)), 2),
          'tax_ids' : [(4, impuesto_IVA.id, 0)],
        }])
        
      else:
        ### INVERSIONES INICIALES
        lines.append([0,0,{
          'account_id' : initial_investment,
          'name' : name,
          'debit' : 0,
          'credit' : sum(contracts.payment_ids.filtered(lambda r : r.reference == 'stationary').mapped('amount')),
          'analytic_account_id' : warehouse_id.analytic_account_id.id or False,
        }])
        ### EXCEDENTES
        lines.append([0,0,{
          'account_id' : excedent,
          'name' : name,
          'debit' : 0,
          'credit' : sum(contracts.payment_ids.filtered(lambda r: r.reference == 'surplus').mapped('amount')),
          'analytic_account_id' : warehouse_id.analytic_account_id.id or False,
        }])
    ### Linea de banco
    lines.append([0,0,{
      'account_id' : bank,
      'name' : name,
      'debit' : self.total,
      'credit' : 0
    }])
    return {
      'ref' : name,
      'date' : date,
      'journal_id' : journal_id,
      'company_id' : company_id.id,
      'line_ids' : lines
    }
    
  def generate_account_move(self):
    ### Generación de objetos
    move_obj = self.env['account.move']
    ### guardamos el dato
    date = self.ecobro_date
    name = "INVERSIONES INICIALES Y EXCEDENTES {}".format(date)
    ### Validamos que no puedan crear más de 1 póliza bajo este concepto
    res = self.validate_account_move(name)
    if res:
      move_id = res
    else:
      ### Información de la póliza
      data = self.get_lines()
      ### Creamos la poliza
      move_id = move_obj.create(data)
      ### Validamos la póliza
      move_id.action_post()
    ### Retornamos la póliza
    return {
      'name' : name,
      'view_type' : 'form',
      'view_mode' : 'form',
      'res_model' : 'account.move',
      'view_id' : self.env.ref('account.view_move_form').id,
      'res_id' : move_id.id,
      'type': 'ir.actions.act_window',
    }
