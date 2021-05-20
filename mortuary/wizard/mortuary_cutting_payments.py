# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import ValidationError
from dateutil import tz

class CuttingMortuaryPayments(models.TransientModel):
  _name = 'mortuary.cutting.payments'
  _description = 'Corte de pagos de funeraria'

  start_date = fields.Date(string='Fecha Inicial',
    default=fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General')),
    required=True)

  end_date = fields.Date(string='Fecha Final')

  def print_pdf(self):
    ### BUSCAMOS PAGOS DE FUNERARIA
    payment_obj = self.env['account.payment']
    ### GENERAMOS DOMINIO
    domain = [('state','=','posted'),
      ('reference','=','payment_mortuary')]
    ### SI TIENE FECHA FINAL
    if self.end_date:
      ### AGREGAMOS RANGO DE FECHAS
      domain.append(('payment_date','>=',self.start_date))
      domain.append(('payment_date','<=',self.end_date))
    ### SI NO
    else:
      ### AGREGAMOS LA UNICA FECHA EN EL DOMINIO
      domain.append(('payment_date','=',self.start_date))
    ### BUSCAMOS LOS PAGOS CON LOS PARAMETROS DE BUSQUEDA GENERADOS
    payment_ids = payment_obj.search(domain)
    ### SI NO SE ENCONTRÓ NINGÚN PAGO
    if not payment_ids:
      ### MENSAJE DE ERROR
      raise ValidationError("No existen pagos para procesar")
    ### AGREGAMOS PARAMETROS AL DATA
    data = {
      'start_date' : self.start_date,
      'end_date' : self.end_date,
      'payment_ids' : payment_ids.ids
    }
    ### RETORNAMOS EL REPORTE
    return self.env.ref('mortuary.report_mortuary_payments').report_action(self, data=data)

class CuttingMortuaryPDFReport(models.AbstractModel):
  _name = 'report.mortuary.mortuary_payment_report'

  @api.model
  def _get_report_values(self, docids, data):
    ### DECALRAMOS OBJETOS
    payment_obj = self.env['account.payment']
    ### SI VIENEN PAGOS
    if data.get('payment_ids'):
      ### OBTENEMOS LOS OBJETOS DE LOS PAGOS
      payment_ids = payment_obj.browse(data.get('payment_ids'))
    return {
      'data' : data,
      'payment_ids' : payment_ids
    }
