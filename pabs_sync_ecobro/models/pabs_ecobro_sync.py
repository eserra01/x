# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging
import requests
from dateutil import tz
#import threading
import json

_logger = logging.getLogger(__name__)

URL = {
  'COBRADORES' : '/controlusuarios/cargarCobradores',
  'CONTRATOS' : '/controlcartera/cargarContratos',
  'RECIBOS_PENDIENTES' : '/controlpagos/obtenerCobrosPorAfectar',
  'ACTUALIZAR_RECIBOS' : '/controlpagos/actualizarCobrosAfectados',
  'LOG_CONTRATOS' : '/controlodoo/saveLogsContratos',
  'LOG_COBRADORES' : '/controlodoo/saveLogsCobradores',
  'LOG_PAGOS' : '/controlodoo/saveLogsPagos',
  'LOG_SUSP' : '/controlodoo/saveLogsSuspensiones',
}

class PABSEcobroSync(models.Model):
  _name = 'pabs.ecobro.sync'

  def get_url(self, company_id, path):
    ### INSTANCIACIÓN DE OBJETOS
    company_obj = self.env['res.company'].sudo()
    ### VALIDAMOS QUE TENGA ALGÚN DATO
    if company_id:
      ### GENERAMOS EL OBJETO DE LA COMPAÑIA
      company_id = company_obj.browse(company_id)
      ### MOSTRAMOS LA COMPAÑIA QUE SE ESTA SINCRONIZANDO...
      _logger.info("Sincronizando: {}".format(company_id.name))
    ### SI NO SE ENCUENTRA LA COMPAÑIA
    else:
      ### ENVIAMOS MENSAJE DE ERROR
      raise ValidationError((
        "No se pudo generar la URL por que no se envió una compañia como parametro"))
    ### GENERAMOS LA URL BASICA
    basic_url = "{}/{}".format(company_id.ecobro_ip, company_id.extension_path)
    ### SÍ ENCUENTRA EL PATH
    if URL.get(path):
      ### GENERANDO LA URL PARA LA PETICIÓN
      url = "http://{}{}".format(basic_url,URL.get(path))
    ### SÍ NO
    else:
      ### GENERA URL NULA
      url = False
    ### RETORNO DE LA URL GENERADA
    _logger.warning("La url generada es: {}".format(url))
    return url

  def sync_collectors(self, company_id=False):
    ### GENERAMOS LA VARIABLE DE LOS LOGS
    log = "Sincronización de Cobradores \n"
    ### INSTANCIACIÓN DE OBJECTOS
    debt_collector_obj = self.env['pabs.comission.debt.collector'].sudo()
    ### MANDAR A LLAMAR LA URL DE COBRADORES
    url = self.get_url(company_id, "COBRADORES")
    ### SI NO GENERA LA URL
    if not url:
      ### ENVÍA AL LOG QUE NO SE PUDO CONFIGURAR LA URL
      _logger.warning("No se ha configurado ninguna IP de sincronización con ecobro")
      ### FINALIZA EL MÉTODO
      return
    ### BUSCAMOS EN LAS COMISIONES DE COBRADORES TODOS LOS QUE TENGAN ASIGNADAS SERIES
    debt_collector_ids = debt_collector_obj.search([
      ('company_id','=',company_id),
      ('receipt_series','!=',False)])

    ### CONTAMOS TODOS LOS REGISTROS
    len_employees = len(debt_collector_ids)
    ### LO ENVIAMOS A LOS LOGS
    log+= 'Sincronización de {} Cobradores\n'.format(len_employees)
    ### LISTA DE INFORMACIÓN VACÍA
    employee_data = []
    ### BUSCAMOS EL ESTATUS ACTIVO
    status_id = self.env['hr.employee.status'].search([
      ('name','=','ACTIVO')],limit=1)
    ### SÍ EXISTEN COBRADORES CON SERIES ASIGNADAS, CREAMOS CICLO
    for index, debt_collector_id in enumerate(debt_collector_ids):
      ### INFORMACIÓN DEL COBRADOR
      employee_id = debt_collector_id.debt_collector_id

      ### AGREGAMOS EL COBRADOR AL LOG
      log+= 'Cobrador {} de {} \n'.format((index + 1), len_employees)

      employee_info = {
        'codigo' : employee_id.barcode,
        'nombre' : employee_id.name,
        'serie' : debt_collector_id.receipt_series,
        'telefono' : employee_id.mobile_phone or "",
        'cobradorID' : int(employee_id.ecobro_id) or employee_id.id
      }

      ### VALIDAR QUE EL COBRADOR ESTÉ ACTIVO
      if employee_id.employee_status.id == status_id.id:
        ### EMPAQUETANDO INFORMACIÓN DEL COBRADOR
        employee_info.update({
          'vigente' : 1
        })
        log+= 'Código:{}\nCobrador:{}\nEstatus: {} Sincronizado con Exito \n'.format(employee_id.barcode,employee_id.name,employee_id.employee_status.name)
      else:
        employee_info.update({
          'vigente' : 0
        })
        log+= 'Código:{}\nCobrador:{}\nEstatus: {} Sincronizado con Exito \n'.format(employee_id.barcode,employee_id.name,employee_id.employee_status.name)
      log += '\n\n'
      employee_data.append(employee_info)

    ### MANEJADOR DE ERRORES
    try:
      ### SI SE EMPAQUETÓ INFORMACIÓN
      if employee_data:
        ### SE PREPARA INFORMACIÓN PARA ENVIAR AL WEB-SERVICE
        data = {
          'cobradores' : employee_data
        }
        _logger.info("El JSON enviado es: {}".format(data))
        ### SE ENVÍA PETICIÓN POST
        req = requests.post(url, json=data)
        ### RECIBIENDO RESPUESTA
        response = json.loads(req.text)
        _logger.info("Respuesta del WC: {}".format(response))
        ### SI SE ENCUENTRAN ERRORES
        if response['fail']:
          ### RECORRER LA LISTA DE ERRORES
          for rec in response['fail']:
            ### ENVIAR LA INFORMACIÓN AL LOG
            _logger.warning('Se Encontrarón algunos errores: Cobrador: {} error: {}'.format(
              rec['codigo'],rec['error']))
        ### SI NO HAY NINGUN ERROR
        else:
          ### ENVIAR MENSAJE DE SINCRONIZACIÓN EXITOSA
          _logger.info("Sincronización de Cobradores Exitosa!!")
      ### SI NO SE ENVÍA INFORMACIÓN
      else:
        ### SE ENVÍA RESPUESTA DE QUE NO HAY COBRADORES PARA PROCESAR
        _logger.info("No hay Cobradores para procesar")
    ### EN CASO DE ALGÚN ERROR
    except Exception as e:
      ### ENVIANDO INFORMACIÓN DE ERROR AL LOG
      _logger.warning(e)
    try:
      url_log = self.get_url(company_id, "LOG_COBRADORES")
      req_log = requests.post(url_log, log)
    except Exception as e:
      _logger.warning(e)

  def calc_last_payment(self,contract_id):
    ### VARIABLE DE LA FECHA A RETORNAR
    last_payment = False
    ### SI RECIBIO CONTRATO
    if contract_id:
      ### BUSCA TODOS LOS PAGOS, FILTRA POR LOS QUE SEAN DE TIPO ABONO, Y LOS ORDENA POR LA FECHA DE PAGO
      payment_ids = contract_id.payment_ids.filtered(
        lambda x: x.reference == 'payment').sorted(
        key=lambda p: p.payment_date)
      ### SI HUBO PAGOS DE TIPO ABONO
      if payment_ids:
        ### GUARDA EL ULTIMO PAGO
        payment_id = payment_ids[-1]
        ### SI HUBO ULTIMO PAGO
        if payment_id:
          ### GUARDA LA FECHA DEL ULTIMO PAGO
          last_payment = payment_id.payment_date
      ### SI HUBO FECHA DE ULTIMO PAGO
      if last_payment:
        ### SE RETORNA LA FECHA FORMATEADA EJ: 2021-02-12
        return last_payment.strftime('%Y-%m-%d')
      ### SI NO
      else:
        ### RETORNA LA FECHA EN FORMATOS DE 0
        return 0000-00-00

  def sync_contracts(self, company_id=False):
    ### GENERAR VARIABLE DE LOG
    log = "Sincronización de Contratos de Odoo \n"
    ### INSTANCIACIÓN DE OBJECTOS
    company_obj = self.env['res.company'].sudo()
    contract_obj = self.env['pabs.contract'].sudo()
    mortuary_obj = self.env['mortuary'].sudo()
    ### MANDAR A LLAMAR LA URL DE CONTRATOS
    url = self.get_url(company_id, "CONTRATOS")
    ### SI NO GENERA LA URL
    if not url:
      ### ENVÍA AL LOG QUE NO SE PUDO CONFIGURAR LA URL
      _logger.warning("No se ha configurado ninguna IP de sincronización con ecobro")
      ### FINALIZA EL MÉTODO
      return
    ### TRAEMOS EL OBJETO DE LA COMPAÑIA
    company = company_obj.browse(company_id)
    ### BUSCAMOS SI SE PUEDE SINCRONIZAR ALGO CON COOPERATIVA O APOYO
    cont_comp = company.contract_companies.filtered(lambda r: r.type_company in ('support','cooperative'))
    _logger.warning("Valor encontrado: {}".format(cont_comp))
    if cont_comp:
      ### BUSCAR TODOS LOS CONTRATOS QUE NO ESTÉN EN ESTATUS CANCELADO, PAGADO Ó REALIZADO
      contract_ids = contract_obj.search([
        ('company_id','=',company_id),
        ('state','=','contract'),
        ('contract_status_item','not in',('CANCELADO','PAGADO','REALIZADO','TRASPASO'))])
    else:
      _logger.warning("No se configuró ninguna compañia para sincronización de contratos")
      log += 'No se configuró ninguna compañia para sincronización de contratos'
      url_log = self.get_url(company_id, "LOG_CONTRATOS")
      req_log = requests.post(url_log, log)
      raise ValidationError("No se encontró compañia configurada para sincronizar Contratos")

    mortuary_comp = company.contract_companies.filtered(lambda r: r.type_company == 'mortuary')
    _logger.warning("Valor encontrado: {}".format(mortuary_comp))
    if mortuary_comp:
      ### BUSCAMOS TODAS LAS BITACORAS
      mortuary_ids = mortuary_obj.search([('company_id','=',company_id),('name','!=',False)]).filtered(lambda r: r.ii_servicio.name in ('PENDIENTE','TERMINADO'))
    else:
      _logger.warning("No se configuró ninguna compañia para sincronización de Bitacoras")
      log += "No se configuró ninguna compañia para sincronización de Bitacoras"
      url_log = self.get_url(company_id, "LOG_CONTRATOS")
      req_log = requests.post(url_log, log)
      raise ValidationError("No se encontró compañia configurada para sincronizar Bitacoras")

    ### AGREGAMOS LA CANTIDAD DE CONTRATOS EN EL LOG
    len_contract = len(contract_ids)
    log += 'Contratos a sincronizar: {}\n'.format(len_contract)

    ### LISTA DE CONTRATOS VACÍA
    contract_info = []
    ### SI SE ENCONTRARÓN REGISTROS SE CICLARÁ
    for index, contract_id in enumerate(contract_ids):
      ### VALIDANDO LA FORMA DE PAGO ACTUAL: SEMANAL / QUINCENAL / MENSUAL
      if contract_id.way_to_payment == 'weekly':
        way_payment = 1
      elif contract_id.way_to_payment == 'biweekly':
        way_payment = 2
      elif contract_id.way_to_payment == 'monthly':
        way_payment = 3

      ### BUSCAMOS LA DIRECCIÓN A SINCRONIZAR
      if contract_id.street_name_toll:
        street = contract_id.street_name_toll
        number_address = contract_id.street_number_toll or ''
        colony_name = contract_id.toll_colony_id.name or ''
        locality_name = contract_id.toll_municipallity_id.name or ''
        between = contract_id.between_streets_toll or ''
      elif contract_id.street_name:
        street = contract_id.street_name
        number_address = contract_id.street_number or ''
        colony_name = contract_id.neighborhood_id.name or ''
        locality_name = contract_id.municipality_id.name or ''
        between = contract_id.between_streets or ''
      else:
        street = ''
        number_address = ''
        colony_name = ''
        locality_name = ''
        between = ''
      ### AGREGANDO INFORMACIÓN DE CONTRATO A LA LISTA
      log += 'Contrato {} de {} \n'.format((index + 1), len_contract)

      monto_atrasado = 0
      if company_id == 7:
        monto_atrasado = 0
      else:
        monto_atrasado = contract_id.late_amount or 0

      contract_info.append({
        'contratoID' : int(contract_id.ecobro_id) or contract_id.id,
        'serie' : contract_id.name[0:3],
        'no_contrato' : contract_id.name[3:],
        'nombre' : contract_id.partner_name or '',
        'apellido_paterno' : contract_id.partner_fname or '',
        'apellido_materno' : contract_id.partner_mname or '',
        'empresa' : cont_comp.serie,
        'calle' : street,
        'numero_exterior' : number_address,
        'colonia' : colony_name,
        'localidad' : locality_name,
        'entre_calles' : between,
        'forma_pago_actual' : way_payment,
        'monto_pago_actual' : contract_id.payment_amount or 0,
        'cobradorID' : contract_id.debt_collector.ecobro_id or contract_id.debt_collector.id,
        'estatus' : contract_id.contract_status_item.ecobro_code or 1,
        'fecha_ultimo_abono' : self.calc_last_payment(contract_id),
        'monto_atrasado' : monto_atrasado, #contract_id.late_amount or 0,
        'fecha_primer_abono' : contract_id.date_first_payment.strftime('%Y-%m-%d') if contract_id.date_first_payment else "",
        'fecha_reactivacion' : contract_id.reactivation_date.strftime('%Y-%m-%d') if contract_id.reactivation_date else "",
        'detalle_servicio' : '',
        'solicitud' : contract_id.lot_id.name or '',
        'nombre_plan' : contract_id.name_service.name or '',
        'costo_plan' : contract_id.product_price or 0,
        'codigo_promotor' : contract_id.sale_employee_id.barcode or contract_id.employee_id.barcode,
        'saldo' : contract_id.balance or 0,
        'abonado' : contract_id.paid_balance or 0,
        'telefono' : contract_id.phone_toll or '',
      })
      ### ESCRIBIMOS EL CONTRATO QUE SE ESTA PROCESANDO
      log += 'Número de Contrato: {} \n'.format(contract_id.name)

      _logger.info("Contrato: {}".format(contract_id.name))
      _logger.info("Cobrador: {}-{}".format(contract_id.debt_collector.barcode,contract_id.debt_collector.name))
      log += '\n\n'
    ### RECORREMOS TODAS LAS BITACORAS
    _logger.info("Iniciamos Enpaquetado de bitacoras!")
    for index, mortuary_id in enumerate(mortuary_ids):
      if mortuary_id.balance > 0:
        contract_info.append({
          'contratoID' : int(mortuary_id.id) + 20000000,
          'serie' : mortuary_id.name[0:3],
          'no_contrato' : mortuary_id.name[3:],
          'nombre' : mortuary_id.ii_finado,
          'apellido_paterno' : '',
          'apellido_materno' : '',
          'empresa' : mortuary_comp.serie,
          'calle' : mortuary_id.podp_calle_y_number or '',
          'numero_exterior' : '',
          'colonia' : mortuary_id.podp_colonia_id.name or '',
          'localidad' : mortuary_id.podp_municipio_id.name or '',
          'entre_calles' : '',
          'forma_pago_actual' : 1,
          'monto_pago_actual' : 1,
          'cobradorID' : mortuary_id.employee_id.id or '',
          'estatus' : 1,
          'fecha_ultimo_abono' : '',
          'monto_atrasado' : 0,
          'fecha_primer_abono' : "",
          'fecha_reactivacion' : "",
          'detalle_servicio' : '',
          'solicitud' : '',
          'nombre_plan' : '',
          'costo_plan' : 0,
          'codigo_promotor' : '',
          'saldo' : mortuary_id.balance,
          'abonado' : 0,
          'telefono' :'',
        })
        ### ESCRIBIMOS EL CONTRATO QUE SE ESTA PROCESANDO
        log += 'Número de bitacora: {} \n'.format(mortuary_id.name)

        _logger.info("bitacora: {}".format(mortuary_id.name))
        log += '\n\n'
    ### MANEJO DE ERRORES AL ENVIAR AL WEB SERVICE
    try:
      ### SI EXISTE ALGÚN DATO POR SINCRONIZAR
      if contract_info:
        ###
        data = {
          'contratos' : contract_info
        }
        _logger.warning("La cantidad de contratos enviados es: {}".format(len(contract_info)))
        _logger.info("Información Enviada: {}".format(data))
        ### ENVIAR LA PETICIÓN
        req = requests.post(url, json=data)
        ### RECIBIENDO RESPUESTA
        response = json.loads(req.text)
        ### SI SE ENCUENTRAN ERRORES
        if response['fail']:
          ### RECORRER LA LISTA DE ERRORES
          for rec in response['fail']:
            ### ENVIAR LA INFORMACIÓN AL LOG
            _logger.warning('Se Encontrarón algunos errores: serie: {} contrato: {} error: {}'.format(
              rec['serie'],rec['no_contrato'],rec['error']))
        ### SI NO HAY NINGUN ERROR
        else:
          _logger.info("Información Recibida: {}".format(response))
          ### ENVIAR MENSAJE DE SINCRONIZACIÓN EXITOSA
          _logger.info("Sincronización de Contratos Exitosa!!")
      ### SI NO SE ENVÍA INFORMACIÓN
      else:
        ### SE ENVÍA RESPUESTA DE QUE NO HAY COBRADORES PARA PROCESAR
        _logger.info("No hay Contratos para procesar")
      ### EN CASO DE ALGÚN ERROR
    except Exception as e:
      ### ENVIANDO INFORMACIÓN DE ERROR AL LOG
      _logger.warning(e)
    try:
      url_log = self.get_url(company_id, "LOG_CONTRATOS")
      req_log = requests.post(url_log, log)
    except Exception as e:
      _logger.warning(e)

  ### CONCILIAR LOS DOCUMENTOS
  def reconcile_all(self, reconcile={}):
    ### DECLARACIÓN DE OBJETOS
    account_move_line_obj = self.env['account.move.line']
    reconcile_model = self.env['account.partial.reconcile']
    ### VALIDAMOS SI ESTAMOS RECIBIENDO LA LINEA DE FACTURA A CONCILIAR
    if reconcile.get('debit_move_id'):
      ### VALIDAMOS SI ESTAMOS RECIBIENDO LA LINEA DEL PAGO A CONCILIAR
      if reconcile.get('payment'):
        ### BUSCAMOS LA LINEA DEL PAGO
        line = account_move_line_obj.browse(reconcile.get('payment'))
        data = {
          'debit_move_id' : reconcile.get('debit_move_id'),
          'credit_move_id' : reconcile.get('payment'),
          'amount' : abs(line.balance),
        }
        reconcile_model.create(data)
        return True
    return False

  def get_pending_payments(self, company_id=False):
    log = False
    ### DECLARACIÓN DE OBJETOS
    contract_obj = self.env['pabs.contract'].sudo()
    account_obj = self.env['account.move'].sudo()
    journal_obj = self.env['account.journal'].sudo()
    payment_method_obj = self.env['account.payment.method'].sudo()
    payment_obj = self.env['account.payment'].sudo()
    hr_employee_obj = self.env['hr.employee'].sudo()
    company_obj = self.env['res.company'].sudo()
    mortuary_obj = self.env['mortuary'].sudo()
    ### DICCIONARIO DE RECONCILIACIÓN
    reconcile = {}
    ### MANDAR A LLAMAR LA URL DE PAGOS PENDIENTES
    url_pending = self.get_url(company_id, "RECIBOS_PENDIENTES")
    ### SI NO GENERA LA URL
    if not url_pending:
      ### ENVÍA AL LOG QUE NO SE PUDO CONFIGURAR LA URL
      _logger.warning("No se ha configurado ninguna IP de sincronización con ecobro")
      ### FINALIZA EL MÉTODO
      return
    try:
      company = company_obj.browse(company_id)
      ### SE ENVIA LA PETICIÓN PARA RECIBIR LOS PAGOS
      req = requests.post(url_pending)
      ### CASTEANDO A JSON LA RESPUESTA
      response = json.loads(req.text)
    except Exception as e:
      _logger.warning("Información recibida: {}".format(e))
      return
    ### DECLARANDO ARRAY PARA LOS CORRECTOS
    done = []
    ### DECLARANDO ARRAY PARA CANCELADOS
    fails = []
    ### OBTENIENDO LA MONEDA POR DEFAULT
    currency_id = account_obj.with_context(
      default_type='out_invoice')._get_default_currency()
    ### OBTENIENDO EL DIARIO POR DEFAULT
    cash_journal_id = journal_obj.search([
      ('company_id','=',company_id),
      ('type','=','cash')],limit=1)
    ### OBTENIENDO EL METODO DE PAGO
    payment_method_id = payment_method_obj.search([
      ('payment_type','=','inbound'),
      ('code','=','manual')],limit=1)
    ### CANTIDAD DE PAGOS RECIBIDOS
    len_payments = len(response['result'])
    if len_payments > 0:
      ### GENERANDO LA VARIABLE DE LOG
      log = 'Sincronización de Pagos \n'
    ### RECORRER LA RESPUESTA
    _logger.info("Registros a procesar: {}".format(len_payments))
    for index, rec in enumerate(response['result']):
      ### CONTANDO EL PAGO QUE SE ESTA GENERANDO
      log += 'Pago {} de {} \n'.format((index + 1), len_payments)
      ### CONCATENAR LA SERIE CON EL NUMERO DE CONTRATO
      contract_name = "{}{}".format(rec['serie'],rec['no_contrato'])
      ### BUSCAR EL COBRADOR
      _logger.info("El cobrador fue: {}".format(rec['no_cobrador']))
      collector_id = hr_employee_obj.search([
        ('company_id','=',company_id),
        ('ecobro_id','=',rec['no_cobrador'])],limit=1)

      if not collector_id:
        collector_id = hr_employee_obj.search([
        ('company_id','=',company_id),
        ('id','=',rec['no_cobrador'])], limit=1)

      ### AGREGAMOS LA INFORMACIÓN DEL PAGO AL LOG
      log += 'Número de Contrato: {}\n'.format(contract_name)

      ### VALIDAMOS QUE HAYA ENCONTRADO UN COBRADOR
      if not collector_id:
        ### LO AGREGA A LAS LISTAS DE FAILS
        fails.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          'detalle' : "No se pudo encontrar el cobrador"
        })
        log += 'No se pudo encontrar el Cobrador: {} \n'.format(rec['no_cobrador'])
        continue

      log += 'Cobrador: {} \n'.format(collector_id.name)

      ### Validar que el recibo no exista previamente
      ecobro_number = "{}{}".format(rec['serie_recibo'],rec['no_recibo'])
      recibo_afectado = payment_obj.search([
        ('company_id','=',company_id),
        ('ecobro_affect_id','=',rec['afectacionID'])
      ])

      log += 'Número de recibo: {} \n'.format(ecobro_number)

      ### VERIFICAMOS LA CANTIDAD DE RECIBOS ENCONTRADOS
      if len(recibo_afectado) > 1:
        fail.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          'detalle' : "Se encontro {} recibos".format(len(recibo_afectado))
        })
        log += 'Estatus: Se econtraron {} recibos \n'.format(len(recibo_afectado))
        continue

      ### IMPRIMIMOS EL NUMERO DE RECIBO
      _logger.info("Numero: {}".format(ecobro_number))

      ### Imprimimos para ver si existe el pago realizado previamente
      _logger.info("encontrado: {}".format(recibo_afectado))

      ### Imprimimos en el log el estatus del recibo
      _logger.info("Estatus del recibo: {}".format(rec['status']))
      ### SI LO ENVIAN A AFECTAR Y YA SE ENCUENTRA AFECTADO ENVIA RESPUESTA COMO FAIL
      if rec['status'] == '1':
        if recibo_afectado:
          done.append({
            'afectacionID' : rec['afectacionID'],
            'estatus' : 1,
            'detalle' : "El recibo ya existe. No se realizo afectacion"
          })
          log += 'Estatus: El recibo fue afectado previamente \n'
          continue

      ### SI LO ENVIAN A CANCELAR Y YA EXISTE EL MOVIMIENTO, LO CANCELA
      if rec['status'] == '7':
        if recibo_afectado:
          recibo_afectado.cancel()
          _logger.warning("el recibo: {} fue cancelado".format(ecobro_number))
          done.append({
            'afectacionID' : rec['afectacionID'],
            'estatus' : 1,
            'detalle' : "Se cancelo el recibo correctamente"
          })
          log += 'Estatus: Se cancelo el recibo correctamente \n'
          continue

      ### VERIFICAMOS EL TIPO DE COMPAÑIA
      company_sync = company.companies.filtered(lambda r: r.serie == rec['empresa'])
      if not company_sync:
        _logger.warning("No se encontró el tipo de compañia: {} para la empresa {}".format(rec['empresa'],company.name))
        fails.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          'detalle' : "No esta configurado el tipo de empresa: {}".format(rec['empresa'])
        })
        log += 'Estatus: No esta configurado el tipo de empresa: {}'.format(rec['empresa'])
        continue
      contract_id = False
      mortuary_id = False
      ### SI EL COBRO HACE REFERENCIA A COOPERATIVA O APOYO
      if company_sync.type_company in ('support', 'cooperative'):
        ### BUSCAMOS EL CONTRATO QUE SE CONCATENO
        contract_id = contract_obj.search([
          ('company_id','=',company_id),
          ('name', '=', contract_name)],limit=1)
        ### SI NO ENCUENTRA EL CONTRATO
        if not contract_id:
          ### LO AGREGA A LAS LISTAS DE FAILS
          fails.append({
            'afectacionID' : rec['afectacionID'],
            'estatus' : 2,
            'detalle' : "No se encontró el contrato"
          })
          log += 'Estatus: No se encontró el contrato al que debe de afectar \n'
          ### CONTINUA CON EL SIGUIENTE REGISTRO
          continue
        ### BUSCANDO LA/LAS FACTURA QUE VA A AFECTAR
        invoice_ids = contract_id.refund_ids.filtered(
          lambda x: x.type == 'out_invoice').sorted(
          key=lambda p: p.invoice_date)
      ### SI EL COBRO HACE REFERENCIA A FUNERARIA
      elif company_sync.type_company == 'mortuary':
        ###  BUSCAMOS EN BICATACORAS
        mortuary_id = mortuary_obj.search([
          ('company_id','=',company_id),
          ('name','=',contract_name)], limit=1)
        ### SI NO ENCUENTRA LA BITACORA
        if not mortuary_id:
          ### LO AGREGAMOS A LA LISTA DE FAILS
          fails.append({
            'afectacionID' : rec['afectacionID'],
            'estatus' : 2,
            'detalle' : "No se encontró la bitacora"
          })
          log += 'Estatus: No se encontró la bitacora que debe de afectar \n'
          ### CONTINUA CON EL SIGUIENTE REGISTRO
          continue
        ### BUSCAMOS LAS FACTURAS PERTENECIENTES A LA BITACORA
        invoice_ids = account_obj.search([
          ('company_id','=',company_id),
          ('type','=','out_invoice'),
          ('state','=','posted'),
          ('mortuary_id','=',mortuary_id.id)
        ])

      ### SI NO HAY NINGUNA FACTURA
      if not invoice_ids:
        fails.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          'detalle' : "No se encontro la factura"
        })
        log += 'Estatus: Se econtró la factura para aplicar el pago \n'
        continue

      ### Obtener el saldo del contrato
      saldo = 0
      for invoice_id in invoice_ids:
        saldo = saldo + float(invoice_id.amount_residual)

      ### Validar saldo del contrato
      if saldo < float(rec['monto']):
        message = "El Monto del recibo: {} es mayor que el saldo del contrato: {}".format(float(rec['monto']), saldo)
        fails.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          'detalle' : message
        })
        log += 'Estatus: El monto del recibo: {} es mayor que el saldo del contrato: {}'.format(float(rec['monto']), saldo)
        continue

      ##### PENDIENTE trabajar con mas de una factura #####
      ### SI EXISTE MÁS DE UN DOCUMENTO PARA AFECTAR
      if len(invoice_ids) >= 1:
        ### CICLAMOS LAS FACTURAS
        for invoice_id in invoice_ids:
          ### BUSCAMOS LA LINEA DONDE EL DEBITO SEA MAYOR QUE 0
          line = invoice_id.line_ids.filtered(
            lambda l: l.debit > 0)[0]
          ### AGREGAMOS LA LINEA A RECONCILIAR
          reconcile.update({'debit_move_id' : line.id})

      ### GENERANDO INFORMACIÓN PARA APLICAR EL PAGO
      payment_data = {
        'payment_reference' : 'Sincronizado de Ecobro',
        'reference' : 'payment',
        'way_to_pay' : 'cash',
        'communication' : 'Sync Ecobro',
        'payment_type' : 'inbound',
        'partner_type' : 'customer',
        'debt_collector_code' : collector_id.id,
        'contract' : contract_id.id if contract_id else False,
        'binnacle' : mortuary_id.id if mortuary_id else False,
        'partner_id' : contract_id.partner_id.id if contract_id else mortuary_id.partner_id.id,
        'amount' : rec['monto'],
        'currency_id' : currency_id.id,
        'date_receipt' : rec['fecha_recibo'],
        'payment_date' : rec['fecha_oficina'],
        'ecobro_affect_id' : rec['afectacionID'], 
        'ecobro_receipt' : ecobro_number,
        'journal_id' : cash_journal_id.id,
        'payment_method_id' : payment_method_id.id,
      }
      ### INTENTARÁ
      try:
        ### INDICANDO AL LOG QUE ESTA CREANDO PAGO...
        _logger.info("Creando Pago por: {}".format(rec['monto']))
        ### CREANDO EL PAGO...
        payment_id = payment_obj.with_context(force_company=company_id).create(payment_data)
        ### VALIDAMOS EL PAGO...
        payment_id.post()
        ### BUSCAMOS LA LINEA CON LA CUAL VA A CONCILIAR LA FACTURA
        payment_line = payment_id.move_line_ids.filtered(
          lambda p: p.credit > 0)[0]
        ### AGREGAMOS LA LINEA DEL PAGO PARA CONCILIAR
        reconcile.update({'payment' : payment_line.id})
        
      ### SI HUBÓ ALGÚN PROBLEMA LO AGREGARÁ A FAIL
      except Exception as e:
        fails.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          #'detalle' : e,
          'detalle' : str(e).replace('"','').replace("'",'')
        })
        log += 'Estatus: {}\n'.format(e)
        continue
      try:
        ### SI EL ESTATÚS ES PARA CANCELAR EL PAGO PROCESADO PREVIAMENTE SE DEBERÁ CANCELAR
        if rec['status'] == '7':
          payment_id.cancel()
          done.append({
            "afectacionID": rec['afectacionID'],
            "estatus":1,
            "detalle" : "Cancelado Correctamente",
          })
          log += 'Estatus: Se canceló el pago correctamente \n'
          continue
        elif rec['status'] == '1':
          ### EJECUTAMOS LA CONCILIACIÓN
          conciliation = self.reconcile_all(reconcile)
          if conciliation:
            done.append({
              "afectacionID": rec['afectacionID'],
              "estatus":1,
              "detalle" : "Afectado Correctamente",
            })
            log += 'Estatus: Correcto! \n'
            continue
          else:
            _logger.warning("no se concilió el pago y la factura")
            done.append({
              "afectacionID": rec['afectacionID'],
              "estatus":1,
              "detalle" : "Afectado sin conciliar",
            })
            log += 'Estatus: Se creó el pago, pero no se concilió \n'
            continue
        ### SI SE CREO Y RECONCILIO CORRECTAMENTE SE AGREGA A LA LISTA "DONE"
        
      except Exception as e:
        fails.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          'detalle' : str(e).replace("'",'').replace('"', ''),
        })
        log += 'Estatus: {} \n'.format(e)
        continue
      ### SE TERMINA LA ITERACIÓN DE LOS PAGOS
      log += '\n\n'
      
    ### AL FINALIZAR DE PROCESAR TODA LA INFORMACIÓN

    ### BUSCAMOS LA URL PARA ACTUALIZAR LOS PAGOS
    url_update = self.get_url(company_id, "ACTUALIZAR_RECIBOS")
    ### ENVIANDO LA URL AL LOG
    _logger.warning('URL DE ACTUALIZAR RECIBOS: {}'.format(url_update))
    ### SI NO GENERA LA URL
    if not url_update:
      ### ENVÍA AL LOG QUE NO SE PUDO CONFIGURAR LA URL
      _logger.warning("No se ha configurado ninguna IP de sincronización con ecobro")
    ### JUNTAMOS TODAS LAS PETICIONES PROCESADAS, TANTO LAS CORRECTAS COMO LAS FALLIDAS
    result = fails + done
    ### AGREGAMOS LAS RESPUESTAS A UN DICCIONARIO
    data_response = {'result' : result}
    try:
      _logger.warning("Estó es lo que se enviará a la petición: {}".format(data_response))
      ### SE ENVIA LA PETICIÓN PARA ACTUALIZAR LOS RECIBOS COMO AFECTADOS
      req2 = requests.post(url_update,json=data_response)
          ### LEYENDO RESPUESTA DEL WEB SERVICE
      ### RESPUESTA ANTES DE CASTEAR
      _logger.info("La respuesta del WebService: {}".format(req2.text))
      response2 = json.loads(req2.text)
      ### SI HUBO ALGÚN ERROR
      if response2['fail']:
        ### DECLARAMOS LA VARIABLE RECEIPTS PARA CAPTURAR LOS RECIBOS
        receipts = ""
        ### RECORREMOS EL FAIL
        for o in response2['fail']:
          ### SI LA VARIABLE ESTA VACIA 
          if receipt == "":
            ### ESCRIBIMOS EL PRIMER DATO
            receipts = "{}".format(o['afectacionID'])
          ### SI NO
          else:
            ### YA EXISTE UN REGISTRO POR ESO, SE LE ANTEPONE UNA COMA
            receipts = receipts + ",{}".format(o['afectacionID'])
        ### UNA VEZ TERMINADO DE LISTAR LOS RECIBOS NO AFECTADOS, ENVIAMOS EL ERROR AL LOG
        _logger.warning("Algunos de los recibos no pudieron ser actualizados: {}".format(fails))
      ### SI NO HUBO NINGÚN ERROR
      else:
        _logger.info("Todos los recibos fueron afectados correctamente, esta totalmente actualizado!!")
    except Exception as e:
      self._cr.rollback()
      _logger.warning("Hubo un problema con la petición al webservice, mensaje: {}".format(e))
    if log:
      try:
        url_log = self.get_url(company_id, "LOG_PAGOS")
        req_log = requests.post(url_log, log)
      except Exception as e:
        _logger.warning(e)

  def reactivate_contract(self):
    ### DECLARAMOS LOS OBJECTOS
    contract_obj = self.env['pabs.contract']
    contract_status_obj = self.env['pabs.contract.status']
    contract_status_reason_obj = self.env['pabs.contract.status.reason']

    ### TRAEMOS LA FECHA ACTUAL
    today = fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General'))

    ### BUSCAMOS EL ESTATUS SUPENSIÓN TEMPORAL
    status_id = contract_status_obj.search([
      ('ecobro_code','=',5)],limit=1)

    ### VALIDAMOS QUE HAYA TRAÍDO UN REGISTRO
    if not status_id:
      raise ValidationError((
        "No se encontró el estatus '5' - suspensión temporal, favor de verificar los estatus"))

    ### BUSCAMOS EL ESTATUS ACTIVO
    status_active_id = contract_status_obj.search([
      ('ecobro_code','=',1)],limit=1)

    ### BUSCAMOS LA RAZÓN DE ACTIVO
    status_reason_id = contract_status_reason_obj.search([
      ('reason','=','ACTIVO'),
      ('status_id','=',status_active_id.id)])

    ### VALIDAMOS QUE HAYA TRAÍDO UN REGISTRO
    if not status_active_id:
      raise ValidationError((
        "No se encontró el estatus '1' - Activo, favor de verificar los estatus"))

    ### BUSCAMOS LOS CONTRATOS QUE SE TENGAN QUE REACTIVAR HOY, O ANTERIOR A HOY
    contract_ids = contract_obj.search([
      ('contract_status_item','=',status_id.id),
      ('state','=','contract'),
      ('reactivation_date','<=',today)])

    ### ESCRIBIMOS EL ESTATUS ACTIVO EN TODOS LOS REGISTROS QUE SE ENCONTRARON
    contract_ids.write({
      'contract_status_item' : status_active_id.id,
      'contract_status_reason' : status_reason_id.id,
      'reactivation_date' : False,
    })

    _logger.info("Se reactivaron {} contratos el día de hoy: {}".format(len(contract_ids), today))
    contract_names = contract_ids.mapped('name')
    _logger.info("Los contratos que se procesaron son: {}".format(contract_names))

  def empty_tree_comission(self, contracts):
    ### DECLARACIÓN DE OBJETOS
    contract_obj = self.env['pabs.contract']

    contract_ids = contract_obj.search([
      ('name','in',contracts)])

    collector_job_id = self.env['hr.job'].search([
      ('name','=','COBRADOR')])

    for contract_id in contract_ids:
      tree_comission_ids = contract_id.commission_tree
      for comission_id in tree_comission_ids:
        if comission_id.job_id.id == collector_job_id.id:
          comission_id.unlink()
        else:
          amount = comission_id.corresponding_commission
          comission_id.remaining_commission = amount
          comission_id.commission_paid = 0
          comission_id.actual_commission_paid = 0


  def asign_comissions(self, contracts):
    ### DECLARAMOS OBJETOS
    contract_obj = self.env['pabs.contract']
    pabs_comission_tree_obj = self.env['pabs.comission.tree']

    contract_ids = contract_obj.search([
      ('name','in',contracts)])

    collector_job_id = self.env['hr.job'].search([
      ('name','=','COBRADOR')])

    id_cargo_cobrador = self.env['hr.job'].search([('name', '=', "COBRADOR")]).id

    for contract_id in contract_ids:
      comission_tree = contract_id.commission_tree
      _logger.info("El contrato procesado es: {}".format(contract_id.name))

      refund_ids = contract_id.refund_ids.filtered(lambda r: r.type == 'out_refund').sorted(lambda r: r.invoice_date)

      _logger.info("Cantidad de notas a procesar: {}".format(len(refund_ids)))

      for refund_id in refund_ids:
        _logger.info("La nota de crédito va por concepto de: {}".format(refund_id.ref))
        for comission_out in refund_id.comission_output_ids:
          line = comission_tree.filtered_domain(['&', ('job_id','=',comission_out.job_id.id),('comission_agent_id','=',comission_out.comission_agent_id.id)])
          line.remaining_commission = (line.remaining_commission - comission_out.commission_paid)
          line.commission_paid = (line.commission_paid + comission_out.commission_paid)
          line.actual_commission_paid = (line.actual_commission_paid + comission_out.actual_commission_paid)
          _logger.info("Valor aplicado: {}".format(comission_out.actual_commission_paid))

      payment_ids = contract_id.payment_ids.filtered(lambda r: r.state == 'posted').sorted(lambda r: r.payment_date)
      _logger.info("Cantidad de pagos a procesar: {}".format(len(payment_ids)))
      for payment_id in payment_ids:
        _logger.info("Número de recibo: {} por {}".format(payment_id.ecobro_receipt, payment_id.amount))
        for comission_out in payment_id.comission_output_ids:
            line = comission_tree.filtered_domain(['&', ('job_id','=',comission_out.job_id.id),('comission_agent_id','=',comission_out.comission_agent_id.id)])
            if line:
              line.remaining_commission = (line.remaining_commission - comission_out.commission_paid)
              line.commission_paid = (line.commission_paid + comission_out.commission_paid)
              line.actual_commission_paid = (line.actual_commission_paid + comission_out.actual_commission_paid)
            else:
              if comission_out.job_id.id == collector_job_id.id:
                com = pabs_comission_tree_obj.create(
                  {
                  'contract_id' : contract_id.id,
                  'pay_order' : comission_tree.sorted(lambda r: r.pay_order).mapped('pay_order')[-1] + 1,
                  'job_id' : collector_job_id.id,
                  'comission_agent_id' : comission_out.comission_agent_id.id,
                  'actual_commission_paid' : comission_out.actual_commission_paid,
                  })
                comission_tree += com

  def contracts_susp_to_cancel(self):
    log = "Sincronización de SUSP. PARA CANCELAR \n"
    ### DECLARACIÓN DE OBJETOS
    contract_obj = self.env['pabs.contract']
    status_obj = self.env['pabs.contract.status']
    reason_obj = self.env['pabs.contract.status.reason']

    ### MANDAR A LLAMAR LA URL DE SUSPENSIONES PARA CANCELAR
    url = self.get_url("LOG_SUSP")
    ### SI NO GENERA LA URL
    if not url:
      ### ENVÍA AL LOG QUE NO SE PUDO CONFIGURAR LA URL
      _logger.warning("No se ha configurado ninguna IP de sincronización con ecobro")
      ### FINALIZA EL MÉTODO
      return
    ### BUSCAMOS ESTATUS ACTIVO
    active_status_id = status_obj.search([
      ('status','=','ACTIVO')])
    ### SI NO SE ENCUENTRA ESTATUS ACTIVO
    if not active_status_id:
      raise ValidationError("No se encontró el estatus de Activo")
    ### BUSCAMOS EL ESTATUS DE SUSPENSIÓN PARA CANCELAR
    susp_status_id = status_obj.search([
      ('status','=','SUSP. PARA CANCELAR')])
    ### BUSCAMOS EL MOTIVO DE NO ABONA
    reason_id = reason_obj.search([
      ('reason','=','NO ABONA')])
    if not susp_status_id:
      raise ValidationError("No se encontró el estatus de Susp. para cancelar")
    if not reason_id:
      raise ValidationError("No se encontró la razón de No abona")
    ### BUSCAMOS TODOS LOS CONTRATOS
    contracts = contract_obj.search([
      ('state','=','contract'),
      ('contract_status_item','=',active_status_id.id)])
    ### FILTRAMOS DE TODOS LOS CONTRATOS, LOS QUE TENGAN MAS DE 91 DÍAS SIN ABONAR
    contract_ids = contracts.filtered(lambda r: (r.days_without_payment >= 91 and r.contract_status_reason.reason == 'ACTIVO'))
    ### SE ENVIAN TODOS ESOS CONTRATOS A SUSP. PARA CANCELAR
    if contract_ids:
      ### CONTAMOS TODOS LOS CONTRATOS QUE SE VAN A PROCESAR
      total_contracts = len(contract_ids)
      ### AGREGAMOS EL DATO AL LOG
      log += "{} Contratos para SUSP. TEMPORAL\n".format(total_contracts)
      ### RECORREMOS TODOS LOS CONTRATOS QUE SE TIENEN QUE SUSPENDER
      for index, contract_id in enumerate(contract_ids):
        ### LOS CAMBIAMOS DE ESTATUS
        contract_id.write({
          'contract_status_item' : susp_status_id.id,
          'contract_status_reason' : reason_id.id,
        })
        ### AGREGAMOS LA INFORMACION DE CONTRATO AL LOG
        log += "{} de {}\nContrato: {}\nDías sin abonar: {}\n\n".format(
          (index + 1),
          total_contracts,
          contract_id.name, 
          contract_id.days_without_payment)
      ### INTENTAREMOS
      try:
        ### ENVIAR LA INFORMACION AL WS
        req_log = requests.post(url, log)
      ### SI HAY ALGUN ERROR
      except Exception as e:
        ### lO ENVIAMOS AL LOG DE ODOO
        _logger.warning(e)

  def delete_payments(self,payments):
    ### DECLARACION DE OBJETOS
    del_ids = []
    payment_obj = self.env['account.payment']
    for payment in payments:
      payment_ids = payment_obj.search([
        ('ecobro_receipt','=',payment)])
      count = len(payment_ids) -2
      for index, payment_id in enumerate(payment_ids):
        if index <= count:
          payment_id.action_draft()
          payment_id.cancel()
          del_ids.append(payment_id.id)
    query = "DELETE FROM account_payment where id in {}".format(del_ids).replace("[","(").replace("]",")")
    self._cr.execute(query)
    self._cr.commit()

  # A. Cambia los contratos con saldo = 0 a estatus PAGADO
  # B. Cambia los contratos con saldo = 0 y estatus o detalle REALIZADO POR COBRAR a estatus REALIZADO
  # Actualiza todas las compañias
  def mover_a_estatus_final(self):  
    _logger.warning("Comienza proceso: Mover a estatus final")

    #####     1. Buscar estatus con los que se trabajará     #####

    # 1.1 Estatus PAGADO
    obj_estatus_pagado = self.env['pabs.contract.status'].search([('status','=','PAGADO')])
    if not obj_estatus_pagado:
      _logger.warning("No se encontró el estatus PAGADO")
      raise ValidationError("{}".format("No se encontró el estatus PAGADO"))

    # 1.2 Estatus REALIZADO
    obj_estatus_realizado = self.env['pabs.contract.status'].search([('status','=','REALIZADO')])
    if not obj_estatus_realizado:
      raise ValidationError("{}".format("No se encontró el estatus REALIZADO"))

    # 1.3 Estatus ACTIVO
    obj_estatus_activo = self.env['pabs.contract.status'].search([('status','=','ACTIVO')])
    if not obj_estatus_activo:
      raise ValidationError("{}".format("No se encontró el estatus ACTIVO"))

    # 1.4 Motivo REALIZADO POR COBRAR del estatus ACTIVO
    obj_realizado_por_cobrar = self.env['pabs.contract.status.reason'].search([('status_id','=',obj_estatus_activo.id), ('reason','=','REALIZADO POR COBRAR')])
    id_realizado_por_cobrar = 0
    if obj_realizado_por_cobrar:
      id_realizado_por_cobrar = obj_realizado_por_cobrar.id

    #####     2. Proceso para pasar contratos a pagado     #####  
    # Criterios: Los contratos deben tener saldo 0, no estar en estatus PAGADO ni REALIZADO, no tener motivo ni detalle de servicio REALIZADO POR COBRAR

    # 2.1 Buscar motivo PAGADO del estatus PAGADO
    obj_motivo_pagado = self.env['pabs.contract.status.reason'].search([('status_id','=',obj_estatus_pagado.id), ('reason','=','PAGADO')])
    if not obj_motivo_pagado:
      _logger.warning("No se encontró el motivo PAGADO para el estatus PAGADO")
      raise ValidationError("{}".format("No se encontró el motivo PAGADO para el estatus PAGADO"))

    # 2.2 Buscar contratos. Nota: Se cambió a consulta sql porque obtener el saldo mediante api es lento
    consulta = """
      SELECT 
        con.id, comp.name, con.name
      FROM pabs_contract AS con
      INNER JOIN account_move AS fac ON con.id = fac.contract_id AND fac.type = 'out_invoice' AND fac.state = 'posted'
      INNER JOIN res_company as comp ON con.company_id = comp.id
        WHERE con.state = 'contract'
        AND con.contract_status_item NOT IN ({},{})
        AND con.service_detail IN ('unrealized')
        AND NOT (con.contract_status_reason = {})
          GROUP BY con.id, comp.name, con.name HAVING SUM(fac.amount_residual) = 0 AND COUNT(fac.id) > 0
            ORDER BY con.company_id, con.name
      """.format(obj_estatus_pagado.id, obj_estatus_realizado.id, id_realizado_por_cobrar,)
    
    self.env.cr.execute(consulta)

    # 2.3 Escribir en log los contratos a pagar y construir lista con los id de los contratos obtenidos
    lista_id_contratos = []

    for row in self.env.cr.fetchall():
      lista_id_contratos.append(row[0])
      #bitacora = bitacora + row[1] + " -> " + row[2] + "\n"

    _logger.warning("Contratos a pagar: {}".format( len(lista_id_contratos) ))

    # 2.4 Obtener contratos mediante ORM 
    contratos_a_pagar = self.env['pabs.contract'].sudo().browse(lista_id_contratos)

    # 2.5 Actualizar estatus y motivo
    indice = 1
    for con in contratos_a_pagar:
      con.write({'contract_status_item': obj_estatus_pagado.id, 'contract_status_reason': obj_motivo_pagado.id})
      _logger.warning("{}. Contrato pagado: {} -> {}".format(indice, con.company_id.name, con.name))
      indice = indice + 1
    
    #####     3. Proceso para pasar contratos a realizado     #####  
    # Los contratos deben tener saldo 0, tener motivo o detalle de servicio REALIZADO POR COBRAR

    # 3.1 Buscar motivo REALIZADO del estatus REALIZADO
    obj_motivo_realizado = self.env['pabs.contract.status.reason'].search([('status_id','=',obj_estatus_realizado.id), ('reason','=','REALIZADO')])
    if not obj_motivo_realizado:
      _logger.warning("No se encontró el motivo REALIZADO para el estatus REALIZADO")
      raise ValidationError("{}".format("No se encontró el motivo REALIZADO para el estatus REALIZADO"))

    # 3.2 Buscar contratos. Nota: Se cambió a consulta sql porque obtener el saldo mediante api es lento
    consulta = """
      SELECT 
        con.id, comp.name, con.name
      FROM pabs_contract AS con
      INNER JOIN account_move AS fac ON con.id = fac.contract_id AND fac.type = 'out_invoice' AND fac.state = 'posted'
      INNER JOIN res_company as comp ON con.company_id = comp.id
        WHERE con.state = 'contract'
        AND con.contract_status_item NOT IN ({},{})
        AND (con.contract_status_reason = {} OR con.service_detail IN ('made_receivable', 'realized') )
          GROUP BY con.id, comp.name, con.name HAVING SUM(fac.amount_residual) = 0 AND COUNT(fac.id) > 0
            ORDER BY con.company_id, con.name
      """.format(obj_estatus_pagado.id, obj_estatus_realizado.id, id_realizado_por_cobrar)

    self.env.cr.execute(consulta)

    # 3.3 Escribir en log los contratos a realizar y construir lista con los id de los contratos obtenidos
    lista_id_contratos = []

    for row in self.env.cr.fetchall():
      lista_id_contratos.append(row[0])
      #bitacora = bitacora + row[1] + " -> " + row[2] + "\n"

    _logger.warning("Contratos a realizar: {}".format( len(lista_id_contratos) ))

    # 3.4 Obtener contratos mediante ORM
    contratos_a_realizar = self.env['pabs.contract'].sudo().browse(lista_id_contratos)

    # 3.5 Actualizar estatus, motivo y detalle de servicio
    indice = 1
    for con in contratos_a_realizar:
      con.write({'contract_status_item': obj_estatus_realizado.id, 'contract_status_reason': obj_motivo_realizado.id, 'service_detail' : 'realized'})
      _logger.warning("{}. Contrato realizado: {} -> {}".format(indice, con.company_id.name, con.name))
      indice = indice + 1

    _logger.warning("Se terminó proceso Mover contratos a estatus final")