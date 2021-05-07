# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request, Response
import datetime
import json
import logging

_logger = logging.getLogger(__name__)


class APIREST(http.Controller):

  @http.route('/api/search', type='http', auth='none',methods=['POST'], csrf=False)
  def search_query(self, **kargs):
    response_header = {'Content-Type': 'application/json'}
    cr = request.cr
    if kargs.get('query'):
      try:
        cr.execute(kargs.get('query'))
        records = []
        headers = [d[0] for d in cr.description]
        for res in cr.fetchall():
          data = {}
          for ind, rec in enumerate(headers):
            if isinstance(res[ind], datetime.date):
              value = res[ind].strftime("%d/%m/%Y")
            else:
              value = res[ind]
            data.update({
              headers[ind] : value
            })
          records.append(data)
          response = {
            'result' : records
          }
        return Response(json.dumps(response),headers=response_header)
      except Exception as e:
        return str(e)
    return Response("Petición Denegada", status=400)


  @http.route('/api/get/flujo', type='http', auth='none', csrf=False)
  def get_flujo(self):
    response_header = {'Content-Type': 'application/json'}
    cr = request.cr
    query = """SELECT 
          Grupo,
          Plaza, 
          TipoDato,
            Fecha, 
            CodigoCuenta, 
            NombreCuenta,
            TipoMovimiento, 
            Agrupacion, 
            SubAgrupacion, 
            CodigoIDFlujo, 
            ConceptoFlujo, 
            Diario, 
            TipoPoliza, 
            Folio, 
            ConceptoMovimiento, 
            Referencia,
            ImporteMovimiento, 
            SaldoSemanal, 
            SaldoMensual, 
            saldoAnual
        FROM
        (
          SELECT 
            *
          FROM
          (
            SELECT 
                'Occidente' as Grupo,     
                'Acapulco' as Plaza,
                'Financieros' as TipoDato,
                invoice_date as Fecha,
                DATE_PART('year', enc.invoice_date) as año, 
              DATE_PART('month', enc.invoice_date) as mes,
              DATE_PART('week', enc.invoice_date) as Semana,
              Substring(cue.code,1, POSITION('.' IN cue.code) - 1) as CodigoCuenta,
              cue.name as NombreCuenta,
              'No identificado' as TipoMovimiento,
                'No identificado' as Agrupacion,
                'No identificado' as SubAgrupacion,
                'No identificado' as CodigoIDFlujo,
                'No identificado' as ConceptoFlujo,
                jou.name as Diario,
                'NA' AS TipoPoliza,
                enc.id as Folio,
                COALESCE(mov.name,'Sin concepto') AS ConceptoMovimiento,
                mov.ref as Referencia,
                mov.Debit AS Cargos,
              mov.Credit AS Abonos,
              (mov.Debit - mov.Credit) as ImporteMovimiento,
              0 as SaldoSemanal,
                0 as SaldoMensual,
                0 as saldoAnual
            FROM account_move as enc
            LEFT JOIN account_move_line as mov on enc.id = mov.move_id
            LEFT JOIN account_account as cue on mov.account_id = cue.id
            LEFT JOIN account_journal AS jou ON enc.journal_id = jou.id
              WHERE Substring(cue.code,1, POSITION('.' IN cue.code) - 1) like '101%' 
              OR Substring(cue.code,1, POSITION('.' IN cue.code) - 1) like '102%' 
              OR Substring(cue.code,1, POSITION('.' IN cue.code) - 1) like '103%'
          ) as detalle
        
        UNION ALL
          SELECT 
            Grupo,
            Plaza, 
            TipoDato,
              Fecha, 
              Año, 
              0 as Mes, 
              Semana,
            CodigoCuenta, 
            NombreCuenta,
            'Saldo semanal' as TipoMovimiento,
            'Saldo semanal' as Agrupacion,
            'Saldo semanal' as SubAgrupacion,
            'Saldo semanal' as CodigoIDFlujo,
            'Saldo semanal' as ConceptoFlujo,
            'Saldo' as Diario,
            'Saldo' as TipoPoliza,
            0 as Folio,
            'Saldo' as ConceptoMovimiento,
            '-' as Referencia,
            0 AS Cargos,
            0 AS Abonos,
            0 AS ImporteMovimiento,
            sum(ImporteMovimiento) over (Partition by CodigoCuenta, Año order by CodigoCuenta, Fecha) as SaldoSemanal,
              0 as SaldoMensual,
              0 as saldoAnual
          FROM
          (
            SELECT 
              Grupo,
              Plaza, 
              TipoDato, 
              Fecha + (7 - DATE_PART('dow', Fecha)) * INTERVAL '1 day' as Fecha,
                DATE_PART('year', Fecha) as Año,
                DATE_PART('week', Fecha) as Semana,
                CodigoCuenta,
                NombreCuenta,
                (Sum(Cargos)-SUM(Abonos)) as ImporteMovimiento
            FROM 
            (
              SELECT 
                  'Occidente' as Grupo,     
                  'Acapulco' as Plaza,
                  'Financieros' as TipoDato,
                  invoice_date as Fecha,
                  DATE_PART('year', enc.invoice_date) as año, 
                DATE_PART('month', enc.invoice_date) as mes,
                DATE_PART('week', enc.invoice_date) as Semana,
                Substring(cue.code,1, POSITION('.' IN cue.code) - 1) as CodigoCuenta,
                cue.name as NombreCuenta,
                'No identificado' as TipoMovimiento,
                  'No identificado' as Agrupacion,
                  'No identificado' as SubAgrupacion,
                  'No identificado' as CodigoIDFlujo,
                  'No identificado' as ConceptoFlujo,
                  jou.name as Diario,
                  'NA' AS TipoPoliza,
                  enc.id as Folio,
                  COALESCE(mov.name,'Sin concepto') AS ConceptoMovimiento,
                  mov.ref as Referencia,
                  mov.Debit AS Cargos,
                mov.Credit AS Abonos,
                (mov.Debit - mov.Credit) as ImporteMovimiento,
                0 as SaldoSemanal,
                  0 as SaldoMensual,
                  0 as saldoAnual
              FROM account_move as enc
              LEFT JOIN account_move_line as mov on enc.id = mov.move_id
              LEFT JOIN account_account as cue on mov.account_id = cue.id
              LEFT JOIN account_journal AS jou ON enc.journal_id = jou.id
                WHERE Substring(cue.code,1, POSITION('.' IN cue.code) - 1) like '101%' 
                OR Substring(cue.code,1, POSITION('.' IN cue.code) - 1) like '102%' 
                OR Substring(cue.code,1, POSITION('.' IN cue.code) - 1) like '103%'
        
            ) as x1
              GROUP BY Grupo, Plaza, TipoDato, Fecha + (7 - DATE_PART('dow', Fecha)) * INTERVAL '1 day', DATE_PART('year', Fecha), DATE_PART('week', Fecha), CodigoCuenta, NombreCuenta     
          ) AS semanales
        
        UNION ALL
          Select 
            Grupo,
            Plaza, 
            TipoDato, 
            Fecha, 
            Año, 
            Mes, 
            0 AS Semana,
            CodigoCuenta, 
            NombreCuenta,
            'Saldo mensual' as TipoMovimiento,
            'Saldo mensual' as Agrupacion,
            'Saldo mensual' as SubAgrupacion,
            'Saldo mensual' as CodigoIDFlujo,
            'Saldo mensual' as ConceptoFlujo,
            'Saldo' as Diario,
            'Saldo' as TipoPoliza,
            0 as Folio,
            'Saldo' as ConceptoMovimiento,
            '-' as Referencia,
            0 AS Cargos,
            0 AS Abonos,
            0 AS ImporteMovimiento,
            0 AS SaldoSemanal,
            sum(ImporteMovimiento) over (Partition by CodigoCuenta, Año order by CodigoCuenta, Fecha) as SaldoMensual,
            0 as saldoAnual
          FROM
          ( 
            SELECT 
              Grupo,
              Plaza, 
              TipoDato, 
              (date_trunc('MONTH', (Fecha)::date) + INTERVAL '1 MONTH - 1 day')::DATE as Fecha,
                DATE_PART('year', Fecha) as Año,
              DATE_PART('month', Fecha) as Mes,
              CodigoCuenta, 
              NombreCuenta, 
              (Sum(Cargos)-SUM(Abonos)) as ImporteMovimiento
            FROM 
            (
              SELECT 
                  'Occidente' as Grupo,     
                  'Acapulco' as Plaza,
                  'Financieros' as TipoDato,
                  invoice_date as Fecha,
                  DATE_PART('year', enc.invoice_date) as año, 
                DATE_PART('month', enc.invoice_date) as mes,
                DATE_PART('week', enc.invoice_date) as Semana,
                Substring(cue.code,1, POSITION('.' IN cue.code) - 1) as CodigoCuenta,
                cue.name as NombreCuenta,
                'No identificado' as TipoMovimiento,
                  'No identificado' as Agrupacion,
                  'No identificado' as SubAgrupacion,
                  'No identificado' as CodigoIDFlujo,
                  'No identificado' as ConceptoFlujo,
                  jou.name as Diario,
                  'NA' AS TipoPoliza,
                  enc.id as Folio,
                  COALESCE(mov.name,'Sin concepto') AS ConceptoMovimiento,
                  mov.ref as Referencia,
                  mov.Debit AS Cargos,
                mov.Credit AS Abonos,
                (mov.Debit - mov.Credit) as ImporteMovimiento,
                0 as SaldoSemanal,
                  0 as SaldoMensual,
                  0 as saldoAnual
              FROM account_move as enc
              LEFT JOIN account_move_line as mov on enc.id = mov.move_id
              LEFT JOIN account_account as cue on mov.account_id = cue.id
              LEFT JOIN account_journal AS jou ON enc.journal_id = jou.id
                WHERE Substring(cue.code,1, POSITION('.' IN cue.code) - 1) like '101%' 
                OR Substring(cue.code,1, POSITION('.' IN cue.code) - 1) like '102%' 
                OR Substring(cue.code,1, POSITION('.' IN cue.code) - 1) like '103%'
            ) as y1
              GROUP BY Grupo,Plaza, TipoDato, (date_trunc('MONTH', (Fecha)::date) + INTERVAL '1 MONTH - 1 day')::DATE , DATE_PART('year', Fecha), DATE_PART('month', Fecha),CodigoCuenta, NombreCuenta
          ) AS mensuales
        
        UNION ALL
          SELECT 
            Grupo,Plaza, TipoDato, Fecha, Año, 
            0 AS Mes, 
            0 AS Semana,
            CodigoCuenta, 
            NombreCuenta,
            'Saldo anuales' as TipoMovimiento,
            'Saldo anuales' as Agrupacion,
            'Saldo anuales' as SubAgrupacion,
            'Saldo anuales' as CodigoIDFlujo,
            'Saldo anuales' as ConceptoFlujo,
            'Saldo' as Diario,
            'Saldo' as TipoPoliza,
            0 as Folio,
            'Saldo' as ConceptoMovimiento,
            '-' as Referencia,
            0 AS Cargos,
            0 AS Abonos,
            0 AS ImporteMovimiento,
            0 AS SaldoSemanal,
            0 AS SaldoMensual,
            sum(ImporteMovimiento) over (Partition by CodigoCuenta order by CodigoCuenta, Fecha ) as saldoAnual
          FROM
          ( 
            SELECT
              Grupo,
              Plaza, 
              TipoDato, 
              Fecha + (365 - DATE_PART('doy', Fecha)) * INTERVAL '1 day' as Fecha,
              DATE_PART('year', Fecha) as Año,
              CodigoCuenta, 
              NombreCuenta,
              (Sum(Cargos)-SUM(Abonos)) as ImporteMovimiento
            FROM
            (
              SELECT 
                  'Occidente' as Grupo,     
                  'Acapulco' as Plaza,
                  'Financieros' as TipoDato,
                  invoice_date as Fecha,
                  DATE_PART('year', enc.invoice_date) as año, 
                DATE_PART('month', enc.invoice_date) as mes,
                DATE_PART('week', enc.invoice_date) as Semana,
                Substring(cue.code,1, POSITION('.' IN cue.code) - 1) as CodigoCuenta,
                cue.name as NombreCuenta,
                'No identificado' as TipoMovimiento,
                  'No identificado' as Agrupacion,
                  'No identificado' as SubAgrupacion,
                  'No identificado' as CodigoIDFlujo,
                  'No identificado' as ConceptoFlujo,
                  jou.name as Diario,
                  'NA' AS TipoPoliza,
                  enc.id as Folio,
                  COALESCE(mov.name,'Sin concepto') AS ConceptoMovimiento,
                  mov.ref as Referencia,
                  mov.Debit AS Cargos,
                mov.Credit AS Abonos,
                (mov.Debit - mov.Credit) as ImporteMovimiento,
                0 as SaldoSemanal,
                  0 as SaldoMensual,
                  0 as saldoAnual
              FROM account_move as enc
              LEFT JOIN account_move_line as mov on enc.id = mov.move_id
              LEFT JOIN account_account as cue on mov.account_id = cue.id
              LEFT JOIN account_journal AS jou ON enc.journal_id = jou.id
                WHERE Substring(cue.code,1, POSITION('.' IN cue.code) - 1) like '101%' 
                OR Substring(cue.code,1, POSITION('.' IN cue.code) - 1) like '102%' 
                OR Substring(cue.code,1, POSITION('.' IN cue.code) - 1) like '103%'
            ) as Z1
              GROUP BY Grupo,Plaza, TipoDato, Fecha + (365 - DATE_PART('doy', Fecha)) * INTERVAL '1 day', DATE_PART('year', Fecha), CodigoCuenta, NombreCuenta
          ) AS anuales    
        ) as consulta"""
    try:
      cr.execute(query)
      records = []
      headers = [d[0] for d in cr.description]
      for res in cr.fetchall():
        data = {}
        for ind, rec in enumerate(headers):
          if isinstance(res[ind], datetime.date):
            value = res[ind].strftime("%d/%m/%Y")
          else:
            value = res[ind]
          data.update({
            headers[ind] : value
          })
        records.append(data)
        response = {
          'result' : records
        }
      return Response(json.dumps(response),headers=response_header)
    except Exception as e:
      return str(e)
    return Response("Petición Denegada", status=400)

  @http.route('/api/get/funeraria', type='http', auth='none', csrf=False)
  def get_mortuary_service(self):
    response_header = {'Content-Type': 'application/json'}
    cr = request.cr
    query =  """SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      'Guadalajara' as Plaza,
      bita.ii_fecha_creacion as Fecha,
      'Funeraria' as AreaDeNegocio,
      'Funerarias' as CentroCosto,
      suc.name as SucursaluOficina,
      'No aplica' as CodSubCta,
      'No aplica' as TipoEstadistico,
      'No aplica' CodigoCuenta,
      tipo.name as Estadistico,
      bita.name as Bitacora,
      1 AS Servicios,
      1 AS ServiciosPorSuOrigen,
      0 AS ServXTipoPABS,
      0 AS ServXLugarVelacion,
      0 AS ServXTipo,
      0 AS ServXCertMedico,
      0 AS ServXEmbalsamado,
      0 AS ServXLugarCremacion,
      0 AS ServXAplicaSeguro,
      ser.name as estatus_servicio,
      bita.cs_nuevo_comentario as Notes,
      '' as U_observacrm
    FROM mortuary AS bita
    LEFT JOIN ds_sucursal_velacion AS suc on bita.ds_sucursal_de_velacion = suc.id
    LEFT JOIN ii_servicio AS ser on bita.ii_servicio = ser.id
    LEFT JOIN ds_tipo_servicio AS tipo on bita.ds_tipo_de_servicio = tipo.id
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      'Guadalajara' as Plaza,
      bita.ii_fecha_creacion as Fecha,
      'Funeraria' as AreaDeNegocio,
      'Funerarias' as CentroCosto,
      suc.name as SucursaluOficina,
      'No aplica' as CodSubCta,
      'No aplica' as TipoEstadistico,
      'No aplica' CodigoCuenta,
      CASE
        WHEN inter.name = 'No' THEN 'LOCAL'
        WHEN inter.name = 'Si' THEN 'INTERPLAZA'
        ELSE NULL
      END as Estadistico,
      bita.name as Bitacora,
      0 AS Servicios,
      0 AS ServiciosPorSuOrigen,
      1 AS ServXTipoPABS,
      0 AS ServXLugarVelacion,
      0 AS ServXTipo,
      0 AS ServXCertMedico,
      0 AS ServXEmbalsamado,
      0 AS ServXLugarCremacion,
      0 AS ServXAplicaSeguro,
      ser.name as estatus_servicio,
      bita.cs_nuevo_comentario as Notes,
      '' as U_observacrm
    FROM mortuary AS bita
    LEFT JOIN ds_sucursal_velacion AS suc on bita.ds_sucursal_de_velacion = suc.id
    LEFT JOIN ii_servicio AS ser on bita.ii_servicio = ser.id
    LEFT JOIN ds_interplaza as inter on bita.ds_interplaza = inter.id
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      'Guadalajara' as Plaza,
      bita.ii_fecha_creacion as Fecha,
      'Funeraria' as AreaDeNegocio,
      'Funerarias' as CentroCosto,
      suc.name as SucursaluOficina,
      'No aplica' as CodSubCta,
      'No aplica' as TipoEstadistico,
      'No aplica' CodigoCuenta,
      '' as Estadistico,
      bita.name as Bitacora,
      0 AS Servicios,
      0 AS ServiciosPorSuOrigen,
      0 AS ServXTipoPABS,
      1 AS ServXLugarVelacion,
      0 AS ServXTipo,
      0 AS ServXCertMedico,
      0 AS ServXEmbalsamado,
      0 AS ServXLugarCremacion,
      0 AS ServXAplicaSeguro,
      ser.name as estatus_servicio,
      bita.cs_nuevo_comentario as Notes,
      '' as U_observacrm
    FROM mortuary AS bita
    LEFT JOIN ds_sucursal_velacion AS suc on bita.ds_sucursal_de_velacion = suc.id
    LEFT JOIN ii_servicio AS ser on bita.ii_servicio = ser.id
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      'Guadalajara' as Plaza,
      bita.ii_fecha_creacion as Fecha,
      'Funeraria' as AreaDeNegocio,
      'Funerarias' as CentroCosto,
      suc.name as SucursaluOficina,
      'No aplica' as CodSubCta,
      'No aplica' as TipoEstadistico,
      'No aplica' CodigoCuenta,
      tipo.name as Estadistico,
      bita.name as Bitacora,
      0 AS Servicios,
      0 AS ServiciosPorSuOrigen,
      0 AS ServXTipoPABS,
      0 AS ServXLugarVelacion,
      1 AS ServXTipo,
      0 AS ServXCertMedico,
      0 AS ServXEmbalsamado,
      0 AS ServXLugarCremacion,
      0 AS ServXAplicaSeguro,
      ser.name as estatus_servicio,
      bita.cs_nuevo_comentario as Notes,
      '' as U_observacrm
    FROM mortuary AS bita
    LEFT JOIN ds_sucursal_velacion AS suc on bita.ds_sucursal_de_velacion = suc.id
    LEFT JOIN ii_servicio AS ser on bita.ii_servicio = ser.id
    LEFT JOIN ii_servicio2 AS tipo on bita.ii_servicio_2 = tipo.id
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      'Guadalajara' as Plaza,
      bita.ii_fecha_creacion as Fecha,
      'Funeraria' as AreaDeNegocio,
      'Funerarias' as CentroCosto,
      suc.name as SucursaluOficina,
      'No aplica' as CodSubCta,
      'No aplica' as TipoEstadistico,
      'No aplica' CodigoCuenta,
      cert.name as Estadistico,
      bita.name as Bitacora,
      0 AS Servicios,
      0 AS ServiciosPorSuOrigen,
      0 AS ServXTipoPABS,
      0 AS ServXLugarVelacion,
      0 AS ServXTipo,
      1 AS ServXCertMedico,
      0 AS ServXEmbalsamado,
      0 AS ServXLugarCremacion,
      0 AS ServXAplicaSeguro,
      ser.name as estatus_servicio,
      bita.cs_nuevo_comentario as Notes,
      '' as U_observacrm
    FROM mortuary AS bita
    LEFT JOIN ds_sucursal_velacion AS suc on bita.ds_sucursal_de_velacion = suc.id
    LEFT JOIN ii_servicio AS ser on bita.ii_servicio = ser.id
    LEFT JOIN ii_certificamos AS cert on bita.ii_certificamos = cert.id
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      'Guadalajara' as Plaza,
      bita.ii_fecha_creacion as Fecha,
      'Funeraria' as AreaDeNegocio,
      'Funerarias' as CentroCosto,
      suc.name as SucursaluOficina,
      'No aplica' as CodSubCta,
      'No aplica' as TipoEstadistico,
      'No aplica' CodigoCuenta,
      CASE
        WHEN emb.name IS NULL THEN 'No'
        ELSE 'Si'
      END as Estadistico,
      bita.name as Bitacora,
      0 AS Servicios,
      0 AS ServiciosPorSuOrigen,
      0 AS ServXTipoPABS,
      0 AS ServXLugarVelacion,
      0 AS ServXTipo,
      0 AS ServXCertMedico,
      1 AS ServXEmbalsamado,
      0 AS ServXLugarCremacion,
      0 AS ServXAplicaSeguro,
      ser.name as estatus_servicio,
      bita.cs_nuevo_comentario as Notes,
      '' as U_observacrm
    FROM mortuary AS bita
    LEFT JOIN ds_sucursal_velacion AS suc on bita.ds_sucursal_de_velacion = suc.id
    LEFT JOIN ii_servicio AS ser on bita.ii_servicio = ser.id
    LEFT JOIN ig_proveedor_embalsama AS emb on bita.ig_proveedor_embalsama = emb.id 
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      'Guadalajara' as Plaza,
      bita.ii_fecha_creacion as Fecha,
      'Funeraria' as AreaDeNegocio,
      'Funerarias' as CentroCosto,
      suc.name as SucursaluOficina,
      'No aplica' as CodSubCta,
      'No aplica' as TipoEstadistico,
      'No aplica' CodigoCuenta,
      mor.name as Estadistico,
      bita.name as Bitacora,
      0 AS Servicios,
      0 AS ServiciosPorSuOrigen,
      0 AS ServXTipoPABS,
      0 AS ServXLugarVelacion,
      0 AS ServXTipo,
      0 AS ServXCertMedico,
      0 AS ServXEmbalsamado,
      1 AS ServXLugarCremacion,
      0 AS ServXAplicaSeguro,
      ser.name as estatus_servicio,
      bita.cs_nuevo_comentario as Notes,
      '' as U_observacrm
    FROM mortuary AS bita
    LEFT JOIN ds_sucursal_velacion AS suc on bita.ds_sucursal_de_velacion = suc.id
    LEFT JOIN ii_servicio AS ser on bita.ii_servicio = ser.id
    LEFT JOIN mortuary_cremation as mor on bita.cremation_id = mor.id
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      'Guadalajara' as Plaza,
      bita.ii_fecha_creacion as Fecha,
      'Funeraria' as AreaDeNegocio,
      'Funerarias' as CentroCosto,
      suc.name as SucursaluOficina,
      'No aplica' as CodSubCta,
      'No aplica' as TipoEstadistico,
      'No aplica' CodigoCuenta,
      seg.name as Estadistico,
      bita.name as Bitacora,
      0 AS Servicios,
      0 AS ServiciosPorSuOrigen,
      0 AS ServXTipoPABS,
      0 AS ServXLugarVelacion,
      0 AS ServXTipo,
      0 AS ServXCertMedico,
      0 AS ServXEmbalsamado,
      0 AS ServXLugarCremacion,
      1 AS ServXAplicaSeguro,
      ser.name as estatus_servicio,
      bita.cs_nuevo_comentario as Notes,
      '' as U_observacrm
    FROM mortuary AS bita
    LEFT JOIN ds_sucursal_velacion AS suc on bita.ds_sucursal_de_velacion = suc.id
    LEFT JOIN ii_servicio AS ser on bita.ii_servicio = ser.id
    LEFT JOIN ds_aplica_seguro AS seg on bita.ds_aplica_seguro = seg.id"""
    try:
      cr.execute(query)
      records = []
      headers = [d[0] for d in cr.description]
      for res in cr.fetchall():
        data = {}
        for ind, rec in enumerate(headers):
          if isinstance(res[ind], datetime.date):
            value = res[ind].strftime("%d/%m/%Y")
          else:
            value = res[ind]
          data.update({
            headers[ind] : value
          })
        records.append(data)
        response = {
          'result' : records
        }
      return Response(json.dumps(response),headers=response_header)
    except Exception as e:
      return str(e)
    return Response("Petición Denegada", status=400)