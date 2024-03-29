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

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

  @http.route('/api/get/flujo/<int:company_id>', type='http', methods=['GET'], auth='none', csrf=False)
  def get_flujo(self, **kargs):
    if not kargs.get('company_id'):
      return Response("Necesitas enviar un parametro de busqueda", status=400)
    else:
      company_id = kargs.get('company_id')
      company = request.env['res.company'].browse(company_id)
    response_header = {'Content-Type': 'application/json'}
    cr = request.cr
    query = """
      SELECT 
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
              '{}' as Plaza,
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
          INNER JOIN account_move_line as mov on enc.id = mov.move_id
          LEFT JOIN account_account as cue on mov.account_id = cue.id
          LEFT JOIN account_journal AS jou ON enc.journal_id = jou.id
            WHERE (cue.code like '101%' OR cue.code like '102%' OR cue.code like '103%')
            AND enc.company_id = {}
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
                '{}' as Plaza,
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
            INNER JOIN account_move_line as mov on enc.id = mov.move_id
            LEFT JOIN account_account as cue on mov.account_id = cue.id
            LEFT JOIN account_journal AS jou ON enc.journal_id = jou.id
              WHERE (cue.code like '101%' OR cue.code like '102%' OR cue.code like '103%')
              AND enc.company_id = {}
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
                '{}' as Plaza,
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
            INNER JOIN account_move_line as mov on enc.id = mov.move_id
            LEFT JOIN account_account as cue on mov.account_id = cue.id
            LEFT JOIN account_journal AS jou ON enc.journal_id = jou.id
              WHERE (cue.code like '101%' OR cue.code like '102%' OR cue.code like '103%')
              AND enc.company_id = {}
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
            INNER JOIN account_move_line as mov on enc.id = mov.move_id
            LEFT JOIN account_account as cue on mov.account_id = cue.id
            LEFT JOIN account_journal AS jou ON enc.journal_id = jou.id
              WHERE (cue.code like '101%' OR cue.code like '102%' OR cue.code like '103%')
              AND enc.company_id = {}
          ) as Z1
            GROUP BY Grupo,Plaza, TipoDato, Fecha + (365 - DATE_PART('doy', Fecha)) * INTERVAL '1 day', DATE_PART('year', Fecha), CodigoCuenta, NombreCuenta
        ) AS anuales    
      ) as consulta""".format(company.name,company_id,company.name,company_id,company.name,company_id,company_id)
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

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

  @http.route('/api/get/funeraria/<int:company_id>', type='http', auth='none', csrf=False)
  def get_mortuary_service(self, **kargs):
    if not kargs.get('company_id'):
      return Response("Necesitas enviar un parametro de busqueda", status=400)
    else:
      company_id = kargs.get('company_id')
      company = request.env['res.company'].browse(company_id)
    response_header = {'Content-Type': 'application/json'}
    cr = request.cr
    query =  """SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      '{}' as Plaza,
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
    WHERE bita.company_id = {}
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      '{}' as Plaza,
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
    WHERE bita.company_id = {}
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      '{}' as Plaza,
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
    WHERE bita.company_id = {}
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      '{}' as Plaza,
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
    WHERE bita.company_id = {}
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      '{}' as Plaza,
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
    WHERE bita.company_id = {}
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      '{}' as Plaza,
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
    WHERE bita.company_id = {}
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      '{}' as Plaza,
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
    WHERE bita.company_id = {}
  
  UNION ALL
    SELECT 
      'Estadísticos de funeraria' as TipoDato,
      'Occidente' as Grupo,
      '{}' as Plaza,
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
    LEFT JOIN ds_aplica_seguro AS seg on bita.ds_aplica_seguro = seg.id
    WHERE bita.company_id = {}""".format(
      company.name, company_id, 
      company.name, company_id, 
      company.name, company_id,
      company.name, company_id,
      company.name, company_id,
      company.name, company_id,
      company.name, company_id,
      company.name, company_id)
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

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

  @http.route('/api/get/financieros/<int:company_id>', type='http', auth='none', csrf=False)
  def get_financial(self, **kargs):
    if not kargs.get('company_id'):
      return Response("Necesitas enviar un parametro de busqueda", status=400)
    else:
      company_id = kargs.get('company_id')
      company = request.env['res.company'].browse(company_id)
    response_header = {'Content-Type': 'application/json'}
    cr = request.cr
    query = """
    SELECT 
      Grupo, 
      Plaza, 
      TipoDato,
      Fecha, 
      Diario, 
      TipoPoliza, 
      Folio, 
      ConceptoPoliza,
      NumMovto, 
      AreaDeNegocio, 
      CentroCosto, 
      CodSegNegocio, 
      SegmentoNegocio, 
      CodCtaMayor, 
      NomCtaMayor, 
      CodSubCta, 
      NomSubCta, 
      CodSubSubCta, 
      NomSubSubCta, 
      CodSubSubSubCta, 
      NomSubSubSubCta, 
      CodigoCuenta, 
      NombreCuenta,
      Referencia, 
      ConceptoMovimiento,
      CuentaAnalitica,
      Cargos, 
      Abonos, 
      ImporteNeto,
      SaldoSemanal, 
      SaldoMensual, 
      SaldoAnual, 
      Project, 
      Comments
    FROM
    (
      SELECT 
        'Occidente' as Grupo,     
          '{}' as Plaza,
          'Financieros' as TipoDato,
        DATE_PART('year', enc.date) as año, 
        DATE_PART('month', enc.date) as mes,
        DATE_PART('week', enc.date) as Semana,
        enc.date as Fecha,
        part.name as Usuario,
        jou.name as Diario,
        CASE 
          WHEN enc.type = 'entry' THEN 'Asiento contable'
          WHEN enc.type = 'out_invoice' THEN 'Factura de cliente'
          WHEN enc.type = 'out_refund' THEN 'Nota de crédito de cliente'
          WHEN enc.type = 'in_invoice' THEN 'Factura de proveedor'
          WHEN enc.type = 'in_refund' THEN 'Nota de crédito de proveedor'
          WHEN enc.type = 'out_receipt' THEN 'Recibo de ventas'
          WHEN enc.type = 'in_receipt' THEN 'Recibo de compra'
          ELSE enc.type
        END AS TipoPoliza,
        enc.id as Folio,
        CASE
           WHEN enc.ref = 'Sync Ecobro' THEN 'Abono'
           ELSE enc.ref
        END as ConceptoPoliza,
        ROW_NUMBER() OVER (PARTITION BY enc.name) as NumMovto,

        /*Falta definir las cuentas analiticas (una por movimiento) y las etiquetas analiticas (una o más por movimiento)*/
        CASE
          WHEN substring(ana.name, 1,1) = '1' THEN 'PABS'
          WHEN substring(ana.name, 1,1) = '2' THEN 'Funeraria'
          WHEN substring(ana.name, 1,1) = '3' THEN 'Panteon'
          WHEN substring(ana.name, 1,2) = '98' THEN 'Apoyos'
          WHEN substring(ana.name, 1,2) = '99' THEN 'Personales'
          ELSE substring(ana.name, 1,2)
        END as AreaDeNegocio,

        CASE
          WHEN substring(ana.name, 1,4) = '1001' THEN 'Administración'
          WHEN substring(ana.name, 1,4) = '1002' THEN 'Cobranza'
          WHEN substring(ana.name, 1,2) = '11' THEN 'Ventas'
          WHEN substring(ana.name, 1,1) = '2' THEN 'Funerarias'
          WHEN substring(ana.name, 1,2) = '98' THEN 'Apoyos'
          WHEN substring(ana.name, 1,2) = '99' THEN 'Gastos personales'
          ELSE substring(ana.name, 1,2)
        END as CentroCosto,
        substring(ana.name, 6, 99) as SegmentoNegocio,
        substring(ana.name, 1,4) as CodSegNegocio,

        /*CodCtaMayor*/
        substring(acc.code,1,3) as CodCtaMayor,
        CASE
          WHEN substring(acc.name,1,3) = '601' THEN CASE
                                WHEN substring(acc.code,5,2) = '01' THEN 'Caja'
                                WHEN substring(acc.code,5,2) = '02' THEN 'Bancos'
                                WHEN substring(acc.code,5,2) = '03' THEN 'RIF'
                                WHEN substring(acc.code,5,2) = '00' THEN 'Programa de beneficio pabs'
                                WHEN substring(acc.code,5,2) = '10' THEN 'Cooperativa de desarrollo'
                                ELSE substring(acc.code,5,2)
                              END
          ELSE acc.name
        END as NomCtaMayor,

        /*CodSubCta*/
        substring(acc.code,5,2) as CodSubCta,
        CASE 
          WHEN substring(acc.name,1,3) = '601' THEN acc.name
          ELSE ''
        END as NomSubCta,

        /*CodSubSubCta*/
        '' as CodSubSubCta,
        '' as NomSubSubCta,

        /*CodSubSubSubCta*/
        '' as CodSubSubSubCta,
        CASE
          WHEN substring(acc.name,1,3) = '601' THEN acc.name
          ELSE ''
        END as NomSubSubSubCta,

        substring(acc.code,1,3) as CodCtaMayorX,
        CASE
          WHEN substring(acc.code,1,3) = '004' THEN 'INGRESOS'
          WHEN substring(acc.code,1,3) = '005' THEN 'COSTO DE VENTA'
          WHEN substring(acc.code,1,3) = '006' THEN 'GASTOS DE OPERACIÓN'
          WHEN substring(acc.code,1,3) = '007' THEN 'PRODUCTOS FINANCIEROS'
          WHEN substring(acc.code,1,3) = '010' THEN 'ACTIVO CIRCULANTE'
          WHEN substring(acc.code,1,3) = '015' THEN 'ACTIVO FIJO'
          WHEN substring(acc.code,1,3) = '018' THEN 'ACTIVO DIFERIDO'
          WHEN substring(acc.code,1,3) = '020' THEN 'PASIVO EXIGIBLE'
          WHEN substring(acc.code,1,3) = '025' THEN 'PASIVO A LARGO PLAZO'
          WHEN substring(acc.code,1,3) = '027' THEN 'INGRESOS POR REALIZAR Y COMPROMISOS DIFERIDOS'
          WHEN substring(acc.code,1,3) = '028' THEN 'ANTICIPOS CLIENTES'
          WHEN substring(acc.code,1,3) = '085' THEN 'OTROS INGRESOS Y OTROS GASTOS'
          WHEN substring(acc.code,1,3) = '088' THEN 'IMPUESTOS CAUSADOS'
          WHEN substring(acc.code,1,3) = '089' THEN 'RESERVAS Y RETIROS DE UTILIDADES'
          WHEN substring(acc.code,1,4) = '1012' THEN 'Cajas en Tesorería'
          ELSE substring(acc.code,1,3)
        END as NomCtaMayorX,

        substring(acc.code,5,2) as CodSubCtaX,
        CASE
          WHEN substring(acc.code,5,2) = '01' THEN 'Caja'
          WHEN substring(acc.code,5,2) = '02' THEN 'Bancos'
          WHEN substring(acc.code,5,2) = '03' THEN 'RIF'
          WHEN substring(acc.code,5,2) = '00' THEN 'Programa de beneficio pabs'
          WHEN substring(acc.code,5,2) = '10' THEN 'Cooperativa de desarrollo'
          ELSE substring(acc.code,5,2)
        END as NomSubCtaX,

        substring(acc.code,8,99) as CodSubSubCtaX,
        acc.name as NomSubSubCtaX,

        '' as CodSubSubSubCtaX,
        '' as NomSubSubSubCtaX,

        acc.code as CodigoCuenta,
        acc.name as NombreCuenta,
        acc.name as NombreCuentaSAP,
        /*Fin cuentas*/

        mov.ref as Referencia,
        COALESCE(mov.name,'Sin concepto') AS ConceptoMovimiento,
        aaa.name AS CuentaAnalitica,
        mov.Debit AS Cargos,
        mov.Credit AS Abonos,
        (mov.Debit - mov.Credit) as ImporteNeto,
        0 as SaldoSemanal,
        0 as SaldoMensual,
        0 as SaldoAnual,
        '' as Project,
        mov.name as comments

      FROM account_move AS enc
      INNER JOIN account_move_line as mov on enc.id = mov.move_id
      INNER JOIN res_users AS usr ON enc.create_uid = usr.id
      INNER JOIN res_partner AS part ON usr.partner_id = part.id
      INNER JOIN account_analytic_account AS aaa ON mov.analytic_account_id = aaa.id
      LEFT JOIN account_journal AS jou ON enc.journal_id = jou.id
      LEFT JOIN account_account as acc on mov.account_id = acc.id
      LEFT JOIN account_analytic_account as ana on mov.analytic_account_id = ana.id
        WHERE enc.state = 'posted'
        AND enc.company_id = {}
    ) as financieros""".format(company.name, company_id)
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

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

  @http.route('/api/get/financieros_group/<int:company_id>', type='http', auth='none', csrf=False)
  def get_financial(self, **kargs):
    if not kargs.get('company_id'):
      return Response("Necesitas enviar un parametro de busqueda", status=400)
    else:
      company_id = kargs.get('company_id')
      company = request.env['res.company'].browse(company_id)
    response_header = {'Content-Type': 'application/json'}
    cr = request.cr
    #
    query = """
    SELECT Cliente,
      Grupo, 
      Plaza, 
      TipoDato,
      Fecha, 
      Diario, 
      TipoPoliza, 
      Folio, 
      ConceptoPoliza,
      NumMovto, 
      AreaDeNegocio, 
      CentroCosto, 
      CodSegNegocio, 
      SegmentoNegocio, 
      CodCtaMayor, 
      NomCtaMayor, 
      CodSubCta, 
      NomSubCta, 
      CodSubSubCta, 
      NomSubSubCta, 
      CodSubSubSubCta, 
      NomSubSubSubCta, 
      CodigoCuenta, 
      NombreCuenta,
      Referencia, 
      ConceptoMovimiento,
      CuentaAnalitica,
      Cargos, 
      Abonos, 
      ImporteNeto,
      Project, 
      Comments,
      EtiquetaAnalitica,
      move_name
    FROM
    (
      SELECT mortuary.name as Cliente,
        'Occidente' as Grupo,     
          'Mérida' as Plaza,
          'Financieros' as TipoDato,
        DATE_PART('year', enc.date) as año, 
        DATE_PART('month', enc.date) as mes,
        DATE_PART('week', enc.date) as Semana,
        enc.date as Fecha,
        part.name as Usuario,
        jou.name as Diario,
        CASE 
          WHEN enc.type = 'entry' THEN 'Asiento contable'
          WHEN enc.type = 'out_invoice' THEN 'Factura de cliente'
          WHEN enc.type = 'out_refund' THEN 'Nota de crédito de cliente'
          WHEN enc.type = 'in_invoice' THEN 'Factura de proveedor'
          WHEN enc.type = 'in_refund' THEN 'Nota de crédito de proveedor'
          WHEN enc.type = 'out_receipt' THEN 'Recibo de ventas'
          WHEN enc.type = 'in_receipt' THEN 'Recibo de compra'
          ELSE enc.type
        END AS TipoPoliza,
        enc.id as Folio,
        CASE
           WHEN enc.ref = 'Sync Ecobro' THEN 'Abono'
           ELSE enc.ref
        END as ConceptoPoliza,
        ROW_NUMBER() OVER (PARTITION BY enc.name) as NumMovto,
        CASE
          WHEN substring(ana.name, 1,1) = '1' THEN 'PABS'
          WHEN substring(ana.name, 1,1) = '2' THEN 'Funeraria'
          WHEN substring(ana.name, 1,1) = '3' THEN 'Panteon'
          WHEN substring(ana.name, 1,2) = '98' THEN 'Apoyos'
          WHEN substring(ana.name, 1,2) = '99' THEN 'Personales'
          ELSE substring(ana.name, 1,2)
        END as AreaDeNegocio,

        CASE
          WHEN substring(ana.name, 1,4) = '1001' THEN 'Administración'
          WHEN substring(ana.name, 1,4) = '1002' THEN 'Cobranza'
          WHEN substring(ana.name, 1,2) = '11' THEN 'Ventas'
          WHEN substring(ana.name, 1,1) = '2' THEN 'Funerarias'
          WHEN substring(ana.name, 1,2) = '98' THEN 'Apoyos'
          WHEN substring(ana.name, 1,2) = '99' THEN 'Gastos personales'
          ELSE substring(ana.name, 1,2)
        END as CentroCosto,
        substring(ana.name, 6, 99) as SegmentoNegocio,
        substring(ana.name, 1,4) as CodSegNegocio,
        substring(acc.code,1,3) as CodCtaMayor,
        CASE
          WHEN substring(acc.name,1,3) = '601' THEN CASE
                                WHEN substring(acc.code,5,2) = '01' THEN 'Caja'
                                WHEN substring(acc.code,5,2) = '02' THEN 'Bancos'
                                WHEN substring(acc.code,5,2) = '03' THEN 'RIF'
                                WHEN substring(acc.code,5,2) = '00' THEN 'Programa de beneficio pabs'
                                WHEN substring(acc.code,5,2) = '10' THEN 'Cooperativa de desarrollo'
                                ELSE substring(acc.code,5,2)
                              END
          ELSE acc.name
        END as NomCtaMayor,
        substring(acc.code,5,2) as CodSubCta,
        CASE 
          WHEN substring(acc.name,1,3) = '601' THEN acc.name
          ELSE ''
        END as NomSubCta,
        '' as CodSubSubCta,
        '' as NomSubSubCta,
        '' as CodSubSubSubCta,
        CASE
          WHEN substring(acc.name,1,3) = '601' THEN acc.name
          ELSE ''
        END as NomSubSubSubCta,
        substring(acc.code,1,3) as CodCtaMayorX,
        CASE
          WHEN substring(acc.code,1,3) = '004' THEN 'INGRESOS'
          WHEN substring(acc.code,1,3) = '005' THEN 'COSTO DE VENTA'
          WHEN substring(acc.code,1,3) = '006' THEN 'GASTOS DE OPERACIÓN'
          WHEN substring(acc.code,1,3) = '007' THEN 'PRODUCTOS FINANCIEROS'
          WHEN substring(acc.code,1,3) = '010' THEN 'ACTIVO CIRCULANTE'
          WHEN substring(acc.code,1,3) = '015' THEN 'ACTIVO FIJO'
          WHEN substring(acc.code,1,3) = '018' THEN 'ACTIVO DIFERIDO'
          WHEN substring(acc.code,1,3) = '020' THEN 'PASIVO EXIGIBLE'
          WHEN substring(acc.code,1,3) = '025' THEN 'PASIVO A LARGO PLAZO'
          WHEN substring(acc.code,1,3) = '027' THEN 'INGRESOS POR REALIZAR Y COMPROMISOS DIFERIDOS'
          WHEN substring(acc.code,1,3) = '028' THEN 'ANTICIPOS CLIENTES'
          WHEN substring(acc.code,1,3) = '085' THEN 'OTROS INGRESOS Y OTROS GASTOS'
          WHEN substring(acc.code,1,3) = '088' THEN 'IMPUESTOS CAUSADOS'
          WHEN substring(acc.code,1,3) = '089' THEN 'RESERVAS Y RETIROS DE UTILIDADES'
          WHEN substring(acc.code,1,4) = '1012' THEN 'Cajas en Tesorería'
          ELSE substring(acc.code,1,3)
        END as NomCtaMayorX,
        substring(acc.code,5,2) as CodSubCtaX,
        CASE
          WHEN substring(acc.code,5,2) = '01' THEN 'Caja'
          WHEN substring(acc.code,5,2) = '02' THEN 'Bancos'
          WHEN substring(acc.code,5,2) = '03' THEN 'RIF'
          WHEN substring(acc.code,5,2) = '00' THEN 'Programa de beneficio pabs'
          WHEN substring(acc.code,5,2) = '10' THEN 'Cooperativa de desarrollo'
          ELSE substring(acc.code,5,2)
        END as NomSubCtaX,
        substring(acc.code,8,99) as CodSubSubCtaX,
        acc.name as NomSubSubCtaX,
        '' as CodSubSubSubCtaX,
        '' as NomSubSubSubCtaX,
        acc.code as CodigoCuenta,
        acc.name as NombreCuenta,
        acc.name as NombreCuentaSAP,
        mov.ref as Referencia,
        COALESCE(mov.name,'Sin concepto') AS ConceptoMovimiento,
        aaa.name AS CuentaAnalitica,
        mov.Debit AS Cargos,
        mov.Credit AS Abonos,
        (mov.Debit - mov.Credit) as ImporteNeto,
        '' as Project,
        mov.name as comments,
        tag.name as EtiquetaAnalitica,
        icp.name as move_name
      FROM "public".account_move AS enc
      INNER JOIN "public".account_move_line as mov on enc.id = mov.move_id
      INNER JOIN "public".res_users AS usr ON enc.create_uid = usr.id
      INNER JOIN "public".res_partner AS part ON usr.partner_id = part.id
      LEFT JOIN "public".account_analytic_account AS aaa ON mov.analytic_account_id = aaa.id
      LEFT JOIN "public".account_journal AS jou ON enc.journal_id = jou.id
      LEFT JOIN "public".account_account as acc on mov.account_id = acc.id
      LEFT JOIN "public".account_analytic_account as ana on mov.analytic_account_id = ana.id
      left join public.mortuary ON enc.mortuary_id = mortuary.id
      LEFT JOIN account_analytic_tag_account_move_line_rel idmov ON account_move_line_id = mov.id
      left join account_analytic_tag tag ON idmov.account_analytic_tag_id = tag.id
      left join invoice_create_person icp ON enc.create_person_id = icp.id 
        WHERE enc.state = 'posted'
        AND COALESCE(enc.ref, '') NOT IN ('Inversión inicial', 'Excedente Inversión Inicial', 'Bono por inversión inicial', 'Sync Ecobro')
        AND NOT (enc.type = 'out_invoice' AND enc.contract_id IS NOT NULL)
        AND enc.company_id = {}
    UNION
    SELECT mortuary.name as Cliente,
        'Occidente' as Grupo,     
        'Mérida' as Plaza,
        'Financieros' as TipoDato,
        DATE_PART('year', enc.date) as año, 
        DATE_PART('month', enc.date) as mes,
        DATE_PART('week', enc.date) as Semana,
        enc.date as Fecha,
        '' as Usuario,
        jou.name as Diario,
        CASE 
          WHEN enc.type = 'entry' THEN 'Asiento contable'
          WHEN enc.type = 'out_invoice' THEN 'Factura de cliente'
          WHEN enc.type = 'out_refund' THEN 'Nota de crédito de cliente'
          WHEN enc.type = 'in_invoice' THEN 'Factura de proveedor'
          WHEN enc.type = 'in_refund' THEN 'Nota de crédito de proveedor'
          WHEN enc.type = 'out_receipt' THEN 'Recibo de ventas'
          WHEN enc.type = 'in_receipt' THEN 'Recibo de compra'
          ELSE enc.type
        END AS TipoPoliza,
        0 as Folio,
        CASE
           WHEN enc.ref = 'Sync Ecobro' THEN 'Abono'
           ELSE enc.ref
        END as ConceptoPoliza,
        ROW_NUMBER() OVER () as NumMovto,
        CASE
          WHEN substring(ana.name, 1,1) = '1' THEN 'PABS'
          WHEN substring(ana.name, 1,1) = '2' THEN 'Funeraria'
          WHEN substring(ana.name, 1,1) = '3' THEN 'Panteon'
          WHEN substring(ana.name, 1,2) = '98' THEN 'Apoyos'
          WHEN substring(ana.name, 1,2) = '99' THEN 'Personales'
          ELSE substring(ana.name, 1,2)
        END as AreaDeNegocio,
        CASE
          WHEN substring(ana.name, 1,4) = '1001' THEN 'Administración'
          WHEN substring(ana.name, 1,4) = '1002' THEN 'Cobranza'
          WHEN substring(ana.name, 1,2) = '11' THEN 'Ventas'
          WHEN substring(ana.name, 1,1) = '2' THEN 'Funerarias'
          WHEN substring(ana.name, 1,2) = '98' THEN 'Apoyos'
          WHEN substring(ana.name, 1,2) = '99' THEN 'Gastos personales'
          ELSE substring(ana.name, 1,2)
        END as CentroCosto,
        substring(ana.name, 6, 99) as SegmentoNegocio,
        substring(ana.name, 1,4) as CodSegNegocio,
        substring(acc.code,1,3) as CodCtaMayor,
        CASE
          WHEN substring(acc.name,1,3) = '601' THEN CASE
                                WHEN substring(acc.code,5,2) = '01' THEN 'Caja'
                                WHEN substring(acc.code,5,2) = '02' THEN 'Bancos'
                                WHEN substring(acc.code,5,2) = '03' THEN 'RIF'
                                WHEN substring(acc.code,5,2) = '00' THEN 'Programa de beneficio pabs'
                                WHEN substring(acc.code,5,2) = '10' THEN 'Cooperativa de desarrollo'
                                ELSE substring(acc.code,5,2)
                              END
          ELSE acc.name
        END as NomCtaMayor,
        substring(acc.code,5,2) as CodSubCta,
        CASE 
          WHEN substring(acc.name,1,3) = '601' THEN acc.name
          ELSE ''
        END as NomSubCta,
        '' as CodSubSubCta,
        '' as NomSubSubCta,
        '' as CodSubSubSubCta,
        CASE
          WHEN substring(acc.name,1,3) = '601' THEN acc.name
          ELSE ''
        END as NomSubSubSubCta,
        substring(acc.code,1,3) as CodCtaMayorX,
        CASE
          WHEN substring(acc.code,1,3) = '004' THEN 'INGRESOS'
          WHEN substring(acc.code,1,3) = '005' THEN 'COSTO DE VENTA'
          WHEN substring(acc.code,1,3) = '006' THEN 'GASTOS DE OPERACIÓN'
          WHEN substring(acc.code,1,3) = '007' THEN 'PRODUCTOS FINANCIEROS'
          WHEN substring(acc.code,1,3) = '010' THEN 'ACTIVO CIRCULANTE'
          WHEN substring(acc.code,1,3) = '015' THEN 'ACTIVO FIJO'
          WHEN substring(acc.code,1,3) = '018' THEN 'ACTIVO DIFERIDO'
          WHEN substring(acc.code,1,3) = '020' THEN 'PASIVO EXIGIBLE'
          WHEN substring(acc.code,1,3) = '025' THEN 'PASIVO A LARGO PLAZO'
          WHEN substring(acc.code,1,3) = '027' THEN 'INGRESOS POR REALIZAR Y COMPROMISOS DIFERIDOS'
          WHEN substring(acc.code,1,3) = '028' THEN 'ANTICIPOS CLIENTES'
          WHEN substring(acc.code,1,3) = '085' THEN 'OTROS INGRESOS Y OTROS GASTOS'
          WHEN substring(acc.code,1,3) = '088' THEN 'IMPUESTOS CAUSADOS'
          WHEN substring(acc.code,1,3) = '089' THEN 'RESERVAS Y RETIROS DE UTILIDADES'
          WHEN substring(acc.code,1,4) = '1012' THEN 'Cajas en Tesorería'
          ELSE substring(acc.code,1,3)
        END as NomCtaMayorX,
        substring(acc.code,5,2) as CodSubCtaX,
        CASE
          WHEN substring(acc.code,5,2) = '01' THEN 'Caja'
          WHEN substring(acc.code,5,2) = '02' THEN 'Bancos'
          WHEN substring(acc.code,5,2) = '03' THEN 'RIF'
          WHEN substring(acc.code,5,2) = '00' THEN 'Programa de beneficio pabs'
          WHEN substring(acc.code,5,2) = '10' THEN 'Cooperativa de desarrollo'
          ELSE substring(acc.code,5,2)
        END as NomSubCtaX,
        substring(acc.code,8,99) as CodSubSubCtaX,
        acc.name as NomSubSubCtaX,
        '' as CodSubSubSubCtaX,
        '' as NomSubSubSubCtaX,
        acc.code as CodigoCuenta,
        acc.name as NombreCuenta,
        acc.name as NombreCuentaSAP,
        enc.ref as Referencia,
        enc.ref AS ConceptoMovimiento,
        aaa.name AS CuentaAnalitica,
        SUM(mov.Debit) AS Cargos,
        SUM(mov.Credit) AS Abonos,
        SUM(mov.Debit) - SUM(mov.Credit) as ImporteNeto,
        '' as Project,
        '' as comments,
        tag.name as EtiquetaAnalitica,
        icp.name as move_name
      FROM "public".account_move AS enc
      INNER JOIN "public".account_move_line as mov on enc.id = mov.move_id
      INNER JOIN "public".res_users AS usr ON enc.create_uid = usr.id
      INNER JOIN "public".res_partner AS part ON usr.partner_id = part.id
      LEFT JOIN "public".account_analytic_account AS aaa ON mov.analytic_account_id = aaa.id
      LEFT JOIN "public".account_journal AS jou ON enc.journal_id = jou.id
      LEFT JOIN "public".account_account as acc on mov.account_id = acc.id
      LEFT JOIN "public".account_analytic_account as ana on mov.analytic_account_id = ana.id      
      left join public.mortuary ON enc.mortuary_id = mortuary.id
      LEFT JOIN account_analytic_tag_account_move_line_rel idmov ON account_move_line_id = mov.id
      left join account_analytic_tag tag ON idmov.account_analytic_tag_id = tag.id 
      left join invoice_create_person icp ON enc.create_person_id = icp.id
        WHERE enc.state = 'posted'
        AND COALESCE(enc.ref, '') IN ('Inversión inicial', 'Excedente Inversión Inicial', 'Bono por inversión inicial', 'Sync Ecobro')
        AND enc.company_id = {}
          GROUP BY enc.date, jou.name, enc.type , enc.ref, ana.name, acc.code, acc.name, aaa.name, mortuary.name, tag.name, icp.name
    UNION
    SELECT mortuary.name as Cliente,
        'Occidente' as Grupo,     
        'Mérida' as Plaza,
        'Financieros' as TipoDato,
        DATE_PART('year', enc.date) as año, 
        DATE_PART('month', enc.date) as mes,
        DATE_PART('week', enc.date) as Semana,
        enc.date as Fecha,
        '' as Usuario,
        jou.name as Diario,
        CASE 
          WHEN enc.type = 'entry' THEN 'Asiento contable'
          WHEN enc.type = 'out_invoice' THEN 'Factura de cliente'
          WHEN enc.type = 'out_refund' THEN 'Nota de crédito de cliente'
          WHEN enc.type = 'in_invoice' THEN 'Factura de proveedor'
          WHEN enc.type = 'in_refund' THEN 'Nota de crédito de proveedor'
          WHEN enc.type = 'out_receipt' THEN 'Recibo de ventas'
          WHEN enc.type = 'in_receipt' THEN 'Recibo de compra'
          ELSE enc.type
        END AS TipoPoliza,
        0 as Folio,
        'Factura de contratos' as ConceptoPoliza,
        ROW_NUMBER() OVER () as NumMovto,
        CASE
          WHEN substring(ana.name, 1,1) = '1' THEN 'PABS'
          WHEN substring(ana.name, 1,1) = '2' THEN 'Funeraria'
          WHEN substring(ana.name, 1,1) = '3' THEN 'Panteon'
          WHEN substring(ana.name, 1,2) = '98' THEN 'Apoyos'
          WHEN substring(ana.name, 1,2) = '99' THEN 'Personales'
          ELSE substring(ana.name, 1,2)
        END as AreaDeNegocio,
        CASE
          WHEN substring(ana.name, 1,4) = '1001' THEN 'Administración'
          WHEN substring(ana.name, 1,4) = '1002' THEN 'Cobranza'
          WHEN substring(ana.name, 1,2) = '11' THEN 'Ventas'
          WHEN substring(ana.name, 1,1) = '2' THEN 'Funerarias'
          WHEN substring(ana.name, 1,2) = '98' THEN 'Apoyos'
          WHEN substring(ana.name, 1,2) = '99' THEN 'Gastos personales'
          ELSE substring(ana.name, 1,2)
        END as CentroCosto,
        substring(ana.name, 6, 99) as SegmentoNegocio,
        substring(ana.name, 1,4) as CodSegNegocio,
        substring(acc.code,1,3) as CodCtaMayor,
        CASE
          WHEN substring(acc.name,1,3) = '601' THEN CASE
                                WHEN substring(acc.code,5,2) = '01' THEN 'Caja'
                                WHEN substring(acc.code,5,2) = '02' THEN 'Bancos'
                                WHEN substring(acc.code,5,2) = '03' THEN 'RIF'
                                WHEN substring(acc.code,5,2) = '00' THEN 'Programa de beneficio pabs'
                                WHEN substring(acc.code,5,2) = '10' THEN 'Cooperativa de desarrollo'
                                ELSE substring(acc.code,5,2)
                              END
          ELSE acc.name
        END as NomCtaMayor,
        substring(acc.code,5,2) as CodSubCta,
        CASE 
          WHEN substring(acc.name,1,3) = '601' THEN acc.name
          ELSE ''
        END as NomSubCta,
        '' as CodSubSubCta,
        '' as NomSubSubCta,
        '' as CodSubSubSubCta,
        CASE
          WHEN substring(acc.name,1,3) = '601' THEN acc.name
          ELSE ''
        END as NomSubSubSubCta,
        substring(acc.code,1,3) as CodCtaMayorX,
        CASE
          WHEN substring(acc.code,1,3) = '004' THEN 'INGRESOS'
          WHEN substring(acc.code,1,3) = '005' THEN 'COSTO DE VENTA'
          WHEN substring(acc.code,1,3) = '006' THEN 'GASTOS DE OPERACIÓN'
          WHEN substring(acc.code,1,3) = '007' THEN 'PRODUCTOS FINANCIEROS'
          WHEN substring(acc.code,1,3) = '010' THEN 'ACTIVO CIRCULANTE'
          WHEN substring(acc.code,1,3) = '015' THEN 'ACTIVO FIJO'
          WHEN substring(acc.code,1,3) = '018' THEN 'ACTIVO DIFERIDO'
          WHEN substring(acc.code,1,3) = '020' THEN 'PASIVO EXIGIBLE'
          WHEN substring(acc.code,1,3) = '025' THEN 'PASIVO A LARGO PLAZO'
          WHEN substring(acc.code,1,3) = '027' THEN 'INGRESOS POR REALIZAR Y COMPROMISOS DIFERIDOS'
          WHEN substring(acc.code,1,3) = '028' THEN 'ANTICIPOS CLIENTES'
          WHEN substring(acc.code,1,3) = '085' THEN 'OTROS INGRESOS Y OTROS GASTOS'
          WHEN substring(acc.code,1,3) = '088' THEN 'IMPUESTOS CAUSADOS'
          WHEN substring(acc.code,1,3) = '089' THEN 'RESERVAS Y RETIROS DE UTILIDADES'
          WHEN substring(acc.code,1,4) = '1012' THEN 'Cajas en Tesorería'
          ELSE substring(acc.code,1,3)
        END as NomCtaMayorX,
        substring(acc.code,5,2) as CodSubCtaX,
        CASE
          WHEN substring(acc.code,5,2) = '01' THEN 'Caja'
          WHEN substring(acc.code,5,2) = '02' THEN 'Bancos'
          WHEN substring(acc.code,5,2) = '03' THEN 'RIF'
          WHEN substring(acc.code,5,2) = '00' THEN 'Programa de beneficio pabs'
          WHEN substring(acc.code,5,2) = '10' THEN 'Cooperativa de desarrollo'
          ELSE substring(acc.code,5,2)
        END as NomSubCtaX,
        substring(acc.code,8,99) as CodSubSubCtaX,
        acc.name as NomSubSubCtaX,
        '' as CodSubSubSubCtaX,
        '' as NomSubSubSubCtaX,
        acc.code as CodigoCuenta,
        acc.name as NombreCuenta,
        acc.name as NombreCuentaSAP,
        'Factura de contratos' as Referencia,
        'Factura de contratos' AS ConceptoMovimiento,
        aaa.name AS CuentaAnalitica,
        SUM(mov.Debit) AS Cargos,
        SUM(mov.Credit) AS Abonos,
        SUM(mov.Debit) - SUM(mov.Credit) as ImporteNeto,
        '' as Project,
        '' as comments,
        tag.name as EtiquetaAnalitica,
        icp.name as move_name
      FROM "public".account_move AS enc
      INNER JOIN "public".account_move_line as mov on enc.id = mov.move_id
      INNER JOIN "public".res_users AS usr ON enc.create_uid = usr.id
      INNER JOIN "public".res_partner AS part ON usr.partner_id = part.id
      LEFT JOIN "public".account_analytic_account AS aaa ON mov.analytic_account_id = aaa.id
      LEFT JOIN "public".account_journal AS jou ON enc.journal_id = jou.id
      LEFT JOIN "public".account_account as acc on mov.account_id = acc.id
      LEFT JOIN "public".account_analytic_account as ana on mov.analytic_account_id = ana.id
      left join public.mortuary ON enc.mortuary_id = mortuary.id
      LEFT JOIN account_analytic_tag_account_move_line_rel idmov ON account_move_line_id = mov.id
      left join account_analytic_tag tag ON idmov.account_analytic_tag_id = tag.id 
      left join invoice_create_person icp ON enc.create_person_id = icp.id
        WHERE enc.state = 'posted'
        AND COALESCE(enc.ref, '') NOT IN ('Inversión inicial', 'Excedente Inversión Inicial', 'Bono por inversión inicial', 'Sync Ecobro')
        AND enc.type = 'out_invoice'
        AND enc.contract_id IS NOT NULL
        AND enc.company_id = {}
          GROUP BY enc.date, jou.name, enc.type , ana.name, acc.code, acc.name, aaa.name, mortuary.name, tag.name, icp.name
    ) as financieros;
    """.format(company_id,company_id,company_id)
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


#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

  @http.route('/api/get/financieros_param/<int:company_id>/<int:year>/<int:month>', type='http', auth='none', csrf=False)
  def get_financial_param(self, **kargs):
    if not kargs.get('company_id'):
      return Response("No se definió una compañia", status=400)
    elif not kargs.get('year'):
      return Response("No se definió un año", status=400)
    elif not kargs.get('month'):
      return Response("No se definió un mes", status=400)
    else:
      company_id = kargs.get('company_id')
      year = kargs.get('year')
      month = kargs.get('month')
      company = request.env['res.company'].browse(company_id)
    response_header = {'Content-Type': 'application/json'}
    cr = request.cr
    query = """
    SELECT 
      Grupo, 
      Plaza, 
      TipoDato,
      Fecha, 
      Diario, 
      TipoPoliza, 
      Folio, 
      ConceptoPoliza,
      NumMovto, 
      AreaDeNegocio, 
      CentroCosto, 
      CodSegNegocio, 
      SegmentoNegocio, 
      CodCtaMayor, 
      NomCtaMayor, 
      CodSubCta, 
      NomSubCta, 
      CodSubSubCta, 
      NomSubSubCta, 
      CodSubSubSubCta, 
      NomSubSubSubCta, 
      CodigoCuenta, 
      NombreCuenta,
      Referencia, 
      ConceptoMovimiento,
      CuentaAnalitica,
      Cargos, 
      Abonos, 
      ImporteNeto,
      SaldoSemanal, 
      SaldoMensual, 
      SaldoAnual, 
      Project, 
      Comments
    FROM
    (
      SELECT 
        'Occidente' as Grupo,     
          '{}' as Plaza,
          'Financieros' as TipoDato,
        DATE_PART('year', enc.date) as año, 
        DATE_PART('month', enc.date) as mes,
        DATE_PART('week', enc.date) as Semana,
        enc.date as Fecha,
        part.name as Usuario,
        jou.name as Diario,
        CASE 
          WHEN enc.type = 'entry' THEN 'Asiento contable'
          WHEN enc.type = 'out_invoice' THEN 'Factura de cliente'
          WHEN enc.type = 'out_refund' THEN 'Nota de crédito de cliente'
          WHEN enc.type = 'in_invoice' THEN 'Factura de proveedor'
          WHEN enc.type = 'in_refund' THEN 'Nota de crédito de proveedor'
          WHEN enc.type = 'out_receipt' THEN 'Recibo de ventas'
          WHEN enc.type = 'in_receipt' THEN 'Recibo de compra'
          ELSE enc.type
        END AS TipoPoliza,
        enc.id as Folio,
        CASE
           WHEN enc.ref = 'Sync Ecobro' THEN 'Abono'
           ELSE enc.ref
        END as ConceptoPoliza,
        ROW_NUMBER() OVER (PARTITION BY enc.name) as NumMovto,

        /*Falta definir las cuentas analiticas (una por movimiento) y las etiquetas analiticas (una o más por movimiento)*/
        CASE
          WHEN substring(ana.name, 1,1) = '1' THEN 'PABS'
          WHEN substring(ana.name, 1,1) = '2' THEN 'Funeraria'
          WHEN substring(ana.name, 1,1) = '3' THEN 'Panteon'
          WHEN substring(ana.name, 1,2) = '98' THEN 'Apoyos'
          WHEN substring(ana.name, 1,2) = '99' THEN 'Personales'
          ELSE substring(ana.name, 1,2)
        END as AreaDeNegocio,

        CASE
          WHEN substring(ana.name, 1,4) = '1001' THEN 'Administración'
          WHEN substring(ana.name, 1,4) = '1002' THEN 'Cobranza'
          WHEN substring(ana.name, 1,2) = '11' THEN 'Ventas'
          WHEN substring(ana.name, 1,1) = '2' THEN 'Funerarias'
          WHEN substring(ana.name, 1,2) = '98' THEN 'Apoyos'
          WHEN substring(ana.name, 1,2) = '99' THEN 'Gastos personales'
          ELSE substring(ana.name, 1,2)
        END as CentroCosto,
        substring(ana.name, 6, 99) as SegmentoNegocio,
        substring(ana.name, 1,4) as CodSegNegocio,

        /*CodCtaMayor*/
        substring(acc.code,1,3) as CodCtaMayor,
        CASE
          WHEN substring(acc.name,1,3) = '601' THEN CASE
                                WHEN substring(acc.code,5,2) = '01' THEN 'Caja'
                                WHEN substring(acc.code,5,2) = '02' THEN 'Bancos'
                                WHEN substring(acc.code,5,2) = '03' THEN 'RIF'
                                WHEN substring(acc.code,5,2) = '00' THEN 'Programa de beneficio pabs'
                                WHEN substring(acc.code,5,2) = '10' THEN 'Cooperativa de desarrollo'
                                ELSE substring(acc.code,5,2)
                              END
          ELSE acc.name
        END as NomCtaMayor,

        /*CodSubCta*/
        substring(acc.code,5,2) as CodSubCta,
        CASE 
          WHEN substring(acc.name,1,3) = '601' THEN acc.name
          ELSE ''
        END as NomSubCta,

        /*CodSubSubCta*/
        '' as CodSubSubCta,
        '' as NomSubSubCta,

        /*CodSubSubSubCta*/
        '' as CodSubSubSubCta,
        CASE
          WHEN substring(acc.name,1,3) = '601' THEN acc.name
          ELSE ''
        END as NomSubSubSubCta,

        substring(acc.code,1,3) as CodCtaMayorX,
        CASE
          WHEN substring(acc.code,1,3) = '004' THEN 'INGRESOS'
          WHEN substring(acc.code,1,3) = '005' THEN 'COSTO DE VENTA'
          WHEN substring(acc.code,1,3) = '006' THEN 'GASTOS DE OPERACIÓN'
          WHEN substring(acc.code,1,3) = '007' THEN 'PRODUCTOS FINANCIEROS'
          WHEN substring(acc.code,1,3) = '010' THEN 'ACTIVO CIRCULANTE'
          WHEN substring(acc.code,1,3) = '015' THEN 'ACTIVO FIJO'
          WHEN substring(acc.code,1,3) = '018' THEN 'ACTIVO DIFERIDO'
          WHEN substring(acc.code,1,3) = '020' THEN 'PASIVO EXIGIBLE'
          WHEN substring(acc.code,1,3) = '025' THEN 'PASIVO A LARGO PLAZO'
          WHEN substring(acc.code,1,3) = '027' THEN 'INGRESOS POR REALIZAR Y COMPROMISOS DIFERIDOS'
          WHEN substring(acc.code,1,3) = '028' THEN 'ANTICIPOS CLIENTES'
          WHEN substring(acc.code,1,3) = '085' THEN 'OTROS INGRESOS Y OTROS GASTOS'
          WHEN substring(acc.code,1,3) = '088' THEN 'IMPUESTOS CAUSADOS'
          WHEN substring(acc.code,1,3) = '089' THEN 'RESERVAS Y RETIROS DE UTILIDADES'
          WHEN substring(acc.code,1,4) = '1012' THEN 'Cajas en Tesorería'
          ELSE substring(acc.code,1,3)
        END as NomCtaMayorX,

        substring(acc.code,5,2) as CodSubCtaX,
        CASE
          WHEN substring(acc.code,5,2) = '01' THEN 'Caja'
          WHEN substring(acc.code,5,2) = '02' THEN 'Bancos'
          WHEN substring(acc.code,5,2) = '03' THEN 'RIF'
          WHEN substring(acc.code,5,2) = '00' THEN 'Programa de beneficio pabs'
          WHEN substring(acc.code,5,2) = '10' THEN 'Cooperativa de desarrollo'
          ELSE substring(acc.code,5,2)
        END as NomSubCtaX,

        substring(acc.code,8,99) as CodSubSubCtaX,
        acc.name as NomSubSubCtaX,

        '' as CodSubSubSubCtaX,
        '' as NomSubSubSubCtaX,

        acc.code as CodigoCuenta,
        acc.name as NombreCuenta,
        acc.name as NombreCuentaSAP,
        /*Fin cuentas*/

        mov.ref as Referencia,
        COALESCE(mov.name,'Sin concepto') AS ConceptoMovimiento,
        aaa.name AS CuentaAnalitica,
        mov.Debit AS Cargos,
        mov.Credit AS Abonos,
        (mov.Debit - mov.Credit) as ImporteNeto,
        0 as SaldoSemanal,
        0 as SaldoMensual,
        0 as SaldoAnual,
        '' as Project,
        mov.name as comments

      FROM account_move AS enc
      INNER JOIN account_move_line as mov on enc.id = mov.move_id
      INNER JOIN res_users AS usr ON enc.create_uid = usr.id
      INNER JOIN res_partner AS part ON usr.partner_id = part.id
      LEFT JOIN account_analytic_account AS aaa ON mov.analytic_account_id = aaa.id
      LEFT JOIN account_journal AS jou ON enc.journal_id = jou.id
      LEFT JOIN account_account as acc on mov.account_id = acc.id
      LEFT JOIN account_analytic_account as ana on mov.analytic_account_id = ana.id
        WHERE enc.state = 'posted'
        AND DATE_PART('year', enc.date) = {}
        AND DATE_PART('month', enc.date) = {}
        AND enc.company_id = {}
    ) as financieros""".format(company.name, year, month, company_id)
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

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

  @http.route('/api/get/commissions_by_range', type='http', auth='none', csrf=False)
  def get_commissions_by_range(self, **kargs):
    if not kargs.get('company_id') or not kargs.get('date_start') or not kargs.get('date_end'):
      return Response("Necesita enviar todos los parámetros de búsqueda", status=400)
    else:
      company_id = kargs.get('company_id')
      date_start = kargs.get('date_start')
      date_end = kargs.get('date_end')    
    response_header = {'Content-Type': 'application/json'}
    cr = request.cr
    query = """
    SELECT 
      TO_CHAR(x.fecha_oficina :: DATE, 'yyyy-mm-dd') AS fecha_oficina,
      x.no_nomina,
      x.cargo,
      x.comision,
      x.comision_cobrador
    FROM
    (
      SELECT 
          MIN(abo.payment_date) as "fecha_oficina",
          emp.barcode as "no_nomina",
          '' as "contrato",
          car.name as "cargo",
          SUM(com.actual_commission_paid) as "comision",
          CASE
            WHEN car.name IN ('COBRADOR', 'SUPERVISOR') THEN 0
            ELSE SUM(com.commission_paid) - SUM(com.actual_commission_paid)
          END as "comision_cobrador"
      FROM account_payment AS abo
      LEFT JOIN pabs_comission_output AS com ON abo.id = com.payment_id
      LEFT JOIN pabs_contract AS con ON abo.contract = con.id
      LEFT JOIN hr_employee AS emp ON com.comission_agent_id = emp.id
      LEFT JOIN hr_job AS car ON emp.job_id = car.id
          WHERE abo.state = 'posted' 
          AND abo.reference in ('payment', 'surplus')
          AND con.company_id = {} 
          AND payment_date BETWEEN '{}' AND '{}' 
              GROUP BY emp.barcode, car.name
    ) as x
      WHERE x.cargo NOT IN ('FIDEICOMISO', 'PAPELERIA')
        ORDER BY x.no_nomina, x.cargo, x.fecha_oficina;
        """.format(company_id, date_start,date_end)
    #
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
  
  # Gastos
  @http.route('/api/get/expenses/<int:company_id>', type='http', auth='none', csrf=False)
  def get_expenses(self, **kargs):
    if not kargs.get('company_id'):
      return Response("Necesitas enviar un parametro de búsqueda", status=400)
    else:
      company_id = kargs.get('company_id')
      company = request.env['res.company'].browse(company_id)
    #
    response_header = {'Content-Type': 'application/json'}
    cr = request.cr
    query = """
    SELECT A.name,B.name AS employee,A.create_date,A.accounting_date,A.total_amount,state, A.state_log 
    FROM hr_expense_sheet A 
    INNER JOIN hr_employee B ON A.employee_id = B.id 
    WHERE A.company_id = {}
    """.format(company_id)
    #
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
 