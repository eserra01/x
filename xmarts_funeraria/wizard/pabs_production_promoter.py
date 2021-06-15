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
    subtitle_format = workbook.add_format({'font_size' : 12, 'center_across' : True})
    bold_format = workbook.add_format({'bold' : True})
    header_format = workbook.add_format({'bold' : True,'bg_color': '#76A8F9'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})
    subtotal_format = workbook.add_format({'top' : 2, 'bold' : True, 'num_format': '$#,##0.00'})

    ### BUSCAMOS LOS CONTRATOS DE ESE ASISTENTE
    contract_ids = contract_obj.search([
      ('state' , '=', 'contract'),
      ('sale_employee_id','=',data.get('employee_id'))])


    ### ESCRIBIMOS EL ENCABEZADO DE LA PAGINA
    sheet.merge_range("A2:R2","Programa de Apoyo en Beneficio Social", title_format)
    sheet.merge_range("A3:R3", "Producción de asistente", subtitle_format)
    sheet.merge_range("A4:R4", "{} - {}".format(employee_id.barcode, employee_id.name))

    for index, val in enumerate(HEADERS):
      sheet.write(5,index,val,header_format)

    ### CONTADOR
    count = 6

    ### RECORREMOS LOS CONTRATOS
    for contract_id in contract_ids:
      ### CÓDIGO DEL PROMOTOR
      sheet.write(count, 1, contract_id.sale_employee_id.barcode)
      ### NOMBRE DEL PROMOTOR
      sheet.write(count, 2, contract_id.sale_employee_id.name)
      ### OFICINA
      sheet.write(count, 3, contract_id.warehouse_id.name or '')
      ### ESTATUS DEL PROMOTOR
      sheet.write(count, 4, contract_id.sale_employee_id.employee_status.name or '')
      ### TIPO DE INGRESO
      sheet.write(count, 6, contract_id.payment_scheme_id.name or '')
      ### FECHA DE ELABORACIÓN
      sheet.write(count, 7, contract_id.invoice_date or '')
      ### CONTRATO
      sheet.write(count, 8, contract_id.name or '')
      ### COSTO
      sheet.write(count, 9, contract_id.product_price or 0)
      ### SALDO
      sheet.write(count, 10, contract_id.balance or 0)
      ### CLIENTE
      sheet.write(count, 11, contract_id.full_name or '')
      street = ''
      neightborhood = ''
      municipality = ''
      phone = ''
      if contract_id.street_name_toll:
        street = "{} {}".format(
          contract_id.street_name_toll or '', contract_id.street_number_toll or '')
        neightborhood = contract_id.toll_colony_id.name
        municipality = contract_id.toll_municipallity_id.name
        phone = contract_id.phone_toll
      elif contract_id.street_name:
        street = "{} {} {}".format(
          contract_id.street_name or '', contract_id.street_number or '')
        neightborhood = contract_id.neighborhood_id.name
        municipality = contract_id.municipality_id.name
        phone = contract_id.phone
      ### DOMICILIO
      sheet.write(count, 12, street)
      ### COLONIA
      sheet.write(count, 13, neightborhood)
      ### MUNICIPIO
      sheet.write(count, 14, municipality)
      ### TELÉFONO
      sheet.write(count, 15, phone)
      ### ESTATUS
      sheet.write(count, 16, contract_id.contract_status_item.status or '')
      ### MOTIVO
      sheet.write(count, 17, contract_id.contract_status_reason.reason or '')
      ### COBRADOR
      sheet.write(count, 18, contract_id.debt_collector.name or '')
    count += 1
