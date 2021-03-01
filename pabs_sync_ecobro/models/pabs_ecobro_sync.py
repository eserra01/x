# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging
import requests
#import threading
import json

_logger = logging.getLogger(__name__)

WORKERS = 10

URL = {
  'COBRADORES' : '/controlusuarios/cargarCobradores',
  'CONTRATOS' : '/controlcartera/cargarContratos',
  'RECIBOS_PENDIENTES' : '/controlpagos/obtenerCobrosPorAfectar',
  'ACTUALIZAR_RECIBOS' : '/controlpagos/actualizarCobrosAfectados',
}

class PABSEcobroSync(models.Model):
  _name = 'pabs.ecobro.sync'

  def get_url(self, path):
    ### INSTANCIACIÓN DE OBJETOS
    param_obj = self.env['ir.config_parameter']
    ### OBTENER PARAMETRO DE DATOS DE PRUEBA
    demo = param_obj.get_param('testing_ecobro')
    ### OBTENER PARAMETRO DE IP DE ECOBRO
    ip = param_obj.get_param('ecobro_ip')
    ### OBTENER LA CIUDAD DE ECOBRO
    if demo:
      city = "ecobroSAP_TEST"
    else:
      city = param_obj.get_param('ecobro_city')
    basic_url = "{}/{}".format(ip,city)
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

  def sync_collectors(self):
    ### INSTANCIACIÓN DE OBJECTOS
    debt_collector_obj = self.env['pabs.comission.debt.collector']
    ### MANDAR A LLAMAR LA URL DE COBRADORES
    url = self.get_url("COBRADORES")
    ### SI NO GENERA LA URL
    if not url:
      ### ENVÍA AL LOG QUE NO SE PUDO CONFIGURAR LA URL
      _logger.warning("No se ha configurado ninguna IP de sincronización con ecobro")
      ### FINALIZA EL MÉTODO
      return
    ### BUSCAMOS EN LAS COMISIONES DE COBRADORES TODOS LOS QUE TENGAN ASIGNADAS SERIES
    debt_collector_ids = debt_collector_obj.search([('receipt_series','!=',False)])
    ### LISTA DE INFORMACIÓN VACÍA
    employee_data = []
    ### SÍ EXISTEN COBRADORES CON SERIES ASIGNADAS, CREAMOS CICLO
    for debt_collector_id in debt_collector_ids:
      ### INFORMACIÓN DEL COBRADOR
      employee_id = debt_collector_id.debt_collector_id
      ### PARA SINCRONIZAR SOLAMENTE LOS ACTIVOS
      if employee_id.employee_status == 'ACTIVO':
        ### EMPAQUETANDO INFORMACIÓN DEL COBRADOR
        employee_data.append({
        'codigo' : employee_id.barcode,
        'nombre' : employee_id.name,
        'serie' : debt_collector_id.receipt_series,
        'telefono' : employee_id.mobile_phone or "",
        'cobradorID' : int(employee_id.ecobro_id) or employee_id.id
        })
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

  ### POR MEDIO DEL CONTRATO RETORNA EL ID PARA EL SINCRONIZADOR
  def get_estatus(self, contract_id):
    ### VERIFICA SI SE ENVIÓ UN CONTRATO
    if contract_id:
      ### GUARDANDO EL ESTATUS
      status = contract_id.contract_status_item
      ### DECLARANDO EL CÓDIGO DE ESTATUS
      status_code = 0
      ### CASTEANDO A MAYUSCULAS EL ESTATUS
      status_name = status.status
      ### SI EL ESTATUS ES ACTIVO
      if status_name == 'ACTIVO':
        status_code = 1
      ### SI EL ESTATUS ES REALIZADO
      elif status_name == 'REALIZADO':
        status_code = 2
      ### SI EL ESTATUS ES PAGADO
      elif status_name == 'PAGADO':
        status_code = 3
      ### SI EL ESTATUS ES SUSPENDIDO TEMPORAL
      elif status_name == 'SUSPENDIDO TEMPORAL':
        status_code = 4
      ### SI EL ESTATUS ES SUSPENDIDO POR CANCELAR
      elif status_name == 'SUSPENDIDO POR CANCELAR':
        status_code = 5
      ### SI EL ESTATUS ES VERIFICACION TEMPORAL
      elif status_name =='VERIFICACION TEMPORAL':
        status_code = 15
      ### SI EL ESTATUS ES VERIFICACION SC
      elif status_name == 'VERIFICACION SC':
        status_code = 16
      ### RETORNA EL VALOR DEL CODIGO
      return status_code

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

  def sync_contracts(self):
    ### INSTANCIACIÓN DE OBJECTOS
    contract_obj = self.env['pabs.contract']
    ### MANDAR A LLAMAR LA URL DE CONTRATOS
    url = self.get_url("CONTRATOS")
    ### SI NO GENERA LA URL
    if not url:
      ### ENVÍA AL LOG QUE NO SE PUDO CONFIGURAR LA URL
      _logger.warning("No se ha configurado ninguna IP de sincronización con ecobro")
      ### FINALIZA EL MÉTODO
      return
    ### BUSCAR TODOS LOS CONTRATOS QUE NO ESTÉN EN ESTATUS CANCELADO, PAGADO Ó REALIZADO
    contract_ids = contract_obj.search([
      ('state','=','contract'),
      ('contract_status_item','not in',('CANCELADO','PAGADO','REALIZADO')),
      ('invoice_date','>=','2021-02-15')])

    ### LISTA DE CONTRATOS VACÍA
    contract_info = []
    ### SI SE ENCONTRARÓN REGISTROS SE CICLARÁ
    for contract_id in contract_ids:
      ### VALIDANDO LA FORMA DE PAGO ACTUAL: SEMANAL / QUINCENAL / MENSUAL
      if contract_id.way_to_payment == 'weekly':
        way_payment = 1
      elif contract_id.way_to_payment == 'biweekly':
        way_payment = 2
      elif contract_id.way_to_payment == 'monthly':
        way_payment = 3
      ### AGREGANDO INFORMACIÓN DE CONTRATO A LA LISTA
      contract_info.append({
        'contratoID' : int(contract_id.ecobro_id) or contract_id.id,
        'serie' : contract_id.name[0:3],
        'no_contrato' : contract_id.name[3:],
        'nombre' : contract_id.partner_name or '',
        'apellido_paterno' : contract_id.partner_fname or '',
        'apellido_materno' : contract_id.partner_mname or '',
        'empresa' : '01',
        'calle' : contract_id.street_name_toll or '',
        'numero_exterior' : contract_id.street_number_toll or '',
        'colonia' : contract_id.toll_colony_id.name or '',
        'localidad' : contract_id.toll_municipallity_id.name or '',
        'entre_calles' : contract_id.between_streets_toll or '',
        'forma_pago_actual' : way_payment,
        'monto_pago_actual' : contract_id.payment_amount or 0,
        'cobradorID' : contract_id.debt_collector.ecobro_id or contract_id.debt_collector.id,
        'estatus' : self.get_estatus(contract_id),
        'fecha_ultimo_abono' : self.calc_last_payment(contract_id),
        'monto_atrasado' : contract_id.late_amount or 0,
        'fecha_primer_abono' : contract_id.date_first_payment.strftime('%Y-%m-%d'),
        'fecha_reactivacion' : contract_id.reactivation_date.strftime('%Y-%m-%d') if contract_id.reactivation_date else "",
        'detalle_servicio' : '',
        'solicitud' : contract_id.lot_id.name or '',
        'nombre_plan' : contract_id.name_service.name or '',
        'costo_plan' : contract_id.product_price or 0,
        'codigo_promotor' : contract_id.sale_employee_id.barcode or contract_id.employee_id.barcode,
        'saldo' : contract_id.balance or 0,
        'abonado' : contract_id.paid_balance or 0,
      })
    ### MANEJO DE ERRORES AL ENVIAR AL WEB SERVICE
    try:
      ### SI EXISTE ALGÚN DATO POR SINCRONIZAR
      if contract_info:
        ###
        data = {
          'contratos' : contract_info
        }
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

  def get_pending_payments(self):
    ### DECLARACIÓN DE OBJETOS
    contract_obj = self.env['pabs.contract']
    account_obj = self.env['account.move']
    journal_obj = self.env['account.journal']
    payment_method_obj = self.env['account.payment.method']
    payment_obj = self.env['account.payment']
    hr_employee_obj = self.env['hr.employee']
    ### DICCIONARIO DE RECONCILIACIÓN
    reconcile = {}
    ### MANDAR A LLAMAR LA URL DE PAGOS PENDIENTES
    url_pending = self.get_url("RECIBOS_PENDIENTES")
    ### SI NO GENERA LA URL
    if not url_pending:
      ### ENVÍA AL LOG QUE NO SE PUDO CONFIGURAR LA URL
      _logger.warning("No se ha configurado ninguna IP de sincronización con ecobro")
      ### FINALIZA EL MÉTODO
      return
    ### SE ENVIA LA PETICIÓN PARA RECIBIR LOS PAGOS
    req = requests.post(url_pending)
    ### CASTEANDO A JSON LA RESPUESTA
    try:
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
      ('type','=','cash')],limit=1)
    ### OBTENIENDO EL METODO DE PAGO
    payment_method_id = payment_method_obj.search([
      ('payment_type','=','inbound'),
      ('code','=','manual')],limit=1)
    ### RECORRER LA RESPUESTA
    _logger.info("Registros a procesar: {}".format(len(response['result'])))
    for rec in response['result']:
      ### CONCATENAR LA SERIE CON EL NUMERO DE CONTRATO
      contract_name = "{}{}".format(rec['serie'],rec['no_contrato'])
      ### BUSCAR EL COBRADOR
      collector_id = hr_employee_obj.search([
        '|',('ecobro_id','=',rec['no_cobrador']),
        ('id','=',rec['no_cobrador'])],limit=1)

      ### VALIDAMOS QUE HAYA ENCONTRADO UN COBRADOR
      if not collector_id:
        ### LO AGREGA A LAS LISTAS DE FAILS
        fails.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          'detalle' : "No se pudo encontrar el cobrador"
        })
        continue

      ### Validar que el recibo no esté afectado
      ecobro_number = "{}{}".format(rec['serie_recibo'],rec['no_recibo'])
      recibo_afectado = payment_obj.search([
        ('Ecobro_receipt','=',ecobro_number),
        ('state','in',['posted','sent','reconciled'])
      ])

      ### VERIFICAMOS LA CANTIDAD DE RECIBOS ENCONTRADOS
      if len(recibo_afectado) > 1:
        fail.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          'detalle' : "Se encontro {} recibos".format(len(recibo_afectado))
          })

      ### SI LO ENVIAN A AFECTAR Y YA SE ENCUENTRA AFECTADO ENVIA RESPUESTA COMO FAIL
      if rec['status'] == 1:
        if recibo_afectado:
          done.append({
            'afectacionID' : rec['afectacionID'],
            'estatus' : 1,
            'detalle' : "El recibo ya existe. No se realizo afectacion"
          })
          continue

      ### SI LO ENVIAN A CANCELAR Y YA EXISTE EL MOVIMIENTO, LO CANCELA
      elif rec['status'] == 7:
        if recibo_afectado:
          recibo_afectado.cancel()
          done.append({
            'afectacionID' : rec['afectacionID'],
            'estatus' : 1,
            'detalle' : "Se cancelo el recibo correctamente"
          })
          continue


      ### BUSCAMOS EL CONTRATO QUE SE CONCATENO
      contract_id = contract_obj.search([
        ('name', '=', contract_name)],limit=1)
      ### SI NO ENCUENTRA EL CONTRATO
      if not contract_id:
        ### LO AGREGA A LAS LISTAS DE FAILS
        fails.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          'detalle' : "No se encontró el contrato"
        })
        ### CONTINUA CON EL SIGUIENTE REGISTRO
        continue
      ### BUSCANDO LA/LAS FACTURA QUE VA A AFECTAR
      invoice_ids = contract_id.refund_ids.filtered(
        lambda x: x.type == 'out_invoice').sorted(
        key=lambda p: p.invoice_date)
      ### SI NO HAY NINGUNA FACTURA
      if not invoice_ids:
        fails.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          'detalle' : "No se encontro la factura"
        })
        continue

      ### Obtener el saldo del contrato
      saldo = 0
      for invoice_id in invoice_ids:
        saldo = saldo + float(invoice_id.amount_residual)

      ### Validar saldo del contrato
      if saldo < float(rec['monto']):
        message = "El Monto del recibo: '{}' es mayor que el saldo del contrato: '{}'".format(float(rec['monto']), saldo)
        fails.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          'detalle' : message
        })
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

      ### LANZANDO NUMERO DE CONTRATO QUE ESTA SIENDO AFECTADO
      _logger.info("Número de Contrato: {}".format(contract_id.name))
      ### GENERANDO INFORMACIÓN PARA APLICAR EL PAGO
      payment_data = {
        'payment_reference' : 'Sincronizado de Ecobro',
        'reference' : 'payment',
        'way_to_pay' : 'cash',
        'communication' : 'Sync Ecobro',
        'payment_type' : 'inbound',
        'partner_type' : 'customer',
        'debt_collector_code' : collector_id.id,
        'contract' : contract_id.id,
        'partner_id' : contract_id.partner_id.id,
        'amount' : rec['monto'],
        'currency_id' : currency_id.id,
        'date_receipt' : rec['fecha_recibo'],
        'payment_date' : rec['fecha_oficina'],
        'ecobro_affect_id' : rec['afectacionID'], 
        'Ecobro_receipt' : ecobro_number,
        'journal_id' : cash_journal_id.id,
        'payment_method_id' : payment_method_id.id,
      }
      ### INTENTARÁ
      try:
        ### INDICANDO AL LOG QUE ESTA CREANDO PAGO...
        _logger.info("Creando Pago por: {}".format(rec['monto']))
        ### CREANDO EL PAGO...
        payment_id = payment_obj.create(payment_data)
        ### VALIDAMOS EL PAGO...
        payment_id.post()
        ### BUSCAMOS LA LINEA CON LA CUAL VA A CONCILIAR LA FACTURA
        payment_line = payment_id.move_line_ids.filtered(
          lambda p: p.credit > 0)[0]
        ### AGREGAMOS LA LINEA DEL PAGO PARA CONCILIAR
        reconcile.update({'payment' : payment_line.id})
        ### EJECUTAMOS LA CONCILIACIÓN
        conciliation = self.reconcile_all(reconcile)
        if not conciliation:
          _logger.warning("no se concilió el pago y la factura")
          done.append({
          "afectacionID": rec['afectacionID'],
          "estatus":1,
          "detalle" : "Afectado Correctamente",
        })
        continue
        
      ### SI HUBÓ ALGÚN PROBLEMA LO AGREGARÁ A FAIL
      except Exception as e:
        fails.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          #'detalle' : e,
          'detalle' : "No se pudo procesar"
        })
        continue
      try:
        ### SI EL ESTATÚS ES PARA CANCELAR EL PAGO PROCESADO PREVIAMENTE SE DEBERÁ CANCELAR
        if rec['status'] == 7:
          payment_id.cancel()
          done.append({
          "afectacionID": rec['afectacionID'],
          "estatus":1,
          "detalle" : "Cancelado Correctamente",
        })
        ### SI SE CREO Y RECONCILIO CORRECTAMENTE SE AGREGA A LA LISTA "DONE"
        
      except Exception as e:
        fails.append({
          'afectacionID' : rec['afectacionID'],
          'estatus' : 2,
          #'detalle' : e,
          'detalle' : "No se pudo cancelar el pago"
        })
    ### AL FINALIZAR DE PROCESAR TODA LA INFORMACIÓN

    ### BUSCAMOS LA URL PARA ACTUALIZAR LOS PAGOS
    url_update = self.get_url("ACTUALIZAR_RECIBOS")
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
