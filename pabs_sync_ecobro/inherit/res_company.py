# -*- coding: utf-8 -*-

COMPANIES = [
  ('support','Apoyo'),
  ('cooperative','Cooperativa'),
  ('mortuary' , 'Funeraria')]

from odoo import api, fields, models

class ResCompany(models.Model):
  _inherit = 'res.company'

  ecobro_ip = fields.Char(string = 'IP WebService')

  extension_path = fields.Char(string = 'Path de Conexión')

  path_update_address = fields.Char(string = 'Path webservice (datos)')
  path_update_address_confirm = fields.Char(string = 'Path webservice (confirmar)')
  log_address_ids = fields.One2many(comodel_name="update.address.log", inverse_name="company_id",string="Log de cambio de direcciones", readonly=True)

  contract_companies = fields.One2many(comodel_name='contract.companies',
    inverse_name='company_id',
    string='Compañia de Contrato')

  companies = fields.One2many(comodel_name = 'companies',
    inverse_name = 'company_id',
    string = 'Compañias de sincronización')

class ContractCompanies(models.Model):
  _name = 'contract.companies'

  company_id = fields.Many2one(comodel_name = 'res.company',
    string='Comañia')

  serie = fields.Char(string = 'Número de empresa',
    required = True)

  type_company = fields.Selection(selection = COMPANIES,
    string = 'Tipo de Compañia',
    required = True)

  _sql_constraints = [
    ('unique_companie',
      'UNIQUE(type_company, company_id)',
      'No se puede crear el registro: ya existe una fila con los mismos datos -> [Tipo de compañia, Compañia]'
    )
  ]

class Companies(models.Model):
  _name = 'companies'

  company_id = fields.Many2one(comodel_name = 'res.company',
    string = 'Compañia')

  serie = fields.Char(string = 'Número de empresa',
    required = True)

  type_company = fields.Selection(selection = COMPANIES,
    string = 'Tipo de Compañia',
    required = True)

  _sql_constraints = [
    ('unique_companie',
      'UNIQUE(type_company, company_id)',
      'No se puede crear el registro: ya existe una fila con los mismos datos -> [Tipo de compañia, Compañia]'
    )
  ]