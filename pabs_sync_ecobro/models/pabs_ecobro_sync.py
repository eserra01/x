# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging
import requests
from dateutil import tz
#import threading
import json

_logger = logging.getLogger(__name__)

WORKERS = 10

CONTRACTS_1 = [
    '1CJ002055','1CJ000560','1CJ002091','1CJ003666','1CJ001696','1CJ003702','1CJ002415','1CJ000100',
    '1CJ001357','1CJ004261','1CJ000811','1CJ000188','1CJ003519','1CJ001511','1CJ001510','1CJ002753',
    '1CJ000552','1CJ002495','1CJ003042','1CJ001770','1CJ001896','1CJ003513','1CJ001857','1CJ002463',
    '1CJ000742','1CJ002016','1CJ001996','1CJ001997','1CJ003554','1CJ002923','1CJ002924','1CJ003731',
    '1CJ003732','1CJ001203','1CJ003703','1CJ003116','1CJ003871','1CJ002780','1CJ002779','1CJ002338',
    '1CJ001149','1CJ003273','1CJ001473','1CJ004009','1CJ001265','1CJ001266','1CJ003544','1CJ004210',
    '1CJ001514','1CJ000246','1CJ004209','1CJ000899','1CJ001153','1CJ003291','1CJ003864','1CJ001171',
    '1CJ002397','1CJ000967','1CJ001753','1CJ001752','1CJ002197','1CJ003472','1CJ003825','1CJ000545',
    '1CJ002176','1CJ002170','1CJ003305','1CJ002631','1CJ003712','1CJ003713','1CJ002528','1CJ002527',
    '1CJ003659','1CJ001135','1CJ004222','1CJ002933','1CJ000287','1CJ002043','1CJ002035','1CJ002459']
CONTRACTS_2 = [
    '1CJ002856','1CJ002969','1CJ002968','1CJ002731','1CJ000183','1CJ000445','1CJ004204','1CJ002265',
    '1CJ000722','1CJ000723','1CJ000724','1CJ002356','1CJ002357','1CJ004574','1CJ002023','1CJ002024',
    '1CJ003692','1CJ000677','1CJ001700','1CJ001619','1CJ004260','1CJ003129','1CJ003128','1CJ002092',
    '1CJ000454','1CJ002674','1CJ004022','1CJ004895','1CJ001108','1CJ000307','1CJ001691','1CJ003865',
    '1CJ002627','1CJ002256','1CJ001690','1CJ001841','1CJ002082','1CJ004158','1CJ004159','1CJ001942',
    '1CJ004982','1CJ003972','1CJ004150','1CJ003866','1CJ003445','1CJ003444','1CJ004083','1CJ004142',
    '1CJ003101','1CJ001714','1CJ002877','1CJ005370','1CJ004086','1CJ002959','1CJ003960','1CJ003961',
    '1CJ003962','1CJ003959','1CJ005233','1CJ004950','1CJ002817','1CJ005402','1CJ002895','1CJ004126',
    '1CJ004125','1CJ002852','1CJ005219','1CJ004266','1CJ004281','1CJ002623','1CJ002507','1CJ002291',
    '1CJ005139','1CJ004479','1CJ004480','1CJ004094','1CJ004093','1CJ000039','1CJ001129','1CJ004476',
    '1CJ001136','1CJ004234','1CJ001190','1CJ004235','1CJ000171','1CJ000446','1CJ000181','1CJ000201',
    '1CJ000109','1CJ000110','1CJ000477','1CJ001735','1CJ000298','1CJ000518','1CJ000406','1CJ004041']
CONTRACTS_3 = [
    '1CJ000623','1CJ000499','1CJ000176','1CJ000177','1CJ000538','1CJ000657','1CJ001589','1CJ000961',
    '1CJ000267','1CJ000154','1CJ000147','1CJ001468','1CJ003594','1CJ000150','1CJ001218','1CJ000158',
    '1CJ000498','1CJ003550','1CJ003549','1CJ001483','1CJ000616','1CJ000713','1CJ003873','1CJ001469',
    '1CJ001658','1CJ000195','1CJ000274','1CJ000699','1CJ001596','1CJ004932','1CJ000655','1CJ001292',
    '1CJ003076','1CJ000561','1CJ002876','1CJ000808','1CJ004514','1CJ001724','1CJ002175','1CJ004861',
    '1CJ001016','1CJ001963','1CJ002799','1CJ000652','1CJ004835','1CJ003567','1CJ002189','1CJ004002',
    '1CJ004174','1CJ005191','1CJ000978','1CJ000142','1CJ002445','1CJ003565','1CJ000583','1CJ000320',
    '1CJ002785','1CJ000607','1CJ001867','1CJ002178','1CJ003350','1CJ002491','1CJ000066','1CJ005223',
    '1CJ000613','1CJ002332','1CJ003373','1CJ002814','1CJ002037','1CJ000091','1CJ001562','1CJ000973',
    '1CJ002199','1CJ000592','1CJ003908','1CJ000434','1CJ004487','1CJ001362','1CJ003909','1CJ003988',
    '1CJ000813','1CJ000213','1CJ003615','1CJ003617','1CJ003735','1CJ001221','1CJ002299','1CJ000269',
    '1CJ004283','1CJ003734','1CJ003256','1CJ003255','1CJ001913','1CJ001945','1CJ001376','1CJ002287',
    '1CJ003910','1CJ001456','1CJ000327','1CJ002086','1CJ000945','1CJ001051','1CJ002722','1CJ001401',
    '1CJ003041','1CJ000128','1CJ004030','1CJ003355','1CJ004262','1CJ004263','1CF000063','1CJ002812']
CONTRACTS_4 = [
    '1CJ004193','1CJ004264','1CJ004265','1CJ003430','1CJ004361','1CJ000516','1CJ003045','1CJ000562',
    '1CJ002637','1CJ002389','1CJ003929','1CJ003225','1CJ003547','1CJ000901','1CJ003595','1CJ002840',
    '1CJ002846','1CJ000058','1CJ000047','1CJ001295','1CJ001300','1CJ003008','1CJ000732','1CJ000733',
    '1CJ003548','1CJ001591','1CJ001592','1CJ004850','1CJ004848','1CJ004847','1CJ000734','1CJ003133',
    '1CJ005195','1CJ003208','1CJ003983','1CJ003982','1CJ003209','1CJ003038','1CJ003205','1CJ001610',
    '1CJ001611','1CJ001702','1CJ001703','1CJ003884','1CJ001789','1CJ004576','1CJ004057','1CJ004525',
    '1CJ003469','1CJ004655','1CJ004346','1CJ000547','1CJ004439','1CJ004141','1CJ004323','1CJ000241',
    '1CJ000776','1CJ000097','1CJ004152','1CJ000333','1CJ000332','1CJ001106','1CJ003945','1CJ001333',
    '1CJ005056','1CJ001556','1CJ001557','1CJ001496','1CJ000503','1CJ005489','1CJ001331','1CJ000311',
    '1CJ002688','1CJ000870','1CJ002066','1CJ002276','1CJ002277','1CJ002275','1CJ000322','1CJ001566',
    '1CJ000035','1CJ002577','1CJ004164','1CJ002579','1CJ002578','1CJ001602','1CJ000334','1CJ004181',
    '1CJ003178','1CJ004019','1CJ004180','1CJ003527','1CJ001662','1CJ004116','1CJ000939','1CJ003447',
    '1CJ003119','1CJ003120','1CJ002508','1CJ001489','1CJ004227','1CJ002853','1CJ004844','1CJ002790',
    '1CJ001306','1CJ000651','1CJ004930','1CJ003573','1CJ004934','1CJ002719','1CJ000456','1CJ000107',
    '1CJ000279','1CJ000357','1CJ001962','1CJ001916','1CJ000411','1CJ000412','1CJ003889','1CJ004103',
    '1CJ002270','1CJ003454','1CJ003455','1CJ002894','1CJ004165','1CJ003885','1CJ000691','1CJ001270',
    '1CJ000130','1CJ003925','1CJ003473','1CJ001883','1CJ000384','1CJ000383','1CJ001663','1CJ005124',
    '1CJ004214','1CJ000336','1CJ004230','1CJ001560','1CJ005369','1CJ000842','1CJ003151','1CJ003546',
    '1CJ000694','1CJ000006','1CJ003451','1CJ002295','1CJ004040','1CJ002110','1CJ004219','1CJ001504',
    '1CJ004140','1CJ003955','1CJ004085','1CJ003954','1CJ003931']

CONTRACTS_5 = ['1CJ003665','1CJ000167','1CJ000568','1CJ005093','1CJ005095','1CJ005094','1CJ004144',
    '1CJ004145','1CJ003992','1CJ003719','1CJ003738','1CJ003774','1CJ001143','1CJ001130','1CJ000381',
    '1CJ003965','1CJ003964','1CJ004357','1CJ004356','1CJ000465','1CJ003574','1CJ003575','1CJ003580',
    '1CJ003581','1CJ003655','1CJ004995','1CJ001245','1CJ000254','1CJ002253','1CJ001069','1CJ005681',
    '1CJ000495','1CJ004061','1CJ004344','1CJ002597','1CJ002598','1CJ004143','1CJ001264','1CJ005490',
    '1CJ004058','1CJ003248','1CJ003247','1CJ003619','1CJ004175','1CJ003876','1CJ005137','1CJ004178',
    '1CJ004179','1CJ001455','1CJ001912','1CJ003387','1CJ002442','1CJ000586','1CJ000587','1CJ000627',
    '1CJ001197','1CJ002912','1CJ002911','1CJ004023','1CJ000161','1CJ004198','1CJ000462','1CJ002209',
    '1CJ001120','1CJ002318','1CJ002317','1CJ002934','1CJ005103','1CJ005102','1CJ004119','1CJ002313',
    '1CJ002145','1CJ002146','1CJ002847','1CJ001513','1CJ003658','1CJ002044','1CJ005202','1CJ000442',
    '1CJ000443','1CJ000444','1CJ000458','1CJ000121','1CJ000501','1CJ000500','1CJ003277','1CJ003443',
    '1CJ003442','1CJ000257','1CJ000149','1CJ000789','1CJ004097','1CJ001798','1CJ001794','1CJ005708',
    '1CJ005709','1CJ002621','1CJ003981','1CJ004575','1CJ001989','1CJ001119','1CJ004221','1CJ004231',
    '1CJ000376','1CJ000224','1CJ003809','1CJ003810','1CJ000604','1CJ001971','1CJ000431','1CJ000127',
    '1CJ004401','1CJ004607','1CJ000386','1CJ000277','1CJ002172','1CJ003395','1CJ000299','1CJ002872',
    '1CJ003642','1CJ003990','1CJ000379','1CJ002403','1CJ000131','1CJ001598','1CJ001436','1CJ002111']
CONTRACTS_6 = [
    '1CJ001396','1CJ004237','1CJ002803','1CJ003795','1CJ000803','1CJ005145','1CJ003354','1CJ003943',
    '1CJ000233','1CJ001491','1CJ002138','1CJ000741','1CJ005115','1CJ005116','1CJ005119','1CJ005122',
    '1CJ005126','1CJ005220','1CJ005221','1CJ005224','1CJ005247','1CJ005251','1CJ004229','1CJ004228',
    '1CJ002040','1CJ002039','1CJ002624','1CJ002290','1CJ004542','1CJ003824','1CJ000731','1CJ000554',
    '1CJ002437','1CJ002941','1CJ001612','1CJ005123','1CJ005176','1CJ005182','1CJ003998','1CJ002390',
    '1CF000134','1CJ003599','1CJ000180','1CJ000152','1CJ000218','1CJ004118','1CJ001848','1CJ002600',
    '1CJ004218','1CJ005541','1CJ000345','1CJ002769','1CJ004059','1CJ004060','1CJ001279','1CJ001632',
    '1CJ002609','1CJ002608','1CJ002607','1CJ000678','1CJ003232','1CJ002748','1CJ002749','1CJ000087',
    '1CJ003106','1CJ004481','1CJ000318','1CJ001503','1CF000047','1CJ001582','1CJ002095','1CJ004168',
    '1CJ004172','1CJ004171','1CJ004177','1CJ001791','1CJ004224','1CJ004225','1CJ004226','1CJ004223',
    '1CJ002342','1CJ002341','1CJ003102','1CF000107','1CJ003470','1CJ000143','1CJ003385','1CJ005257',
    '1CJ001358','1CJ000960','1CJ003950','1CJ002957','1CJ003031','1CJ003922','1CJ003921','1CJ004149',
    '1CJ003630','1CJ001246','1CJ000798','1CJ001409','1CJ003882','1CJ001314','1CJ000242','1CJ004153',
    '1CJ004151','1CJ000502','1CJ005199','1CJ000373','1CJ004026','1CJ002976','1CJ000461','1CJ003737',
    '1CJ000239','1CJ002433','1CJ005055','1CJ002931','1CJ001705','1CJ001695','1CJ003628','1CJ001252']
CONTRACTS_7 = [
    '1CJ000326','1CJ000210','1CJ003478','1CJ000489','1CJ003044','1CJ003043','1CJ002231','1CJ002230',
    '1CJ002962','1CJ003872','1CJ003870','1CJ002001','1CJ001113','1CJ003596','1CJ002205','1CJ000355',
    '1CJ003629','1CJ000893','1CJ000335','1CJ002158','1CJ005518','1CJ003539','1CJ003538','1CJ000358',
    '1CJ000052','1CJ001790','1CJ004714','1CJ001041','1CJ003419','1CJ004769','1CJ002626','1CJ004098',
    '1CJ002384','1CJ004045','1CJ005640','1CJ000982','1CJ003759','1CJ003622','1CJ000525','1CJ003963',
    '1CJ005196','1CJ000301','1CJ000302','1CJ002171','1CJ003390','1CJ001307','1CJ001689','1CJ000132',
    '1CJ003054','1CJ002414','1CJ000515','1CJ000514','1CJ005186','1CJ002362','1CJ001303','1CJ001301',
    '1CJ001070','1CJ001900','1CJ000702','1CJ005255','1CJ004169','1CJ005113','1CJ000876','1CJ001229',
    '1CJ005144','1CJ005159','1CJ005154','1CJ005160','1CJ005209','1CJ005185','1CJ000410','1CJ000469',
    '1CJ000004','1CJ000003','1CJ000163','1CJ004240','1CJ004090','1CJ003219','1CJ002141','1CJ002164',
    '1CJ003493','1CJ003139','1CJ002761','1CJ002371','1CJ004017','1CJ001780','1CJ004186','1CJ003545',
    '1CJ004533','1CD000001','1CJ004192','1CJ002067','1CJ004054','1CJ002306','1CJ002300','1CJ002302',
    '1CJ004137','1CJ004146','1CJ004148','1CJ001559','1CJ004581','1CJ004091','1CJ004021','1CJ004084',
    '1CJ002309','1CJ004113','1CJ003058','1CJ002386','1CJ002943','1CJ002730','1CJ002678','1CJ003986',
    '1CJ003969','1CJ003970','1CJ004025','1CJ004024','1CJ000831','1CJ003989','1CJ004099','1CJ004092',
    '1CJ004100','1CJ004138','1CJ004220','1CJ001293','1CJ004170','1CJ002531','1CJ004236','1CJ002677']
CONTRACTS_8 = [
    '1CJ004238','1CJ001231','1CJ004239','1CJ001233','1CJ004345','1CJ004101','1CJ001232','1CJ004139',
    '1CJ000897','1CJ000983','1CJ004096','1CJ001180','1CJ000841','1CJ001630','1CJ001074','1CJ001085',
    '1CJ001548','1CJ001348','1CJ001349','1CJ001721','1CJ003920','1CJ002015','1CJ001346','1CJ001107',
    '1CJ001128','1CJ003946','1CJ003536','1CJ002673','1CJ000969','1CJ001935','1CJ001936','1CJ002913',
    '1CJ003516','1CJ004342','1CJ001512','1CJ002249','1CJ003085','1CJ003086','1CJ001008','1CJ001532',
    '1CJ003428','1CJ003265','1CJ003429','1CJ004232','1CJ004233','1CJ002177','1CJ003991','1CJ000187',
    '1CJ003386','1CJ004147','1CJ003656','1CJ004095','1CJ001110','1CJ004067','1CJ004066','1CJ003874',
    '1CJ005582','1CJ000508','1CJ000767','1CJ000638','1CJ003801','1CJ000263','1CJ000450','1CJ000378',
    '1CJ000361','1CJ000744','1CJ000986','1CJ001533','1CJ000991','1CJ002594','1CJ002238','1CJ001871',
    '1CJ001439','1CJ002303','1CJ002301','1CJ000968','1CJ002670','1CJ002671','1CJ003157','1CJ001998']

URL = {
  'COBRADORES' : '/controlusuarios/cargarCobradores',
  'CONTRATOS' : '/controlcartera/cargarContratos',
  'RECIBOS_PENDIENTES' : '/controlpagos/obtenerCobrosPorAfectar',
  'ACTUALIZAR_RECIBOS' : '/controlpagos/actualizarCobrosAfectados',
  'LOG_CONTRATOS' : '/controlodoo/saveLogsContratos',
  'LOG_COBRADORES' : '/controlodoo/saveLogsCobradores',
  'LOG_PAGOS' : '/controlodoo/saveLogsPagos',
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