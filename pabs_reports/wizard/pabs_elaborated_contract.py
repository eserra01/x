# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ContractsElaboratedW1zard(models.TransientModel):
  _name = 'pabs.elaborated.contract.wizard'
  _description = 'Corte de contratos elaborados'

  date_contract = fields.Date(string = 'Fecha Inicio de Corte',
    default = fields.Date.today())

  date_end = fields.Date(string = 'Fecha Final de Corte',
    default=fields.Date.today())

  def get_contracts_per_day(self):
    ### VARIABLE DE DATOS PARA EL PICKING
    contract_data = {}
    #OBJETOS
    contract_obj = self.env['pabs.contract']  

    #ENCABEZADO PARA EL REPORTE
    """day = self.date_contract.strftime('%d')
    month = MONTHS.get(self.date_contract.strftime('%B'))
    year = self.date_contract.strftime('%Y')"""

    params = {
    'start_date' : self.date_contract,
    'end_date': self.date_end
    }

      ### PARAMETROS DE BUSQUEDA EN LA FECHA
    start_date = '{} 00:00:00'.format(self.date_contract)
    end_date = '{} 23:59:59'.format(self.date_end)

    contract_ids = contract_obj.search([
          ('state','=','contract'),
          ('invoice_date','>=',start_date),
          ('invoice_date','<=',end_date)])

    lot_ids = [x.lot_id for x in contract_ids]
    warehouse_ids = [x.warehouse_id for x in lot_ids] #lot_ids.filtered(lambda x: x.warehouse_ids)
    warehouse_ids = set(warehouse_ids)
    warehouse_names = []

    plans_ids = [x.product_id.product_tmpl_id.name for x in lot_ids]
    plans_ids = set(plans_ids)
    plan_name =[]
    

    
    

    for rec in warehouse_ids:
      warehouse_name = rec.name
      warehouse_names.append(warehouse_name)
      record_ids = []
      for req in lot_ids:
        if req.warehouse_id.id == rec.id:
          record_ids.append(req)

        

      ### GUARDAR LA LISTA DE CADA ALMACÉN
      info = []
      ### recorremos las solicitudes
      for record in record_ids:
        contract_id = contract_obj.search([
          ('lot_id','=',record.id)],limit=1)
        info.append({
          'product_id' : contract_id.name_service.name,
          'contract': contract_id.name,
          'price': contract_id.product_price,  
          'papeleria':contract_id.stationery,  
          'exc_inv': (contract_id.initial_investment - contract_id.stationery),  
          'initial_investment':contract_id.initial_investment,
          'bono':contract_id.investment_bond,
          'solicitud':contract_id.lot_id.name,  
          'promoter':contract_id.lot_id.employee_id.name
          })
      contract_data.update({
        warehouse_name : info
      })
    
    data = {
      'params' : params,
      'headers' : warehouse_names,
      'data' : contract_data
    }
    return self.env.ref('pabs_reports.elaborated_contracts_print').report_action(self, data=data)

class ElaboratedContract(models.AbstractModel):
  _name = 'report.pabs_reports.elaborated_contracts'

  @api.model
  def _get_report_values(self, docids, data):
    headers = data.get('headers')
    logo = self.env.user.company_id.logo
    user = self.env.user.name
    info = data['data']
    return {
      'user' : user,
      'logo' : logo,
      'headers' : headers,
      'data' : data,
      'info' : info,
    }



