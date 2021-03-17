# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz

class PABSCommissionsToRecover(models.TransientModel):
  _name = 'pabs.commissions.recovery'
  _description = 'Reporte de Comisiones por Recuperar'

  start_date = fields.Date(string='Fecha de inicio',
    default=fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General')),
    required=True)

  end_date = fields.Date(string='Fecha de Fin')

  def print_pdf_report(self):
    ### ARMANDO LOS PARAMETROS
    data = {
      'start_date' : self.start_date,
      'end_date' : self.end_date,
    }
    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_reports.commissions_recovery_pdf_report').report_action(self, data=data)

class CollectorReport(models.AbstractModel):
  _name = 'report.pabs_reports.commissions_recovery_pdf_template'

  @api.model
  def _get_report_values(self, docids, data): 
    ### PARAMETRO DE LOGO DE LA EMPRESA
    logo = self.env.user.company_id.logo

    ### DECLARACION DE OBJETOS
    contract_obj = self.env['pabs.contract']
    job_obj = self.env['hr.job']

    ### OBTENEMOS LOS PARAMETROS DE BUSQUEDA
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    ### GENERAMOS EL DOMINIO DE BUSQUEDA
    ### SI TIENE FECHA FIN ES UN RANGO DE FECHAS
    if end_date:
      params = [
      ('invoice_date','>=', start_date),
      ('invoice_date','<=', end_date)]
    ### SI NO, BUSCAMOS LAS SALIDAS DE UN MISMO DÍA
    else:
      params = [
      ('invoice_date','=',start_date)]


    ### BUSCAMOS LOS CONTRATOS GENERADOS EN ESAS FECHAS
    contract_ids = contract_obj.search(params)

    ### FILTRAMOS TODOS LOS PROMOTORES
    employee_ids = contract_ids.mapped('sale_employee_id')

    ### AQUI GUARDAREMOS TODA LA INFORMACIÓN
    info = {}

    ### RECORREMOS TODOS LOS PROMOTORES
    for employee_id in employee_ids:

      ### DECLARAMOS LA VARIABLE QUE VA A CONTENER LA INFORMACIÓN
      records = []

      ### filtramos todos los contratos pertenecientes a ese promotor
      contracts= contract_ids.filtered(lambda k: k.sale_employee_id.id == employee_id.id)

      ### RECORREMOS LA INFORMACIÓN DE LOS CONTRATOS
      for contract in contracts:
        job_id = job_obj.search([
          ('name','=','ASISTENTE SOCIAL')])
        commission_line = contract.commission_tree.filtered(lambda k: k.job_id.id == job_id.id)
        records.append({
          'date' : contract.invoice_date or "",
          'contract' : contract.name or "",
          'partner' : contract.full_name or "", 
          'colony' : contract.toll_colony_id.name or "",
          'municipality' : contract.toll_municipallity_id.name or "",
          'phone' : contract.phone_toll or "",
          'collector' : contract.debt_collector.name or "",
          'commission' : commission_line.corresponding_commission or 0,
          'commission_paid' : commission_line.commission_paid or 0,
          'commission_x_paid' : commission_line.remaining_commission or 0,
        })
      info.update({
        employee_id.name : records
      })

    return {
      'logo' : logo,
      'data' : data,
      'info' : info
    }