# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz

class PABSCollectorReport(models.TransientModel):
  _name = 'pabs.collector.report.wizard'
  _description = 'Reporte de Cobradores por día'

  first_date = fields.Date(string='Fecha de inicio',
    default=fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General')),
    required=True)

  end_date = fields.Date(string='Fecha de Fin',
    default=fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General')))

  def get_collectors_report(self):
    ### DECLARACION DE OBJETOS
    payment_obj = self.env['account.payment']

    params = {
    'start_date' : self.first_date,
    'end_date': self.end_date
    }

    ### BUSCAMOS TODOS LOS PAGOS EN EL RANGO DE DÍAS
    payment_ids = payment_obj.search([
      ('state','in',('posted','sent','reconciled')),
      ('reference','=','payment'),
      ('payment_date','>=',self.first_date),
      ('payment_date','<=',self.end_date)])
    ### SI NO ENCUENTRA PAGOS
    if not payment_ids:
      ### ENVIAMOS MENSAJE DE ERROR
      raise ValidationError((
        "No se encontraron pagos en el rango de fechas seleccionado"))
    
    data = {'params' : params}
    data_info = {}
    collector_ids = payment_ids.mapped('debt_collector_code')
    for collector_id in collector_ids:
      payment_lst = []
      payments = payment_ids.filtered(lambda x: x.debt_collector_code.id == collector_id.id)
      data_detail = {
        'counting' : len(payments),
        'total' : "${:,.2f}".format(int(sum(payments.mapped('amount'))))
      }
      data_info.update({
        collector_id.name : data_detail
      })
    data.update({
      "info" : data_info,
      "counting" : len(payment_ids),
      "total" : "${:,.2f}".format(int(sum(payment_ids.mapped('amount'))))
    })

    return self.env.ref('pabs_reports.collector_concentrated_report').report_action(self, data=data)

class CollectorReport(models.AbstractModel):
  _name = 'report.pabs_reports.collector_concentrated_report_template'

  @api.model
  def _get_report_values(self, docids, data):
    logo = self.env.user.company_id.logo
    return {
      'logo' : logo,
      'data' : data
    }

