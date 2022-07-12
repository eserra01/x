# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz

TIPO_DE_REPORTE = [
  ('realizados', 'Contratos realizados (fechas en que los contratos fueron realizados)'),
  ('no_realizados', 'Contratos no realizados (fechas de oficina de cobranza)'),
  ('cancelados', 'Contratos cancelados (fechas en que los contratos fueron cancelados)')
]

# -- REALIZADOS --
# Parámetros company_id, fecha minima de creacion de contratos nuevo esquema, fecha inicial de estatus, fecha final de estatus
# Funcion: model.RegistrarContratosRealizados(12, '2021-11-01', '2022-05-01', '2022-05-31')

# -- NO REALIZADOS --
# Parametros: company_id, factor, echa minima de creacion de contratos nuevo esquema, fecha_inicial de abonos, fecha final de abonos
# Funcion: model.RegistrarContratos(12, 500000, '2021-11-01', '2022-05-01', '2022-05-31')

# -- CANCELADOS --
# Parámetros: company_id, fecha minima de creacion de contratos nuevo esquema, fecha inicial de estatus, fecha_final de estatus
# Funcion: model.RegistrarContratosCancelados(12, '2021-11-01', '2022-05-01', '2022-05-31')

class PabsTaxesCreateWizard(models.TransientModel):
  _name = 'pabs.taxes.create.wizard'
  _description = 'Wizard para crear registros de impuestos'

  report_type = fields.Selection(selection=TIPO_DE_REPORTE, string="Tipo de registro", default='realizados')

  start_date = fields.Date(string='Fecha inicial', default = fields.date.today(),required=True)
  end_date = fields.Date(string='Fecha final', default = fields.date.today(), required=True)

  factor = fields.Float(string="Factor")

  def CrearRegistros(self):
    company_id = self.env.company.id

    #HARCODED !!!
    fecha_minima_creacion = '1900-01-01'
    if company_id == 12: #SALTILLO
      fecha_minima_creacion = '2021-11-01' #PROD
    elif company_id  == 13: #MONCLOVA
      fecha_minima_creacion = '2021-12-01'
    elif company_id  == 15: #ACAPULCO
      fecha_minima_creacion = '2022-01-01'
    elif company_id  == 16: #TAMPICO
      fecha_minima_creacion = '2022-02-01'
    else:
      raise ValidationError("La compañia no aplica para la generación de impuestos")

    pabs_tax_obj = self.env['pabs.taxes']
    if self.report_type == 'realizados':
      pabs_tax_obj.RegistrarContratosRealizados(company_id, fecha_minima_creacion, self.start_date, self.end_date)
    if self.report_type == 'no_realizados':
      if self.factor <= 0:
        raise ValidationError("No se ha colocado el monto de factor")
      else:
        pabs_tax_obj.RegistrarContratos(company_id, self.factor, fecha_minima_creacion, self.start_date, self.end_date)
    if self.report_type == 'cancelados':
      pabs_tax_obj.RegistrarContratosCancelados(company_id, fecha_minima_creacion, self.start_date, self.end_date)
