# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz

TIPO_DE_REPORTE = [
  ('contratos', 'Contratos activos (elaborados entre dos fechas)'),
  ('abonos', 'Abonos (con fecha de oficina entre dos fechas)'),
]

class PabsInvoicingWizard(models.TransientModel):
  _name = 'pabs.invoicing.wizard'
  _description = 'Wizard para reporte de facturacion'

  report_type = fields.Selection(selection=TIPO_DE_REPORTE, string="Tipo de reporte", default='contratos')

  start_date = fields.Date(string='Fecha inicial', default = fields.date.today(),required=True)
  end_date = fields.Date(string='Fecha final', default = fields.date.today(), required=True)

  #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  

  def print_xls_report(self):
    data = {
      'start_date' : self.start_date,
      'end_date' : self.end_date,
      'report_type': self.report_type
    }

    return self.env.ref("pabs_account.pabs_invoicing_xlsx").report_action(self, data=data)

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  

class PabsInvoicingXLSX(models.AbstractModel):
  _name = 'report.pabs_account.pabs_invoicing_xlsx'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    company_id = self.env.company.id
    fecha_inicial = data['start_date']
    fecha_final = data['end_date']

    #HARCODED !!!
    fecha_minima_creacion = '1900-01-01'
    if company_id == 12: #SALTILLO
      fecha_minima_creacion = '2022-05-01' #PROD
      #fecha_minima_creacion = '2022-01-01' #TEST

    ############################################################################################################
    #                                              CONTRATOS
    ############################################################################################################
    if data['report_type'] == 'contratos':
      
      consulta = """
      SELECT
          con.invoice_date as fecha_contrato,
          con.name as contrato,
          CONCAT(con.partner_name,' ', con.partner_fname,' ', con.partner_mname) as cliente,
          CONCAT(con.street_name, ' #', con.street_number) as domicilio,
          col_casa.name as colonia,
          loc_casa.name as localidad,
          con.between_streets as entre_calles,
          col_casa.zip_code as cp,
          con.phone as Telefono,
          est.status as estatus,
          COALESCE(motivo.reason, '') as motivo,
          CAST( (fac.costo - COALESCE(nota.total, 0) - COALESCE(tras.total, 0))
              / 1.16 AS DECIMAL(10,2)) as costo
      FROM pabs_contract AS con
      INNER JOIN pabs_contract_status AS est ON con.contract_status_item = est.id
      LEFT JOIN pabs_contract_status_reason as motivo on con.contract_status_reason = motivo.id
      LEFT JOIN colonias AS col_casa ON col_casa.id = con.neighborhood_id
      LEFT JOIN res_locality AS loc_casa ON loc_casa.id = con.municipality_id
      INNER JOIN
      (
          /*Factura*/
          SELECT 
              fac.contract_id as "id_contrato",
              SUM(fac.amount_total) as "costo",
              SUM(fac.amount_residual) as "saldo",
              SUM(fac.amount_total) - SUM(fac.amount_residual) as "abonado"
          FROM pabs_contract AS con 
          INNER JOIN account_move AS fac on con.id = fac.contract_id 
              WHERE fac.type = 'out_invoice'
              AND fac.state = 'posted'
              AND con.state = 'contract'
              AND con.company_id = {} /*Compañia*/
                  GROUP BY fac.contract_id
      ) AS fac on con.id = fac.id_contrato
      LEFT JOIN
      (
          /*Notas*/
          SELECT 
              con.id as id_contrato,
              COALESCE(SUM(nota.amount_total), 0) as total
          FROM pabs_contract AS con 
          INNER JOIN account_move AS nota ON nota.contract_id = con.id AND nota.type = 'out_refund' AND nota.state IN ('posted')
              WHERE con.company_id = {} /*Compañia*/
              AND nota.ref NOT LIKE '%ABONO%CONVENIO%'
                  GROUP BY con.id
      ) AS nota ON con.id = nota.id_contrato
      LEFT JOIN
      (
          /*Traspasos*/
          SELECT 
              contract_dest_id as id_contrato_destino,
              COALESCE(SUM(amount_transfer), 0) as total
          FROM pabs_balance_transfer
              WHERE state = 'done'
              AND company_id = {} /*Compañia*/
                  GROUP BY contract_dest_id
      ) AS tras ON con.id = tras.id_contrato_destino
          WHERE con.state = 'contract'
          AND est.status IN ('ACTIVO', 'SUSP. TEMPORAL', 'PAGADO')
          AND con.invoice_date >= '{}' /*Fecha minima de creacion del contrato*/
          AND con.invoice_date BETWEEN '{}' AND '{}' /*Fecha de contratos de la nueva empresa*/
          AND con.company_id = {} /*Compañia*/
      """.format(company_id, company_id, company_id, fecha_minima_creacion, fecha_inicial, fecha_final, company_id)
      self.env.cr.execute(consulta)

      contratos = []
      for res in self.env.cr.fetchall():
          contratos.append({
              'Fecha_contrato': res[0],
              'Contrato': res[1],
              'Cliente': res[2],
              'domicilio': res[3],
              'colonia': res[4],
              'localidad': res[5],
              'Entre calles': res[6],
              'CP': res[7],
              'Telefono': res[8],
              'Estatus': res[9],
              'Motivo': res[10],
              'Costo': float(res[11])
          })
      
      ### Generar Excel
      sheet = workbook.add_worksheet('Contratos')
      fila = 0

      # Crear formatos
      bold_format = workbook.add_format({'bold': True})
      date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
      money_format = workbook.add_format({'num_format': '$#,##0.00'})

      # Escribir encabezados
      encabezados = ['Fecha_contrato','Contrato','Cliente','domicilio','colonia','localidad','Entre calles','CP','Telefono','Estatus','Motivo','Costo']
      for index, val in enumerate(encabezados):
        sheet.write(fila, index, val, bold_format)

      # Escribir lineas
      for con in contratos:
        fila = fila + 1
        col = -1
        
        col = col + 1; sheet.write(fila, col, con['Fecha_contrato'], date_format)     #Fecha_creacion
        col = col + 1; sheet.write(fila, col, con['Contrato'])                        #Contrato
        col = col + 1; sheet.write(fila, col, con['Cliente'])                         #Cliente
        col = col + 1; sheet.write(fila, col, con['domicilio'])                       #domicilio
        col = col + 1; sheet.write(fila, col, con['colonia'])                         #colonia
        col = col + 1; sheet.write(fila, col, con['localidad'])                       #localidad
        col = col + 1; sheet.write(fila, col, con['Entre calles'])                    #Entre calles
        col = col + 1; sheet.write(fila, col, con['CP'])                              #CP
        col = col + 1; sheet.write(fila, col, con['Telefono'])                        #Telefono
        col = col + 1; sheet.write(fila, col, con['Estatus'])                         #Estatus
        col = col + 1; sheet.write(fila, col, con['Motivo'])                          #Motivo
        col = col + 1; sheet.write(fila, col, con['Costo'], money_format)             #Costo

    ############################################################################################################
    #                                              ABONOS
    ############################################################################################################
    elif data['report_type'] == 'abonos':
      
      consulta = """
      SELECT
          abo.payment_date as fecha_oficina,
          abo.create_date as fecha_creacion,
          abo.name as nombre,
          CONCAT(dia.name, ' (MXN)') as diario,
          met.name as metodo_pago,
          con.name as empresa,
          abo.amount as importe,
          CASE
            WHEN abo.state = 'draft' THEN 'Borrador'
            WHEN abo.state = 'posted' THEN 'Validado'
            WHEN abo.state = 'sent' THEN 'Enviado'
            WHEN abo.state = 'reconciled' THEN 'Conciliado'
            WHEN abo.state = 'cancelled' THEN 'Cancelado'
          END as estado,
          abo.ecobro_receipt as recibo
      FROM pabs_contract AS con
      INNER JOIN pabs_contract_status AS est ON con.contract_status_item = est.id
      INNER JOIN account_payment AS abo ON con.id = abo.contract
      INNER JOIN account_payment_method AS met ON abo.payment_method_id = met.id
      INNER JOIN account_journal AS dia ON abo.journal_id = dia.id
          WHERE con.state = 'contract'
          AND est.status IN ('ACTIVO', 'SUSP. TEMPORAL', 'PAGADO')
          AND con.invoice_date >= '{}' /*Fecha minima de creacion del contrato*/
          AND abo.reference IN ('stationary', 'surplus', 'payment')
          AND abo.state IN ('posted', 'sent', 'reconciled')
          AND abo.payment_date BETWEEN '{}' AND '{}' /*Fecha de abonos*/
          AND con.company_id = {} /*Compañia*/
      """.format(fecha_minima_creacion, fecha_inicial, fecha_final, company_id)
      self.env.cr.execute(consulta)

      abonos = []
      for res in self.env.cr.fetchall():
          abonos.append({
              'fecha_oficina': res[0],
              'fecha_creacion': res[1],
              'nombre': res[2],
              'diario': res[3],
              'metodo_pago': res[4],
              'empresa': res[5],
              'importe': res[6],
              'estado': res[7],
              'recibo': res[8]
          })

      ### Generar Excel      
      sheet = workbook.add_worksheet('abonos')
      fila = 0

      bold_format = workbook.add_format({'bold': True})
      date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
      datetime_format = workbook.add_format({'num_format': 'dd/mm/yy hh:mm:ss'})
      money_format = workbook.add_format({'num_format': '$#,##0.00'})

      encabezados = ['Fecha','Creado el','Nombre','Diario','Método de pago','Empresa','Importe','Estado','Recibo Ecobro']

      for index, val in enumerate(encabezados):
        sheet.write(fila, index, val, bold_format)

      for abo in abonos:
        fila = fila + 1
        col = -1
        
        col = col + 1; sheet.write(fila, col, abo['fecha_oficina'], date_format)  #Fecha
        col = col + 1; sheet.write(fila, col, abo['fecha_creacion'], datetime_format) #Creado el
        col = col + 1; sheet.write(fila, col, abo['nombre'])                      #Nombre
        col = col + 1; sheet.write(fila, col, abo['diario'])                      #Diario
        col = col + 1; sheet.write(fila, col, abo['metodo_pago'])                 #Método de pago
        col = col + 1; sheet.write(fila, col, abo['empresa'])                     #Empresa
        col = col + 1; sheet.write(fila, col, abo['importe'], money_format)       #Importe
        col = col + 1; sheet.write(fila, col, abo['estado'])                      #Estado
        col = col + 1; sheet.write(fila, col, abo['recibo'])                      #Recibo Ecobro