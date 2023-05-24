# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from dateutil import tz
import logging

_logger = logging.getLogger(__name__)

class ContratosPagados(models.TransientModel):
  _name = 'pabs.contratos.pagados'
  _description = 'Reporte de contratos pagados'

  start_date = fields.Date(string='Fecha Inicial de último abono', required=True)
  end_date = fields.Date(string='Fecha Final de último abono', required=True)

  def generate_xls_report(self):
    ### ARMANDO LOS PARAMETROS
    data = {
        'start_date': self.start_date,
        'end_date': self.end_date
    }

    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_reports.contratos_pagados_xlsx_report').report_action(self, data=data)

class ContratosPagadosXLSXReport(models.AbstractModel):
  _name = 'report.pabs_reports.contratos_pagados_xls'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    
    company_id = self.env.company.id

    start_date = data['start_date']
    end_date = data['end_date']
    
    ### Obtener estatus pagado ###
    est_activo = self.env['pabs.contract.status'].search([('status','=','PAGADO')], limit=1)
    if not est_activo:
        raise UserError('No se encuentra el estatus PAGADO')

    id_activo = est_activo.id
    
    query = """
        /*Contrato*/
        SELECT 
            CONCAT(con.partner_name, ' ', con.partner_fname, ' ', con.partner_mname) as cliente,
            con.name as contrato,
            con.invoice_date as fecha_contrato,
            costo.costo as costo,
            cob.name as cobrador,
            CASE
                WHEN con.street_name_toll IS NOT NULL THEN CONCAT(con.street_name_toll, ' #', con.street_number_toll)
                ELSE CONCAT(con.street_name, ' #', con.street_number)
            END as domicilio,
            CASE
                WHEN con.street_name_toll IS NOT NULL THEN col_cobro.name
                ELSE col_casa.name
            END as colonia,
            CASE
                WHEN con.street_name_toll IS NOT NULL THEN loc_cobro.name
                ELSE loc_casa.name
            END as localidad,
            COALESCE(con.phone_toll, con.phone) as telefono,
            COALESCE(con.between_streets_toll, con.between_streets) as entre_calles,
            prom.name as promotor,
            prom.name as codigo_promotor,
            GREATEST(abo.fecha_ultimo_abono, nota.fecha_ultima_nota) as fecha_ultimo_abono
        FROM pabs_contract AS con
        INNER JOIN pabs_contract_status AS est ON est.id = con.contract_status_item
        INNER JOIN pabs_contract_status_reason AS mot ON mot.id = con.contract_status_reason
        LEFT JOIN colonias AS col_cobro ON col_cobro.id = con.toll_colony_id
        LEFT JOIN colonias AS col_casa ON col_casa.id = con.neighborhood_id
        LEFT JOIN res_locality AS loc_cobro ON loc_cobro.id = con.toll_municipallity_id
        LEFT JOIN res_locality AS loc_casa ON loc_casa.id = con.municipality_id
        LEFT JOIN hr_employee AS prom ON prom.id = con.sale_employee_id
        LEFT JOIN hr_employee AS cob ON cob.id = con.debt_collector
        INNER JOIN
        (
            /*Facturas (5 seg)*/
            SELECT 
                con.id as id_contrato,
                SUM(fac.amount_total) as costo
            FROM pabs_contract AS con 
            INNER JOIN account_move AS fac ON con.id = fac.contract_id
                WHERE con.state = 'contract'
                AND fac.type = 'out_invoice' AND fac.state = 'posted'
                AND con.contract_status_item = {}
                AND con.company_id = {}
                    GROUP BY con.id
        ) AS fac ON con.id = fac.id_contrato
        LEFT JOIN 
        (
            /*Factura de precio de plan 11 seg*/
            SELECT 
                con.id as id_contrato,
                SUM(fac.amount_total) as costo
            FROM pabs_contract AS con 
            INNER JOIN account_move AS fac ON con.id = fac.contract_id 
            INNER JOIN account_move_line AS linea ON fac.id = linea.move_id
            INNER JOIN product_product AS prod ON linea.product_id = prod.id 
                WHERE con.state = 'contract'
                AND fac.type = 'out_invoice' AND fac.state = 'posted'
                AND prod.default_code LIKE 'PL%'
                AND con.contract_status_item = {}
                AND con.company_id = {}
                    GROUP BY con.id
        ) AS costo ON con.id = costo.id_contrato
        LEFT JOIN
        (
            /*Abonos 91 seg*/
            SELECT 
                con.id as id_contrato,
                SUM(abo.amount) as total,
                MAX(abo.date_receipt) as fecha_ultimo_abono
            FROM pabs_contract AS con 
            INNER JOIN account_payment AS abo ON con.id = abo.contract 
                WHERE con.state = 'contract'
                AND abo.state = 'posted'
                AND con.contract_status_item = {}
                AND con.company_id = {}
                    GROUP BY con.id
        ) AS abo ON con.id = abo.id_contrato
        LEFT JOIN
        (
            /*Notas 2 seg*/
            SELECT 
                con.id as id_contrato,
                SUM(nota.amount_total) as total,
                MAX(nota.date) as fecha_ultima_nota
            FROM pabs_contract AS con 
            INNER JOIN account_move AS nota ON nota.contract_id = con.id 
                WHERE con.state = 'contract'
                AND nota.type = 'out_refund' AND nota.state = 'posted'
                AND con.contract_status_item = {}
                AND con.company_id = {}
                    GROUP BY con.id
        ) AS nota ON con.id = nota.id_contrato
        LEFT JOIN 
        (
            /*Traspasos 1 seg*/
            SELECT 
                contract_id as id_contrato,
                (SUM(balance) * -1) as total
            FROM account_move_line
                WHERE ref LIKE '%TRASPASO%'
                AND parent_state = 'posted'
                AND contract_id IS NOT NULL
                    GROUP BY contract_id
        ) AS trasp ON con.id = trasp.id_contrato
            WHERE con.state = 'contract'
            AND mot.reason != 'PRESTAMO PERCAPITA'
            AND ( fac.costo - (COALESCE(abo.total, 0) + COALESCE(nota.total, 0) + COALESCE(trasp.total, 0)) ) <= 0
            AND est.id = {}
            AND con.company_id = {}
            AND GREATEST(abo.fecha_ultimo_abono, nota.fecha_ultima_nota) BETWEEN '{}' AND '{}'
      """.format(id_activo, company_id, id_activo, company_id, id_activo, company_id, id_activo, company_id, id_activo, company_id, start_date, end_date)

    ### EJECUTAMOS EL QUERY
    self.env.cr.execute(query)

    ### GENERAMOS LA HOJA
    sheet = workbook.add_worksheet("Contratos pagados")

    ### AGREGAMOS FORMATOS
    bold_format = workbook.add_format({'bold': True,'bg_color': '#2978F8'})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})

    HEADERS = ['Cliente','Contrato','Fecha','Costo','Cobrador','Domicilio','Colonia','Localidad','Telefono','EntreCalles','Promotor','CódigoPromotor','FechaUltimoAbono']

    for row, row_data in enumerate(HEADERS):
      sheet.write(0,row,row_data,bold_format)

    for index, rec in enumerate(self.env.cr.fetchall()):
      ### ESCRIBIMOS LOS RESULTADOS DEL QUERY
      sheet.write((index + 1), 0, rec[0])                   # Cliente
      sheet.write((index + 1), 1, rec[1])                   # Contrato
      sheet.write((index + 1), 2, rec[2], date_format)      # Fecha contrato
      sheet.write((index + 1), 3, rec[3], money_format)     # Costo
      sheet.write((index + 1), 4, rec[4])                   # Cobrador
      sheet.write((index + 1), 5, rec[5])                   # Domicilio
      sheet.write((index + 1), 6, rec[6])                   # Colonia
      sheet.write((index + 1), 7, rec[7])                   # Localidad
      sheet.write((index + 1), 8, rec[8])                   # Telefono
      sheet.write((index + 1), 9, rec[9])                   # Entre calles
      sheet.write((index + 1), 10, rec[10])                 # Promotor
      sheet.write((index + 1), 11, rec[11])                 # Código promotor
      sheet.write((index + 1), 12, rec[12], date_format)    # Fecha de último abono