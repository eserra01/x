from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError

HEADERS = [
  'Código del Promotor',
  'Nombre Promotor',
  'Oficina',
  'Estatus del Promotor',
  'Tipo de Ingreso',
  'Fecha de elaboración',
  'Contrato',
  'Costo',
  'Saldo',
  'Cliente',
  'Domicilio',
  'Colonia',
  'Municipio',
  'Teléfono',
  'Estatus',
  'Motivo',
  'Cobrador',
  'Recomendado'
  ### VALIDAR CONCEPTOS DE DE ARBOL DE COMISIONES
]

class PabsProductionPromoter(models.TransientModel):
  _name = 'pabs.production.promoter'
  _description = 'Producción por Asistente'

  employee_id = fields.Many2one(comodel_name='hr.employee',
    required=True,
    string='Asistente')

  def print_xlsx_report(self):
    data = {
      'employee_id' : self.employee_id.id,
    }
    return self.env.ref('xmarts_funeraria.production_promoter_report_xlsx').report_action(self, data=data)

class PABSProductionPromoterXLSX(models.AbstractModel):
  _name = 'report.xmarts_funeraria.promoter_production_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    ### DECLARAMOS OBJETOS
    contract_obj = self.env['pabs.contract']
    employee_obj = self.env['hr.employee']

    ### INSTANCIAMOS EL OBJETO DEL EMPLEADO
    employee_id = employee_obj.browse(data.get('employee_id'))

    ### BUSCAMOS LOS CONTRATOS DE ESE ASISTENTE
    contract_ids = contract_obj.search([
      ('state','=','contract'),
      ('sale_employee_id','=',data.get(employee_id))])

