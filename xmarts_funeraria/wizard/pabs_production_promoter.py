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

    ### AGREGAMOS LA HOJA DE PRODUCCION AL EXCEL
    sheet = workbook.add_worksheet("Produccion de {}".format(employee_id.name))

    ### AGREGAMOS FORMATOS
    title_format = workbook.add_format({'bold' : True, 'font_size' : 14, 'center_across' : True})
    bold_format = workbook.add_format({'bold' : True})
    header_format = workbook.add_format({'bold' : True,'bg_color': '#2978F8'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})
    subtotal_format = workbook.add_format({'top' : 2, 'bold' : True, 'num_format': '$#,##0.00'})

    ### ESCRIBIMOS EL ENCABEZADO DE LA PAGINA
    sheet.merge_range("A2:D2","Programa de Apoyo en Beneficio Social", title_format)
    sheet.merge_range("A3:D3", "Producción de asistente", subtitle_format)
    sheet.merge_range("A4:B4", "{} - {}".format(employee_id.barcode, employee_id.name))

    for index, val in enumerate(HEADERS):
      sheet.write(5,index,val,header_format)

