# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz

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
    ### INSTANCIAMOS OBJETOS
    contract_obj = self.env['pabs.contract']
    contract_status_obj = self.env['pabs.contract.status']
    ### BUSCANDO PARAMETROS DE ENCABEZADO
    logo = self.env.user.company_id.logo
    date = data.get('data') or fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General'))

    status_id = contract_status_obj.search([('status','=','ACTIVO')])

    ### BUSCAMOS TODOS LOS CONTRATOS
    all_contracts = contract_obj.search([
        ('state','=','contract'),
        ('contract_status_item','in',status_id.ids)], order="name")

    ### TRAEMOS TODOS LOS COBRADORES
    collectors = all_contracts.mapped('debt_collector.name')

    data = {}

    ### CICLAMOS LA LISTA DE COBRADORES
    for collector in collectors:
        data_rec = []
        ### FILTRAMOS LOS CONTRATOS PERTENECIENTES A ESE COBRADOR
        contract_ids = all_contracts.filtered(lambda r: r.debt_collector.name == collector)

        ### RECORREMOS LOS CONTRATOS
        for contract_id in contract_ids:
            ### SI EL CONTRATO ES PAGO SEMANAL Y TIENE MAS DE 15 DIAS SIN ABONAR
            if contract_id.way_to_payment == 'weekly' and contract_id.days_without_payment > 14:
                last_payment = contract_id.payment_ids.filtered(lambda r: r.state == 'posted').sorted(key=lambda r: r.payment_date)[-1].payment_date
                data_rec.append({
                    'contract_name' : contract_id.name,
                    'partner_name' : contract_id.full_name,
                    'address' : "{} {}".format(contract_id.street_name_toll, contract_id.street_number_toll),
                    'colony' : contract_id.toll_colony_id.name or '',
                    'municipality' : contract_id.toll_municipallity_id.name or '',
                    'last_payment' : last_payment or '',
                    'period' : 'S'
                })
            ### SI EL CONTRATO ES PAGO QUINCENAL Y TIENE MAS DE 30 DÍAS SIN ABONAR
            elif contract_id.way_to_payment == 'biweekly' and contract_id.days_without_payment > 30:
                last_payment = contract_id.payment_ids.filtered(lambda r: r.state == 'posted').sorted(key=lambda r: r.payment_date)[-1].payment_date
                data_rec.append({
                    'contract_name' : contract_id.name,
                    'partner_name' : contract_id.full_name,
                    'address' : "{} {}".format(contract_id.street_name_toll, contract_id.street_number_toll),
                    'colony' : contract_id.toll_colony_id.name or '',
                    'municipality' : contract_id.toll_municipallity_id.name or '',
                    'last_payment' : last_payment or '',
                    'period' : 'Q'
                })
            ### SI EL CONTRATO ES PAGO MENSUAL Y TIENE MAS DE 60 DIAS SIN ABONAR
            elif contract_id.way_to_payment == 'monthly' and contract_id.days_without_payment > 60:
                last_payment = contract_id.payment_ids.filtered(lambda r: r.state == 'posted').sorted(key=lambda r: r.payment_date)[-1].payment_date
                data_rec.append({
                    'contract_name' : contract_id.name,
                    'partner_name' : contract_id.full_name,
                    'address' : "{} {}".format(contract_id.street_name_toll, contract_id.street_number_toll),
                    'colony' : contract_id.toll_colony_id.name or '',
                    'municipality' : contract_id.toll_municipallity_id.name or '',
                    'last_payment' : last_payment or '',
                    'period' : 'M'
                })
        data.update({
            collector: data_rec,
        })

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
      SELECT *
        FROM (
            SELECT 
            c.invoice_date AS "Fecha de contrato",
            c.name AS "contrato",
            CONCAT(c.partner_name,
                    ' ',
                    c.partner_fname,
                    ' ',
                    c.partner_mname) AS "Cliente",
            CONCAT(c.street_name_toll,
                    ' #',
                    c.street_number_toll) AS "Domicilio",
            col.name AS "Colonia",
            loc.name AS "Localidad",
            c.between_streets_toll AS "Entre calles",
            c.phone AS "Telefono",
            prom.name AS "Promotor",
            cob.name AS "Cobrador",
            CASE
                WHEN c.way_to_payment = 'weekly' THEN 'S'
                WHEN c.way_to_payment = 'biweekly' THEN 'Q'
                WHEN c.way_to_payment = 'monthly' THEN 'M'
            END AS "Forma de Pago",
            c.date_of_last_status "Fecha estatus",
            pEst.status AS "Estatus",
            pMot.reason AS "Motivo",
            c.id AS "id contrato",
            c.payment_amount AS "Monto pago actual",
            prod.name AS "Servicio",
            ppl.fixed_price AS "Costo",
            am.amount_residual AS "Saldo",
            0 AS "Ultimo abono",
            (Select MAX(date_receipt) from account_payment as last where last.contract = c.id) AS "Fecha de ultimo abono",
            (SELECT 
                    P.name
                FROM
                    account_payment AS a
                        LEFT JOIN
                    hr_employee AS p ON a.debt_collector_code = p.id
                WHERE
                    a.id = (SELECT 
                            MAX(ab.id)
                        FROM
                            account_payment ab
                        WHERE
                            (ab.reference = 'stationary'
                                OR ab.reference = 'payment'
                                OR ab.reference = 'surplus')
                                AND ab.contract = c.id)) AS "Ultimo cobrador",
            (SELECT 
                    a.amount
                FROM
                    account_payment AS a
                WHERE
                    a.id = (SELECT 
                            MAX(ab.id)
                        FROM
                            account_payment AS ab
                        WHERE
                            (ab.reference = 'stationary'
                                OR ab.reference = 'payment'
                                OR ab.reference = 'surplus')
                                AND ab.contract = c.id)) AS "Importe ultimo abono",
            CASE
                WHEN
                    c.contract_status_item <> 21
                        THEN
                            (CASE
                                WHEN c.contract_status_item = 11 THEN 2
                                WHEN c.contract_status_item = 14 THEN 14
                                WHEN c.contract_status_item = 18 THEN 13
                                WHEN c.contract_status_item = 19 THEN 15
                                WHEN c.contract_status_item = 20 THEN 16
                                WHEN c.contract_status_item = 13 THEN 3
                                WHEN c.contract_status_item = 12 THEN 4
                                WHEN c.contract_status_item = 17 THEN 5
                                WHEN c.contract_status_item = 16 THEN 6
                            END)
                
                WHEN c.contract_status_item = 21 AND CURRENT_DATE - GREATEST(c.date_first_payment, (Select MAX(date_receipt) from account_payment as last where last.contract = c.id)) <= (
                        CASE
                            WHEN way_to_payment = 'weekly' THEN 14
                            WHEN way_to_payment = 'biweekly' THEN 30
                            WHEN way_to_payment = 'monthly' THEN 60
                        END)
                    THEN 21

                WHEN c.contract_status_item = 21 AND CURRENT_DATE - GREATEST(c.date_first_payment, (Select MAX(date_receipt) from account_payment as last where last.contract = c.id)) > (
                            CASE
                                WHEN way_to_payment = 'weekly' THEN 14
                                WHEN way_to_payment = 'biweekly' THEN 30
                                WHEN way_to_payment = 'monthly' THEN 60
                            END)
                        THEN 7
            END AS estatus_moroso
        FROM
            pabs_contract AS c
                LEFT JOIN
            colonias AS col ON col.id = c.toll_colony_id
                LEFT JOIN
            res_locality AS loc ON loc.id = c.toll_municipallity_id
                LEFT JOIN
            hr_employee AS prom ON prom.id = c.sale_employee_id
                LEFT JOIN
            pabs_contract_status AS pEst ON pEst.id = c.contract_status_item
                LEFT JOIN
            pabs_contract_status_reason AS pMot ON pMot.id = c.contract_status_reason
                LEFT JOIN
            hr_employee AS cob ON cob.id = c.debt_collector
                LEFT JOIN
            stock_production_lot AS sl ON sl.id = c.lot_id
                LEFT JOIN
            product_template AS prod ON prod.id = sl.product_id
                LEFT JOIN
            product_pricelist_item AS ppl ON ppl.product_id = sl.product_id
                LEFT JOIN
            account_move AS am ON am.contract_id = c.id
        WHERE
            am.type = 'out_invoice'
                AND c.invoice_date <= CURRENT_DATE
                AND c.state = 'contract'
                AND c.company_id = {}
        ORDER BY pEst.id , c.invoice_date )
    AS mor
    WHERE mor.estatus_moroso = 7""".format(company_id)
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