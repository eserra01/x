# -*- encoding: utf-8 -*-
###########################################################################################
#
#   Author: PABS (pabsmr.org)
#   Coded by: Jaime Rodriguez (jaime.rodriguez@pabsmr.org)
#
###########################################################################################

from tkinter import BROWSE
from odoo import fields, models, _, api
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
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
  ### ASIGNAR CUENTAS A CONTACTOS QUE NO TIENEN ###
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
      ('company_id', '=', company_id), 
      ('name', 'not ilike', 'MON'),
      ('name', 'not ilike', 'SLW'),
      '|',
      ('property_account_receivable_id', '=', False),
      ('property_account_payable_id', '=', False)
    ], limit = limite)

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

      _logger.info("Cuentas asignadas")

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

      limite_fechas_pabs = " AND abo.fecha_oficina BETWEEN '{}' AND '{}' ".format(fecha_inicial, fecha_final)
      limite_fechas_odoo = " AND abo.payment_date BETWEEN '{}' AND '{}' ".format(fecha_inicial, fecha_final)

    # b) Entre fechas elegidas
    else:
      limite_fechas_pabs = " AND abo.fecha_Oficina BETWEEN '{}' AND '{}'".format(desde, hasta)
      limite_fechas_odoo = " AND abo.payment_date BETWEEN '{}' AND '{}'".format(desde, hasta)

    #--- Consultar pagos de pabs basandose en las fechas del punto anterior ---#
    no_movimiento = 0
    series_notas = ""
    cobrador_notas = 0

    if company_id == COMPANY_SAL:
      series_notas = ""
      cobrador_notas = 0
    elif company_id == COMPANY_MON:
      series_notas = "CNC"
      cobrador_notas = 50

    pagos = []
    recibos_odoo = []
    cobradores_odoo = []

    if tipo_pago in ("stationary", "surplus"):

      if tipo_pago == "stationary":
        no_movimiento = 2
      elif tipo_pago == "surplus":
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
					{} /*Limitar fechas pabs*/
            ORDER BY fecha_oficina DESC, no_abono DESC
      """.format(no_movimiento, limite_fechas_pabs)

      respuesta = self._get_data(company_id, consulta)

      for res in respuesta:
        pagos.append({
          'fecha_oficina': res['fecha_oficina'],
          'contrato': res['contrato'],
          'importe': float(res['importe']),
          'recibo': res['recibo'],
          'ya_existe': False
        })

      #--- Consultar pagos de odoo basandose en las fechas del punto anterior ---#
      consulta = """
        SELECT 
					abo.ecobro_receipt as recibo
				FROM account_payment AS abo
				INNER JOIN pabs_contract AS con ON abo.contract = con.id
					WHERE abo.reference = '{}'
          AND abo.state IN ('posted', 'sent', 'reconciled')
					AND con.company_id = {}
					{} /*Limitar fechas odoo*/
            ORDER BY abo.payment_date DESC, abo.ecobro_receipt DESC
      """.format(tipo_pago, company_id, limite_fechas_odoo)

      self.env.cr.execute(consulta)

      for res in self.env.cr.fetchall():
        recibos_odoo.append(res[0])

    elif tipo_pago in ("payment", "transfer"):
      no_movimiento = 1

      #--- Consultar pagos de pabs basandose en las fechas del punto anterior ---#
      consulta = """
        SELECT
					abo.fecha_oficina as fecha_oficina,
					abo.fecha_recibo as fecha_recibo,
					CONCAT(con.serie, con.no_contrato) as contrato,
					abo.importe as importe,
					CONCAT(rec.serie, rec.no_recibo) as recibo,
					per.no_empleado_ext as codigo_cobrador
				FROM abonos AS abo
				INNER JOIN contratos AS con ON abo.id_contrato = con.id_contrato
				INNER JOIN recibos AS rec ON abo.id_recibo = rec.id_recibo
				INNER JOIN personal AS per ON abo.no_cobrador = per.no_personal
					WHERE abo.no_movimiento = {}
					AND rec.serie NOT IN ('{}')
					AND abo.no_cobrador NOT IN ({})
					{} /*Limitar fechas pabs*/
            ORDER BY abo.fecha_oficina DESC, no_abono DESC
      """.format(no_movimiento, series_notas, cobrador_notas, limite_fechas_pabs)

      respuesta = self._get_data(company_id, consulta)

      for res in respuesta:
        pagos.append({
          'fecha_oficina': res['fecha_oficina'],
          'fecha_recibo': res['fecha_recibo'],
          'contrato': res['contrato'],
          'importe': float(res['importe']),
          'recibo': res['recibo'],
          'codigo_cobrador': res['codigo_cobrador'],
          'ya_existe': False
        })

      #--- Consultar pagos de odoo basandose en las fechas del punto anterior ---#
      consulta = """
        SELECT 
					abo.ecobro_receipt as recibo
				FROM account_payment AS abo
				INNER JOIN pabs_contract AS con ON abo.contract = con.id
					WHERE abo.reference = '{}'
          AND abo.state IN ('posted', 'sent', 'reconciled')
					AND con.company_id = {}
					{} /*Limitar fechas odoo*/
            ORDER BY abo.payment_date DESC, abo.ecobro_receipt DESC
      """.format(tipo_pago, company_id, limite_fechas_odoo)

      self.env.cr.execute(consulta)

      for res in self.env.cr.fetchall():
        recibos_odoo.append(res[0])

      #--- Consultar cobradores de odoo ---#
      consulta = """
        SELECT 
					emp.barcode as codigo, 
          emp.id as id_cobrador
				FROM hr_employee AS emp
        INNER JOIN hr_job AS car ON emp.job_id = car.id
					WHERE car.name NOT LIKE '%ASIS%'
					AND emp.company_id = {}
      """.format(company_id)

      self.env.cr.execute(consulta)

      for res in self.env.cr.fetchall():
        cobradores_odoo.append({
          'codigo': res[0],
          'id': int(res[1])
        })

    #--- Marcar pagos que ya existen ---#
    for abo in pagos:
      if abo['recibo'] in recibos_odoo:
        abo['ya_existe'] = True

    #--- Dejar en la lista pagos que no existen ---#
    pagos = [elem for elem in pagos if elem['ya_existe'] == False]

    if not pagos:
      _logger.info("No hay pagos")
      return

    pagos = pagos[0 : limite]

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

      #--- Segunda validación de que no existe el pago ---#
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

      #--- Asignar el cobrador de odoo a cada pago (solo para abonos)---#
      id_cobrador = 0
      if tipo_pago in ('payment', 'transfer'):
        for cob in cobradores_odoo:
          if cob['codigo'] == pago['codigo_cobrador']:
            id_cobrador = cob['id']
            break

        if id_cobrador == 0:
          raise ValidationError("No se encontró el cobrador {} para el recibo {}".format(pago['codigo_cobrador'], pago['recibo']))
      
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
          'ecobro_receipt': pago['recibo'],
          'journal_id' : cash_journal_id.id,
          'payment_method_id' : payment_method_id.id
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
          'ecobro_receipt': pago['recibo'],
          'journal_id' : cash_journal_id.id,
          'payment_method_id' : payment_method_id.id
        }
      elif tipo_pago == "payment":
        payment_data = {
          'payment_reference' : 'Migracion PABS',
          'reference' : 'payment',
          'way_to_pay' : 'cash',
          'payment_type' : 'inbound',
          'partner_type' : 'customer',
          'debt_collector_code' : id_cobrador,
          'contract' : con_obj.id,
          'partner_id' : con_obj.partner_id.id,
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
          'debt_collector_code' : id_cobrador,
          'contract' : con_obj.id,
          'partner_id' : con_obj.partner_id.id,
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

  def CrearNotas(self, tipo_nota, company_id, desde, hasta, automatico, dias_hacia_atras, limite):
    if tipo_nota not in ('bonos', 'notas'):
      raise ValidationError("No se envio un tipo de nota")

    _logger.info("Comienza consulta de notas: {}".format(tipo_nota))

    #--- Asignar fechas de nota a buscar ---#

    # a) Por fecha mas antigua de nota
    consulta = ""
    limite_fechas_pabs = ""
    if automatico and tipo_nota == 'bonos':
      consulta = """
        SELECT 
          COALESCE(MIN(invoice_date), '2021-12-01') as fecha_minima /*PROD*/
        FROM account_move
          WHERE type = 'out_refund'
          AND state IN ('posted', 'sent', 'reconciled')
          AND company_id = '{}'
      """.format(company_id)

      self.env.cr.execute(consulta)

      fecha_final = "1900-01-01"
      for res in self.env.cr.fetchall():
        fecha_final = res[0]

      fecha_inicial = fecha_final - timedelta(days = dias_hacia_atras)

      limite_fechas_pabs = " AND abo.fecha_oficina BETWEEN '{}' AND '{}' ".format(fecha_inicial, fecha_final)
      limite_fechas_odoo = " AND nota.invoice_date BETWEEN '{}' AND '{}' ".format(fecha_inicial, fecha_final)

    # b) Entre fechas elegidas
    elif tipo_nota == 'notas':
      limite_fechas_pabs = " AND abo.fecha_Oficina BETWEEN '1900-01-01' AND '2999-12-31'"
      limite_fechas_odoo = " AND nota.invoice_date BETWEEN '1900-01-01' AND '2999-12-31'"
    else:
      limite_fechas_pabs = " AND abo.fecha_Oficina BETWEEN '{}' AND '{}'".format(desde, hasta)
      limite_fechas_odoo = " AND nota.invoice_date BETWEEN '{}' AND '{}'".format(desde, hasta)

    #--- Consultar notas de pabs basandose en las fechas del punto anterior ---#

    no_movimiento = 0
    series_notas = ""
    cobrador_bonos = 0
    cobrador_notas = 0
    referencia = ""

    if company_id == COMPANY_SAL:
      series_notas = ""
      cobrador_notas = 0
    elif company_id == COMPANY_MON:
      cobrador_bonos = 9
      series_notas = "CNC"
      cobrador_notas = 50

    notas = []
    recibos_odoo = []

    if tipo_nota == 'bonos':
      no_movimiento = 3
      referencia = 'Bono por inversión inicial'

      consulta = """
        SELECT
					CONCAT(con.serie, con.no_contrato) as contrato,
					abo.importe as importe,
					abo.fecha_oficina as fecha_oficina,
					CONCAT(rec.serie, rec.no_recibo) as recibo
				FROM abonos AS abo
        INNER JOIN recibos AS rec ON abo.id_recibo = rec.id_recibo
				INNER JOIN contratos AS con ON abo.id_contrato = con.id_contrato
					WHERE con.tipo_bd != 20
          AND abo.importe > 0
          AND rec.serie NOT IN ('{}')
          AND (abo.no_cobrador IN ({}) OR (abo.no_movimiento = {} AND abo.no_cobrador NOT IN ({})) ) 
          {}
						ORDER BY fecha_oficina DESC, no_abono DESC
      """.format(series_notas, cobrador_bonos, no_movimiento, cobrador_notas, limite_fechas_pabs)

    elif tipo_nota == 'notas':
      referencia = 'Migracion de nota de crédito'

      consulta = """
        SELECT
					CONCAT(con.serie, con.no_contrato) as contrato,
					abo.importe as importe,
					abo.fecha_oficina as fecha_oficina,
					CONCAT(rec.serie, rec.no_recibo) as recibo
				FROM abonos AS abo
        INNER JOIN recibos AS rec ON abo.id_recibo = rec.id_recibo
				INNER JOIN contratos AS con ON abo.id_contrato = con.id_contrato
					WHERE con.tipo_bd != 20
          AND abo.importe > 0
          AND (rec.serie IN ('{}') OR abo.no_cobrador IN ('{}'))
						ORDER BY fecha_oficina DESC, no_abono DESC
      """.format(series_notas, cobrador_notas)

    respuesta = self._get_data(company_id, consulta)

    for res in respuesta:
      notas.append({
        'contrato': res['contrato'],
        'importe': float(res['importe']),
        'fecha_oficina': res['fecha_oficina'],
        'recibo': res['recibo'],
        'ya_existe': False
      })

    #--- Consultar notas de odoo basandose en las fechas del punto anterior ---#
    consulta = """
      SELECT 
        recibo as recibo
      FROM account_move AS nota
        WHERE type = 'out_refund'
        AND ref = '{}'
        AND company_id = {}
        {}
    """.format(referencia, company_id, limite_fechas_odoo)

    self.env.cr.execute(consulta)

    for res in self.env.cr.fetchall():
      recibos_odoo.append(res[0])

    #--- Marcar notas que ya existen ---#
    for nota in notas:
      if nota['recibo'] in recibos_odoo:
        nota['ya_existe'] = True

    #--- Dejar en la lista pagos que no existen ---#
    notas = [elem for elem in notas if elem['ya_existe'] == False]

    if len(notas) == 0:
      _logger.info("No hay notas")
      return

    notas = notas[0 : limite]

    #--- Datos constantes ---#
    account_obj = self.env['account.move']
    account_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)
    journal_obj = self.env['account.journal']
    reconcile_obj = self.env['account.partial.reconcile']
    
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

      _logger.info("{} de {}. {} {} {}".format(index, cantidad_notas, nota['contrato'], nota['recibo'], nota['fecha_oficina']))

      existe_nota = self.env['account.move'].search([
        ('company_id', '=', company_id),
        ('type', '=', 'out_refund'),
        ('recibo', '=', nota['recibo'])
      ])

      if existe_nota:
        _logger.info("La nota ya existe")
        continue

      #--- Buscar contrato en ODOO ---#
      con_obj = self.env['pabs.contract'].search([
        ('company_id', '=', company_id),
        ('name', '=', nota['contrato'])
      ])

      if not con_obj:
        _logger.info("No se encontró el contrato {}".format(nota['contrato']))
        continue

      #--- Buscar factura del contrato ---#
      factura = account_obj.search([
        ('company_id', '=', company_id),
        ('type', '=', 'out_invoice'),
        ('contract_id', '=', con_obj.id)
      ], limit = 1)

      if not factura:
        _logger.info("No se encontró la factura del contrato {}".format(nota['contrato']))
        continue

      #--- Crear nota de crédito---#

      # Encabezado
      refund_data = {
        'type' : 'out_refund',
        'ref' : referencia,
        'invoice_date' : nota['fecha_oficina'],
        'recibo': nota['recibo'],
        'contract_id' : con_obj.id,
        'commercial_partner_id' : con_obj.partner_id.id,
        'partner_id' : con_obj.partner_id.id,
        'journal_id' : journal_id.id,
        'state' : 'draft',
        # 'currency_id' : currency_id.id,
        'auto_post' : False,
        'invoice_user_id' : self.env.user.id,
        'reversed_entry_id' : factura.id,
        'company_id': company_id
      }        
      
      refund_id = account_obj.create(refund_data)
      _logger.info("Encabezado")
      
      # Linea principal de débito
      debit_line_vals = {
        'move_id' : refund_id.id,
        'account_id' : account_id.id,
        'quantity' : 1,
        'price_unit' : nota['importe'],
        'debit' : nota['importe'],
        'product_uom_id' : product_id.uom_id.id,
        'partner_id' : con_obj.partner_id.id,
        'amount_currency' : 0,
        'product_id' : prod_id,
        'is_rounding_line' : False,
        'exclude_from_invoice_tab' : False,
        'name' : nombre_producto,
        'company_id': company_id
      }

      debit_line = account_line_obj.create(debit_line_vals)
      _logger.info("Linea debito")

      # Linea principal de crédito
      credit_line_vals = {
        'move_id' : refund_id.id,
        'account_id' : refund_id.partner_id.property_account_receivable_id.id,
        'quantity' : 1,
        'date_maturity' : nota['fecha_oficina'],
        'amount_currency' : 0,
        'partner_id' : con_obj.partner_id.id,
        'tax_exigible' : False,
        'is_rounding_line' : False,
        'exclude_from_invoice_tab' : True,
        'credit' : nota['importe'],
        'company_id': company_id
      }
      
      credit_line = account_line_obj.create(credit_line_vals)
      _logger.info("Linea credito")

      refund_id.with_context(migration=True).action_post()
      _logger.info("Nota publicada")

      #--- Conciliar nota con su factura ---#  

      # Obtenemos linea de débito
      debit_line = 0
      inv_credit_line = False
      for line in factura.line_ids:
        if line.debit > 0:
          inv_credit_line = line 
          debit_line = inv_credit_line

      # Construir objeto de conciliacion
      data = {
        'debit_move_id' : debit_line.id,
        'credit_move_id' : credit_line.id,
        'amount' : abs(credit_line.balance),
      }

      conciliacion = reconcile_obj.create(data)    

      if conciliacion:
        _logger.info("Nota conciliada")
      else:
        _logger.info("ERROR: Nota no conciliada")

###################################################################################################################

  # Nota: Se toma el campo cargo_general de la tabla cargos de PABS. Estos puestos deben existir en odoo.
  def CrearSalidas(self, company_id, tipo, limite):
    _logger.info("Comienza creacion de salidas: {}".format(tipo))
    
    if tipo not in ('pagos', 'notas'):
      raise ValidationError("No se envio el parámetro tipo: pagos o notas")

    tipo_salida = ""

    #--- Consultar abonos de odoo sin salida ---#
    if tipo == 'pagos':
      tipo_salida = "payment_id"

      consulta = """
        SELECT 
					abo.id as id,
          abo.ecobro_receipt as recibo
				FROM account_payment as abo
        INNER JOIN pabs_contract as con on abo.contract = con.id
				LEFT JOIN pabs_comission_output as sal on abo.id = sal.payment_id
					WHERE abo.state IN ('posted', 'sent', 'reconciled')
					AND sal.id IS NULL
          AND abo.ecobro_receipt IS NOT NULL
					AND con.company_id = {}
						ORDER BY abo.payment_date DESC, abo.id DESC
              LIMIT {}
      """.format(company_id, limite)
    elif tipo == 'notas':
      tipo_salida = "refund_id"

      consulta = """
        SELECT 
					mov.id as id,
					mov.recibo as recibo
				FROM account_move AS mov
				LEFT JOIN pabs_comission_output AS sal ON mov.id = sal.refund_id
					WHERE mov.state = 'posted'
					AND mov.type = 'out_refund'
					AND sal.id IS NULL
          AND mov.recibo IS NOT NULL
					AND mov.company_id = '{}'
						ORDER BY mov.invoice_date DESC, mov.id DESC
              LIMIT {}
      """.format(company_id, limite)

    self.env.cr.execute(consulta)

    recibos_odoo = []
    solo_recibos = []
    for res in self.env.cr.fetchall():
      recibo = res[1]
      
      recibos_odoo.append({
        'id': res[0],
        'recibo': recibo
      })

      solo_recibos.append("'{}'".format(recibo))

    if not recibos_odoo:
      _logger.info("No hay recibos")
      return

    #--- Consultar salidas de pabs ---#
    consulta = """
      SELECT 
				pago.no_pago_abono as x_no_salida_pabs,
        CASE 
          WHEN abo.no_movimiento IN (2,11) THEN abo.no_abono
          ELSE CONCAT(rec.serie, rec.no_recibo) 
        END as recibo,
				per.no_empleado_ext as codigo,
				UPPER(car.cargo_general) as cargo,
				CASE
					WHEN pago.no_cargo = 2 THEN 0     /*COBRADOR comision_pagada = 0*/
					ELSE pago.comision 
				END as commission_paid,
				pago.comision - pago.com_cobrador as actual_commission_paid
			FROM pago_abonos AS pago
			INNER JOIN abonos AS abo ON pago.no_abono = abo.no_abono
      INNER JOIN recibos AS rec ON abo.id_recibo = rec.id_recibo
			INNER JOIN personal AS per ON pago.no_personal = per.no_personal
			INNER JOIN cargos AS car ON pago.no_cargo = car.no_cargo
				WHERE pago.comision > 0
				AND CONCAT(rec.serie, rec.no_recibo) IN ({})
    """.format(",".join(solo_recibos))

    respuesta = self._get_data(company_id, consulta)

    salidas = []
    for res in respuesta:
      salidas.append({
        'x_no_salida_pabs': int(res['x_no_salida_pabs']),
        'recibo': res['recibo'],
        'codigo': res['codigo'],
        'cargo': res['cargo'],
        'commission_paid': float(res['commission_paid']),
        'actual_commission_paid': float(res['actual_commission_paid'])
      })

    if not salidas:
      _logger.info("No hay salidas de {} en PABS".format(tipo))

    #--- Consultar cargos de odoo ---#
    cargos = []
    consulta = "SELECT id, name FROM hr_job WHERE company_id = {}".format(company_id)

    self.env.cr.execute(consulta)

    cargos = []
    for res in self.env.cr.fetchall():
      cargos.append({
        'id': res[0],
        'cargo': res[1]
      })

    #--- Consultar empleados de odoo ---#
    empleados = []
    consulta = """
      SELECT 
        emp.id as id,
        emp.barcode as codigo
      FROM hr_employee AS emp
      INNER JOIN hr_job AS job ON emp.job_id = job.id
        WHERE emp.company_id = {}
    """.format(company_id)

    self.env.cr.execute(consulta)

    empleados = []
    for res in self.env.cr.fetchall():
      empleados.append({
        'id': res[0],
        'codigo': res[1]
      })

    #--- Crear salidas ---#
    output_obj = self.env['pabs.comission.output']

    cantidad_salidas = len(salidas)
    for index, sal in enumerate(salidas, 1):
      _logger.info("{} de {}. {} -> {} {} ${}".format(index, cantidad_salidas, sal['recibo'], sal['cargo'], sal['codigo'], sal['actual_commission_paid']))

      # Validar que no exista salida
      ya_existe = output_obj.search([
        ('company_id', '=', company_id),
        ('x_no_salida_pabs', '=', sal['x_no_salida_pabs'])
      ])

      if ya_existe:
        _logger.info("Ya existe la salida {}".format(sal['x_no_salida_pabs']))
        continue

      # Buscar id de recibo de odoo
      id_recibo_odoo = 0
      for rec in recibos_odoo:
        if rec['recibo'] == sal['recibo']:
          id_recibo_odoo = rec['id']
          break

      if id_recibo_odoo == 0:
        _logger.info("No se encontró el recibo {} en odoo".format(sal['recibo']))
        continue

      # Buscar cargo
      id_cargo = 0
      for car in cargos:
        if car['cargo'] == sal['cargo']:
          id_cargo = car['id']
          break

      if id_cargo == 0:
        _logger.info("No existe el cargo {}".format(sal['cargo']))
        continue

      # Buscar empleado
      id_empleado = 0
      for emp in empleados:
        if emp['codigo'] == sal['codigo']:
          id_empleado = emp['id']
          break

      if id_empleado == 0:
        _logger.info("No existe el empleado {}".format(sal['cargo']))
        continue

      data = {
        tipo_salida: id_recibo_odoo,
        'job_id': id_cargo,
        'comission_agent_id': id_empleado,
        'commission_paid': sal['commission_paid'],
        'actual_commission_paid': sal['actual_commission_paid'],
        'x_no_salida_pabs': sal['x_no_salida_pabs'],
        'company_id': company_id
      }

      nuevo_id = output_obj.create(data)

      if nuevo_id:
        _logger.info("Salida de {} creada".format(tipo))
      else:
        _logger.info("ERROR: Salida no creada")

###################################################################################################################

  def CrearArboles(self, company_id, limite, contrato_individual = ""):
    _logger.info("Comienza creacion de árboles")

    #--- Consulta de contratos de ODOO sin árbol ---#

    # Por contratos sin árbol
    consulta = """
      SELECT 
        con.id, 
        con.name as contrato
      FROM pabs_contract AS con
      LEFT JOIN pabs_comission_tree AS arb ON con.id = arb.contract_id
        WHERE con.company_id = {}
        AND con.contract_status_item IS NOT NULL
          GROUP BY con.id, con.name	HAVING COUNT(arb.id) = 0
            ORDER BY con.invoice_date DESC, name DESC
              LIMIT {}
    """.format(company_id, limite)

    if contrato_individual != "":
      # Por contratos individual sin árbol
      consulta = """
        SELECT 
          con.id, 
          con.name as contrato
        FROM pabs_contract AS con
        LEFT JOIN pabs_comission_tree AS arb ON con.id = arb.contract_id
          WHERE con.company_id =  {}
          AND con.contract_status_item IS NOT NULL
          AND con.name = '{}'
            GROUP BY con.id, con.name	HAVING COUNT(arb.id) = 0
              ORDER BY con.invoice_date DESC, name DESC
      """.format(company_id, contrato_individual)

    self.env.cr.execute(consulta)

    contratos = []
    numeros_contrato = []
    for res in self.env.cr.fetchall():
      contrato = res[1]
      
      contratos.append({
        'id': res[0],
        'contrato': contrato
      })

      numeros_contrato.append("'{}'".format(contrato))

    if not contratos:
      _logger.info("No hay contratos de odoo sin arbol")
      return

    #--- Consulta ids de contratos de Pabs ---#
    consulta = "SELECT id_contrato FROM contratos WHERE CONCAT(serie, no_contrato) IN ({})".format(",".join(numeros_contrato))

    respuesta = self._get_data(company_id, consulta)

    ids_contratos_pabs = []
    for res in respuesta:
      ids_contratos_pabs.append(res['id_contrato'])

    #--- Consulta árboles de contratos de Pabs ---#

    consulta = """
      /* Registros de empleados de ventas */
      SELECT 
        con.id_contrato,
        con.fecha_contrato,
        CASE
          WHEN com.no_cargo = 4 THEN 1
          WHEN com.no_cargo = 5 THEN 2
          WHEN com.no_cargo = 6 THEN 3
          WHEN com.no_cargo = 10 THEN 4
          WHEN com.no_cargo = 12 THEN 5
          WHEN com.no_cargo = 14 THEN 6
          WHEN com.no_cargo = 15 THEN 7
          WHEN com.no_cargo = 16 THEN 8
          WHEN com.no_cargo = 18 THEN 9
        END as orden_de_pago,
        car.cargo_general AS cargo,
        CONCAT(con.serie, con.no_contrato) as contrato,
        CASE
          WHEN per.nombre = "Papeleria" THEN "PAPE"
          WHEN per.nombre = "Fideicomiso" THEN "FIDE"
          ELSE per.no_empleado_ext
        END as codigo_comisionista,
        com.comision AS comision_correspondiente,
        com.comision_resta AS comision_restante,
        (com.comision - com.comision_resta) as comision_pagada,
        IFNULL(
          (SELECT SUM(pago.comision - pago.com_cobrador) 
            FROM pago_abonos AS pago 
            INNER JOIN abonos AS abo ON pago.no_abono = abo.no_abono
              WHERE abo.id_contrato = con.id_contrato
              AND pago.no_personal = per.no_personal
              AND pago.no_cargo = car.no_cargo
        ),0) as comision_real_pagada
      FROM comxcontrato AS com
      INNER JOIN contratos AS con ON com.id_contrato = con.id_contrato
      INNER JOIN personal AS per ON com.no_personal = per.no_personal
      INNER JOIN cargos AS car ON com.no_cargo = car.no_cargo
      INNER JOIN servicios AS ser ON con.no_servicio = ser.no_servicio
        WHERE com.comision > 0
        AND con.id_contrato IN ({})
    UNION
    /* Registros de cobradores */
      SELECT 
				con.id_contrato,
				con.fecha_contrato,
				10 as orden_de_pago,
				"COBRADOR" as cargo,
				CONCAT(con.serie, con.no_contrato) as contrato,
				per.no_empleado_ext as codigo_comisionista,
				0 as comision_correspondiente,
				0 as comision_restante,
				0 as comision_pagada,
				SUM(pago.comision - pago.com_cobrador) as comision_real_pagada
			FROM pago_abonos AS pago
			INNER JOIN abonos AS abo ON pago.no_abono = abo.no_abono
			INNER JOIN personal AS per ON pago.no_personal = per.no_personal
			INNER JOIN contratos AS con ON abo.id_contrato = con.id_contrato
				WHERE pago.no_cargo = 2
				AND con.id_contrato IN ({})
					GROUP BY con.id_contrato, per.no_personal HAVING SUM(pago.comision - pago.com_cobrador) > 0
          						
      ORDER BY id_contrato DESC, orden_de_pago
    """.format(",".join(ids_contratos_pabs), ",".join(ids_contratos_pabs))

    respuesta = self._get_data(company_id, consulta)

    arboles = []
    orden_de_pago = 0

    for res in respuesta:  
      cargo = res['cargo']

      if cargo == 'COBRADOR':
        orden_de_pago = orden_de_pago + 1
      else:
        orden_de_pago = int(res['orden_de_pago'])

      arboles.append({
        'id_contrato': res['id_contrato'],
        'fecha_contrato': res['fecha_contrato'],
        'orden_de_pago': orden_de_pago,
        'cargo': cargo,
        'contrato': res['contrato'],
        'codigo_comisionista': res['codigo_comisionista'],
        'comision_correspondiente': float(res['comision_correspondiente']),
        'comision_restante': float(res['comision_restante']),
        'comision_pagada': float(res['comision_pagada']),
        'comision_real_pagada': float(res['comision_real_pagada'])
      })

    if not arboles:
      _logger.info("No hay árboles de PABS")
      return

    #--- Consultar cargos de odoo ---#
    cargos = []
    consulta = "SELECT id, name FROM hr_job WHERE company_id = {}".format(company_id)

    self.env.cr.execute(consulta)

    cargos = []
    for res in self.env.cr.fetchall():
      cargos.append({
        'id': res[0],
        'cargo': res[1]
      })

    #--- Consultar empleados de odoo ---#
    empleados = []
    consulta = """
      SELECT 
        emp.id as id,
        emp.barcode as codigo
      FROM hr_employee AS emp
      INNER JOIN hr_job AS job ON emp.job_id = job.id
        WHERE emp.company_id = {}
    """.format(company_id)

    self.env.cr.execute(consulta)

    empleados = []
    for res in self.env.cr.fetchall():
      empleados.append({
        'id': res[0],
        'codigo': res[1]
      })

    #--- Crear árboles de contratos ---#
    tree_obj = self.env['pabs.comission.tree']

    cantidad_registros = len(arboles)
    for index, arb in enumerate(arboles, 1):
      _logger.info("{} de {}: {}. {} -> {}".format(index, cantidad_registros, arb['contrato'], arb['orden_de_pago'], arb['cargo']))

      # Buscar id de contrato de odoo
      id_contrato_odoo = 0
      for con in contratos:
        if con['contrato'] == arb['contrato']:
          id_contrato_odoo = con['id']
          break

      if id_contrato_odoo == 0:
        _logger.info("No se encontró el contrato {} en odoo".format(arb['contrato']))
        continue

      # Buscar cargo
      id_cargo = 0
      for car in cargos:
        if car['cargo'] == arb['cargo']:
          id_cargo = car['id']
          break

      if id_cargo == 0:
        _logger.info("No existe el cargo {}".format(arb['cargo']))
        continue

      # Buscar empleado
      id_empleado = 0
      for emp in empleados:
        if emp['codigo'] == arb['codigo_comisionista']:
          id_empleado = emp['id']
          break

      if id_empleado == 0:
        _logger.info("No existe el empleado {}".format(arb['cargo']))
        continue

      data = {
        'contract_id': id_contrato_odoo,
        'pay_order': arb['orden_de_pago'],
        'job_id': id_cargo,
        'comission_agent_id': id_empleado,
        'corresponding_commission': arb['comision_correspondiente'],
        'remaining_commission': arb['comision_restante'],
        'commission_paid': arb['comision_pagada'],
        'actual_commission_paid': arb['comision_real_pagada'],
        'company_id': company_id
      }

      tree_obj.create(data)
      _logger.info("Registro de arbol creado")

###################################################################################################################

  def CrearEmpleados(self, company_id):
    resource_obj = self.env['resource.resource']
    employee_obj = self.env['hr.employee']

    _logger.info("Comienza consulta de empleados")

    #--- Consultar empleados de Odoo ---#
    consulta = """
      SELECT
        emp.barcode as codigo
      FROM hr_employee AS emp
      INNER JOIN hr_job AS job ON emp.job_id = job.id
        WHERE emp.company_id = {}
    """.format(company_id)

    self.env.cr.execute(consulta)
    
    empleados_odoo = []
    for res in self.env.cr.fetchall():
      empleados_odoo.append(res[0])

    #--- Consultar empleados de Pabs ---#
    consulta = """
      /* Empleados de ventas */
        SELECT 
          0 as no_personal,
          asi.no_nomina_asociado as codigo,
          asi.nombre as nombre,
          CONCAT(asi.apellido_pat, " ", asi.apellido_mat) as apellidos,
          asi.fecha_ingreso as fecha_ingreso,
          CASE 
            WHEN tipo_contrato = 'C' THEN 'COMISION'
            WHEN tipo_contrato = 'S' THEN 'SUELDO'
            ELSE tipo_contrato
          END as esquema,
          CASE
            WHEN UPPER(cargo_general) = "LIBRE" THEN "ASISTENTE SOCIAL"
            ELSE UPPER(cargo_general)
          END as cargo,
          ofi.nombre_oficina as oficina,
          CASE 
            WHEN estatus = "A" THEN "ACTIVO"
            WHEN estatus = "BP" THEN "BAJA PENDIENTE"
            WHEN estatus = "BC" THEN "BAJA COMPLETA"
            WHEN estatus = "P" THEN "PERMISO"
            ELSE "ACTIVO"
          END as estatus
        FROM asociados AS asi
        INNER JOIN cargos AS car ON asi.no_categoria = car.no_cargo
        INNER JOIN oficina AS ofi ON asi.no_oficina = ofi.no_oficina
          WHERE asi.no_nomina_asociado != ""
      UNION
      /* Cobradores */
      SELECT 
        no_personal as no_personal,
        no_empleado_ext as codigo,
        nombre as nombre,
          '' as apellidos,
          '2000-01-01' as fecha_ingreso,
          '' as esquema,
          'COBRADOR' as cargo,
          '' as oficina,
          CASE 
          WHEN vigente = 1 THEN 'ACTIVO'
              ELSE 'BAJA COMPLETA'
        END as estatus
      FROM personal
        WHERE no_empleado_ext != ''
          AND tipo = 2
      ORDER BY codigo
    """

    datos = self._get_data(company_id, consulta)

    empleados_pabs = []
    for dato in datos:
      empleados_pabs.append({
        'no_personal': int(dato['no_personal']),
        'codigo': dato['codigo'], 
        'nombre': dato['nombre'], 
        'apellidos': dato['apellidos'], 
        'fecha_ingreso': dato['fecha_ingreso'], 
        'esquema': dato['esquema'], 
        'cargo': dato['cargo'], 
        'oficina': dato['oficina'], 
        'estatus': dato['estatus'],
        'existe': False
      })

    #--- Marcar empleados que no existen ---#
    for emp in empleados_pabs:
      if emp['codigo'] in empleados_odoo:
        emp.update({'existe': True})

    #--- Dejar en la lista empleados que no existen ---#
    empleados_pabs = [elem for elem in empleados_pabs if elem['existe'] == False]

    if not empleados_pabs:
      _logger.info("No hay empleados")
      return
    
    #--- Consultar departamentos ---#
    id_depto_ventas = self.env['hr.department'].search([
      ('company_id', '=', company_id),
      ('name', '=', 'VENTAS')
    ]).id

    if not id_depto_ventas:
      raise ValidationError("No se encontró el departamento de VENTAS")

    id_depto_cobranza = self.env['hr.department'].search([
      ('company_id', '=', company_id),
      ('name', '=', 'COBRANZA')
    ]).id

    if not id_depto_cobranza:
      raise ValidationError("No se encontró el departamento de COBRANZA")    

    #--- Crear empleados ---#
    cantidad_empleados = len(empleados_pabs)

    for index, emp in enumerate(empleados_pabs, 1):
      _logger.info("{} de {}. {} - {}".format(index, cantidad_empleados, emp['codigo'], emp['cargo']))

      #--- Consultar estatus ---#
      estatus = self.env['hr.employee.status'].search([
        ('name', '=', emp['estatus'])
      ])

      if not estatus:
        _logger.info("No existe el estatus {}".format(emp['estatus']))
        continue

      #--- Consultar cargo ---#
      cargo = self.env['hr.job'].search([
        ('company_id', '=', company_id),
        ('name', '=', emp['cargo'])
      ])

      if not cargo:
        _logger.info("No existe el cargo {}".format(emp['cargo']))
        continue

      resource_id = resource_obj.create({'name': "{} {}".format(emp['nombre'], emp['apellidos'])})
      employee_vals = {}

      # Cobradores
      if emp['cargo'] == 'COBRADOR':
        employee_vals = {
          'first_name': emp['nombre'],
          'last_name': emp['apellidos'],
          'date_of_admission': emp['fecha_ingreso'], 
          'barcode': emp['codigo'], 
          'resource_id': resource_id.id, 
          'job_id': cargo.id,
          'department_id': id_depto_cobranza,
          'employee_status': estatus.id,
          'ecobro_id': emp['no_personal'],
          'company_id' : company_id
        }
      else:
      # Empleados de ventas
        #--- Consultar esquema de pago ---#
        esquema = self.env['pabs.payment.scheme'].search([('name', '=', emp['esquema'])])

        if not esquema:
          _logger.info("No existe el esquema {}".format(emp['esquema']))
          continue

        #--- Consultar oficinas ---#
        oficina = self.env['stock.warehouse'].search([
          ('company_id', '=', company_id),
          ('name', '=', emp['oficina'])
        ])

        if not oficina:
          _logger.info("No existe la oficina {}".format(emp['oficina']))
          continue

        employee_vals = {
          'first_name': emp['nombre'],
          'last_name': emp['apellidos'],
          'date_of_admission': emp['fecha_ingreso'], 
          'barcode': emp['codigo'], 
          'resource_id': resource_id.id, 
          'department_id': id_depto_ventas,
          'payment_scheme': esquema.id,
          'job_id': cargo.id,
          'warehouse_id': oficina.id,
          'employee_status': estatus.id,
          'company_id' : company_id
        }
      
      employee_id = employee_obj.create(employee_vals)

      if employee_id:
        _logger.info("Empleado creado")
      else:
        _logger.info("ERROR: Empleado no creado")

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