# -*- coding: utf-8 -*-

from asyncio.log import logger
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class PabsTaxes(models.Model):
    """Modelo para almacenar lo reportado en impuestos ISR y IVA de cada contrato"""
    _name = 'pabs.taxes'
    _description = 'Impuestos ISR e IVA PABS'
    _rec_name = 'id_contrato'

    id_contrato = fields.Many2one(comodel_name = 'pabs.contract', string = 'Contrato', required = True)
    fecha_estatus = fields.Date(string = 'Fecha de estatus', required = True)
    id_estatus = fields.Many2one(comodel_name = 'pabs.contract.status', string = "Status", required = True)
    id_motivo = fields.Many2one(comodel_name = 'pabs.contract.status.reason', string = "Motivo", required = True)
    costo = fields.Float(string = 'Costo', required = True)
    abonado = fields.Float(string = 'Abonado', required = True)
    iva = fields.Float(string = 'IVA', required = True)
    isr = fields.Float(string = 'Base para ISR', required = True)
    factor = fields.Float(string = 'Importe factor', required = True, default = 0)
    
    company_id = fields.Many2one(comodel_name = 'res.company', string = 'Compañia', required=True, default=lambda s: s.env.company.id)

    # EN ACAPULCO SE REPORTARÁ SOBRE LOS CONTRATOS ELABORADOS A PARTIR DE ENERO 2022
    # EN SALTILLO SE REPORTARÁ SOBRE LOS CONTRATOS ELABORADOS A PARTIR DE NOVIEMBRE 2021
    # EN TAMPICO SE REPORTARÁ SOBRE LOS CONTRATOS ELABORADOS A PARTIR DE FEBRERO 2022
    # EN MONCLOVA SE REPORTARÁ SOBRE LOS CONTRATOS ELABORADOS A PARTIR DE DICIEMBRE 2021

    # DIA 3 DEL MES COFIPLEM OBTIENE EL REPORTE DE COBRANZA DEL MES (SIN TOMAR EN CUENTA LOS REALIZADOS)
    # DIA 5 DEL MES COFIPLEM CALCULA UN FACTOR Y LO ENTREGA A SISTEMAS
    # DIA 6 DEL MES SISTEMAS GENERA REPORTE DE ISR PARA CONTRATOS REALIZADOS. TAMBIEN GENERA REPORTE DE ISR PARA CONTRATOS ACTIVOS CON EL FACTOR RECIBIDO.

    ###################################################
    ### REGISTRO DE CONTRATOS ACTIVOS (MES CON MES) ###
    ###################################################
    def RegistrarContratos(self, company_id, factor, fecha_minima_creacion, fecha_inicial, fecha_final):

        _logger.info("Comienza registro de impuestos de cobranza de contratos ACTIVOS del {} al {}".format(fecha_inicial, fecha_final))

        ### Consulta de contratos ###
        consulta = """
        SELECT 
            '{}' as fecha_estatus,
            est.id as id_estatus,
            mot.id as id_motivo,
            con.name as contrato,
            con.id as id_contrato,
            CAST( (fac.costo - COALESCE(nota.total, 0) - COALESCE(tras.total, 0))
                / 1.16 AS DECIMAL(10,2)) as costo,
            CAST(abo.total / 1.16 AS DECIMAL(10,2)) as abonado,
            fac.saldo as saldo,
            CAST(arb.commission_paid AS DECIMAL(10,2)) as iva,
            COALESCE(imp.isr_reportado_no_realizado, 0) as isr_reportado_no_realizado,
            COALESCE(imp.isr_reportado_realizado, 0) as isr_reportado_realizado,
            COALESCE(imp.isr_reportado_cancelado, 0) as isr_reportado_cancelado
        FROM pabs_contract AS con
        INNER JOIN pabs_contract_status AS est ON con.contract_status_item = est.id
        INNER JOIN pabs_contract_status_reason AS mot ON con.contract_status_reason = mot.id
        INNER JOIN pabs_comission_tree AS arb ON con.id = arb.contract_id
        INNER JOIN hr_job AS car ON arb.job_id = car.id AND car.name = 'IVA'
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
        INNER JOIN 
        (
            /*Cantidad abonada en el periodo*/
            SELECT 
                con.id as id_contrato,
                COALESCE(SUM(abo.amount), 0) as total
            FROM pabs_contract AS con 
            INNER JOIN account_payment AS abo ON con.id = abo.contract AND abo.state IN ('posted', 'sent', 'reconciled')
                WHERE con.company_id = {} /*Compañia*/
                AND abo.payment_date BETWEEN '{}' AND '{}' /*Fecha de oficina de abonos*/
                    GROUP BY con.id
        ) AS abo ON con.id = abo.id_contrato
        LEFT JOIN
        (
            /*Registros de impuestos*/
            SELECT 
                id_contrato as id_contrato,
                SUM( CASE WHEN est.status NOT IN ('REALIZADO', 'CANCELADO') AND mot.reason != 'REALIZADO POR COBRAR' THEN imp.isr ELSE 0 END) as isr_reportado_no_realizado,
                SUM( CASE WHEN est.status = 'REALIZADO' OR mot.reason = 'REALIZADO POR COBRAR' THEN imp.isr ELSE 0 END) as isr_reportado_realizado,
                SUM( CASE WHEN est.status = 'CANCELADO' THEN imp.isr ELSE 0 END) as isr_reportado_cancelado
            FROM pabs_taxes as imp
            INNER JOIN pabs_contract_status AS est ON imp.id_estatus = est.id
            INNER JOIN pabs_contract_status_reason AS mot ON imp.id_motivo = mot.id
                WHERE company_id = {} /*Compañia*/
                    GROUP BY id_contrato
        ) AS imp ON con.id = imp.id_contrato
            WHERE est.status NOT IN ('REALIZADO', 'CANCELADO') AND mot.reason != 'REALIZADO POR COBRAR'
            AND con.invoice_date >= '{}' /*Fecha de contratos de la nueva empresa*/
            AND con.company_id = {} /*Compañia*/
        """.format(fecha_final, company_id, company_id, company_id, company_id, fecha_inicial, fecha_final, company_id, fecha_minima_creacion, company_id)
        self.env.cr.execute(consulta)

        #Construye lista de contratos
        contratos = []
        for res in self.env.cr.fetchall():
            contratos.append({
                'fecha_estatus': res[0],
                'id_estatus': int(res[1]),
                'id_motivo': int(res[2]),
                'contrato': res[3],
                'id_contrato': int(res[4]),
                'costo': float(res[5]),
                'abonado': float(res[6]),
                'saldo': float(res[7]),
                'iva': float(res[8]),
                'isr_reportado_no_realizado': float(res[9]),
                'isr_reportado_realizado': float(res[10]),
                'isr_reportado_cancelado': float(res[11])
            })

        if not contratos:
            logger.info("No hay contratos")
            raise ValidationError("No se encontraron contratos")

        imp_obj = self.env['pabs.taxes'].sudo()

        # Calcular el total de la cobranza
        total_cobranza = 0
        for con in contratos:
            total_cobranza = total_cobranza + con['abonado']

        cantidad_contratos = len(contratos)
        for index, con in enumerate(contratos, 1):
            logger.info("{} de {}. {}".format(index, cantidad_contratos, con['contrato']))

            if con['isr_reportado_realizado'] != 0:
                logger.info("Ya existe registro con estatus realizado por {}".format(con['isr_reportado_realizado']))
                raise ValidationError("{} -> Ya existe registro con estatus realizado por {}".format(con['contrato'], con['isr_reportado_realizado']))

            if con['isr_reportado_cancelado'] != 0:
                logger.info("Ya existe registro con estatus cancelado por {}".format(con['isr_reportado_cancelado']))
                raise ValidationError("{} -> Ya existe registro con estatus cancelado por {}".format(con['contrato'], con['isr_reportado_cancelado']))

            isr = (con['abonado'] / total_cobranza) * factor

            imp_obj.create({
                'id_contrato': con['id_contrato'],
                'fecha_estatus': con['fecha_estatus'],
                'id_estatus': con['id_estatus'],
                'id_motivo': con['id_motivo'],
                'costo': con['costo'],
                'abonado': con['abonado'],
                'iva': con['iva'],
                'isr': isr,
                'company_id': company_id
            })

    ########################################
    ### REGISTRO DE CONTRATOS REALIZADOS ###
    ########################################
    def RegistrarContratosRealizados(self, company_id, fecha_minima_creacion, fecha_inicial, fecha_final):
        _logger.info("Comienza registro de impuestos de contratos REALIZADOS del {} al {}".format(fecha_inicial, fecha_final))

        ### Consulta de contratos Realizados ###
        consulta = """
        SELECT 
            CAST(con.date_of_last_status AS DATE) as fecha_estatus,
            est.id as id_estatus,
            mot.id as id_motivo,
            con.name as contrato,
            con.id as id_contrato,
            CAST( (fac.costo - COALESCE(nota.total, 0) - COALESCE(tras.total, 0))
                / 1.16 AS DECIMAL(10,2)) as costo,
            CAST( (fac.abonado - COALESCE(nota.total, 0) - COALESCE(tras.total, 0)) 
                / 1.16 AS DECIMAL(10,2)) as abonado,
            fac.saldo as saldo,
            CAST( arb.commission_paid AS DECIMAL(10,2)) as iva,
            CAST( 
                ( fac.costo - COALESCE(nota.total, 0) - COALESCE(tras.total, 0)) / 1.16 
            AS DECIMAL(10,2)) as isr,
            COALESCE(imp.isr_reportado_no_realizado, 0) as isr_reportado_no_realizado,
            COALESCE(imp.isr_reportado_realizado, 0) as isr_reportado_realizado,
            COALESCE(imp.isr_reportado_cancelado, 0) as isr_reportado_cancelado
        FROM pabs_contract AS con
        INNER JOIN pabs_contract_status AS est ON con.contract_status_item = est.id
        INNER JOIN pabs_contract_status_reason AS mot ON con.contract_status_reason = mot.id
        INNER JOIN pabs_comission_tree AS arb ON con.id = arb.contract_id
        INNER JOIN hr_job AS car ON arb.job_id = car.id AND car.name = 'IVA'
        INNER JOIN
        (
            /* Factura */
            SELECT 
                fac.contract_id as id_contrato,
                SUM(fac.amount_total) as costo,
                SUM(fac.amount_residual) as saldo,
                SUM(fac.amount_total) - SUM(fac.amount_residual) as abonado
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
        LEFT JOIN
        (
            /*Registros de impuestos*/
            SELECT 
                id_contrato as id_contrato,
                SUM( CASE WHEN est.status NOT IN ('REALIZADO', 'CANCELADO') AND mot.reason != 'REALIZADO POR COBRAR' THEN imp.isr ELSE 0 END) as isr_reportado_no_realizado,
                SUM( CASE WHEN est.status = 'REALIZADO' OR mot.reason = 'REALIZADO POR COBRAR' THEN imp.isr ELSE 0 END) as isr_reportado_realizado,
                SUM( CASE WHEN est.status = 'CANCELADO' THEN imp.isr ELSE 0 END) as isr_reportado_cancelado
            FROM pabs_taxes as imp
            INNER JOIN pabs_contract_status AS est ON imp.id_estatus = est.id
            INNER JOIN pabs_contract_status_reason AS mot ON imp.id_motivo = mot.id
                WHERE company_id = {} /*Compañia*/
                    GROUP BY id_contrato
        ) AS imp ON con.id = imp.id_contrato
            WHERE (est.status = 'REALIZADO' OR mot.reason = 'REALIZADO POR COBRAR')
            AND con.invoice_date >= '{}' /*Fecha de contratos de la nueva empresa*/
            AND CAST(con.date_of_last_status AS DATE) BETWEEN '{}' AND '{}' /*Fechas de realizado*/
            AND con.company_id = {} /*Compañia*/
        """.format(company_id, company_id, company_id, company_id, fecha_minima_creacion, fecha_inicial, fecha_final, company_id)
        self.env.cr.execute(consulta)

        #Construye lista de contratos
        contratos = []
        for res in self.env.cr.fetchall():
            contratos.append({
                'fecha_estatus': res[0],
                'id_estatus': int(res[1]),
                'id_motivo': int(res[2]),
                'contrato': res[3],
                'id_contrato': int(res[4]),
                'costo': float(res[5]),
                'abonado': float(res[6]),
                'saldo': float(res[7]),
                'iva': float(res[8]),
                'isr': float(res[9]),
                'isr_reportado_no_realizado': float(res[10]),
                'isr_reportado_realizado': float(res[11]),
                'isr_reportado_cancelado': float(res[12])
            }) 

        if not contratos:
            logger.info("No hay contratos")
            raise ValidationError("No hay contratos")

        imp_obj = self.env['pabs.taxes'].sudo()

        cantidad_contratos = len(contratos)
        for index, con in enumerate(contratos, 1):
            logger.info("{} de {}. {}".format(index, cantidad_contratos, con['contrato']))

            if con['isr_reportado_realizado'] != 0:
                logger.info("Ya existe registro con estatus realizado por {}".format(con['isr_reportado_realizado']))
                raise ValidationError("{} -> Ya existe registro con estatus realizado por {}".format(con['contrato'], con['isr_reportado_realizado']))

            if con['isr_reportado_cancelado'] != 0:
                logger.info("Ya existe registro con estatus cancelado por {}".format(con['isr_reportado_cancelado']))
                raise ValidationError("{} -> Ya existe registro con estatus cancelado por {}".format(con['contrato'], con['isr_reportado_cancelado']))
            
            imp_obj.create({
                'id_contrato': con['id_contrato'],
                'fecha_estatus': con['fecha_estatus'],
                'id_estatus': con['id_estatus'],
                'id_motivo': con['id_motivo'],
                'costo': con['costo'],
                'abonado': con['abonado'],
                'iva': con['iva'],
                'isr': con['isr'] - con['isr_reportado_no_realizado'],
                'company_id': company_id
            })

    #######################################################
    ### REGISTRO DE CONTRATOS CANCELADOS (CADA 3 MESES) ###
    #######################################################
    def RegistrarContratosCancelados(self, company_id, fecha_minima_creacion, fecha_inicial, fecha_final):
        _logger.info("Comienza registro de impuestos de contratos CANCELADOS del {} al {}".format(fecha_inicial, fecha_final))

        ### Consulta de contratos ###
        consulta = """
        SELECT 
            CAST(con.date_of_last_status AS DATE) as fecha_estatus,
            est.id as id_estatus,
            mot.id as id_motivo,
            con.name as contrato,
            con.id as id_contrato,
            CAST( (fac.costo - COALESCE(nota.total, 0) - COALESCE(tras.total, 0))
                / 1.16 AS DECIMAL(10,2)) as costo,
            CAST( abo.total / 1.16 AS DECIMAL(10,2)) as abonado,
            fac.saldo as saldo,
            CAST(arb.commission_paid AS DECIMAL(10,2)) as iva,
            COALESCE(imp.isr_reportado_no_realizado, 0) as isr_reportado_no_realizado,
            COALESCE(imp.isr_reportado_realizado, 0) as isr_reportado_realizado,
            COALESCE(imp.isr_reportado_cancelado, 0) as isr_reportado_cancelado
        FROM pabs_contract AS con
        INNER JOIN pabs_contract_status AS est ON con.contract_status_item = est.id
        INNER JOIN pabs_contract_status_reason AS mot ON con.contract_status_reason = mot.id
        INNER JOIN pabs_comission_tree AS arb ON con.id = arb.contract_id
        INNER JOIN hr_job AS car ON arb.job_id = car.id AND car.name = 'IVA'
        INNER JOIN
        (
            /*Factura*/
            SELECT 
                fac.contract_id as id_contrato,
                SUM(fac.amount_total) as costo,
                SUM(fac.amount_residual) as saldo,
                SUM(fac.amount_total) - SUM(fac.amount_residual) as abonado
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
        INNER JOIN 
        (
            /*Cantidad abonada de los contratos*/
            SELECT 
                con.id as id_contrato,
                COALESCE(SUM(abo.amount), 0) as total
            FROM pabs_contract AS con 
            INNER JOIN account_payment AS abo ON con.id = abo.contract AND abo.state IN ('posted', 'sent', 'reconciled')
                WHERE con.company_id = {} /*Compañia*/
                    GROUP BY con.id
        ) AS abo ON con.id = abo.id_contrato
        LEFT JOIN
        (
            /*Registros de impuestos*/
            SELECT 
                id_contrato as id_contrato,
                SUM( CASE WHEN est.status NOT IN ('REALIZADO', 'CANCELADO') AND mot.reason != 'REALIZADO POR COBRAR' THEN imp.isr ELSE 0 END) as isr_reportado_no_realizado,
                SUM( CASE WHEN est.status = 'REALIZADO' OR mot.reason = 'REALIZADO POR COBRAR' THEN imp.isr ELSE 0 END) as isr_reportado_realizado,
                SUM( CASE WHEN est.status = 'CANCELADO' THEN imp.isr ELSE 0 END) as isr_reportado_cancelado
            FROM pabs_taxes as imp
            INNER JOIN pabs_contract_status AS est ON imp.id_estatus = est.id
            INNER JOIN pabs_contract_status_reason AS mot ON imp.id_motivo = mot.id
                WHERE company_id = {} /*Compañia*/
                    GROUP BY id_contrato
        ) AS imp ON con.id = imp.id_contrato
            WHERE est.status IN ('CANCELADO')
            AND con.invoice_date >= '{}' /*Fecha de contratos de la nueva empresa*/
            AND CAST(con.date_of_last_status AS DATE) BETWEEN '{}' AND '{}' /*Fechas de estatus*/
            AND con.company_id = {} /*Compañia*/
        """.format(company_id, company_id, company_id, company_id, company_id, fecha_minima_creacion, fecha_inicial, fecha_final, company_id)
        self.env.cr.execute(consulta)

        #Construye lista de contratos
        contratos = []
        for res in self.env.cr.fetchall():
            contratos.append({
                'fecha_estatus': res[0],
                'id_estatus': int(res[1]),
                'id_motivo': int(res[2]),
                'contrato': res[3],
                'id_contrato': int(res[4]),
                'costo': float(res[5]),
                'abonado': float(res[6]),
                'saldo': float(res[7]),
                'iva': float(res[8]),
                'isr_reportado_no_realizado': float(res[9]),
                'isr_reportado_realizado': float(res[10]),
                'isr_reportado_cancelado': float(res[11])
            }) 

        if not contratos:
            logger.info("No hay contratos")
            raise ValidationError("No hay contratos")

        imp_obj = self.env['pabs.taxes'].sudo()

        cantidad_contratos = len(contratos)
        for index, con in enumerate(contratos, 1):
            logger.info("{} de {}. {}".format(index, cantidad_contratos, con['contrato']))

            if con['isr_reportado_realizado'] != 0:
                logger.info("Ya existe registro con estatus realizado por {}".format(con['isr_reportado_realizado']))
                raise ValidationError("{} -> Ya existe registro con estatus realizado por {}".format(con['contrato'], con['isr_reportado_realizado']))

            if con['isr_reportado_cancelado'] != 0:
                logger.info("Ya existe registro con estatus cancelado por {}".format(con['isr_reportado_cancelado']))
                raise ValidationError("{} -> Ya existe registro con estatus cancelado por {}".format(con['contrato'], con['isr_reportado_cancelado']))

            imp_obj.create({
                'id_contrato': con['id_contrato'],
                'fecha_estatus': con['fecha_estatus'],
                'id_estatus': con['id_estatus'],
                'id_motivo': con['id_motivo'],
                'costo': con['costo'],
                'abonado': con['abonado'],
                'iva': con['iva'],
                'isr': con['abonado'] - con['isr_reportado_no_realizado'],
                'company_id': company_id
            })