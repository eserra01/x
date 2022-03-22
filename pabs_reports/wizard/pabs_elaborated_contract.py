# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

TIPO_DE_CONTRATO = [
  ('traditional', 'Contrato fisico (entre fechas de elaboracion)'),
  ('digital', 'Contrato digital (entre fechas de corte)')
]

class ContractsElaboratedW1zard(models.TransientModel):
  _name = 'pabs.elaborated.contract.wizard'
  _description = 'Corte de contratos elaborados'

  contract_type = fields.Selection(selection=TIPO_DE_CONTRATO, string="Tipo de contrato", default='traditional')

  date_contract = fields.Date(string = 'Fecha Inicio de Corte', default = fields.Date.today())
  date_end = fields.Date(string = 'Fecha Final de Corte', default=fields.Date.today())

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

    ### Buscar contratos ###
    contract_ids = []
    titulo = ""
    if self.contract_type == 'traditional':
      titulo = "CORTE DE CONTRATOS ELABORADOS"

      contract_ids = contract_obj.search([
            ('state','=','contract'),
            ('invoice_date','>=',start_date),
            ('invoice_date','<=',end_date)
      ]).sorted(key=lambda r: r.name)
      
      contract_ids = contract_ids.filtered(lambda x: x.name != x.lot_id.name)
    else:
      titulo = "CORTE DE AFILIACIONES ELECTRÓNICAS"

      closing_ids = self.env['pabs.econtract.move'].search([
        ('company_id', '=', self.env.company.id),
        ('fecha_hora_cierre', '>=', start_date),
        ('fecha_hora_cierre', '<=', end_date),
        ('estatus', 'in', ('cerrado','confirmado') )
      ])
      
      ids = closing_ids.mapped('id_contrato').mapped('id')
      contract_ids = contract_obj.browse(ids).sorted(key=lambda r: r.name)

    if not contract_ids:
      raise ValidationError("No hay contratos")

    lot_ids = contract_ids.mapped('lot_id')
    warehouse_ids = lot_ids.mapped('warehouse_id').sorted(key=lambda r: r.name)
    warehouse_names = []

    plans_ids = lot_ids.mapped('product_id.product_tmpl_id.name')

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
        contract_id = contract_obj.search([('lot_id','=',record.id)],limit=1)
        advanced_commission = 0
        # Se buscan todos los stock.movs en los que el lot_id corresponda
        move_line_ids = self.env['stock.move.line'].search([('lot_id','=',record.id)])
        # Para cada mov
        for movl in move_line_ids:
          # Si se especificó adelantar comisión en el movimiento 
          if movl.move_id.toma_comision > 0:
            advanced_commission = movl.move_id.toma_comision
            break

        info.append({
          'product_id' : contract_id.name_service.name,
          'contract': contract_id.name,
          'price': contract_id.product_price,  
          'papeleria':contract_id.stationery,  
          'exc_inv': (contract_id.initial_investment - contract_id.stationery),  
          'advanced_commission': advanced_commission, 
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
      'data' : contract_data,
      'titulo': titulo
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



