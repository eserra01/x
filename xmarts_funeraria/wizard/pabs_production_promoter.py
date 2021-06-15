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
  ### RECOMENDADO //
  'Recomendado / N/A',
  'Comision correspondiente',
  'Comision restante',
  ### PROMOTOR //
  'Promotor que comisiona',
  'Comission correspondiente',
  'Comision restante',
  ### COORDINADOR // GERENTE JR
  'Coordinador / Gerente Jr',
  'Comisionista',
  'Comision correspondiente',
  'Comision Restante',
  ### GERENTE // GERENTE SR
  'Gerente / Gerente Sr',
  'Comisionista',
  'Comision correspondiente',
  'Comision restante',
  ### SI ES ALEX DEY QUE APLIQUE PRESIDENTE
  'N/A  / Presidente',
  'Comisionista',
  'Comision correspondiente',
  'Comision restante',

  'Fecha de primer abono',
  'Observaciones',
  
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
    comment_obj = self.env['pabs.contract.comments']

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
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    subtotal_format = workbook.add_format({'top' : 2, 'bold' : True, 'num_format': '$#,##0.00'})

    ### BUSCAMOS LOS CONTRATOS DE ESE ASISTENTE
    contract_ids = contract_obj.search([
      ('state' , '=', 'contract'),
      ('sale_employee_id','=',data.get('employee_id'))])


    ### ESCRIBIMOS EL ENCABEZADO DE LA PAGINA
    sheet.merge_range("A2:AK2","Programa de Apoyo en Beneficio Social", title_format)
    sheet.merge_range("A3:AK3", "Producción de asistente", subtitle_format)
    sheet.merge_range("A4:AK4", "{} - {}".format(employee_id.barcode, employee_id.name), subtitle_format)

    for index, val in enumerate(HEADERS):
      sheet.write(5,index,val,header_format)

    ### CONTADOR
    count = 6

    ### RECORREMOS LOS CONTRATOS
    for contract_id in contract_ids:
      ### CÓDIGO DEL PROMOTOR
      sheet.write(count, 0, contract_id.sale_employee_id.barcode)
      ### NOMBRE DEL PROMOTOR
      sheet.write(count, 1, contract_id.sale_employee_id.name)
      ### OFICINA
      sheet.write(count, 2, contract_id.warehouse_id.name or '')
      ### ESTATUS DEL PROMOTOR
      sheet.write(count, 3, contract_id.sale_employee_id.employee_status.name or '')
      ### TIPO DE INGRESO
      sheet.write(count, 4, contract_id.payment_scheme_id.name or '')
      ### FECHA DE ELABORACIÓN
      sheet.write(count, 5, contract_id.invoice_date or '', date_format)
      ### CONTRATO
      sheet.write(count, 6, contract_id.name or '')
      ### COSTO
      sheet.write(count, 7, contract_id.product_price or 0, money_format)
      ### SALDO
      sheet.write(count, 8, contract_id.balance or 0, money_format)
      ### CLIENTE
      sheet.write(count, 9, contract_id.full_name or '')
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
      sheet.write(count, 10, street or '')
      ### COLONIA
      sheet.write(count, 11, neightborhood or '')
      ### MUNICIPIO
      sheet.write(count, 12, municipality or '')
      ### TELÉFONO
      sheet.write(count, 13, phone or '')
      ### ESTATUS
      sheet.write(count, 14, contract_id.contract_status_item.status or '')
      ### MOTIVO
      sheet.write(count, 15, contract_id.contract_status_reason.reason or '')
      ### COBRADOR
      sheet.write(count, 16, contract_id.debt_collector.name or '')
      ### FILTRAMOS EL ARBOL DE COMISIONES
      comission_tree = contract_id.commission_tree
      ### BUSCAMOS SI EXISTE RECOMENDADO
      recomended = comission_tree.filtered(lambda r: r.job_id.name == 'RECOMENDADO')
      ### SI EXISTE RECOMENDADO, ESCRIBIMOS DATOS
      if recomended:
        sheet.write(count, 17, recomended.comission_agent_id.name)
        sheet.write(count, 18, recomended.corresponding_commission or 0, money_format)
        sheet.write(count, 19, recomended.remaining_commission or 0, money_format)
      ### SI NO, ENVIAMOS QUE NO APLICA
      else:
        sheet.write(count, 17, "N/A")
        sheet.write(count, 18, 0, money_format)
        sheet.write(count, 19, 0, money_format)
      ### AGREGAMOS PROMOTOR
      promoter = comission_tree.filtered(lambda r: r.job_id.name == 'ASISTENTE SOCIAL')
      ### SI SE ENCUENTRA EL PROMOTOR
      if promoter:
        ### ESCRIBIMOS PROMOTOR QUE COMISIONA
        sheet.write(count, 20, promoter.comission_agent_id.name)
        sheet.write(count, 21, promoter.corresponding_commission or 0, money_format)
        sheet.write(count, 22, promoter.remaining_commission or 0, money_format)
      ### SI NO EXISTE PROMOTOR
      else:
        sheet.write(count, 20, "N/A")
        sheet.write(count, 21, 0, money_format)
        sheet.write(count, 22, 0, money_format)
      ### BUSCAMOS SI HAY UN COORDINADOR O UN GERENTE JR
      coordinator = comission_tree.filtered(lambda r: r.job_id.name in ('COORDINADOR','GERENTE JR'))
      ### SI ENCONTRAMOS COORDINADOR O UN GERENTE JR
      if coordinator:
        sheet.write(count, 23, coordinator.job_id.name)
        sheet.write(count, 24, coordinator.comission_agent_id.name)
        sheet.write(count, 25, coordinator.corresponding_commission or 0, money_format)
        sheet.write(count, 26, coordinator.remaining_commission or 0, money_format)
      ### SI NO
      else:
        sheet.write(count, 23, "N/A")
        sheet.write(count, 24, "N/A")
        sheet.write(count, 25, 0, money_format)
        sheet.write(count, 26, 0, money_format)
      ### BUSCAMOS SI HAY UN GERENTE
      gerent = comission_tree.filtered(lambda r: r.job_id.name in ('GERENTE','GERENTE SR'))
      ### SI ENCONTRAMOS GERENTE O GERENTE SR
      if gerent:
        sheet.write(count, 27, gerent.job_id.name)
        sheet.write(count, 28, gerent.comission_agent_id.name)
        sheet.write(count, 29, gerent.corresponding_commission or 0, money_format)
        sheet.write(count, 30, gerent.remaining_commission or 0, money_format)
      ### SI NO
      else:
        sheet.write(count, 27, "N/A")
        sheet.write(count, 28, "N/A")
        sheet.write(count, 29, 0, money_format)
        sheet.write(count, 30, 0, money_format)
      ### BUSCAMOS PUESTO DE PRESIDENTE
      president = comission_tree.filtered(lambda r: r.job_id.name == 'PRESIDENTE')
      ### SI ENCONTRAMOS PRESIDENTE (ALEX DEY)
      if president:
        sheet.write(count, 31, president.job_id.name)
        sheet.write(count, 32, president.comission_agent_id.name)
        sheet.write(count, 33, president.corresponding_commission or 0, money_format)
        sheet.write(count, 34, president.remaining_commission or 0, money_format)
      ### SI NO
      else:
        sheet.write(count, 31, "N/A")
        sheet.write(count, 32, "N/A")
        sheet.write(count, 33, 0, money_format)
        sheet.write(count, 34, 0, money_format)
      ### FECHA DE PRIMER ABONO
      sheet.write(count, 35, contract_id.date_first_payment, date_format)
      ### COMENTARIOS
      comment_ids = comment_obj.search([('contract_id','=',contract_id.id)])
      comment = ''
      for line in comment_ids.mapped('comment'):
        comment = comment + line + "\n"
      sheet.write(count, 36, comment)
      count += 1



