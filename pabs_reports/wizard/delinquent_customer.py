# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz
import logging

_logger = logging.getLogger(__name__)

HEADERS = [
  'Fecha de Contrato',
  'Contrato',
  'Cliente',
  'Domicilio',
  'Colonia',
  'Localidad',
  'Entre Calles',
  'Teléfono',
  'Promotor',
  'Cobrador',
  'Forma de Pago',
  'Fecha de Estatus',
  'Estatus',
  'Motivo',
  'id contrato',
  'Monto de Pago',
  'Servicio',
  'Costo',
  'Saldo',
  'Pago',
  'Fecha de Ultimo Abono',
  'Ultimo Cobrador',
  'Importe Ultimo bono',
  'Estatus Moroso']

class DelinquentCustomer(models.TransientModel):
  _name = 'pabs.delinquent.customer'
  _description = 'Reporte Detallado de Morosos'

  def generate_pdf_report(self):
    ### ARMANDO LOS PARAMETROS
    data = {
      'date' : fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General'))
    }

    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_reports.delinquent_customer_report').report_action(self, data=data)

  def generate_xls_report(self):
    ### ARMANDO LOS PARAMETROS
    data = {
      'date' : fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General'))
    }

    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_reports.delinquent_customer_xlsx_report').report_action(self, data=data)

class DelinquentCustomerPDFReport(models.AbstractModel):
  _name = 'report.pabs_reports.delinquent_customer_report_template'

  @api.model
  def _get_report_values(self, docids, data):
    ### BUSCANDO PARAMETROS DE ENCABEZADO
    data = {}
    data_rec = []
    company_id = self.env.company.id
    logo = self.env.user.company_id.logo
    date = data.get('data') or fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General'))
    cr = self._cr
    query = """
        SELECT 
        contrato as "Contrato",
        cliente as "Cliente",
        domicilio as "Domicilio",
        colonia as "Colonia",
        localidad as "Localidad",
        forma_pago as "Forma de Pago",
        fecha_ultimo_abono as "Fecha de ultimo abono",
        cobrador as "Cobrador"
    FROM
    (
        SELECT
            con.contrato as "contrato",
            con.cliente as "cliente",
            con.domicilio as "domicilio",
            con.colonia as "colonia",
            con.localidad as "localidad",
            con.cobrador as "cobrador",
            con.forma_pago as "forma_pago",
            COALESCE(abo.date_receipt, abo.payment_date) as "fecha_ultimo_abono",
             CASE
                WHEN con.id_estatus = 21 AND CURRENT_DATE - GREATEST(con.fecha_primer_abono, COALESCE(abo.date_receipt, abo.payment_date)) <= 
                    (CASE
                        WHEN con.forma_pago = 'S' THEN 14
                        WHEN con.forma_pago = 'Q' THEN 30
                        WHEN con.forma_pago = 'M' THEN 60
                    END)
                THEN 1
                WHEN con.id_estatus = 21 AND CURRENT_DATE - GREATEST(con.fecha_primer_abono, COALESCE(abo.date_receipt, abo.payment_date)) > 
                    (CASE
                        WHEN con.forma_pago = 'S' THEN 14
                        WHEN con.forma_pago = 'Q' THEN 30
                        WHEN con.forma_pago = 'M' THEN 60
                    END)
                THEN 7
            END AS "estatus_moroso"
        FROM
        (
            /*Contrato*/
            SELECT 
                con.name as "contrato",
                CONCAT(con.partner_name, ' ', con.partner_fname, ' ', con.partner_mname) as "cliente",
                CONCAT(con.street_name_toll, ' #', con.street_number_toll) as "domicilio",
                col.name as "colonia",
                loc.name as "localidad",
                cob.name as "cobrador",
                con.id as "id_contrato",
                con.contract_status_item as "id_estatus",
                con.date_first_payment as "fecha_primer_abono",
                CASE
                    WHEN con.way_to_payment = 'weekly' THEN 'S'
                    WHEN con.way_to_payment = 'biweekly' THEN 'Q'
                    WHEN con.way_to_payment = 'monthly' THEN 'M'
                END as "forma_pago"
            FROM pabs_contract AS con
            LEFT JOIN colonias AS col ON col.id = con.toll_colony_id
            LEFT JOIN res_locality AS loc ON loc.id = con.toll_municipallity_id
            LEFT JOIN hr_employee AS cob ON cob.id = con.debt_collector
                WHERE con.invoice_date <= CURRENT_DATE
                AND con.state = 'contract'
                AND con.company_id = {}
                AND con.contract_status_item IN (21)
        ) AS con
        INNER JOIN
        (
            /*Lista de ultimo abono*/
            SELECT      
                ROW_NUMBER() OVER(PARTITION BY abo.contract ORDER BY COALESCE(abo.date_receipt, abo.payment_date) DESC) as "numero", 
                abo.id as "id_abono", 
                abo.contract as "id_contrato"
            FROM account_payment as abo
                WHERE (abo.reference = 'stationary' or abo.reference = 'payment') 
                AND abo.state = 'posted'
        ) as orden ON orden.id_contrato = con.id_contrato AND orden.numero = 1
        LEFT JOIN account_payment as abo ON orden.id_abono = abo.id
    )AS consulta
        WHERE estatus_moroso = 7
            ORDER BY cobrador, contrato""".format(company_id)
    ### EJECUTAMOS EL QUERY
    cr.execute(query)

     # Se obtienen los registros
    recs = [x for x in cr.fetchall()]
    collectors = []
    # Se obtienen los cobradores
    for rec in recs:
        if rec[7] not in collectors:
            collectors.append(rec[7])
    # Para cada cobrador
    for collector in collectors:
        #
        data_rec = []
        for rec in recs:
            if collector == rec[7]:
                data_rec.append({
                    'contract_name' : rec[0],
                    'partner_name' : rec[1],
                    'address' : rec[2],
                    'colony' : rec[3],
                    'municipality' : rec[4],
                    'period' : rec[5],
                    'last_payment' : rec[6],
                })
        
        data.update({collector: data_rec})

    ### RETORNAMOS LA INFORMACIÓN
    return {
      'logo' : logo,
      'date' : date,
      'data' : data
    }

class DelinquentCustomerXLSXReport(models.AbstractModel):
  _name = 'report.pabs_reports.delinquent_customer_xls'
  _inherit = 'report.report_xlsx.abstract'

  def generate_xlsx_report(self, workbook, data, lines):
    ### FECHA ACTUAL
    company_id = self.env.company.id
    date = data.get('data') or fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General'))
    ### CREAMOS CURSOS
    cr = self._cr
    ### ESCRIBIMOS EL QUERY EN UNA VARIABLE
    query = """
      SELECT 
        *
      FROM
      (
        SELECT
            con.fecha_contrato as "Fecha de contrato",
            con.contrato as "contrato",
            con.cliente as "Cliente",
            con.domicilio as "Domicilio",
            con.colonia as "Colonia",
            con.localidad as "Localidad",
            con.entre_calles as "Entre calles",
            con.telefono as "Telefono",
            con.promotor as "Promotor",
            con.cobrador as "Cobrador",
            con.forma_pago as "Forma de Pago",
            con.fecha_estatus as "Fecha estatus",
            con.estatus as "Estatus",
            con.motivo as "Motivo",
            con.id_contrato as "id contrato",
            con.monto_pago as "Monto pago actual",
            con.servicio as "Servicio",
            con.costo as "Costo",
            fac.saldo as "Saldo",
            abo.id as "Ultimo abono",
            COALESCE(abo.date_receipt, abo.payment_date) as "Fecha de ultimo abono",
            emp.name as "Ultimo cobrador",
            abo.amount as "Importe ultimo abono",
            CASE
                WHEN con.id_estatus = 21 AND CURRENT_DATE - GREATEST(con.fecha_primer_abono, COALESCE(abo.date_receipt, abo.payment_date)) <= 
                    (CASE
                        WHEN con.forma_pago = 'S' THEN 14
                        WHEN con.forma_pago = 'Q' THEN 30
                        WHEN con.forma_pago = 'M' THEN 60
                    END)
                THEN 1
                WHEN con.id_estatus = 21 AND CURRENT_DATE - GREATEST(con.fecha_primer_abono, COALESCE(abo.date_receipt, abo.payment_date)) > 
                    (CASE
                        WHEN con.forma_pago = 'S' THEN 14
                        WHEN con.forma_pago = 'Q' THEN 30
                        WHEN con.forma_pago = 'M' THEN 60
                    END)
                THEN 7
            END AS "estatus_moroso"
        FROM
        (
            /*Contrato*/
            SELECT 
                con.invoice_date as "fecha_contrato",
                con.name as "contrato",
                CONCAT(con.partner_name, ' ', con.partner_fname, ' ', con.partner_mname) as "cliente",
                CONCAT(con.street_name_toll, ' #', con.street_number_toll) as "domicilio",
                col.name as "colonia",
                loc.name as "localidad",
                con.between_streets_toll as "entre_calles",
                con.phone as "telefono",
                prom.name as "promotor",
                cob.name as "cobrador",
                CASE
                    WHEN con.way_to_payment = 'weekly' THEN 'S'
                    WHEN con.way_to_payment = 'biweekly' THEN 'Q'
                    WHEN con.way_to_payment = 'monthly' THEN 'M'
                END as "forma_pago",
                con.date_of_last_status "fecha_estatus",
                pEst.status as "estatus",
                pMot.reason as "motivo",
                con.id as "id_contrato",
                con.payment_amount as "monto_pago",
                prod.name as "servicio",
                ppl.fixed_price as "costo",
                con.contract_status_item as "id_estatus",
                con.date_first_payment as "fecha_primer_abono"
            FROM pabs_contract AS con
            LEFT JOIN colonias AS col ON col.id = con.toll_colony_id
            LEFT JOIN res_locality AS loc ON loc.id = con.toll_municipallity_id
            LEFT JOIN hr_employee AS prom ON prom.id = con.sale_employee_id
            LEFT JOIN pabs_contract_status AS pEst ON pEst.id = con.contract_status_item
            LEFT JOIN pabs_contract_status_reason AS pMot ON pMot.id = con.contract_status_reason
            LEFT JOIN hr_employee AS cob ON cob.id = con.debt_collector
            LEFT JOIN stock_production_lot AS sol ON sol.id = con.lot_id
            LEFT JOIN product_template AS prod ON prod.id = sol.product_id
            LEFT JOIN product_pricelist_item AS ppl ON ppl.product_id = sol.product_id
                WHERE con.invoice_date <= CURRENT_DATE
                AND con.state = 'contract'
                AND con.company_id = {}
                AND con.contract_status_item IN (21)
        ) AS con
        INNER JOIN
        (
            /*Factura*/
            SELECT 
                fac.contract_id as "id_contrato",
                SUM(fac.amount_residual) as "saldo"
            FROM pabs_contract AS con 
            INNER JOIN account_move AS fac on con.id = fac.contract_id 
                WHERE fac.type = 'out_invoice'
                AND fac.state = 'posted'
                AND con.state = 'contract'
                AND con.company_id = {}
                    GROUP BY fac.contract_id
        ) AS fac on con.id_contrato = fac.id_contrato
        INNER JOIN
        (
            /*Lista de ultimo abono*/
            SELECT      
                ROW_NUMBER() OVER(PARTITION BY abo.contract ORDER BY COALESCE(abo.date_receipt, abo.payment_date) DESC) as "numero", 
                abo.id as "id_abono", 
                abo.contract as "id_contrato"
            FROM account_payment as abo
                WHERE (abo.reference = 'stationary' or abo.reference = 'payment') 
                AND abo.state = 'posted'
        ) as orden ON orden.id_contrato = con.id_contrato AND orden.numero = 1
        LEFT JOIN account_payment as abo ON orden.id_abono = abo.id
        LEFT JOIN hr_employee AS emp ON abo.debt_collector_code = emp.id
    )AS consulta
        WHERE consulta.estatus_moroso = 7
            ORDER BY consulta.contrato""".format(company_id, company_id)
    ### GENERAMOS LA HOJA
    sheet = workbook.add_worksheet("Reporte de Morosos {}".format(date))

    ### AGREGAMOS FORMATOS
    bold_format = workbook.add_format({'bold': True,'bg_color': '#2978F8'})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})

     ### INSERTAMOS LOS ENCABEZADOS
    for row, row_data in enumerate(HEADERS):
      sheet.write(0,row,row_data,bold_format)

    ### EJECUTAMOS EL QUERY
    cr.execute(query)
    ### ITERAMOS EN EL RESULTADO
    for index, rec in enumerate(cr.fetchall()):
      ### ESCRIBIMOS LOS RESULTADOS DEL QUERY
      sheet.write((index + 1), 0, rec[0], date_format)
      sheet.write((index + 1), 1, rec[1])
      sheet.write((index + 1), 2, rec[2])
      sheet.write((index + 1), 3, rec[3])
      sheet.write((index + 1), 4, rec[4])
      sheet.write((index + 1), 5, rec[5])
      sheet.write((index + 1), 6, rec[6])
      sheet.write((index + 1), 7, rec[7])
      sheet.write((index + 1), 8, rec[8])
      sheet.write((index + 1), 9, rec[9])
      sheet.write((index + 1), 10, rec[10])
      sheet.write((index + 1), 11, rec[11], date_format)
      sheet.write((index + 1), 12, rec[12])
      sheet.write((index + 1), 13, rec[13])
      sheet.write((index + 1), 14, rec[14]) # id contrato
      sheet.write((index + 1), 15, rec[15], money_format) # monto de pago
      sheet.write((index + 1), 16, rec[16])
      sheet.write((index + 1), 17, rec[17], money_format) # costo
      sheet.write((index + 1), 18, rec[18], money_format) # saldo
      sheet.write((index + 1), 19, rec[19]) 
      sheet.write((index + 1), 20, rec[20], date_format) # fecha de ultimo abono
      sheet.write((index + 1), 21, rec[21])
      sheet.write((index + 1), 22, rec[22], money_format) #importe de ultimo abono
      sheet.write((index + 1), 23, rec[23]) # estatus moroso