# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging
import requests
from dateutil import tz
#import threading
import json

PAYMENTS = [
"V1000","P2010","X462","X407","X417","N3112","J70","M2194","F3167","N3086","W214",
"X424","U1804","N3102","F3196","M2180","T1022","U1803","W260","T1013","P1975",
"M2182","OX1117","P2031","U1832","X463","X446","X443","T1012","T1014","T1074",
"OX1105","X468","V995","T1071","U1783","P1968","U1816","R500","W261","U1740","N3133",
"N3129","X476","X457","X412","T1037","X450","X430","W230","Z21","R495","P1984","W215",
"U1731","T1021","M2125","R486","X496","W7","F3225","W253","F3176","F3184","W236","Z15",
"P2038","T1052","U1718","X469","X458","N3107","N3108","U1809","N3116","M2199","U1709",
"M2189","W210","V994","X506","V999","N3103","J71","X440","M2145","P2042","T1007","M2146",
"M2161","X433","M2140","U1771","M2196","T1065","U1820","F3223","R511","W249","W243","M2141",
"U1735","U1781","F3212","V998","U1710","V986","R512","M2136","T1009","P2002","F3187","U1817",
"M2186","X410","T998","M2119","V1008","W254","Y37","P1998","U1745","U1761","P1986","M2177",
"V991","X454","W251","W4","X484","M2117","W228","M2168","X475","T1056","U1737","P2043","U1808",
"P1972","J77","X432","T1024","R479","F3208","T1036","OX1110","N3130","P1994","V980","P2015",
"Y38","M2175","T1041","U1768","M2129","N3074","W238","V1012","F3190","F3182","F3163","F3183",
"X413","U1697","R489","M2172","M2103","N3091","N3069","T1059","V976","U1728","F3174","F3221",
"U1786","P2011","N3123","V984","W252","X409","X467","Y40","U1785","U1815","N3109","U1822",
"U1750","U1826","U1694","OX1095","X490","N3078","F3181","X415","R487","X473","U1794","U1788",
"M2197","X502","P2046","X416","F3180","F3207","P2036","M2137","OX1102","V1014","X421","U1738",
"N3084","M2118","M2200","U1720","X481","R509","P2033","R485","P2029","U1708","M2192","X497","F3178",
"M2116","F3166","F3217","U1757","U1714","P2030","N3096","M2151","U1753","U1748","T996","P2045",
"U1752","X449","U1763","W237","V979","R506","X431","U1719","T1054","P2005","U1759","P1977",
"P2007","P2014","U1699","U1792","P2040","N3113","F3201","M2170","X422","U1799","P1979","U1729",
"W234","F3216","P2022","R483","P2044","J78","U1773","M2150","U1800","M2106","X442","U1747",
"X425","X428","P2047","T1032","N3134","X486","T1017","F3177","R481","F3214","W233","OX1106",
"F3211","X478","U1706","U1716","T1067","R505","N3125","W224","V1016","U1824","U1744","F3173",
"P2019","W255","OX1109","P1988","Z24","R502","X501","OX1100","M2102","M2105","U1821","N3132",
"P2003","V1017","X488","P1970","P2041","W3","R471","X439","OX1097","F3228","V983","V982","N3099",
"P1989","X434","X452","T1055","W262","T1072","M2110","V1004","P1983","V1005","U1841","T1076","J69",
"U1778","M2163","W259","X500","P1995","U1766","F3192","N3087","F3206","X418","V987","U1762","F3168",
"T1046","N3138","W257","U1715","M2132","N3079","U1727","F3199","U1700","P2037","U1741","V988","X503",
"P1973","OX1116","U1782","R507","V978","N3114","P2024","U1784","U1742","U1813","P2006","U1801",
"M2112","U1701","P1982","T1069","X441","P1981","OX1096","T1051","M2104","N3104","T1038","N3070",
"P2027","R498","Z23","V990","U1751","M2205","T1045","F3215","M2109","U1825","R482","U1790","N3071",
"M2158","W5","F3204","Z13","F3222","N3105","R504","U1765","V1003","T1053","N3073","T1028","X444",
"X408","U1836","Z22","T1050","U1793","U1795","X437","U1818","W220","N3093","T1019","F3218","X435",
"P1991","F3170","Z14","U1698","R510","W239","W221","F3169","R472","R494","N3088","N3072","W212",
"T1026","U1749","X499","X455","N3139","M2157","M2191","U1756","T1057","U1837","U1789","M2174",
"OX1099","N3085","X483","P1985","W217","N3136","P1974","P2004","N3106","U1779","W216","M2142",
"X477","M2152","J75","P2023","W6","T1000","M2184","T1063","U1780","P1993","M2144","P1996","T1064",
"V981","M2159","X411","U1830","U1695","U1797","R478","U1796","M2127","V1015","T1049","X460",
"OX1098","V1001","T1062","U1707","N3137","F3227","T999","OX1114","T1047","F3171","M2108",
"M2135","T1029","U1828","T1043","N3115","V993","M2120","P1999","U1764","T1015","T1008","N3127",
"U1722","T1005","P2026","U1829","X456","M2204","U1703","X438","X406","T1058","N3128","X489","T1035",
"P2018","M2133","M2148","U1725","X423","P2009","V977","V1007","U1823","U1838","U1827","X453","Z16",
"W245","N3101","P1992","X427","U1758","F3194","W231","X426","U1726","F3172","OX1104","W240","T1061",
"W227","M2167","T1048","U1775","N3090","X459","N3141","W8","U1721","Z18","F3197","N3082","U1842",
"U1806","M2111","X493","F3210","M2169","F3219","M2190","U1739","U1844","M2203","F3188","P1976",
"P2012","V1002","J74","W232","V1020","T1001","U1743","U1723","N3076","X429","R488","M2164","U1730",
"U1835","R497","M2162","R499","U1840","M2181","M2195","F3213","U1807","T1044","X451","T1010","W211",
"T1030","R493","U1767","U1811","W256","M2147","U1819","T1031","T1020","U1831","X492","M2124","X466",
"P1969","W250","Y43","U1717","U1755","F3226","F3200","X448","M2123","N3089","OX1101","X436","M2173",
"P1990","M2176","T1003","U1713","R484","W223","U1833","F3193","M2187","F3198","T1075","R474","N3111",
"U1777","M2156","U1712","W219","T1066","M2153","T1018","X482","M2131","R491","U1805","V996","T997",
"T995","T1011","N3077","U1787","U1734","X461","F3165","M2126","R473","M2202","X487","N3092","N3081",
"W218","U1802","M2165","F3195","P1987","X414","V992","X465","OX1108","N3131","M2188","F3185","M2179",
"X445","OX1111","P2013","OX1107","P2021","F3205","W213","V1011","N3119","N3121","M2154","V997",
"T1070","M2155","X505","M2171","U1812","M2128","F3164","OX1115","N3118","U1754","U1839","F3224",
"M2183","V1013","X495","W258","M2143","N3100","X419","X420","V1018","M2115","Z19","X504","R503",
"M2101","U1736","X491","P2025","P2017","T1027","T1060","M2198","X471","T1068","U1770","M2113",
"P2032","W263","R475","X474","P1978","T1039","P2034"]

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

  def get_url(self, path):
    ### INSTANCIACIÓN DE OBJETOS
    param_obj = self.env['ir.config_parameter'].sudo()
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
    ### GENERAMOS LA VARIABLE DE LOS LOGS
    log = "Sincronización de Cobradores \n"
    ### INSTANCIACIÓN DE OBJECTOS
    debt_collector_obj = self.env['pabs.comission.debt.collector'].sudo()
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
      log+= '{} . {} \n'.format(employee_id.barcode, employee_id.name)

      ### VALIDAR QUE EL COBRADOR ESTÉ ACTIVO
      if employee_id.employee_status.id == status_id.id:
        ### EMPAQUETANDO INFORMACIÓN DEL COBRADOR
        employee_data.append({
        'codigo' : employee_id.barcode,
        'nombre' : employee_id.name,
        'serie' : debt_collector_id.receipt_series,
        'telefono' : employee_id.mobile_phone or "",
        'cobradorID' : int(employee_id.ecobro_id) or employee_id.id
        })
        log+= 'Estatus: {} Sincronizado con Exito \n'.format(employee_id.employee_status.name)
      else:
        log+= 'Estatus: {} No se Sincronizó'.format(employee_id.employee_status.name)
      log += '\n\n'

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
      url_log = self.get_url("LOG_COBRADORES")
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

  def sync_contracts(self):
    ### GENERAR VARIABLE DE LOG
    log = "Sincronización de Contratos de Odoo \n"
    ### INSTANCIACIÓN DE OBJECTOS
    contract_obj = self.env['pabs.contract'].sudo()
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
      ('contract_status_item','not in',('CANCELADO','PAGADO','REALIZADO'))])

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
      ### AGREGANDO INFORMACIÓN DE CONTRATO A LA LISTA
      log += 'Contrato {} de {} \n'.format((index + 1), len_contract)
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
        'estatus' : contract_id.contract_status_item.ecobro_code or 1,
        'fecha_ultimo_abono' : self.calc_last_payment(contract_id),
        'monto_atrasado' : contract_id.late_amount or 0,
        'fecha_primer_abono' : contract_id.date_first_payment.strftime('%Y-%m-%d') if contract_id.date_first_payment else "",
        'fecha_reactivacion' : contract_id.reactivation_date.strftime('%Y-%m-%d') if contract_id.reactivation_date else "",
        'detalle_servicio' : '',
        'solicitud' : contract_id.lot_id.name or '',
        'nombre_plan' : contract_id.name_service.name or '',
        'costo_plan' : contract_id.product_price or 0,
        'codigo_promotor' : contract_id.sale_employee_id.barcode or contract_id.employee_id.barcode,
        'saldo' : contract_id.balance or 0,
        'abonado' : contract_id.paid_balance or 0,
      })
      ### ESCRIBIMOS EL CONTRATO QUE SE ESTA PROCESANDO
      log += 'Número de Contrato: {} \n'.format(contract_id.name)

      _logger.info("Contrato: {}".format(contract_id.name))
      _logger.info("Cobrador: {}-{}".format(contract_id.debt_collector.barcode,contract_id.debt_collector.name))
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
      url_log = self.get_url("LOG_CONTRATOS")
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

  def get_pending_payments(self):
    log = False
    ### DECLARACIÓN DE OBJETOS
    contract_obj = self.env['pabs.contract'].sudo()
    account_obj = self.env['account.move'].sudo()
    journal_obj = self.env['account.journal'].sudo()
    payment_method_obj = self.env['account.payment.method'].sudo()
    payment_obj = self.env['account.payment'].sudo()
    hr_employee_obj = self.env['hr.employee'].sudo()
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
    try:
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
      collector_id = hr_employee_obj.search(['|',
        ('ecobro_id','=',rec['no_cobrador']),
        ('id','=',rec['no_cobrador'])],limit=1)

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

      ### Validar que el recibo no esté afectado
      ecobro_number = "{}{}".format(rec['serie_recibo'],rec['no_recibo'])
      recibo_afectado = payment_obj.search([
        ('ecobro_affect_id','=',rec['afectacionID']),
        ('state','in',['posted','sent','reconciled'])
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
        log += 'Estatus: No se encontró el contrato al que debe de afectar \n'
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
        'ecobro_receipt' : ecobro_number,
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
    if log:
      try:
        url_log = self.get_url("LOG_PAGOS")
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

    ### MANDAR A LLAMAR LA URL DE SUSPENSIONES PARA CANCELAR
    url = self.get_url("LOG_SUSP")
    ### SI NO GENERA LA URL
    if not url:
      ### ENVÍA AL LOG QUE NO SE PUDO CONFIGURAR LA URL
      _logger.warning("No se ha configurado ninguna IP de sincronización con ecobro")
      ### FINALIZA EL MÉTODO
      return
    ### BUSCAMOS LOS CONTRATOS QUE ESTÁN ACTIVOS
    active_status_id = status_obj.search([
      ('status','=','ACTIVO')])
    if not active_status_id:
      raise ValidationError("No se encontró el estatus de Activo")
    ### BUSCAMOS EL ESTATUS DE SUSPENSIÓN PARA CANCELAR
    susp_status_id = status_obj.search([
      ('status','=','SUSP. PARA CANCELAR')])
    if not susp_status_id:
      raise ValidationError("No se encontró el estatus de Susp. para cancelar")
    ### BUSCAMOS TODOS LOS CONTRATOS
    contracts = contract_obj.search([
      ('state','=','contract'),
      ('contract_status_item','=',active_status_id.id)])
    ### FILTRAMOS DE TODOS LOS CONTRATOS, LOS QUE TENGAN MAS DE 91 DÍAS SIN ABONAR
    contract_ids = contracts.filtered(lambda r: r.days_without_payment >= 91)
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