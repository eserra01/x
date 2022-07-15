# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Jaime Rodriguez (jaime.rodriguez@pabsmr.org)
#
###########################################################################################

from email import header
from os import stat
from random import vonmisesvariate
from termios import VLNEXT
from xml.dom import VALIDATION_ERR
from odoo import fields, models, _, api
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from requests import status_codes
from datetime import datetime, date, timedelta
import requests
import json
import logging

_logger = logging.getLogger(__name__)





### TEST: ASIGNAR COMPAÑIAS DE PRODUCCION ### !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#COMPANY_SAL = 12 #TEST
#COMPANY_MON = 13 #TEST
COMPANY_SAL = 18 #PROD
COMPANY_MON = 19 #PROD





class PabsMigration(models.Model):
  """Modelo para migrar datos desde PABS"""
  _name = 'pabs.migration'
  _description = 'Migracion Pabs'

  url_pabs = fields.Char(string="URL webservice")

  @api.onchange('limit_pabs')
  def _onchange_limit_pabs(self):
      for rec in self:
        rec.offset_pabs = 0     
        rec.response_pabs = ''
  
  @api.onchange('limit2_pabs')
  def _onchange_limit2_pabs(self):
      for rec in self:
        rec.offset_pabs = self.limit2_pabs

  ###################################################################################################################
  ### Llamada a web service que consulta la base de pabs ###

  def _get_data(self, company_id, qry):
    #
    headers = {'Content-Type':'application/x-www-form-urlencoded'}
    params = {'consulta': qry}

    plaza = ""
    if company_id == COMPANY_SAL:
      plaza = "SALTILLO"
    elif company_id == COMPANY_MON:
      plaza = "MONCLOVA"

    url = "http://nomina.dyndns.biz:8099/index.php"

    querystring = {"pwd":"4dm1n","plaza": plaza}

    response = requests.post(url, data=params, headers=headers, params=querystring)
    try:     
      res = json.loads(response.text)
    except Exception as e:    
      raise ValidationError(e)
    return res

  def _get_data_txt(self, company_id, qry):
    #
    headers = {'Content-Type':'application/x-www-form-urlencoded'}
    params = {'consulta': qry}

    plaza = ""
    if company_id == COMPANY_SAL:
      plaza = "SALTILLO"
    elif company_id == COMPANY_MON:
      plaza = "MONCLOVA"

    url = "http://nomina.dyndns.biz:8099/index.php"

    querystring = {"pwd":"4dm1n","plaza": plaza}

    response = requests.post(url, data=params, headers=headers, params=querystring)  
    return response.text 
  
  ###################################################################################################################
  ### CREAR CONTRATOS ###
  def crear_contratos(self, company_id, limite = 0):   

    _logger.info("Comienza creación de contratos compañia: {}, Limite: {}".format(company_id, limite))

    # Consultar todos los ids de contratos de pabs
    contratos_pabs = self._get_data(company_id, "SELECT id_contrato, CONCAT(serie,no_contrato) as contrato FROM contratos WHERE tipo_bd != 20 AND serie != '1CZ' ORDER BY serie, CAST(no_contrato AS DECIMAL)")

    # Consultar todos los ids de contratos de odoo
    consulta = "SELECT name FROM pabs_contract WHERE company_id = {}".format(company_id)
    self.env.cr.execute(consulta)

    contratos_odoo = []
    for res in self.env.cr.fetchall():
      contratos_odoo.append(res[0])

    # Tomar los primeros X contratos que no existen en odoo
    indice = 0
    ids_contratos_nuevos = []

    for con in contratos_pabs:
      if con['contrato'] in contratos_odoo:
        continue
      else:
        if indice >= limite:
          break

        ids_contratos_nuevos.append(con['id_contrato'])
        indice = indice + 1

    if len(ids_contratos_nuevos) == 0:
      _logger.info("No hay contratos")
      return

    consulta = """
    SELECT 
        con.id_contrato,
        con.saldo,
        con.serie,
        CONCAT(con.serie, con.no_contrato) AS contrato,
        CONCAT(sol.serie, sol.no_solicitud) AS solicitud,
        con.fecha_contrato,
        mot.motivo,
        est.no_estatus,
        est.estatus,
        con.fecha_estatus,
        con.fecha_primer_abono,
        con.inversion_inicial,
        con.forma_pago,
        con.monto_pago,
        con.costo,
        cob.nombre AS cobrador,
        cob.no_empleado_ext AS cod_cobrador,
        asi.nombre AS asistente,
        asi.no_empleado_ext AS cod_asistente,
        IFNULL(aso.tipo_contrato, 'COMISION') AS tipo_contrato,
        IFNULL(ofi.nombre_oficina, '') AS oficina,
        cli.nombre AS partner_name,
        cli.apellido_pat AS partner_fname,
        cli.apellido_mat AS partner_mname,
        cli.telefono,
        cli.fecha_nacimiento,
        cli.cp,
        IF(cli.rfc IS NULL, '', cli.rfc) rfc,
        cli.calle,
        cli.no_ext,
        cli.no_int,
        loc.localidad AS municipio,
        cli.entre_calles,
        col.colonia,
        cli.no_col_cobro,
        cli.calle_cobro,
        cli.no_ext_cobro,
        cli.no_int_cobro,
        col_cobro.colonia AS colonia_cobro,
        loc_cobro.localidad AS municipio_cobro,
        pla.DESCRIPCION AS plan
    FROM contratos AS con
    INNER JOIN solicitudes AS sol ON  con.id_solicitud = sol.id_solicitud 
    INNER JOIN servicios AS ser ON con.no_servicio = ser.no_servicio 
    INNER JOIN planes AS pla ON ser.id_plan = pla.ID_PLAN 
    INNER JOIN clientes AS cli ON con.no_cliente = cli.no_cliente 
    INNER JOIN colonias AS col ON cli.no_colonia = col.no_colonia    
    INNER JOIN localidad AS loc ON col.no_loc = loc.no_loc
    INNER JOIN colonias AS col_cobro ON cli.no_col_cobro = col_cobro.no_colonia 
    INNER JOIN localidad AS loc_cobro ON col_cobro.no_loc = loc_cobro.no_loc
    INNER JOIN personal AS cob ON con.no_cobrador = cob.no_personal
    INNER JOIN personal AS asi ON con.no_personal = asi.no_personal 
    INNER JOIN motivos AS mot ON con.no_motivo = mot.no_motivo 
    INNER JOIN estatus AS est ON mot.no_estatus = est.no_estatus 
    LEFT JOIN asociados AS aso ON asi.no_empleado_ext = aso.no_nomina_asociado
    LEFT JOIN oficina AS ofi ON aso.no_oficina = ofi.no_oficina 
        WHERE con.id_contrato IN ({})
    """.format(', '.join(ids_contratos_nuevos))


    #
    data = self._get_data_txt(company_id, consulta)
    #
    i = 0
    vals = []
    #
    while True:
      try:
        x = data.index('{',i)
        o = data.index('}',i) + 1
        val = data[x:o]
        vals.append(val)
        i = o  
      except Exception as e:    
        # raise ValidationError(e) 
        break
    #
    rows = []   
    for v in vals:
      try:                       
        rows.append(eval(v))
      except Exception as e:
        _logger.info("Error: {}".format(e))
        continue        
        # raise ValidationError(e)    
    

    lot_obj = self.env['stock.production.lot']
    product_obj = self.env['product.product']
    stock_obj = self.env['stock.warehouse']
    contract_obj = self.env['pabs.contract']
    locality_obj = self.env['res.locality']
    employee_obj = self.env['hr.employee']
    resource_obj = self.env['resource.resource']
    way_to_payment = [{'1': 'weekly'},{'2': 'biweekly'},{'3': 'monthly'}]
    status_obj = self.env['pabs.contract.status']
    motivos_status_obj = self.env['pabs.contract.status.reason']
   
    # PLANES POR PLAZA
    series_producto = []
    if company_id == COMPANY_SAL:
      series_producto = [    
      ]
    elif company_id == COMPANY_MON:
      series_producto = [    
        {'serie': '1CJ', 'product': 'PL-00005'}
      ]
    
    # Se busca el puesto de trabajo del AS
    job_id = self.env['hr.job'].search([('name','=','ASISTENTE SOCIAL'),('company_id','=', company_id)], limit=1)
    if not job_id:
      raise ValidationError('No se encuentra el puesto de ASISTENTE SOCIAL')     
    # Se busca el puesto COBRADOR
    collector_job_id = self.env['hr.job'].search([('name','=','COBRADOR'),('company_id','=', company_id)], limit=1)
    if not collector_job_id:
      raise ValidationError('No se encuentra el puesto de COBRADOR')
    # Se busca el departamento de COBRANZA
    collector_dept_id = self.env['hr.department'].search([('name','=','COBRANZA'),('company_id','=', company_id)], limit=1)
    if not collector_dept_id:
       raise ValidationError( 'No se encuentra el departamento de VENTAS')
    # Se busca el departamento de ventas
    sales_dept_id = self.env['hr.department'].search([('name','=','VENTAS'),('company_id','=', company_id)], limit = 1)
    if not sales_dept_id:
       raise ValidationError('No se encuentra el departamento de VENTAS')
    # Se buscan los esquemas de pago 
    sueldo_id = self.env['pabs.payment.scheme'].search([('name','=','SUELDO')], limit=1 )
    if not sueldo_id:
       raise ValidationError('No se encuentra esquema de pago SUELDO')
    comision_id = self.env['pabs.payment.scheme'].search([('name','=','COMISION')], limit=1)
    if not comision_id:
        raise ValidationError('No se encuentra esquema de pago COMISIÓN')
    # Se busca el estatus ACTIVO
    active_status_id = status_obj.search([('status','=','ACTIVO')], limit=1)
    # Se busca el motivo ACTIVO
    active_reason_id = motivos_status_obj.search([('reason','=','ACTIVO')], limit=1)
    #
    vals = []
    create_cons = ''
    #
    cantidad_contratos = len(rows)

    # ITERACION EN CADA CONTRATO
    for index, d in enumerate(rows, 1):          
      _logger.info("{} de {}. {}".format(index, cantidad_contratos, d['contrato']))
      # try:            
      # Se busca el almacén
      warehouse_id = stock_obj.search([('name','=',d.get('oficina').upper()),('company_id','=', company_id)], limit=1)      
      if not warehouse_id:
        # errors.append({'contrato': d.get('contrato'),'Motivo': 'No se encuentra el almacén: %s'%(d.get('oficina'))})
        # raise ValidationError('No se encuentra el almacén %s del contrato %s'%(d.get('oficina').upper(),d.get('id_contrato')))
        warehouse_id = stock_obj.search([('name','=','CONTRATOS'),('company_id','=', company_id)], limit=1)      
        
        #Si no encuentra la oficina asignar la de contratos
        if not warehouse_id.id: 
          wh_id = 248
        else:
          wh_id = warehouse_id.id
      
      # Se crea el asistente si no existe
      sale_employee_id = employee_obj.search([('barcode','=',d.get('cod_asistente')), ('company_id','=', company_id)])       
      if not sale_employee_id:
        resource_id = resource_obj.create({'name': d.get('asistente')})
        employee_vals = {
          'first_name': d.get('cobrador'),
          'last_name': '',
          'date_of_admission':fields.Date.today(), 
          'barcode': d.get('cod_asistente'), 
          'resource_id': resource_id.id, 
          'payment_scheme': comision_id.id if d.get('tipo_contrato') == 'C' or d.get('tipo_contrato') == '' else sueldo_id.id,
          'job_id': job_id.id,
          # 'department_id': sales_dept_id.id,
          'warehouse_id': warehouse_id.id if warehouse_id else wh_id
        }
        sale_employee_id = employee_obj.create(employee_vals)
      # Se busca el producto según la serie
      default_code = False
      for s in series_producto:       
        if s.get('serie') == d.get('serie'):
          default_code = s.get('product')
          break
      if not default_code:
        raise ValidationError('No se encuentra un producto para la serie: ' + str(d.get('serie')))
      product_id = product_obj.search([('default_code','=',default_code), ('company_id','=', company_id)], limit=1)
      if not product_id:
        raise ValidationError('No se encuentra el producto : ' + str(default_code))
      # Se busca la linea de tarifa para encontrar la inversión de papelería
      price_list_item_id = self.env['product.pricelist.item'].search([('product_id','=',product_id.id), ('company_id','=', company_id)], limit=1)
      if not price_list_item_id:
        raise ValidationError('No se encuentra la tarifa para el producto  : ' + str(product_id.name))
      stationery = price_list_item_id.stationery
      
      # Se valida que no exista ya el contrato
      # contract_id = contract_id = contract_obj.search([('x_id_contrato_pabs','=',d.get('id_contrato')),('company_id','=', company_id)])
      # if contract_id:
      #   _logger.info("Ya existe el el contrato %s"%(d.get('contrato')))
      #   continue

      # Se crea solicitud
      val = {
        'name': d.get('contrato'),
        'product_id': product_id.id,
        'warehouse_id': warehouse_id.id if warehouse_id else wh_id,
        'employee_id': sale_employee_id.id,
        'company_id': company_id
      }
      try:      
        lot_id = lot_obj.create(val)
      except:
        _logger.info("Error al crear la solicitud, es posible que el lote ya exista - " + str(val))
        raise ValidationError("Error al crear la solicitud, es posible que el lote ya exista - {}".format(str(val)))

      # Se busca el municipio
      municipality_id = locality_obj.search([('name','=',str(d.get('municipio')).strip().upper()), ('company_id','=', company_id)])  
      if not municipality_id:
        if company_id == COMPANY_SAL:
          municipality_id = locality_obj.search([('name','=','SALTILLO'), ('company_id','=', company_id)])
        elif company_id == COMPANY_MON:
          municipality_id = locality_obj.search([('name','=','MONCLOVA'), ('company_id','=', company_id)])

      # Buscar municipio de cobro
      toll_municipality_id = locality_obj.search([('name','=', str(d.get('municipio_cobro')).strip().upper()), ('company_id','=', company_id)])  
      if not municipality_id:
        if company_id == COMPANY_SAL:
          municipality_id = locality_obj.search([('name','=','SALTILLO'), ('company_id','=', company_id)])
        elif company_id == COMPANY_MON:
          municipality_id = locality_obj.search([('name','=','MONCLOVA'), ('company_id','=', company_id)])

      # Se busca la colonia
      neighborhood_id = self.env['colonias'].search([('name','=',str(d.get('colonia')).strip().upper()), ('company_id','=', company_id)],limit=1) 
      # Se busca la colonia de cobro
      toll_neighborhood_id = self.env['colonias'].search([('name','=',str(d.get('colonia_cobro')).strip().upper()), ('company_id','=', company_id)],limit=1)

      # # Se crea el cobrador si no existe
      # debt_collector_id = employee_obj.search([('barcode','=',d.get('cod_cobrador')), ('company_id','=', company_id)])       
      # if not debt_collector_id:        
      #   resource_id = resource_obj.create({'name': d.get('cobrador')})
      #   vals_collector = {
      #     'first_name': d.get('cobrador'),
      #     'last_name': '',
      #     'date_of_admission':fields.Date.today(), 
      #     'barcode': d.get('cod_cobrador'), 
      #     'resource_id': resource_id.id,
      #     'payment_scheme': comision_id.id if d.get('tipo_contrato') == 'C' else sueldo_id.id,
      #     'job_id': collector_job_id.id,
      #     'company_id': company_id
      #     # 'department_id': collector_dept_id.id,
      #   }
      #   debt_collector_id = employee_obj.create(vals_collector)     
        # errors.append({'contrato': d.get('contrato'),'Motivo': 'No se encontró el cobrador: %s'%(d.get('cod_cobrador'))})
        # continue     
      # # Se busca el estatus
      # status_id = status_obj.search([('estatus','=',d.get('esattus').upper())], limit=1)
      # # Se busca el motivo
      # reason_id = motivos_status_obj.search([('reason','=',d.get('motivo').upper())], limit=1)
      
      # Se valida que no exista ya el contrato
      # contract_id = contract_id = contract_obj.search([('x_id_contrato_pabs','=',d.get('id_contrato')),('company_id','=', company_id)])
      
      # Se agregan los valores del contrato a la lista para crear
      val = {
        'lot_id': lot_id.id or False,
        'name': d.get('contrato'),
        'partner_name': d.get('partner_name'),
        'partner_fname': d.get('partner_fname') if len(d.get('partner_fname')) > 0 else ' ',
        'partner_mname': d.get('partner_mname') if len(d.get('partner_mname')) > 0 else ' ',
        'street_name': d.get('calle'),
        'street_name_toll': d.get('calle_cobro'),
        'street_number': d.get('no_ext') + ' ' + d.get('no_int'),
        'street_number_toll': d.get('no_ext_cobro') + ' ' + d.get('no_int_cobro'),
        'between_streets': d.get('entre_calles'),
        'between_streets_toll': d.get('entre_calles'),
        'municipality_id': municipality_id.id or False,
        'toll_municipallity_id': toll_municipality_id.id or False,
        'neighborhood_id': neighborhood_id.id or False,
        'toll_colony_id': toll_neighborhood_id.id or False,
        'phone': d.get('telefono') or '',
        'phone_toll': d.get('telefono') or False,
        'birthdate': d.get('fecha_nacimiento') if d.get('fecha_nacimiento') != '0000-00-00' else '1970-01-01',
        'zip_code': d.get('cp') or '00000',
        'zip_code_toll': d.get('cp') or '00000',
        'vat': d.get('rfc'),        
        'initial_investment': d.get('inversion_inicial'),
        'payment_amount': d.get('monto_pago'),
        # 'debt_collector': debt_collector_id.id,
        'sale_employee_id': sale_employee_id.id,
        'way_to_payment': way_to_payment[int(d.get('forma_pago'))-1].get(d.get('forma_pago')),
        'payment_scheme_id': comision_id.id if d.get('tipo_contrato') == 'C' else sueldo_id.id,
        'contract_status_item': active_status_id.id,
        'contract_status_reason': active_reason_id.id,
        'date_of_last_status': d.get('fecha_estatus'),
        'date_first_payment': d.get('fecha_primer_abono'),
        'invoice_date': d.get('fecha_contrato'),
        'stationery': stationery,
        'company_id': company_id
        # 'x_costo_pabs': d.get('costo'),
        # 'x_id_contrato_pabs': d.get('id_contrato'),  
        # 'x_status_pabs': d.get('no_estatus'),     
        # 'x_saldo_pabs': d.get('saldo'),     
      }
      
      id = contract_obj.create(val)
      if id:
        _logger.info('Contrato creado')
      else:
        _logger.info('XXX ERROR XXX')

###################################################################################################################
  ### ASIGNAR CUENTAS A CONTACTOS ###
  def AsignarCuentasAContactos(self, company_id, limite):
    _logger.info("Comienza asignación de cuentas a contactos: Compañia: {}. Limite: {}".format(company_id, limite))

    #--- Consultar cuentas ---#
    account_obj = self.env['account.account']
    cuenta_a_cobrar = account_obj.search([('company_id', '=', company_id), ('code', '=', '110.01.001')])
    cuenta_a_pagar = account_obj.search([('company_id', '=', company_id), ('code', '=', '201.01.001')])

    if not cuenta_a_cobrar or not cuenta_a_pagar:
      raise ValidationError("No se encontraron las cuentas a cobrar (110.01.001) y a pagar (201.01.001) en el plan contable")

    #--- Consultar contactos sin cuenta ---#
    partner_obj = self.env['res.partner']

    ids_contactos = partner_obj.search([
      ('company_id', '=', company_id), '|' 
      ('property_account_receivable_id.id', '!=', cuenta_a_cobrar.id),
      ('property_account_payable_id.id', '!=', cuenta_a_pagar.id)
    ])

    if not ids_contactos:
      raise ValidationError("No hay contactos")

    #--- Actualizar cuentas ---#
    cantidad_contactos = len(ids_contactos)
    for index, cont in enumerate(ids_contactos, 1):
      _logger.info("{} de {}. {}".format(index, cantidad_contactos, cont.name))
      cont.write({
        'property_account_receivable_id': cuenta_a_cobrar.id,
        'property_account_payable_id': cuenta_a_pagar.id
      })

###################################################################################################################
  ### CREAR FACTURAS (Similar a create_invoice de pabs.contract)###
  def crear_facturas_contratos(self, company_id, limite):
    account_obj = self.env['account.move']
    account_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)
    contract_obj = self.env['pabs.contract']

    _logger.info("Comienza creación de facturas de contratos. Compañia: {},  Limite: {}".format(company_id, limite))

    ## Obtener contratos de ODOO sin factura ##
    consulta = """
      SELECT 
        con.id,
        con.name
      FROM pabs_contract AS con
      LEFT JOIN account_move AS mov ON mov.contract_id = con.id AND mov.type = 'out_invoice'
        WHERE mov.id IS NULL
        AND con.company_id = {}

        AND con.name LIKE '1CJ%' /*TEST*/

          ORDER BY con.name
      LIMIT {}
    """.format(company_id, limite)

    self.env.cr.execute(consulta)

    contratos_odoo = []
    numeros_contrato = []
    for res in self.env.cr.fetchall():
      con = "'{}'".format(res[1])
      
      contratos_odoo.append({
        'id_contrato': res[0],
        'contrato': con
      })

      numeros_contrato.append(con)

    if not contratos_odoo:
      _logger.info("No hay contratos")
      return

    ## Obtener costo de contratos de PABS ##
    consulta = """
      SELECT 
        CONCAT(serie, no_contrato) as contrato,
        costo 
      FROM contratos 
        WHERE CONCAT(serie, no_contrato) IN ({})
    """.format(",".join(numeros_contrato))

    contratos_pabs = self._get_data(company_id, consulta)

    journal_id = self.env['account.journal'].search([('name','=','VENTAS'),('company_id','=', company_id)])
    currency_id = account_obj.with_context(default_type='out_invoice')._get_default_currency()     

    if not journal_id:
      raise ValidationError("No se encontró el diario de ventas")
    
    cantidad_contratos = len(contratos_odoo)
    for index, con in enumerate(contratos_odoo, 1):
      previous = contract_obj.browse(con['id_contrato'])
      
      if not previous:
        _logger.info("No existe el contrato con id: {}".format(con['id_contrato']))
        continue

      _logger.info("{} de {}. {}".format(index, cantidad_contratos, previous.name))

      ## Buscar costo en lista de contratos de PABS. Al encontrarlo quitarlo de la lista ##
      costo = 0 
      for index, pabs in enumerate(contratos_pabs):
        if pabs['contrato'] == previous.name:
          costo = float(pabs['costo'])
          contratos_pabs.pop(index)
          break

      if not costo:
        raise ValidationError("No se encontró el costo para el contrato {}".format(previous.name))

      data = {
        'date' : previous.invoice_date,
        'commercial_partner_id' : previous.partner_id.id,
        'partner_id' : previous.partner_id.id,
        'ref' : previous.full_name,
        'type' : 'out_invoice',
        'journal_id' : journal_id.id,
        'state' : 'draft',
        'currency_id' : currency_id.id,
        'invoice_date' : previous.invoice_date,
        'auto_post' : False,
        'contract_id' : previous.id,
        'invoice_user_id' : self.env.user.id,
        'company_id': company_id
      }

      invoice_id = account_obj.create(data)

      if not invoice_id:
        raise ValidationError("No se pudo crear la factura del contrato {}".format(previous.name))
      
      if invoice_id:
        product_id = previous.name_service
        account_id = product_id.property_account_income_id or product_id.categ_id.property_account_income_categ_id

        # factor_iva = 0
        # # FISCAL
        # if previous.company_id.apply_taxes:
        #   #Buscar impuesto a agregar
        #   iva_tax = self.env['account.tax'].search([('name','=','IVA'), ('company_id','=', previous.company_id.id)])
          
        #   if not iva_tax:
        #     raise ValidationError("No se encontró el impuesto con nombre IVA")

        #   #Buscar linea de repartición de impuesto para facturas
        #   iva_repartition_line = iva_tax.invoice_repartition_line_ids.filtered_domain([
        #     ('repartition_type','=','tax'), 
        #     ('invoice_tax_id','=', iva_tax.id), 
        #     ('company_id','=', previous.company_id.id)
        #   ])

        #   if not iva_repartition_line:
        #     raise ValidationError("No se encontró la repartición de facturas del impuesto {}".format(iva_tax.name))
        #   if len(iva_repartition_line) > 1:
        #     raise ValidationError("Se definió mas de una linea (sin incluir la linea base) en la repartición de facturas del impuesto {}".format(iva_tax.name))

        #   factor_iva = 1 + (iva_tax.amount/100)

        line_data = {
          'move_id' : invoice_id.id,
          'account_id' : account_id.id,
          'quantity' : 1,
          'price_unit' : costo,
          'credit' : costo,
          'product_uom_id' : product_id.uom_id.id,
          'partner_id' : previous.partner_id.id,
          'amount_currency' : 0,
          'product_id' : product_id.id,
          'is_rounding_line' : False,
          'exclude_from_invoice_tab' : False,
          'name' : product_id.description_sale or product_id.name,
          'company_id': company_id
        }

        # FISCAL
        # if previous.company_id.apply_taxes:
        #   line_data.update({
        #     'credit' : round(costo / factor_iva, 2),
        #     'tax_exigible' : True,
        #     'tax_ids' : [(4, iva_tax.id, 0)]
        #   })
        account_line_obj.create(line_data)

        # if previous.company_id.apply_taxes:
        #   #Llenar datos para línea de IVA
        #   iva_data = {
        #     'move_id' : invoice_id.id,
        #     'account_id' : iva_repartition_line.account_id.id,
        #     'quantity' : 1,
        #     'credit' : round(costo - round( costo / factor_iva, 2), 2),
        #     'tax_base_amount' : round(costo - round( costo / factor_iva, 2), 2),
        #     'partner_id' : previous.partner_id.id,
        #     'amount_currency' : 0,
        #     'is_rounding_line' : False,
        #     'exclude_from_invoice_tab' : True,
        #     'tax_exigible' : False,
        #     'name' : iva_tax.name,
        #     'tax_line_id' : iva_tax.id,
        #     'tax_group_id' : iva_tax.tax_group_id.id,
        #     'tax_repartition_line_id' : iva_repartition_line.id,
        #   }

        #   account_line_obj.create(iva_data)

        partner_line_data = {
          'move_id' : invoice_id.id,
          'account_id' : invoice_id.partner_id.property_account_receivable_id.id,
          'quantity' : 1,
          'date_maturity' : fields.Date.today(),
          'amount_currency' : 0,
          'partner_id' : previous.partner_id.id,
          'tax_exigible' : False,
          'is_rounding_line' : False,
          'exclude_from_invoice_tab' : True,
          #'price_unit' : (costo * -1),
          'debit' : costo,
          'company_id': company_id
        }
        account_line_obj.create(partner_line_data)
        invoice_id.action_post()

        _logger.info("Factura creada")

###################################################################################################################
  def CrearPagos(self, tipo_pago, company_id, desde, hasta, automatico, dias_hacia_atras, limite):
    _logger.info("Comienza consulta de pagos: {}. Compañia: {}".format(tipo_pago, company_id))

    if tipo_pago not in ('stationary', 'surplus', 'payment', 'transfer'):
      raise ValidationError("No se envio un tipo de pago")

    #--- Asignar fechas de pago a buscar ---#

    # a) Por fecha mas antigua de pago
    consulta = ""
    limite_fechas_pabs = ""
    if automatico:
      consulta = """
        SELECT 
          COALESCE(MIN(abo.payment_date), '2022-06-30') as fecha_minima /*PROD*/
        FROM account_payment AS abo
        INNER JOIN pabs_contract AS con ON abo.contract = con.id
          WHERE abo.reference = '{}'
          AND abo.state IN ('posted', 'sent', 'reconciled')
          AND con.company_id = '{}'
      """.format(tipo_pago, company_id)

      self.env.cr.execute(consulta)

      fecha_final = "1900-01-01"
      for res in self.env.cr.fetchall():
        fecha_final = res[0]

      fecha_inicial = fecha_final - timedelta(days = dias_hacia_atras)

      limite_fechas_pabs = " AND abo.fecha_Oficina BETWEEN '{}' AND '{}' ".format(fecha_inicial, fecha_final)

    # b) Entre fechas elegidas
    else:
      limite_fechas_pabs = " AND abo.fecha_Oficina BETWEEN '{}' AND '{}'".format(desde, hasta)

    #--- Consultar pagos de pabs basandose en las fechas del punto anterior ---#
    no_movimiento = 0
    series_notas = ""
    cobrador_notas = 0

    pagos = []

    if tipo_pago in ("stationary", "surplus"):

      if tipo_pago == "stationary":
        no_movimiento = 2
      else:
        no_movimiento = 11

      consulta = """
        SELECT
					CONCAT(con.serie, con.no_contrato) as contrato,
					no_abono as no_abono,
					abo.importe as importe,
					abo.fecha_oficina as fecha_oficina,
					abo.fecha_recibo as fecha_recibo,
					no_abono as recibo,
					"" as codigo_cobrador
				FROM abonos AS abo
				INNER JOIN contratos AS con ON abo.id_contrato = con.id_contrato
					WHERE abo.no_movimiento = {}
					{}
            ORDER BY fecha_oficina DESC, no_abono DESC
              LIMIT {}
      """.format(no_movimiento, limite_fechas_pabs, limite)

      respuesta = self._get_data(company_id, consulta)

      for res in respuesta:
        pagos.append({
          'fecha_oficina': res['fecha_oficina'],
          'contrato': res['contrato'],
          'importe': float(res['importe']),
          'no_abono': res['no_abono'],
          'recibo': res['recibo']
        })
    elif tipo_pago in ("payment", "transfer"):
      for res in respuesta:
        pagos.append({
          'fecha_oficina': res['fecha_oficina'],
          'fecha_recibo': res['fecha_recibo'],
          'contrato': res['contrato'],
          'importe': float(res['importe']),
          'no_abono': res['no_abono'],
          'recibo': res['recibo']
        })

    if not pagos:
      _logger.info("No hay pagos")
      return

    #raise ValidationError("{}".format(pagos))

    #--- Datos constantes ---#
    payment_obj = self.env['account.payment']
    account_move_line_obj = self.env['account.move.line']
    reconcile_obj = self.env['account.partial.reconcile']

    account_id = self.env['account.account'].search([('company_id', '=', company_id), ('code', '=', '110.01.001')])
    if not account_id:
      raise ValidationError("No se encontró la cuenta 110.01.001")

    cash_journal_id = self.env['account.journal'].search([('company_id', '=', company_id), ('type','=','cash'), ('name','=','EFECTIVO')],limit=1)
    if not cash_journal_id:
      raise ValidationError("No se encontró el diario EFECTIVO")

    payment_method_id = self.env['account.payment.method'].search([('payment_type','=','inbound'),('code','=','manual')],limit=1)
    if not payment_method_id:
      raise ValidationError("No se encontró el método de pagos")

    currency_id = self.env['account.move'].with_context(default_type='out_invoice')._get_default_currency()
    if not currency_id:
      raise ValidationError("No se encontró la moneda")  

    cantidad_pagos = len(pagos)
    for index, pago in enumerate(pagos, 1):
      _logger.info("{} de {}. {} {} {}".format(index, cantidad_pagos, pago['contrato'], pago['recibo'], pago['fecha_oficina']))

      #--- Validar que no exista el pago ---#
      existe_pago = self.env['account.payment'].search([
        ('company_id', '=', company_id),
        ('ecobro_receipt', '=', pago['recibo'])
      ])

      if existe_pago:
        _logger.info("El pago ya existe")
        continue

      #--- Buscar contrato en ODOO ---#
      con_obj = self.env['pabs.contract'].search([
        ('company_id', '=', company_id),
        ('name', '=', pago['contrato'])
      ])

      if not con_obj:
        _logger.info("No se encontró el contrato")
        continue
      
      #--- Construir datos para creación de pago ---#
      payment_data = {}

      if tipo_pago == "stationary":
        payment_data = {
          'payment_reference' : 'Inversión inicial',
          'reference' : 'stationary',
          'way_to_pay' : 'cash',
          'payment_type' : 'inbound',
          'partner_type' : 'customer',
          'contract' : con_obj.id,
          'partner_id' : con_obj.partner_id.id,
          'amount' : pago['importe'],
          'currency_id' : currency_id.id,
          'payment_date' : pago['fecha_oficina'],
          'journal_id' : cash_journal_id.id,
          'payment_method_id' : payment_method_id.id,
          'ecobro_receipt': pago['recibo']
        }
      elif tipo_pago == "surplus":
        payment_data = {
          'payment_reference' : 'Excedente Inversión Inicial',
          'reference' : 'surplus',
          'way_to_pay' : 'cash',
          'payment_type' : 'inbound',
          'partner_type' : 'customer',
          'contract' : con_obj.id,
          'partner_id' : con_obj.partner_id.id,
          'amount' : pago['importe'],
          'currency_id' : currency_id.id,
          'payment_date' : pago['fecha_oficina'],
          'journal_id' : cash_journal_id.id,
          'payment_method_id' : payment_method_id.id,
          'ecobro_receipt': pago['recibo']
        }
      elif tipo_pago == "payment":
        payment_data = {
          'payment_reference' : 'Migracion PABS',
          'reference' : 'payment',
          'way_to_pay' : 'cash',
          'payment_type' : 'inbound',
          'partner_type' : 'customer',
          'debt_collector_code' : pago['id_cobrador'],
          'contract' : pago['id_contrato'],
          'partner_id' : pago['partner_id'],
          'amount' : pago['importe'],
          'currency_id' : currency_id.id,
          'date_receipt' : pago['fecha_recibo'],
          'payment_date' : pago['fecha_oficina'],
          'ecobro_receipt' : pago['recibo'],
          'journal_id' : cash_journal_id.id,
          'payment_method_id' : payment_method_id.id
        }
      elif tipo_pago == "transfer":
        payment_data = {
          'payment_reference' : 'Traspaso PABS',
          'reference' : 'transfer',
          'way_to_pay' : 'cash',
          'payment_type' : 'inbound',
          'partner_type' : 'customer',
          'debt_collector_code' : pago['id_cobrador'],
          'contract' : pago['id_contrato'],
          'partner_id' : pago['partner_id'],
          'amount' : pago['importe'],
          'currency_id' : currency_id.id,
          'date_receipt' : pago['fecha_recibo'],
          'payment_date' : pago['fecha_oficina'],
          'ecobro_receipt' : pago['recibo'],
          'journal_id' : cash_journal_id.id,
          'payment_method_id' : payment_method_id.id
        }

      payment = payment_obj.create(payment_data)
      _logger.info("Pago creado")

      payment.with_context(migration=True).post()
      _logger.info("Pago publicado")

      #--- Conciliar pago con su factura---#
      reconcile = {}  

      # Obtenemos linea de débito
      inv_credit_line = False
      for refund in con_obj.refund_ids:
        if refund.type == 'out_invoice':
          for line in refund.line_ids:
            if line.debit > 0:
              inv_credit_line = line 
              reconcile.update({'debit_move_id' : inv_credit_line.id})

      # Obtenemos linea de crédito
      if payment.move_line_ids:            
          for obj in payment.move_line_ids:
            if obj.credit > 0:
              reconcile.update({'initial_payment' : obj.id})

      # Construir objeto de conciliacion
      line = account_move_line_obj.browse(reconcile.get('initial_payment'))
      data = {
        'debit_move_id' : reconcile.get('debit_move_id'),
        'credit_move_id' : reconcile.get('initial_payment'),
        'amount' : abs(line.balance),
      }

      conciliacion = reconcile_obj.create(data)    

      if conciliacion:
        _logger.info("Pago conciliado")
      else:
        _logger.info("ERROR: Pago no conciliado")

###################################################################################################################

  def CrearNotas(self, tipo_nota, company_id, publicar):
    if tipo_nota not in ('bonos', 'notas'):
      raise ValidationError("No se envio un tipo de pago")

    _logger.info("Comienza consulta de notas: {}".format(tipo_nota))

    ### Consulta a ECO ODOO
    plaza = ""
    if company_id == 18:
      plaza = "SALTILLO"
    elif company_id == 19:
      plaza = "MONCLOVA"

    url = "http://nomina.dyndns.biz:8098/index.php"

    querystring = {"pwd":"4dm1n","plaza": plaza}

    payload = "consulta=EXEC%20%5Bdig%5D.%5BNotasPorCrear%5D%20%40tipo_nota_odoo%20%3D%20'zztipozz'"
    payload = payload.replace("zztipozz", tipo_nota)

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
    respuesta = json.loads(response.text)

    notas = []
    for res in respuesta:
      notas.append({
        'fecha_oficina': res['fecha_oficina'],
        'contrato': res['contrato'],
        'importe': float(res['importe']),
        'no_abono': res['no_abono'],
        'id_contrato': res['id_contrato'],
        'partner_id': res['partner_id'],
        'recibo': res['recibo'],
        'id_factura': res['id_factura'],
        'id_linea_debito': res['id_linea_debito']
      })

    if len(notas) == 0:
      _logger.info("No hay notas")
      return

    # DATOS CONSTANTES
    
    account_obj = self.env['account.move']
    account_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)
    journal_obj = self.env['account.journal']
    #reconcile_obj = self.env['account.partial.reconcile']
    
    journal_id = journal_obj.search([('company_id', '=', company_id),('type','=','sale'), ('name','=','VENTAS')],limit=1)
    if not journal_id:
      raise ValidationError("No se encontró el diario VENTAS")       

    product_id = self.env['product.template'].search([('company_id', '=', company_id),('name','=','BONO POR INVERSION INICIAL')])
    if not product_id:
      raise ValidationError("No se encontró el producto BONO POR INVERSION INICIAL")
    nombre_producto = product_id.description_sale or product_id.name

    product_product = self.env['product.product'].search([('product_tmpl_id', '=', product_id.id)])
    if not product_product:
      raise ValidationError("Problema el producto BONO POR INVERSION INICIAL: No se encontró la relación product_template({}) en la tabla product_product".format(product_id.id))    

    prod_id = product_product.id

    account_id = product_id.property_account_income_id or product_id.categ_id.property_account_income_categ_id
    if not account_id:
      raise ValidationError("No se encontró la cuenta en los campos product_id.property_account_income_id o product_id.categ_id.property_account_income_categ_id")

    cantidad_notas = len(notas)
    for index, nota in enumerate(notas, 1):

      _logger.info("{} de {}. {} - {}".format(index, cantidad_notas, nota['contrato'], nota['recibo']))

      existe_nota = self.env['account.move'].search([
        ('company_id', '=', company_id),
        ('move_type', '=', 'out_refund'),
        ('x_no_abono_pabs', '=', nota['no_abono'])
      ])

      if existe_nota:
        _logger.info("La nota ya existe")
        continue

      # Encabezado
      refund_data = {
        'date' : nota['fecha_oficina'],
        'commercial_partner_id' : nota['partner_id'],
        'partner_id' : nota['partner_id'],
        'ref' : nota['recibo'],
        'move_type' : 'out_refund',
        'journal_id' : journal_id.id,
        'state' : 'draft',
        # 'currency_id' : currency_id.id,
        'invoice_date' : nota['fecha_oficina'],
        'auto_post' : False,
        'contract_id' : nota['id_contrato'],
        'invoice_user_id' : self.env.user.id,
        'reversed_entry_id' : nota['id_factura'],
        'x_no_abono_pabs': nota['no_abono'],
        'company_id': company_id
      }        
      
      refund_id = account_obj.create(refund_data)
      _logger.info("Encabezado")
      
      # Llenar datos de Linea principal de débito
      debit_line_vals = {
        'move_id' : refund_id.id,
        'account_id' : account_id.id,
        'quantity' : 1,
        'price_unit' : nota['importe'],
        'debit' : nota['importe'],
        'product_uom_id' : product_id.uom_id.id,
        'partner_id' : nota['partner_id'],
        'amount_currency' : 0,
        'product_id' : prod_id,
        'is_rounding_line' : False,
        'exclude_from_invoice_tab' : False,
        'name' : nombre_producto,
        'company_id': company_id
      }

      debit_line = account_line_obj.create(debit_line_vals)
      _logger.info("Linea debito")

      # Llenar datos de Linea principal de débito
      credit_line_vals = {
        'move_id' : refund_id.id,
        'account_id' : refund_id.partner_id.property_account_receivable_id.id,
        'quantity' : 1,
        'date_maturity' : nota['fecha_oficina'],
        'amount_currency' : 0,
        'partner_id' : nota['partner_id'],
        'tax_exigible' : False,
        'is_rounding_line' : False,
        'exclude_from_invoice_tab' : True,
        'credit' : nota['importe'],
        'company_id': company_id
      }
      
      credit_line = account_line_obj.create(credit_line_vals)
      _logger.info("Linea credito")

      if publicar:
        refund_id.with_context(migration=True).action_post()
        _logger.info("Nota creada")

      # Conciliar    
      # dats = {
      #   'debit_move_id' : nota['id_linea_debito'],
      #   'credit_move_id' : credit_line.id,
      #   'debit_amount_currency': abs(credit_line.balance),
      #   'credit_amount_currency': abs(credit_line.balance),
      #   'amount' : abs(line.balance),
      # }

      # reconcile_id = reconcile_obj.create(dats)
      # if reconcile_id:
      #   _logger.info("Conciliada")
      # else:
      #   _logger.info("X X X X X     NO CONCILADA     X X X X X")

###################################################################################################################

  def CrearEmpleadosVentas(self, company_id):
    resource_obj = self.env['resource.resource']
    employee_obj = self.env['hr.employee']

    _logger.info("Comienza consulta de empleados")

    ### Consulta a ECO ODOO
    plaza = ""
    if company_id == 18:
      plaza = "SALTILLO"
    elif company_id == 19:
      plaza = "MONCLOVA"

    url = "http://nomina.dyndns.biz:8098/index.php"

    querystring = {"pwd":"4dm1n","plaza": plaza}

    payload = "consulta=EXEC%20%5Bdig%5D.%5BEmpleadosPorCrear%5D%20%40default%20%3D%200"

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
    respuesta = json.loads(response.text)

    empleados = []
    for res in respuesta:
      empleados.append({
        'nombre': res['nombre'],
        'apellidos': res['apellidos'],
        'fecha_ingreso': res['fecha_ingreso'],
        'codigo': res['codigo'],
        'id_esquema': res['id_esquema'],
        'id_cargo': res['id_cargo'],
        'id_oficina': res['id_oficina'],
        'oficina': res['oficina'],
        'id_estatus': res['id_estatus'],
        'existe_oficina': res['existe_oficina'],
        'existe_cargo': res['existe_cargo']
      })

    if not empleados:
      _logger.info("No hay empleados")
    
    ### DATOS CONSTANTES ###
    id_depto_ventas = self.env['hr.department'].search([
      ('company_id', '=', company_id),
      ('name', '=', 'VENTAS')
    ]).id

    if not id_depto_ventas:
      raise ValidationError("No se encontró el departamento de ventas")

    ### Crear empleados ###
    for emp in empleados:

      if emp['existe_oficina'] == 0:
        _logger.info("No existe oficina")
        continue
      
      if emp['existe_cargo'] == 0:
        _logger.info("No existe cargo")
        continue

      resource_id = resource_obj.create({'name': "{} {}".format(emp['nombre'], emp['apellidos'])})

      employee_vals = {
        'first_name': emp['nombre'],
        'last_name': emp['apellidos'],
        'date_of_admission': emp['fecha_ingreso'], 
        'barcode': emp['codigo'], 
        'resource_id': resource_id.id, 
        'payment_scheme': emp['id_esquema'],
        'job_id': emp['id_cargo'],
        'warehouse_id': emp['id_oficina'],
        #'department_id': id_depto_ventas, #PENDIENTE ASIGNAR DEPTO DE VENTAS AL FINAL
        'employee_status': emp['id_estatus'],
        'company_id' : company_id
      }
      
      sale_employee_id = employee_obj.create(employee_vals)

      if sale_employee_id:
        _logger.info("Empleado creado {}".format(emp['codigo']))
      else:
        _logger.info("XXXXXXXXXXXXXX NO CREADO XXXXXXXXXXXXXX")

###################################################################################################################

  def CrearSalidas(self, company_id, tipo):
    _logger.info("Comienza creacion de salidas: {}".format(tipo))
    
    if tipo not in ('pagos', 'notas'):
      raise ValidationError("No se envio el parámetro tipo: pagos o notas")

    ### Consulta a ECO ODOO
    plaza = ""
    if company_id == 18:
      plaza = "SALTILLO"
    elif company_id == 19:
      plaza = "MONCLOVA"

    url = "http://nomina.dyndns.biz:8098/index.php"

    querystring = {"pwd":"4dm1n","plaza": plaza}

    payload = "consulta=EXEC%20%5Bdig%5D.%5BSalidasPorCrear%5D%20%40tipo_pago_odoo%20%3D%20N'zztipozz'"
    payload = payload.replace("zztipozz", tipo)

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
    respuesta = json.loads(response.text)

    salidas = []
    for res in respuesta:
      salidas.append({
        'id_abo_nota': res['id_abo_nota'],
        'job_id': res['job_id'],
        'emp_id': res['emp_id'],
        'commission_paid': float(res['commission_paid']),
        'actual_commission_paid': float(res['actual_commission_paid']),
        'x_no_salida_pabs': res['x_no_salida_pabs'],
        'no_abono': res['no_abono']
      })

    if not salidas:
      _logger.info("No hay salidas de {}".format(tipo))

    tipo_salida = ""
    if tipo == "pagos":
      tipo_salida = "payment_id"
    else :
      tipo_salida = "refund_id"

    output_obj = self.env['pabs.comission.output']

    cantidad_salidas = len(salidas)
    for index, sal in enumerate(salidas, 1):
      _logger.info("{} de {}. no_pago_abono: {}".format(index, cantidad_salidas, sal['x_no_salida_pabs']))

      data = {
        tipo_salida: sal['id_abo_nota'],
        'job_id': sal['job_id'],
        'comission_agent_id': sal['emp_id'],
        'commission_paid': sal['commission_paid'],
        'actual_commission_paid': sal['actual_commission_paid'],
        'company_id': company_id,
        'x_no_salida_pabs': sal['x_no_salida_pabs']
      }

      output_obj.create(data)
      _logger.info("Salida de {} creada".format(tipo))

###################################################################################################################

  def CrearArboles(self, company_id):
    _logger.info("Comienza creacion de árboles")

    ### Consulta a ECO ODOO
    plaza = ""
    if company_id == 18:
      plaza = "SALTILLO"
    elif company_id == 19:
      plaza = "MONCLOVA"

    url = "http://nomina.dyndns.biz:8098/index.php"

    querystring = {"pwd":"4dm1n","plaza": plaza}

    payload = "consulta=EXEC%20%5Bdig%5D.%5BArbolesPorCrear%5D%20%40default%20%3D%200"

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
    respuesta = json.loads(response.text)

    arboles = []
    for res in respuesta:
      arboles.append({
        'contract_id': res['contract_id'],
        'pay_order': res['pay_order'],
        'job_id': res['job_id'],
        'comission_agent_id': res['comission_agent_id'],
        'corresponding_commission': float(res['corresponding_commission']),
        'remaining_commission': float(res['remaining_commission']),
        'commission_paid': float(res['commission_paid']),
        'actual_commission_paid': float(res['actual_commission_paid']),
        'contrato': res['contrato'],
        'cargo': res['cargo']
      })

    if not arboles:
      _logger.info("No hay árboles")

    tree_obj = self.env['pabs.comission.tree']

    cantidad_registros = len(arboles)
    for index, arb in enumerate(arboles, 1):
      _logger.info("{} de {}. {} -> {}".format(index, cantidad_registros, arb['contrato'], arb['cargo']))

      data = {
        'contract_id': arb['contract_id'],
        'pay_order': arb['pay_order'],
        'job_id': arb['job_id'],
        'comission_agent_id': arb['comission_agent_id'],
        'corresponding_commission': arb['corresponding_commission'],
        'remaining_commission': arb['remaining_commission'],
        'commission_paid': arb['commission_paid'],
        'actual_commission_paid': arb['actual_commission_paid'],
        'company_id': company_id
      }

      tree_obj.create(data)
      _logger.info("Registro de arbol creado")

###################################################################################################################
  def CancelarPagos(self, ids):

    if not ids:
      raise ValidationError("No se enviaron id de pagos")

    _logger.info("Comienza cancelacion de pagos")

    id_pagos = self.env['account.payment'].browse(ids)

    if not id_pagos:
      raise ValidationError("No hay pagos")

    cantidad_pagos = len(id_pagos)
    for index, pago in enumerate(id_pagos, 1):
      _logger.info("{} de {}. {} - {}".format(index, cantidad_pagos, pago.id, pago.ecobro_receipt))
      pago.action_draft()

      pago.write({
        'contract': False,
        'debt_collector_code': False,
        'x_no_abono_pabs': False,
        'partner_id': False
      })
      _logger.info("Pago actualizado")

      pago.action_cancel()
      _logger.info("Pago cancelado")

###################################################################################################################
  ### CREAR MUNICIPIOS ###
  def get_res_locality(self, company_id):
    qry = """
      SELECT 
        UPPER(loc.localidad) as localidad,
        UPPER(col.colonia) as colonia,
        loc.no_loc,
        col.no_colonia
      FROM colonias AS col
      INNER JOIN 
      (
        /*Traer solo ubicaciones que tengan un cliente*/
        SELECT 
          cli.no_colonia as 'no_colonia'
        FROM clientes AS cli
          GROUP BY cli.no_colonia
        UNION
        SELECT 
          cli.no_col_cobro as 'no_colonia'
        FROM clientes AS cli
          GROUP BY cli.no_col_cobro
      ) AS x ON col.no_colonia = x.no_colonia
      INNER JOIN localidad AS loc ON col.no_loc = loc.no_loc
          ORDER BY localidad, colonia
    """
    data = self._get_data(company_id, qry)
    self.response_pabs = data
    
    locality_obj = self.env['res.locality']
    #
    localities = []
    for d in data:
      if str(d.get('localidad')).strip() not in localities:
        localities.append(str(d.get('localidad')).strip().upper())
    #
    country_id = 0
    state_id = 0

    if company_id == 1:
      country_id = 156 # México
      state_id = 1384 # TOLUCA
    else:
      raise ValidationError("No se ha definido una compañia")

    vals = []
    for d in localities:            
      vals.append({'name':d, 'country_id': country_id, 'state_id': state_id, 'company_id': company_id})
    # Se crean los municipios
    locality_obj.create(vals)
    return True
  
  ###################################################################################################################
  ### CREAR COLONIAS ###
  def get_colonias(self, company_id):
    qry = """
      SELECT 
        UPPER(loc.localidad) as localidad,
        UPPER(col.colonia) as colonia,
        loc.no_loc,
        col.no_colonia
      FROM colonias AS col
      INNER JOIN 
      (
        /*Traer solo ubicaciones que tengan un cliente*/
        SELECT 
          cli.no_colonia as 'no_colonia'
        FROM clientes AS cli
          GROUP BY cli.no_colonia
        UNION
        SELECT 
          cli.no_col_cobro as 'no_colonia'
        FROM clientes AS cli
          GROUP BY cli.no_col_cobro
      ) AS x ON col.no_colonia = x.no_colonia
      INNER JOIN localidad AS loc ON col.no_loc = loc.no_loc
          ORDER BY localidad, colonia
    """
    data = self._get_data(company_id, qry)
    self.response_pabs = data
    #
    locality_obj = self.env['res.locality']
    colonia_obj = self.env['colonias']
    # 
    colonias = []
    vals = []
    for d in data:    
      if str(d.get('colonia')).strip() not in colonias:
        colonias.append(str(d.get('colonia')).strip().upper())
        vals.append({'colonia': str(d.get('colonia')).strip().upper(), 'localidad': str(d.get('localidad')).strip().upper(), 'company_id': company_id})

    #   
    vals_ = []
    for d in vals:   
      # Se busca la localidad      
      locality_id = locality_obj.search([('name','=',d.get('localidad').strip().upper())])
      if locality_id:   
          vals_.append({'name': d.get('colonia').strip().upper(), 'municipality_id': locality_id.id})   
    colonia_obj.create(vals_)      
    return True

  ###################################################################################################################
  ### CREAR OFICINAS ###
  def get_oficinas(self, company_id):
    qry = """
      SELECT nombre_oficina FROM oficina;
    """
    data = self._get_data(company_id, qry)
    self.response_pabs = data
    stock_obj = self.env['stock.warehouse']
    #
    stock = []
    for d in data:
      if str(d.get('nombre_oficina')).strip() not in stock:
        stock.append(str(d.get('nombre_oficina')).strip())
    #
    vals = []
    i = 0
    for d in stock:            
      vals.append({'name': d, 'code': d[0:4] + str(i)})
      i += 1
    # Se crean los alamcenes
    stock_obj.create(vals)
    return True