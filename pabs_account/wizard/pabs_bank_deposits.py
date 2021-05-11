# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, models, fields
from odoo.exceptions import ValidationError
import requests
import json
import pytz
from odoo.addons.pabs_sync_ecobro.models.pabs_ecobro_sync import URL
tz = pytz.timezone('America/Mexico_City')

URL.update({
  'DEPOSIT' : '/controldepositos/getAfectedDeposits',
  'DEPOSIT_SYNC' : '/controldepositos/updateAfectedDepositsAsSynced',
})

class PabsBankDeposits(models.TransientModel):
  _name = 'pabs.bank.deposits'

  name = fields.Char(string='Nombre')

  ecobro_date = fields.Date(string='Fecha de deposito',
    required=True, default=datetime.now(tz))

  total = fields.Float(string='Total deposito',
    compute='_calc_total')

  deposit_line_ids = fields.One2many(comodel_name='pabs.bank.deposits.line',
    inverse_name='deposit_id',
    string='Depositos')

  def _calc_total(self):
    self.total = sum(self.deposit_line_ids.mapped('amount')) or 0

  def get_deposits(self):
    ### ENCABEZADO DE LA PETICIÓN
    headers = {'Content-type': 'application/json'}
    ### LIMPIAMOS LA LISTA
    self.deposit_line_ids = [(5,0,0)]
    ### INSTANCIACIÓN A MODELO DE ECOBRO SYNC
    sync_obj = self.env['pabs.ecobro.sync']
    ### ID DE LA COMPAÑIA ACTIVA
    company_id = self.env.company.id
    ### MÉTODO PARA GENERAR LA URL
    url = sync_obj.get_url(company_id, "DEPOSIT")
    ### SI NO HAY URL
    if not url:
      ### MENSAJE DE ERROR
      raise ValidationError("No se pudo generar la URL de petición, favor de comunicarse con sistemas.")
    ### INTENTAMOS
    try:
      ### PARAMETROS PARA EL WEBSERVICE
      payload = {
        'startDate' : self.ecobro_date.strftime("%Y-%m-%d"),
        'endDate' : self.ecobro_date.strftime("%Y-%m-%d")
      }
      ### ENVIAMOS LOS PARAMETROS A LA URL GENERADA BAJO EL METODO POST
      req = requests.post(url, json=payload, headers=headers)
      response = json.loads(req.text)
      rec_data = []
      for rec in response['result']:
        rec_data.append([0,0,{
          'bank_name' : rec['NombreBanco'],
          'employee_code' : rec['CobradorECobro'],
          'debt_collector' : rec['Cobrador'],
          'amount' : float(rec['MontoDeposito']),
          'deposit_date' : rec['FechaDeposito'],
          'cashier' : rec['Cajero'],
          'ref' : rec['ReferenciaDeposito'],
          'id_ref' : rec['ids'],
        }])
      self.deposit_line_ids = rec_data
      self.name = 'Depositos del {}'.format(self.ecobro_date)
    except Exception as e:
      raise ValidationError("Información recibida: {}".format(e))

  def get_account_move(self):
    ### Encabezado de la petición
    headers = {'Content-type': 'application/json'}
    ### CREANDO OBJETOS
    move_obj = self.env['account.move']
    sync_obj = self.env['pabs.ecobro.sync']
    ### GENERANDO LA POLIZA DE LOS DEPOSITOS
    name = 'Depositos del {}'.format(self.ecobro_date)
    ### Obtenemos la compañia
    company_id = self.env.company
    ####  Obtenemos la URL
    url = sync_obj.get_url(company_id.id, "DEPOSIT_SYNC")
    ### Si no conseguimos la url
    if not url:
      ### Mensaje de error
      raise ValidationError("No se pudo generar la URL, favor de verificarlo con sistemas")
    ### Obtenemos el diario configurado
    journal_id = company_id.account_journal_id.id
    ### Obtenemos la cuenta analitica configurada
    analytic_account_id = company_id.deposit_analytic_account_id.id
    ### Si no viene la cuenta analitica
    if not analytic_account_id:
      ### Mensaje de error
      raise ValidationError("No se encuentra configurada la cuenta análitica de depositos, favor de configurar una e intentarlo nuevamente.")
    ### Agregamos array del encabezado de la póliza
    data = {
      'ref' : name,
      'date' : self.ecobro_date,
      'journal_id' : journal_id,
      'company_id' : company_id.id,
    }
    ids_line = []
    lines = []
    ### Reccorremos detalles
    for line in self.deposit_line_ids:
      ids_line.append(line.id_ref)
      if line.account_id:
        lines.append([0,0,{
          'account_id' : line.account_id.id,
          'name' : '{} - ref {}'.format(line.debt_collector, line.ref),
          'debit' : line.amount,
          'credit' : 0,
        }])
      else:
        raise ValidationError("No se encontró la cuenta para el banco: {}".format(line.bank_name))
    if company_id.inverse_account:
      lines.append([0,0,{
        'account_id' : company_id.inverse_account.id,
        'name' : 'Depósitos PABS',
        'debit' : 0,
        'credit' : self.total,
        'analytic_account_id' : analytic_account_id,
      }])
    data.update({'line_ids' : lines})
    ### Creamos la póliza
    move_id = move_obj.create(data)
    ### Validamos la póliza
    move_id.action_post()
    ### Generamos encabezado de la petición
    payload = {
      'doc_entry' : move_id.id,
      'result' : ids_line,
    }
    ### Enviamos la petición
    req = requests.post(url, json=payload, headers=headers)
    ### leemos la respuesta de la petición
    response = json.loads(req.text)
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


class PabsBankDepositsLine(models.TransientModel):
  _name = 'pabs.bank.deposits.line'

  id_ref = fields.Char(string='id')

  bank_name = fields.Char(string='Banco')

  employee_code = fields.Char(string='Código')

  debt_collector = fields.Char(string='Cobrador')

  amount = fields.Float(string='Monto')

  deposit_date = fields.Date(string='Fecha Depósito')

  cashier = fields.Char(string='Cajero')

  ref = fields.Char(string='Referencia')

  account_id = fields.Many2one(comodel_name='account.account',
    compute="_calc_account",
    string='Cuenta Contable')

  deposit_id = fields.Many2one(comodel_name='pabs.bank.deposits',
    string='Depósito')

  @api.depends('bank_name')
  def _calc_account(self):
    for rec in self:
      if rec.bank_name:
        line = self.env.company.bank_account_ids.filtered(lambda r: r.name == rec.bank_name)
        if line:
          rec.account_id = line.account_id.id
