# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import logging
import calendar
from dateutil import tz
from odoo.addons.pabs_custom.externals.calcule import CalculeRFC, CalculeCURP
import json
import math
from num2words import num2words
import os
import paramiko
import base64

_logger = logging.getLogger(__name__)

STATES = [
  ('actived','Solicitud Activada'),
  ('precontract', 'Pre-Contrato'),
  ('contract','Contrato'),
  ('cancel','Cancelado')]

STATUS = [
  ('active','Activo'),
  ('inactive', 'Inactivo')]

WAY_TO_PAY = [
  ('weekly','Semanal'),
  ('biweekly','Quincenal'),
  ('monthly', 'Mensual')]

TYPE = [
  ('activation', 'Activaciones'),
  ('precontract', 'Pre-Contratos'),
  ('contract','Contratos')]

SERVICE = [
  ('unrealized','No realizado'),
  ('realized','Realizado'),
  ('made_receivable','Realizado por cobrar')]

TRANSFERS = [
  ('without','SIN TRASPASO'),  
  ('commission_200','TRASPASO CON COMISIÓN $200'),
  ('commission_400','TRASPASO CON COMISIÓN $400'),
  ('commission_rest','TRASPASO CON COMISIÓN RESTANTE'),
  ('without_commission','TRASPASO SIN COMISIÓN')]

MARITAL_STATUS = [
  ('Casado(a)', 'CASADO(A)'),
  ('Soltero(o)', 'SOLTERO(A)'),
  ('Viudo(a)', 'VIUDO(A)'),
  ('Union libre', 'UNION LIBRE'),
  ('Divorciado(a)', 'DIVORCIADO(A)'),
  ('Otros', 'OTROS'),
  ('sin_definir', 'SIN DEFINIR')
]

SALE_TYPE = [
  ('physical', 'Física'),
  ('digital', 'Digital'),
  ('digital_reafiliation', 'Reafiliación digital')
]

DIGITAL_TYPE = [
  ('reafiliation', 'Reafiliacion digital'),
  ('homo', 'HOMÓNNIMO'),
  ('same', 'AFILIACIÓN MISMO NOMBRE'),  
  ('digital', 'DIGITAL'),  
]

ORIGENES = [
  ('cambaceo', 'Cambaceo'),
  ('servicio', 'Servicio'),
  ('referido', 'Referido'),
  ('reafiliacion', 'Reafiliacion'),
  ('medios_electronicos', 'Medios electrónicos'),
  ('directo', 'Directo'),
  ('sobrantes', 'Sobrantes'),
  ('extravio', 'Extravio'),
  ('buenfin', 'Buen fin'),
  ('tipventa','Tip de venta'),
  ('resguardo','Resguardo'),
  ('evento','Evento')
]

#limit-time-real=2000
class PABSContracts(models.Model):
  _name = 'pabs.contract'
  _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
  _description = 'Pre-Contrato'

#Datos del registro
  state = fields.Selection(selection=STATES,string='state',tracking=True,)

#Datos del pre_contrato
  lot_id = fields.Many2one(comodel_name='stock.production.lot', string='No. de Solicitud', tracking=True, required=True)

  type_view = fields.Selection(selection=TYPE, string='Tipo de vista')
  captured = fields.Boolean(string='Capturado previamente')
  agent_id = fields.Char(string='Agente', required=True, default=lambda self: self.env.user.name,tracking=True,)
  activation_code = fields.Char(string='Número de activación', tracking=True)
  
  employee_id = fields.Many2one(comodel_name='hr.employee', related="lot_id.employee_id", tracking=True, string='Asistente activación')
  salary_scheme = fields.Boolean(string='Esquema de pago del empleado', related="employee_id.payment_scheme.allow_all",tracking=True)
  payment_scheme_id = fields.Many2one(comodel_name='pabs.payment.scheme', tracking=True, string='Esquema de pago')
  trasnsfer_type = fields.Selection(string="Tipo de traspaso", selection=TRANSFERS, default='without')
  commission_rest_amount = fields.Float(string="Monto de comisión")
  full_name = fields.Char(string="Nombre completo", tracking=True, compute="calc_full_name", search="_search_full_name")
  street = fields.Char(tracking=True, string='Calle / Número')
  street_toll = fields.Char(tracking=True, string = 'Calle')
  new_entry = fields.Char(string='Nuevo Ingreso')

  #Datos del contrato
  name = fields.Char(string='Número de Contrato', default='Nuevo Contrato', tracking=True)
  ecobro_format_link = fields.Char(string='Formato ECOBRO', compute='get_link')  
  product_price = fields.Float(tracking=True, string='Costo', compute="calc_price")
  sale_employee_id = fields.Many2one(tracking=True, comodel_name='hr.employee', string='Asistente venta')
  reaffiliation = fields.Boolean(string="Es una reafiliación")
  toma_comision = fields.Float(string="Toma comisión")

  contract_status_item =  fields.Many2one(tracking=True, string="Estatus", comodel_name="pabs.contract.status")
  contract_status_name =  fields.Char(tracking=True, string="Nombre estatus", related="contract_status_item.status")
  contract_status_reason =  fields.Many2one(tracking=True, string="Motivo", comodel_name="pabs.contract.status.reason")
  date_of_last_status = fields.Datetime(tracking=True, string="Fecha estatus")
  reactivation_date = fields.Date(tracking=True, string="Fecha reactivación")

  name_service = fields.Many2one(tracking=True, comodel_name = 'product.product', related="lot_id.product_id", string='Servicio')
  warehouse_id = fields.Many2one(string="Oficina", related="lot_id.warehouse_id")
  product_code = fields.Char(tracking=True, string='Código de plan previsor', related="name_service.default_code")

  initial_investment = fields.Float(tracking=True, string ='Inversión inicial')
  stationery = fields.Float(tracking=True, string ='Papelería')
  excedent = fields.Float(tracking=True, string ='Excedente', compute='_calc_excedent')
  comission = fields.Float(tracking=True, string ='Comisión tomada')
  investment_bond = fields.Float(tracking=True, string ='Bono por inversión')
  amount_received = fields.Float(tracking=True, string='Importe recibido', compute='_calc_amount_received')

  # Afiliación electrónica
  sale_type = fields.Selection(tracking=True, selection=SALE_TYPE, string='Tipo de venta', required=True, default="physical")
  digital_type = fields.Selection(tracking=True, selection=DIGITAL_TYPE, string='Tipo digital', required="1", default="digital")
  origen_solicitud = fields.Selection(tracking=True, selection=ORIGENES, string="Origen de solicitud")
  url_ine = fields.Char(string="INE")
  url_comprobante_domicilio = fields.Char(string="Comprobante domicilio")
  url_fachada_domicilio = fields.Char(string="Fachada domicilio")
  url_contrato_reafiliacion = fields.Char(string="Contrato reafiliación")

  debt_collector = fields.Many2one(tracking=True, comodel_name="hr.employee", string='Nombre del cobrador')
  payment_amount = fields.Float(tracking=True, string= 'Monto de pago')
  payment_amount2text = fields.Char(string="Monto de pago", compute='_get_payment_amount2text')
  initial_investment2text = fields.Char(string="Inversión inicial", compute='_get_initial_investment2text')
  initial_investment_in_words = fields.Char(string="Inversion inicial en letras", compute="_amount_to_words")
  way_to_payment = fields.Selection(tracking=True, selection=WAY_TO_PAY,string = 'Forma de pago')
  date_first_payment = fields.Date(tracking=True, string='Fecha primer abono')
  assign_collector_date = fields.Date(tracking=True, string='Fecha asignación cobrador', readonly=True)
  status_of_contract = fields.Char(tracking=True, string="Estatus")
  contract_expires = fields.Date(tracking=True, string="Vencimiento contrato", compute ="calcular_vencimiento_y_atraso")
  days_without_payment = fields.Integer(tracking=True, string="Dias sin abonar", compute="calcular_dias_sin_abonar")
  late_amount = fields.Float(tracking=True, string="Monto atrasado", compute="calculo_rapido_del_monto_atrasado")
  late_amount_stored = fields.Float(tracking=True, string="Monto atrasado almacenado", default=0)
  late_amount2text = fields.Char(string="Monto atrasado", compute='_get_late_amount2text')
  comments = fields.Text(tracking=True, string='Comentarios de activación')
  service_detail = fields.Selection(tracking=True, selection=SERVICE, string='Detalle de servicio', default="unrealized", required="1")

  commission_tree = fields.One2many(tracking=True, comodel_name='pabs.comission.tree', inverse_name='contract_id', string="Arbol de comisiones")
  payment_ids = fields.One2many(tracking=True, comodel_name='account.payment', inverse_name='contract', string="Abonos")
  refund_ids = fields.One2many(tracking=True, comodel_name='account.move', inverse_name='contract_id', string="Notas")

#Datos del cliente
  partner_name = fields.Char(tracking=True, string='Nombre', required=True)
  partner_fname = fields.Char(tracking=True, string='Apellido paterno', required=True)
  partner_mname = fields.Char(tracking=True, string='Apellido materno', required=True)
  birthdate = fields.Date(tracking=True, string='Fecha de nacimiento', default=fields.Date.today(), required=True)
  partner_id = fields.Many2one(tracking=True, comodel_name='res.partner', string='Cliente')
  vat = fields.Char(tracking=True, string='RFC',compute='_calc_rfc')
  client_email = fields.Char(tracking=True, string='Correo')
  marital_status = fields.Selection(tracking=True, selection=MARITAL_STATUS, string='Estado civil', default="sin_definir")

# Domicilio de casa
  street_name = fields.Char(tracking=True, string='Calle', required=True)
  street_number = fields.Char(tracking=True, string='Numero')
  between_streets = fields.Char(tracking=True, string='Entre calles')
  municipality_id = fields.Many2one(tracking=True, comodel_name='res.locality', required=True, string='Municipio')
  neighborhood_id = fields.Many2one(tracking=True, comodel_name='colonias', string='Colonia')
  phone = fields.Char(tracking=True, string='Teléfono', size=10, required=True)
  zip_code = fields.Char(tracking=True, string='C.P.', required=True, default='00000')
  
# Domicilio de cobro
  street_name_toll = fields.Char(tracking=True, string = 'Calle')
  street_number_toll = fields.Char(tracking=True, string = 'Numero')
  between_streets_toll = fields.Char(tracking=True, string ='Entre calles')
  toll_municipallity_id = fields.Many2one(tracking=True, comodel_name='res.locality',string='Municipio')
  toll_colony_id = fields.Many2one(tracking=True, comodel_name='colonias',string='Colonia')
  phone_toll = fields.Char(tracking=True, string='Teléfono', size=10)
  zip_code_toll = fields.Char(tracking=True, string='C.P.', required=True, default='00000')

  latitude = fields.Char(tracking=False, string = 'Latitud')
  longitude = fields.Char(tracking=False, string = 'Longitud')
  coordinates = fields.Char(string = 'Coordenadas', compute="_compute_coordinates")

#Datos contables
  balance = fields.Float(tracking=True, string="Saldo", compute="_calc_balance")
  paid_balance = fields.Float(tracking=True, string="Abonado", compute="_calc_paid_balance")
  invoice_date = fields.Date(tracking=True, string='Fecha de creación', default=lambda r: r.calc_invoice_date())
  invoice_date_month2text = fields.Char(string="Mes", compute= '_get_invoice_date_month2text')
  qr_string = fields.Char(string='QR')
  invoice_date_month_name = fields.Char(string="Nombre del mes", compute="_calc_month_name")

  allow_create = fields.Boolean(tracking=True, string='¿Permitir Crear Factura?')
  allow_edit = fields.Boolean(tracking=True, string='¿Permitir Modificar?')
  
#Otros datos
  count_comments = fields.Integer(string='Comentarios de contrato',
    compute="_calc_comments")
  search_field = fields.Char(tracking=True, string = "Busqueda")
  new_comment = fields.Text(tracking=True, string = "Nuevo comentario:")
  service_detail = fields.Selection(tracking=True, selection=SERVICE, string='Detalle de servicio', default="unrealized", required="1")
  debt_collector = fields.Many2one(tracking=True, comodel_name="hr.employee", string='Nombre del cobrador')
  contract_status = fields.Selection(selection=STATUS, string='Estatus de contrato', tracking=True)
  has_bf_bonus = fields.Boolean(string="Bono buen fin", default=False)

  company_id = fields.Many2one(
    'res.company', 'Compañia', required=True,
    default=lambda s: s.env.company.id, index=True)

  transfer_balance_ids = fields.One2many(comodel_name='account.move.line',
    inverse_name='contract_id',
    string='Traspasos')

  _sql_constraints = [
    ('unique_activation_lot',
      'UNIQUE(lot_id)',
      'No se puede crear el registro: ya existe un registro referenciado al número de solicitud')]
  
  def _compute_coordinates(self):
    for rec in self:
      if rec.latitude and rec.longitude:
        rec.coordinates = "{},{}".format(rec.latitude, rec.longitude)
      else:
        rec.coordinates = ''

  def action_get_contract_report_sftp(self):       
    # Se genera el reporte
    path = os.path.dirname(os.path.abspath(__file__))
    absolute_path = '/home/odoo/tmp'
    filename = '{}.pdf'.format(self.name)
    # pdf = self.env.ref('merge_docx.id_econtrato').render_qweb_pdf([self.id])[0]
    pdf = self.env.ref('merge_docx.id_econtrato').render([self.id])[0]
    file = open(absolute_path + '/' + filename, "wb")
    file.write(pdf)
    file.close()
    # Se definen los parámetros para la conexión sftp
    host = "35.167.149.196"
    username = "ubuntu_aps"    
    sshk   = path + '/pabs_key'
    # Se crea la conexión al server para enviar el archivo
    with paramiko.SSHClient() as ssh:
      ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())      
      ssh.load_system_host_keys()
      # ssh.connect(host, username=username, password=password)
      ssh.connect(host, username=username, key_filename=sshk)
      sftp = ssh.open_sftp()      
      sftp.chdir('/var/www/html/asistencia_social_SLW/application/files/contratos_odoo')
      sftp.put(absolute_path + '/' + filename, filename)
      # Se elimina el archivo
      os.remove(absolute_path + '/' + filename)
    return True
  
  ### Regresa el estado de cuenta en base 64.
  def get_statement_report_64(self,  contract = False, company_id = False):
    vals = {
      'b64_data': '',
      'msg': ""
    }
    
    try:
      if not company_id or not contract:
        vals = {
          'b64_data': '',
          'msg': 'No se envió alguno de los parámetros: company_id, contract'
        }
      else:
        con = self.search([
          ('company_id', '=', company_id),
          ('name', '=', contract)
        ])

        if not con:
          return {
            'b64_data': '',
            'msg': 'No se envio alguno de los parametros: company_id, contract'
          }
        
        pdf = self.env.ref('xmarts_funeraria.id_estado_cuenta').render(con.id)[0]
            
        vals = {
          'b64_data': base64.b64encode(pdf).decode('utf-8'),
          'msg': ''
        }

        return json.dumps(vals)
    except Exception as ex:
      vals = {
        'b64_data': '',
        'msg': "Error: {}".format(ex)
      }

      return json.dumps(vals)
  
  ### Crea el formato del contrato en pdf y lo regresa en base 64
  def action_get_contract_report(self, activation_code=False, company_id=False):
    try:
      vals = {
          'contract': '',
          'b64_data': '',
          'msg': 'Defina los parámetros de búsqueda'
        }
      
      if activation_code and company_id:
        contract_id = self.env['pabs.contract'].sudo().search([
          ('activation_code', '=', activation_code),
          ('company_id', '=', company_id)
        ], limit=1)

        if contract_id:
          if contract_id.name_service.product_tmpl_id.contract_xml_id:
            xml_id = contract_id.name_service.product_tmpl_id.contract_xml_id
            pdf = self.env.ref(xml_id).render([contract_id.id])[0]
            
            vals = {
              'contract': contract_id.name,
              'b64_data': base64.b64encode(pdf).decode('utf-8'),
              'msg': ''
            }
          else:
            vals = {
              'contract': '',
              'b64_data': '',
              'msg': 'No se ha configurado el xml_id en el producto'
            }
        else:
          vals = {
            'contract': '',
            'b64_data': '',
            'msg': 'No existe un contrato con los parámetros enviados'
          }

        return json.dumps(vals)
      
    except Exception as ex:
      vals = {
        'contract': '',
        'b64_data': '',
        'msg': "{}{}".format('Error: ', ex)
      }

      return json.dumps(vals)
    
  def get_pdf_contract_base64(self, name=False, company_id=False):
    try:
      vals = {
          'contract': '',
          'b64_data': '',
          'msg': 'Defina los parámetros de búsqueda'
        }
      
      if name and company_id:
        contract_id = self.env['pabs.contract'].sudo().search([
          ('name', '=', name),
          ('company_id', '=', company_id)
        ], limit=1)

        if contract_id:
          if contract_id.name_service.product_tmpl_id.contract_xml_id:
            xml_id = contract_id.name_service.product_tmpl_id.contract_xml_id
            pdf = self.env.ref(xml_id).render([contract_id.id])[0]
            
            vals = {
              'contract': contract_id.name,
              'b64_data': base64.b64encode(pdf).decode('utf-8'),
              'msg': ''
            }
          else:
            vals = {
              'contract': '',
              'b64_data': '',
              'msg': 'No se ha configurado el xml_id en el producto'
            }
        else:
          vals = {
            'contract': '',
            'b64_data': '',
            'msg': 'No existe un contrato con los parámetros enviados'
          }

        return json.dumps(vals)
      
    except Exception as ex:
      vals = {
        'contract': '',
        'b64_data': '',
        'msg': "{}{}".format('Error: ', ex)
      }

      return json.dumps(vals)
    
  def get_contract_pdf(self):
    if not self.name_service.product_tmpl_id.contract_xml_id:
      raise ValidationError('No se ha configurado el xml_id en el producto')
    
    xml_id = self.name_service.product_tmpl_id.contract_xml_id
    
    #self.env.ref(xml_id).render([self.id])[0]
    return self.env.ref(xml_id).report_action(self)
  
  def get_link(self):    
    for rec in self:
      if rec.activation_code:        
        rec.ecobro_format_link = 'http://35.167.149.196/ecobroSAP/application/contratos/%s.pdf'%(rec.activation_code)
      else:
        rec.ecobro_format_link = False

  def action_get_images_digital(self):
    vals = {
      'url_ine': self.url_ine,
      'url_comprobante_domicilio': self.url_comprobante_domicilio,
      'url_fachada_domicilio': self.url_fachada_domicilio,
      'url_contrato_reafiliacion': self.url_contrato_reafiliacion,
    }
    wizard_id = self.env['show.digital.images.wizard'].create(vals)

    return {        
      'name': (""),                        
      'view_type': 'form',        
      'view_mode': 'form',        
      'res_model': 'show.digital.images.wizard', 
      'res_id': wizard_id.id,
      'views': [(False, 'form')],        
      'type': 'ir.actions.act_window',        
      'target': 'new',    
    }

  def numero_to_letras(self,numero):
    indicador = [("",""),("MIL","MIL"),("MILLON","MILLONES"),("MIL","MIL"),("BILLON","BILLONES")]
    entero = int(numero)
    decimal = int(round((numero - entero)*100))
    #print 'decimal : ',decimal 
    contador = 0
    numero_letras = ""
    while entero >0:
      a = entero % 1000
      if contador == 0:
        en_letras = self.convierte_cifra(a,1).strip()
      else :
        en_letras = self.convierte_cifra(a,0).strip()
      if a==0:
        numero_letras = en_letras+" "+numero_letras
      elif a==1:
        if contador in (1,3):
          numero_letras = indicador[contador][0]+" "+numero_letras
        else:
          numero_letras = en_letras+" "+indicador[contador][0]+" "+numero_letras
      else:
        numero_letras = en_letras+" "+indicador[contador][1]+" "+numero_letras
      numero_letras = numero_letras.strip()
      contador = contador + 1
      entero = int(entero / 1000)
    numero_letras = numero_letras #+" CON " + str(decimal) +"/100"
    return numero_letras

  def convierte_cifra(self,numero,sw):
    lista_centana = ["",("CIEN","CIENTO"),"DOSCIENTOS","TRESCIENTOS","CUATROCIENTOS","QUINIENTOS","SEISCIENTOS","SETECIENTOS","OCHOCIENTOS","NOVECIENTOS"]
    lista_decena = ["",("DIEZ","ONCE","DOCE","TRECE","CATORCE","QUINCE","DIECISEIS","DIECISIETE","DIECIOCHO","DIECINUEVE"),
            ("VEINTE","VEINTI"),("TREINTA","TREINTA Y "),("CUARENTA" , "CUARENTA Y "),
            ("CINCUENTA" , "CINCUENTA Y "),("SESENTA" , "SESENTA Y "),
            ("SETENTA" , "SETENTA Y "),("OCHENTA" , "OCHENTA Y "),
            ("NOVENTA" , "NOVENTA Y ")
    ]
    lista_unidad = ["",("UN" , "UNO"),"DOS","TRES","CUATRO","CINCO","SEIS","SIETE","OCHO","NUEVE"]
    centena = int (numero / 100)
    decena = int((numero -(centena * 100))/10)
    unidad = int(numero - (centena * 100 + decena * 10))
    #print "centena: ",centena, "decena: ",decena,'unidad: ',unidad
    texto_centena = ""
    texto_decena = ""
    texto_unidad = ""
    #Validad las centenas
    texto_centena = lista_centana[centena]
    if centena == 1:
      if (decena + unidad)!=0:
        texto_centena = texto_centena[1]
      else :
        texto_centena = texto_centena[0]
    #Valida las decenas
    texto_decena = lista_decena[decena]
    if decena == 1 :
      texto_decena = texto_decena[unidad]
    elif decena > 1 :
      if unidad != 0 :
        texto_decena = texto_decena[1]
      else:
        texto_decena = texto_decena[0]
    #Validar las unidades
    #print "texto_unidad: ",texto_unidad
    if decena != 1:
      texto_unidad = lista_unidad[unidad]
      if unidad == 1:
        texto_unidad = texto_unidad[sw]
    return "%s %s %s" %(texto_centena,texto_decena,texto_unidad)

  def _get_invoice_date_month2text(self):
    months = {
      1: 'ENERO',
      2: 'FEBRERO',
      3: 'MARZO',
      4: 'ABRIL',
      5: 'MAYO',
      6: 'JUNIO',
      7: 'JULIO',
      8: 'AGOSTO',
      9: 'SEPTIEMBRE',
      10:'OCTUBRE',
      11:'NOVIEBRE',
      12:'DICIEMBRE'
      }
    for rec in self:
      if rec.invoice_date:
        rec.invoice_date_month2text = months.get(rec.invoice_date.month)
      else:
        rec.invoice_date_month2text = ""

  def _get_initial_investment2text(self):
     for rec in self:
      text = self.numero_to_letras(rec.initial_investment)
      rec.initial_investment2text = text
  
  def _get_payment_amount2text(self):
    for rec in self:
      text = self.numero_to_letras(rec.payment_amount)
      rec.payment_amount2text = text

  def _get_late_amount2text(self):
    for rec in self:
      text = self.numero_to_letras(rec.late_amount)
      rec.late_amount2text = text

  def add_balance_wizard_action(self):
    wizard_id = self.env['add.balance.wizard'].create({})
    return {        
        'name': ("Aumentar saldo"),                         
        'view_type': 'form',        
        'view_mode': 'form',        
        'res_model': 'add.balance.wizard', 
        'res_id': wizard_id.id,                  
        'type': 'ir.actions.act_window',        
        'target': 'new',    
    }
  
  def action_payment_outputs(self):               
        # Se crea el wizard
        wizard_id = self.env['output.payment.wizard'].create({})            
        # Se devuelve el wizard
        return {
            'name': u'Salida de comisiones',
            'type': 'ir.actions.act_window',
            'res_model': 'output.payment.wizard',
            'view_type': 'form',
            'view_mode': 'form',          
            'res_id': wizard_id.id,
            'target': 'new',
        }

  # NC de buen fin 
  def update_bf_contracts(self, company_id):
    journal_id = self.env['account.journal'].search([
      ('company_id', '=', company_id),
      ('name', '=', 'VENTAS'),
      ('type', '=', 'sale')
    ])

    if not journal_id:
      raise ValidationError("No se encontró el diario VENTAS")

    currency_id = 33
    aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
    #  
    # Se obtienen las solictudes en las que se asignó agente del BF
    lot_ids = []
    mov_ids = self.env['stock.move'].search([('asistente_social_bf','!=',False),('company_id','=',company_id)])
    for mov in mov_ids:
      move_line_ids = self.env['stock.move.line'].search([('move_id','=',mov.id)])
      for line in move_line_ids:
        lot_ids.append(line.lot_id)
    # Se obtienen los contratos 
    contract_ids = []
    for lot in lot_ids:
      contract_id = self.search([('lot_id','=',lot.id),('has_bf_bonus','=',False),('company_id','=',company_id)],limit=1)
      if contract_id:
        if contract_id not in contract_ids:
          contract_ids.append(contract_id) 
    # contract_ids = self.search([('company_id','=',company_id),('has_bf_bonus','=',False)])   
    for contract in contract_ids:
      error_log = str(contract.name) + ' - ' + 'Se intentó crear una NC por Bono de inversión inicial (Buen fin) - '
      bf = False
      # Se buscan todos los registros en los que el lot_id corresponda con el contrato
      move_line_ids = self.env['stock.move.line'].search([('lot_id','=',contract.lot_id.id)])
      for movl in move_line_ids:
        # Si se especificó un agente de buen fin
        if movl.move_id.asistente_social_bf:
          bf = True            
          break
      # Si es un contrato de buen fin
      if bf:
        invoice_id = self.env['account.move'].search([('contract_id','=',contract.id)], limit = 1)
        if invoice_id:
          # Se crea la NC             
          # FISCAL
          if contract.company_id.apply_taxes:
            #Buscar impuesto a agregar
            iva_tax = self.env['account.tax'].search([('name','=','IVA'), ('company_id','=', contract.company_id.id)])        
            if not iva_tax:
              error_log += "No se encontró el impuesto con nombre IVA"
              contract.message_post(body=(error_log))
              continue

            #Buscar linea de repartición de impuesto para facturas
            iva_repartition_line = iva_tax.refund_repartition_line_ids.filtered_domain([
              ('repartition_type','=','tax'), 
              ('refund_tax_id','=', iva_tax.id), 
              ('company_id','=', contract.company_id.id)
            ])

            if not iva_repartition_line:
              error_log += "No se encontró la repartición de facturas rectificativas del impuesto {}".format(iva_tax.name)
              contract.message_post(body=(error_log))
              continue
            if len(iva_repartition_line) > 1:
              error_log += "Se definió mas de una linea (sin incluir la linea base) en la repartición de facturas rectificativas del impuesto {}".format(iva_tax.name)
              contract.message_post(body=(error_log))
              continue
          # Datos de la NC
          refund_data = {
            'date' : contract.invoice_date,
            'commercial_partner_id' : contract.partner_id.id,
            'partner_id' : contract.partner_id.id,
            'ref' : 'Bono por inversión inicial',
            'type' : 'out_refund',
            'journal_id' : journal_id.id,
            'state' : 'draft',
            'currency_id' : currency_id,
            'invoice_date' : contract.invoice_date,
            'auto_post' : False,
            'contract_id' : contract.id,
            'invoice_user_id' : self.env.user.id,
            'reversed_entry_id' : invoice_id.id,
          }
          refund_id = self.env['account.move'].create(refund_data)
          if refund_id:
             # Buscar producto Bono por inversión inicial
              product_id = self.env['product.template'].search([('company_id','=',contract.company_id.id),('name','=','BONO POR INVERSION INICIAL')])
              if not product_id:
                error_log += "No se encontró el producto BONO POR INVERSION INICIAL"
                contract.message_post(body=(error_log))
                continue

              product_product = self.env['product.product'].search([('product_tmpl_id', '=', product_id.id)])
              if not product_product:
                error_log += "Problema el producto BONO POR INVERSION INICIAL: No se encontró la relación product_template({}) en la tabla product_product".format(product_id.id)
                contract.message_post(body=(error_log))
                continue

              account_id = product_id.property_account_income_id or product_id.categ_id.property_account_income_categ_id
              if not account_id:
                error_log = "No se encontró la cuenta en los campos product_id.property_account_income_id o product_id.categ_id.property_account_income_categ_id"
                contract.message_post(body=(error_log))
                continue
              # Llenar datos de Linea principal de débito
              amount= 8000
              if contract.payment_amount >= 100:
                amount = 8500              

              line_data = {
                'move_id' : refund_id.id,
                'account_id' : account_id.id,
                'quantity' : 1,
                'price_unit' :amount,
                'debit' : amount,
                'product_uom_id' : product_id.uom_id.id,
                'partner_id' : contract.partner_id.id,
                'amount_currency' : 0,
                'product_id' : product_product.id,
                'is_rounding_line' : False,
                'exclude_from_invoice_tab' : False,
                'name' : product_id.description_sale or product_id.name,
              }
              # FISCAL
              if contract.company_id.apply_taxes:
                line_data.update({
                  'tax_exigible' : True,
                  'tax_ids' : [(4, iva_tax.id, 0)],
                  'debit' : round(amount / (1 + iva_tax.amount/100), 2),
                })
              line = aml_obj.create(line_data)
              
              # FISCAL
              # Llenar datos para línea de IVA
              if contract.company_id.apply_taxes:
                iva_data = {
                  'move_id' : refund_id.id,
                  'account_id' : iva_repartition_line.account_id.id,
                  'quantity' : 1,
                  'price_unit' : amount,
                  'debit' : round(amount - round( (amount / (1 + iva_tax.amount/100)), 2), 2),
                  'tax_base_amount' : round(amount - round( (amount / (1 + iva_tax.amount/100)), 2), 2),
                  'product_uom_id' : product_id.uom_id.id,
                  'partner_id' : contract.partner_id.id,
                  'amount_currency' : 0,
                  'product_id' : product_product.id,
                  'is_rounding_line' : False,
                  'exclude_from_invoice_tab' : True,
                  'name' : iva_tax.name,
                  'tax_line_id' : iva_tax.id,
                  'tax_group_id' : iva_tax.tax_group_id.id,
                  'tax_repartition_line_id' : iva_repartition_line.id,
                }
                line = aml_obj.create(iva_data)
              ### CONTRAPARTIDA DEL DOCUMENTO #Linea de crédito
              partner_line_data = {
                'move_id' : refund_id.id,
                'account_id' : refund_id.partner_id.property_account_receivable_id.id,
                'quantity' : 1,
                'date_maturity' : contract.invoice_date,
                'amount_currency' : 0,
                'partner_id' : contract.partner_id.id,
                'tax_exigible' : False,
                'is_rounding_line' : False,
                'exclude_from_invoice_tab' : True,
                'credit' : amount,
              }
              line = aml_obj.create(partner_line_data)
              ### VALIDANDO NOTA DE CRÉDITO
              try:
                refund_id.with_context(investment_bond=True).action_post()
                # Se concilia la NC
                reconcile = {}
                for line_m in invoice_id.line_ids:
                  if line_m.debit > 0:
                    reconcile.update({'debit_move_id' : line_m.id})
                #
                data = {
                  'debit_move_id' : reconcile.get('debit_move_id'),
                  'credit_move_id' : line.id,
                  'amount' : abs(line.balance)
                }
                self.env['account.partial.reconcile'].create(data)
                contract.has_bf_bonus = True
                contract.message_post(body=("Se creó una NC por Bono de inversión inicial (Buen fin)"))
              except:
                contract.message_post(body=("Error inesperado al intentar validar la NC por inversión inicial (Buen fin), posiblemente el monto de la NC es mayor al monto resiudal del a factura asociada."))
                continue
        else:
          error_log += 'No existe factura asociada al contrato'
          contract.message_post(body=(error_log))    
          continue
    return True

  #Función que busca por nombre completo mediante una consuta a la base utilizando like
  def _search_full_name(self, operator, value):
    #Construye cadena de busqueda
    nombre_completo = "%" + value.replace(" ", "%") + "%"
    nombre_completo = nombre_completo.upper()

    #Ejecuta la consulta
    consulta = "Select name from pabs_contract where company_id = {} AND state = 'contract' AND CONCAT(partner_name, ' ', partner_fname, ' ', partner_mname) like '{}'".format(self.env.company.id, nombre_completo)
    self.env.cr.execute(consulta)

    #Construye lista de contratos a regresar
    contratos = []
    for res in self.env.cr.fetchall():
      contratos.append(res[0]) 

    #Retorna los contratos encontrados
    return [('name', 'in', tuple(contratos))]

  @api.depends('invoice_date')
  def _calc_month_name(self):
    for rec in self:
      meses = ['x', 'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
      rec.invoice_date_month_name = meses[rec.invoice_date.month]

  @api.depends('initial_investment')
  def _amount_to_words(self):
    for rec in self:
      rec.initial_investment_in_words = str(num2words(rec.initial_investment, lang ='es')).upper()

  def _calc_comments(self):
    contract_comments_obj = self.env['pabs.contract.comments']
    for rec in self:
      contract_count = contract_comments_obj.search_count([('contract_id','=',rec.id)])
      rec.count_comments = contract_count

  def button_comments(self):
    return {
      'name': 'Visualizar Comentarios',
      'type': 'ir.actions.act_window',
      'view_mode': 'tree',
      'res_model': 'pabs.contract.comments',
      'view_id': self.env.ref('pabs_custom.view_pabs_custom_comments_tree').id,
      'target' : 'new',
      'domain' : [('contract_id','=',self.id)]
    }

  def calc_invoice_date(self):
    params = self.env['ir.config_parameter'].sudo()
    actually_day = params.get_param('pabs_custom.actually_day')
    last_day = params.get_param('pabs_custom.last_day')
    if actually_day:
      if last_day:
         return last_day
    return fields.Date.context_today(self)

  def validate_date(self, date):
    params = self.env['ir.config_parameter'].sudo()
    allow_last_days = int(params.get_param('pabs_custom.allowed_days'))
    date_format = datetime.strptime(date, '%Y-%m-%d').date()
    today = fields.Date.context_today(self)
    if allow_last_days > 0:
      allowed_date = fields.Date.context_today(self) - timedelta(days=allow_last_days)
    elif allow_last_days == 0:
      allowed_date = fields.Date.context_today(self)
    else:
      raise ValidationError("No tienes permitido crear contratos a futuro")
    ### Validación de creación
    if date_format < allowed_date:
      raise ValidationError("No tienes permitido crear contratos con una fecha anterior a {}".format(allowed_date))
    elif date_format > today:
      raise ValidationError("No puedes crear un contrato con una fecha superior a {}".format(today))
    else:
      return date_format


  #Al elegir un estatus diferente borrar el motivo actual
  @api.onchange('contract_status_item')
  def check_status_reason(self):
    for rec in self:
      rec.contract_status_reason = None

  #Costo: Es la suma de las facturas, de no existir facturas será el costo del plan registrado en la tabla de tarifas.
  def calc_price(self):
    for rec in self:
      rec.product_price = 99999
      invoice_ids = rec.refund_ids.filtered(lambda r: r.type == 'out_invoice' and r.state == 'posted')
      if len(invoice_ids) > 0:
        rec.product_price = sum(invoice_ids.mapped('amount_total'))
      else:
        if rec.name_service:
          pricelist_id = self.env['product.pricelist.item'].search([('product_id','=',rec.name_service.id)], limit=1)
          if pricelist_id:
            rec.product_price = pricelist_id.fixed_price
        #   else:
        #     raise ValidationError("calc_price: No se encontró la tarifa del producto")
        # else:
        #     raise ValidationError("calc_price: No se encontró el producto del contrato")

  # Saldo: Es la suma del monto pendiente de las facturas mas el monto entregado por traspasos
  def _calc_balance(self):
    for rec in self:
      
      saldo = 99999

      # Sumar el monto restante de las facturas
      facturas = rec.refund_ids.filtered(lambda x: x.type == 'out_invoice' and x.state == 'posted')
      if len(facturas) > 0:
        saldo = sum(facturas.mapped('amount_residual'))
      
      # Aumentar el monto entregado por traspasos
      traspasos = rec.transfer_balance_ids.filtered(lambda x: x.move_id.state == 'posted')
      if len(traspasos) > 0:
        
        # No sumar traspasos cuando el contrato ya fue cancelado fiscalmente (tiene una factura con el producto "Cancelación fiscal")
        if rec.company_id.apply_taxes:
          cancelado_fiscalmente = self.env['account.move.line'].search_count([
            ('partner_id', '=', rec.partner_id.id),
            ('parent_state', '=', 'posted'),
            ('product_id.default_code', '=', 'DESC-0009')
          ])

          if cancelado_fiscalmente == 0:
            ### 2024-08-03: no agregar saldo por traspaso a contratos liquidados (no deberian de ingresar pagos a contratos que traspasan importe... pero lo hacen)
            if round(saldo, 2) > 0:
              saldo = saldo + sum(traspasos.mapped('debit'))
        else:
          ### 2024-08-03: no agregar saldo por traspaso a contratos liquidados (no deberian de ingresar pagos a contratos que traspasan importe... pero lo hacen. ej 2CJ033943 Saltillo)
          if round(saldo, 2) > 0:
            saldo = saldo + sum(traspasos.mapped('debit'))

      rec.balance = saldo

  # Abonado = Costo - Saldo
  def _calc_paid_balance(self):
    for rec in self:
      rec.paid_balance = rec.product_price - rec.balance

  @api.onchange('partner_name','partner_fname','partner_mname')
  def calc_full_name(self):
    for rec in self:
      full_name = "{} {} {}".format(
        rec.partner_name,
        rec.partner_fname,
        rec.partner_mname)
      rec.full_name = full_name

  @api.onchange('search_field')
  def calc_search_field(self):
    contract_obj = self.env['pabs.contract']
    lot_obj = self.env['stock.production.lot']
    search = False
    if self.search_field:
      dat = str(self.search_field)
      search = contract_obj.search([
        ('state','=','contract'),
        ('name','=',dat)],limit=1)
      if not search:
        lot_id = lot_obj.search([
          ('name','=',dat)])
        if lot_id:
          search = contract_obj.search([
            ('state','=','contract'),
            ('lot_id','=',lot_id.id)],limit=1)
      if not search:
        search = contract_obj.search([
          ('state','=','contract'),
          ('activation_code','=',dat)],limit=1)
      if not search:
        self.lot_id = False
        return {
          'warning' : {
            'title' : ('Error al buscar coincidencia'),
            'message' :('No se encontró una coincidencia para: {}'.format(dat)),
          }
        }
      self.lot_id = search.lot_id.id
    else:
      self.lot_id = False

  @api.onchange('invoice_date')
  def calc_first_payment(self):
    for rec in self:
      if rec.invoice_date:
        rec.date_first_payment = rec.invoice_date + timedelta(days=15)

  @api.onchange('date_first_payment')
  def validar_fecha_primer_abono(self):
    for rec in self:
      if rec.state == 'precontract' and rec.date_first_payment:
        if rec.date_first_payment < fields.Date.today():
          rec.date_first_payment = fields.Date.today() + timedelta(days=15)
          return {
            'warning': {'title': "Valor no permitido", 'message': "No se puede asignar una fecha de primer abono menor al dia actual"},
          }

  @api.onchange('amount_received','stationery')
  def _calc_excedent(self):
    for rec in self:
      rec.excedent = (float(rec.initial_investment) - float(rec.stationery))

  @api.onchange('initial_investment','comission')
  def _calc_amount_received(self):
    pabs_bonus_obj = self.env['pabs.bonus']
    for rec in self:
      rec.amount_received = (rec.initial_investment - rec.comission) or 0
      if rec.state != 'contract':
        product_id = rec.name_service
        bonus = pabs_bonus_obj.search([('plan_id','=',product_id.id)], order="min_value")
        bon = 0
        for bon_rec in bonus:
          if rec.initial_investment >= bon_rec.min_value and rec.initial_investment <= bon_rec.max_value:
            bon = bon_rec.bonus
        rec.investment_bond = bon
  
  ### Calculo de RFC con la información cargada
  @api.onchange('partner_name','partner_fname','partner_mname','birthdate')
  def _calc_rfc(self):
    if self.partner_name and self.partner_fname and \
      self.partner_mname and self.birthdate:
      name = self.partner_name
      father_lastname = self.partner_fname
      mother_lastname = self.partner_mname
      birthdate = fields.Date.from_string(
        self.birthdate).strftime('%d-%m-%Y')
      try:
        rfc = CalculeRFC(nombres=name,
          paterno=father_lastname,
          materno=mother_lastname,
          fecha=birthdate)
        self.vat = rfc.data
      except:
        self.vat = 'No se pudo generar RFC'

  #Crear Contacto (Cliente)
  def create_partner(self, vals, company_id):
    partner_obj = self.env['res.partner'].sudo()
    lot_obj = self.env['stock.production.lot']
    lot_id = lot_obj.browse(vals.get('lot_id'))
    account_obj = self.env['account.account'].sudo()
    #

    # Buscar cuentas contables
    cuenta_a_cobrar = account_obj.search([('code','=','110.01.001'),('company_id','=',company_id)]) #Afiliaciones plan previsión
    cuenta_a_pagar = account_obj.search([('code','=','201.01.001'),('company_id','=',company_id)]) #Proveedores nacionales

    if not cuenta_a_cobrar:
      raise ValidationError("No se encontró la cuenta 110.01.001 Afiliaciones plan previsión")

    if not cuenta_a_pagar:
      raise ValidationError("No se encontró la cuenta 201.01.001 Proveedores nacionales")

    if lot_id:
      partner_id = partner_obj.search([('name','=',lot_id.name), ('company_id','=',company_id)])
      if partner_id:
        partner_id.write({"property_account_receivable_id": cuenta_a_cobrar.id, "property_account_payable_id": cuenta_a_pagar.id})
        return partner_id
      else: 
        data = {
          'company_type' : 'person',
          'name' : lot_id.name,
          'property_account_receivable_id': cuenta_a_cobrar.id, 
          'property_account_payable_id': cuenta_a_pagar.id,
          'company_id': company_id
        }

        return partner_obj.create(data)
    else:
      raise ValidationError("Create_partner: No se encontró la solicitud")

  @api.model
  def create(self, vals):
    company_id = vals.get('company_id') or self.env.context.get('company_id') or self.env.company.id or False
    ### Valida que si ya existe una activación con ese número de serie, no permita generarla nuevamente
    if company_id:
      domain = [('lot_id','=',vals['lot_id']),('company_id','=',company_id)]
    else:
      domain = [('lot_id','=',vals['lot_id'])]
    previous = self.search(domain,limit=1)
    if previous:
      if previous.state == 'precontract':
        self.create_contract(vals)
        return previous
      if previous.state == 'contract':
        return previous
      raise ValidationError((
        "No puedes activar una solicitud que ya fue previamente activada"))
    ### Cambia el estatús del contrato a activo
    vals['contract_status'] = 'active'
    ### IMPRIMIMOS EL CONTEXTO
    ### Asignación del número de activación
    if not vals.get('activation_code'):
      vals['activation_code'] = self.env['ir.sequence'].with_context(
        force_company=company_id).next_by_code(
        'pabs.contracts')
      ### Se cambia el estado del registro a "Pre-Contrato"
      
    partner_id = self.create_partner(vals, company_id)
    vals['partner_id'] = partner_id.id
    vals['state'] = 'actived'
    full_name = ''
    if vals.get('partner_name'):
      full_name = full_name + vals.get('partner_name')
    if vals.get('partner_fname'):
      full_name = full_name + ' ' + vals.get('partner_fname')
    if vals.get('partner_mname'):
      full_name = full_name + ' ' + vals.get('partner_mname')
    vals['full_name'] = full_name
    ### Se retorna el diccionario modificado
    return super(PABSContracts, self).create(vals)

  def unlink(self):
    for contract in self:
      ### Evita que se elimine un registro que previamente ya fue guardado
      raise ValidationError((
        "No puedes eliminarlo por que fue previamente activado"))
    #return super(PABSContracts, self).unlink()

  def action_cancel(self):
    self.contract_status = 'inactive'
    self.state = 'cancel'
    return False

  def empty_window(self):
  #Datos del registro
    self.state = False

  #Datos del pre_contrato
    self.captured = False
    self.activation_code = False
    self.new_entry = False
    self.payment_scheme_id = False

  #Datos del contrato
    self.name = False
    self.product_price = False
    self.product_code = False

    self.initial_investment = False
    self.stationery = False
    self.excedent = False
    self.comission = False
    self.investment_bond = False
    self.amount_received = False

    self.debt_collector = False
    self.payment_amount = False
    self.way_to_payment = False
    self.date_first_payment = False
    self.days_without_payment = False
    self.late_amount = False
    self.contract_expires = False
    self.comments = False
    self.service_detail = False

  #Datos del cliente
    self.partner_name = False
    self.partner_fname = False
    self.partner_mname = False
    self.birthdate = fields.Date.today()
    self.vat = False

  #Domicilio de casa
    self.street_name = False
    self.street_number = False
    self.between_streets = False
    self.municipality_id = False
    self.neighborhood_id = False
    self.phone = False
    self.zip_code = False

  #Domicilio de cobro
    self.street_name_toll = False
    self.street_number_toll = False
    self.between_streets_toll = False
    self.toll_municipallity_id = False
    self.toll_colony_id = False
    self.phone_toll = False
    self.zip_code_toll = False

  #Datos contables
    self.allow_create = False
    self.invoice_date = False
    self.service_detail = False
    self.product_code = False
    self.status_of_contract = False
    self.contract_expires = False
    self.balance = False
    self.paid_balance = False
    self.days_without_payment = False
    self.late_amount = False
    self.service_detail = False
    self.debt_collector = False

  def set_previous_values(self, contract_id):
    if contract_id:
      #Datos del registro
      self.state = contract_id.state

      #Datos del pre_contrato
      self.captured = True
      self.activation_code = contract_id.activation_code
      self.new_entry = contract_id.new_entry
      self.payment_scheme_id = contract_id.payment_scheme_id
      self.sale_type = contract_id.sale_type

      #Datos del contrato
      self.name = contract_id.name
      self.product_price = contract_id.product_price
      self.product_code = contract_id.product_code

      self.initial_investment = contract_id.initial_investment
      self.stationery = contract_id.stationery
      self.comission = contract_id.comission
      self.investment_bond = contract_id.investment_bond

      self.debt_collector = contract_id.debt_collector
      self.payment_amount = contract_id.payment_amount
      self.way_to_payment = contract_id.way_to_payment

      if contract_id.date_first_payment:
        self.date_first_payment = contract_id.date_first_payment
      else:
        self.date_first_payment = fields.Date.today() + timedelta(days=15)

      self.contract_expires = contract_id.contract_expires
      self.comments = contract_id.comments
      self.service_detail = contract_id.service_detail
      self.days_without_payment = contract_id.days_without_payment
      self.late_amount = contract_id.late_amount
      self.service_detail = contract_id.service_detail

      #Datos del cliente
      self.partner_name = contract_id.partner_name
      self.partner_fname = contract_id.partner_fname
      self.partner_mname = contract_id.partner_mname
      self.birthdate = contract_id.birthdate
      self.vat = contract_id.vat

      #Domicilio de casa
      self.street_name = contract_id.street_name
      self.street_number = contract_id.street_number
      self.between_streets = contract_id.between_streets
      self.municipality_id = contract_id.municipality_id.id
      self.neighborhood_id = contract_id.neighborhood_id.id
      self.phone = contract_id.phone
      self.zip_code = contract_id.zip_code
    
      #Domicilio de cobro
      self.street_name_toll = contract_id.street_name
      self.street_number_toll = contract_id.street_number
      self.between_streets_toll = contract_id.between_streets
      self.toll_municipallity_id = contract_id.municipality_id.id
      self.toll_colony_id = contract_id.neighborhood_id.id
      self.phone_toll = contract_id.phone
      self.zip_code_toll = contract_id.zip_code

      #Datos contables
      self.invoice_date = contract_id.calc_invoice_date()
      self.service_detail = contract_id.service_detail
      self.product_code = contract_id.product_code
      self.status_of_contract = contract_id.status_of_contract
      self.contract_expires = contract_id.contract_expires
      self.balance = contract_id.balance
      self.paid_balance = contract_id.paid_balance
      self.days_without_payment = contract_id.days_without_payment
      self.late_amount = contract_id.late_amount
      self.service_detail = contract_id.service_detail
      self.debt_collector = contract_id.debt_collector

  #Al modificar la forma de pago actualizar el monto de pago
  @api.onchange('way_to_payment')
  def _onchange_(self):
    #Crear objeto de busqueda de tarifas
    pricelist_obj = self.env['product.pricelist.item']
    for rec in self:
      if rec.name_service:
        #Buscar tarifa del producto
        pricelist_id = pricelist_obj.search([('product_id','=',rec.name_service.id)], limit=1)
        #Calcular el monto de pago de acuerdo al monto de la tarifa
        if pricelist_id:
          if self.way_to_payment == 'weekly':
            rec.payment_amount = pricelist_id.payment_amount
          elif self.way_to_payment == 'biweekly':
            rec.payment_amount = pricelist_id.payment_amount * 2
          else:
            rec.payment_amount = pricelist_id.payment_amount * 4
      
  @api.onchange('lot_id')
  def calc_employee(self):    
    location_obj = self.env['stock.location']
    pricelist_obj = self.env['product.pricelist.item']
    stock_quant_obj = self.env['stock.quant']
    hr_obj = self.env['hr.employee']
    contract_id = self.search([('lot_id','=',self.lot_id.id)], limit=1)
    if contract_id:
      self.set_previous_values(contract_id)
      if self.state == 'precontract':
        pricelist_id = pricelist_obj.search([
          ('product_id','=',self.lot_id.product_id.id)], limit=1)
        if not pricelist_id:
          raise ValidationError((
            "El servicio no cuenta con un precio"))
          self.product_price = pricelist_id.fixed_price
        else:
          #Valores de inicio al capturar un contrato
          self.payment_amount = pricelist_id.payment_amount
          self.way_to_payment = WAY_TO_PAY[0][0]
    else:
      self.empty_window()
    quant_id = stock_quant_obj.search([
      ('lot_id','=',self.lot_id.id)]).filtered(
          lambda r: r.location_id.usage == 'internal' and r.inventory_quantity > 0)
    if quant_id:
      location_id = quant_id.location_id
    if self.type_view == 'activation':
      if self.lot_id:
        if self.state == False:
            if not self.employee_id:
              serie = self.lot_id.name
              return {
                'warning' : {
                  'title' : ('Validación'),
                  'message' :('La solicitud {} no puede ser utilizada por que no ha sido asignada a ningún A.S'.format(serie)),
                }
              }
    elif self.type_view == 'precontract':
      if self.lot_id:
        
        ### Validar que la solicitud se encuentre en el inventario y que exista la ubicación de contratos
        if self.sale_type == 'physical':
          quant_id = stock_quant_obj.search([('inventory_quantity','>',0),('lot_id','=',self.lot_id.id)])

          location_id = None
          if quant_id:
            location_id = quant_id.location_id

          received_contract = location_obj.search([('contract_location','=',True),('received_location','=',True)],limit=1)

          if not received_contract:
            raise ValidationError(("No se encuentra la ubicación de contratos"))
          
          if location_id and received_contract.id not in location_id.ids:
            raise ValidationError(("la solicitud {} no se encontró en la ubicación de contratos, se encuentra en {}".format(self.lot_id.name, location_id.name_get()[0][1])))
          
        contract = self.search([
          ('partner_name','=',self.partner_name),
          ('partner_fname','=',self.partner_fname),
          ('partner_mname','=',self.partner_mname),
          ('state','=','contract')])
        if contract:
          contract_names = contract.mapped('name')
          return {
            'warning' : {
              'title' : ('Validación'),
              'message' :('Ya existen contratos con este nombre: {}\nContratos: {}'.format(self.full_name,contract_names)),
            }
          }

  ### Crea el árbol de comisiones del contrato
  def create_commision_tree(self, invoice_id=False):
    comission_template_obj = self.env['pabs.comission.template']
    comission_tree_obj = self.env['pabs.comission.tree']
    pricelist_obj = self.env['product.pricelist.item']
    job_obj = self.env['hr.job']

    if self.employee_id and self.name_service:
      
      pricelist_id = pricelist_obj.search([('product_id','=',self.name_service.id)])
      if not pricelist_id:
        raise ValidationError(("No se encontró la tarifa del plan {}".format(self.name_service.name)))
      
      ### Para planes digitales de Cuernavaca se utilizará la plantilla del plan físico.
      # Se buscará la coincidencia de acuerdo a la referencia interna: Fisico = PL-00006, Digital PL-00096
      if 'DIGITAL' in self.name_service.name:
        physical_default_code = self.name_service.default_code.replace('9', '0', 1)
        product_template = self.env['product.template'].search([
          ('company_id', '=', self.company_id.id),
          ('default_code', '=', physical_default_code)
        ])

        if not product_template:
          raise ValidationError('Arbol: No se encontró el producto con referencia interna {}'.format(physical_default_code))

        pricelist_id = pricelist_obj.search([('product_tmpl_id','=', product_template.id)])
        if not pricelist_id:
          raise ValidationError(("Arbol: No se encontró la tarifa del plan físico {}".format(self.product_id.name)))
        
      comission_template_id = comission_template_obj.search([
        ('employee_id','=',self.employee_id.id),
        ('plan_id','=',pricelist_id.id),
        ('comission_amount','>',0)],order="pay_order")
      
      ### Bloque para buen fin (asignar empleado de buen fin como asistente)
      move_line_ids = self.env['stock.move.line'].search([('lot_id','=',self.lot_id.id)])
      
      for movl in move_line_ids:
        if movl.move_id.asistente_social_bf:
          employee_id = self.env['hr.employee'].search([('local_location_id','=',movl.move_id.asistente_social_bf.id)], limit = 1)

          if employee_id:
            comission_template_id = comission_template_obj.search([
              ('employee_id','=',employee_id.id),
              ('plan_id','=',pricelist_id.id),
              ('comission_agent_id','!=',False)],order="pay_order")
            break     
      
      if not comission_template_id:
        raise ValidationError(("El A.S {} no cuenta con un arbol de comisiones".format(self.employee_id.name)))

      ajuste_por_sueldo = 0
      contratoEsSueldo = (self.payment_scheme_id.name == "SUELDO")

      ##### MODIFICACIONES FISCAL 20/09/2021 #####
      monto_acumulado = 0     #Se utiliza para calcular el monto de fideicomiso en una compañia fiscal
      #ultima_prioridad = max(comission_template_id.mapped('pay_order'))

      ### RECORRER TODAS LAS LINEAS DEL DETALLE DE LA PLANTILLA e insertar el registro
      next_pay_order = 0
      for line in comission_template_id:
        next_pay_order = next_pay_order + 1
        monto_comision = line.comission_amount

        if line.job_id.name != "FIDEICOMISO":
          monto_acumulado = monto_acumulado + monto_comision

        if contratoEsSueldo and line.job_id.name == "ASISTENTE SOCIAL":
          ajuste_por_sueldo = monto_comision
          monto_acumulado = monto_acumulado - monto_comision
          monto_comision = 0
        elif contratoEsSueldo and line.job_id.name == "FIDEICOMISO":
          monto_comision = monto_comision + ajuste_por_sueldo

        data = {
          'contract_id' : self.id,
          'pay_order' : next_pay_order,
          'job_id' : line.job_id.id,
          'comission_agent_id' : line.comission_agent_id.id,
          'corresponding_commission' : monto_comision,
          'remaining_commission' : monto_comision,
          'commission_paid' : 0,
          'actual_commission_paid' : 0,
        }

        ### 2024-08-09: se agrega línea extra para comisionistas ('IVA + Cargo' y (comision * 0.16'))
        if self.company_id.apply_taxes and self.company_id.is_iva_a_commission_agent and line.job_id.name not in ('IVA', 'PAPELERIA', 'RECOMENDADO', 'FIDEICOMISO', 'COBRADOR') and line.comission_amount > 0:
          # Buscar cargo
          iva_job = job_obj.search([
            ('company_id', '=', self.company_id.id),
            ('name', '=', "IVA {}".format(line.job_id.name))
          ])
          
          if not iva_job:
            raise ValidationError("{} No se encontró el cargo IVA {}".format(self.name, line.job_id.name))
          
          # Guardar información de linea de comisión y agregar linea de comision de iva
          data = [data]

          iva_monto_comision = monto_comision * 0.16
          monto_acumulado = monto_acumulado + iva_monto_comision

          next_pay_order = next_pay_order + 1
          data.append({
            'contract_id' : self.id,
            'pay_order' : next_pay_order,
            'job_id' : iva_job.id,
            'comission_agent_id' : line.comission_agent_id.id,
            'corresponding_commission' : iva_monto_comision,
            'remaining_commission' : iva_monto_comision,
            'commission_paid' : 0,
            'actual_commission_paid' : 0,
          })
        
        if line.job_id.name == "FIDEICOMISO":
          ### Cálculo de comisión de fideicomiso e iva para empresa fiscal ###
          if self.company_id.apply_taxes:             
            impuesto_IVA = self.env['account.tax'].search([('name','=','IVA'), ('company_id','=', self.company_id.id)]) # Buscar impuesto de IVA
            if not impuesto_IVA:
              raise ValidationError("No se encontró el impuesto con nombre IVA")

            # Buscar puesto IVA
            cargo_iva = self.env['hr.job'].search([('name','=','IVA'), ('company_id','=', self.company_id.id)])
            if not cargo_iva:
              raise ValidationError("No se encontró el puesto de trabajo con nombre IVA")

            # Buscar empleado IVA
            empleado_iva = self.env['hr.employee'].search([('barcode','=','IVA'), ('company_id','=', self.company_id.id)])
            if not empleado_iva:
              raise ValidationError("No se encontró el empleado con código IVA")

            factor_iva = 1 + (impuesto_IVA.amount/100)
            monto_para_iva = round(pricelist_id.fixed_price - round(pricelist_id.fixed_price / factor_iva, 2), 2)

            # Llenar datos de linea de IVA
            linea_iva = {
              'contract_id' : self.id,
              'pay_order' : 0,
              'job_id' : cargo_iva.id,
              'comission_agent_id' : empleado_iva.id,
              'corresponding_commission' : monto_para_iva,
              'remaining_commission' : monto_para_iva,
              'commission_paid' : 0,
              'actual_commission_paid' : 0,
            }

            # Almacenar datos de fideicomiso (En una sola lista se enviará la creación de la linea de fideicomiso y de IVA)
            linea_fideicomiso = data

            # 2024-09-09 Si el iva se maneja como un comisionista
            if self.company_id.is_iva_a_commission_agent:
              linea_iva.update({'pay_order': linea_fideicomiso['pay_order']})
              linea_fideicomiso.update({'pay_order': linea_iva['pay_order'] + 1})

            # Actualizar el monto del fideicomiso
            monto_fideicomiso = round(pricelist_id.fixed_price - monto_acumulado - monto_para_iva ,2)
            linea_fideicomiso.update({'corresponding_commission': monto_fideicomiso, 'remaining_commission': monto_fideicomiso})
            data = []
            data.append(linea_fideicomiso)
            data.append(linea_iva)

            ##### FIN MODIFICACIONES FISCAL 20/09/2021 #####

        comission_tree_obj.create(data)

  #Crea la factura
  def create_invoice(self, previous=False):
    account_obj = self.env['account.move']
    account_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)
    sequence_obj = self.env['ir.sequence']
    pricelist_obj = self.env['product.pricelist.item']
    currency_id = 33

    if previous:
      journal_id = self.env['account.journal'].search([
        ('company_id', '=', previous.company_id.id),
        ('name', '=', 'VENTAS'),
        ('type', '=', 'sale')
      ])

      if not journal_id:
        raise ValidationError("No se encontró el diario VENTAS")

      #Obtener costo del paquete de la tabla de tarifas
      costo = 0
      if previous.name_service:
        pricelist_id = pricelist_obj.search([('product_id','=',previous.name_service.id)], limit=1)
        if pricelist_id:
          costo = pricelist_id.fixed_price
        elif costo == 0:
          raise ValidationError("El paquete tiene asignado un costo 0")
        else:
          raise ValidationError("No se encontró el costo del paquete en la tabla de tarifas")
      else:
          raise ValidationError("El contrato no tiene un paquete asignado")

      data = {
        'date' : previous.invoice_date,
        'commercial_partner_id' : previous.partner_id.id,
        'partner_id' : previous.partner_id.id,
        'ref' : previous.full_name,
        'type' : 'out_invoice',
        'journal_id' : journal_id.id,
        'state' : 'draft',
        'currency_id' : currency_id,
        'invoice_date' : previous.invoice_date,
        'auto_post' : False,
        'contract_id' : previous.id,
        'invoice_user_id' : self.env.user.id,
      }
      invoice_id = account_obj.create(data)
      if invoice_id:
        product_id = previous.name_service
        account_id = product_id.product_tmpl_id.property_account_income_id or product_id.product_tmpl_id.categ_id.property_account_income_categ_id

        if not account_id:
          category = self.env['product.category'].search([
            ('company_id', '=', previous.company_id.id),
            ('name', '=', 'PLANES DE PREVISION')
          ])

          if not category.property_account_income_categ_id:
            raise ValidationError("No se encontró la cuenta de la linea de crédito de la factura: 271.01.001 Planes a previsión por realizar")
          
          account_id = category.property_account_income_categ_id

        factor_iva = 0
        # FISCAL
        if previous.company_id.apply_taxes:
          #Buscar impuesto a agregar
          iva_tax = self.env['account.tax'].search([('name','=','IVA'), ('company_id','=', previous.company_id.id)])
          
          if not iva_tax:
            raise ValidationError("No se encontró el impuesto con nombre IVA")

          #Buscar linea de repartición de impuesto para facturas
          iva_repartition_line = iva_tax.invoice_repartition_line_ids.filtered_domain([
            ('repartition_type','=','tax'), 
            ('invoice_tax_id','=', iva_tax.id), 
            ('company_id','=', previous.company_id.id)
          ])

          if not iva_repartition_line:
            raise ValidationError("No se encontró la repartición de facturas del impuesto {}".format(iva_tax.name))
          if len(iva_repartition_line) > 1:
            raise ValidationError("Se definió mas de una linea (sin incluir la linea base) en la repartición de facturas del impuesto {}".format(iva_tax.name))

          factor_iva = 1 + (iva_tax.amount/100)

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
        }

        # FISCAL
        if previous.company_id.apply_taxes:
          line_data.update({
            'credit' : round(costo / factor_iva, 2),
            'tax_exigible' : True,
            'tax_ids' : [(4, iva_tax.id, 0)]
          })
        account_line_obj.create(line_data)

        if previous.company_id.apply_taxes:
          #Llenar datos para línea de IVA
          iva_data = {
            'move_id' : invoice_id.id,
            'account_id' : iva_repartition_line.account_id.id,
            'quantity' : 1,
            'credit' : round(costo - round( costo / factor_iva, 2), 2),
            'tax_base_amount' : round(costo - round( costo / factor_iva, 2), 2),
            'partner_id' : previous.partner_id.id,
            'amount_currency' : 0,
            'is_rounding_line' : False,
            'exclude_from_invoice_tab' : True,
            'tax_exigible' : False,
            'name' : iva_tax.name,
            'tax_line_id' : iva_tax.id,
            'tax_group_id' : iva_tax.tax_group_id.id,
            'tax_repartition_line_id' : iva_repartition_line.id,
          }

          account_line_obj.create(iva_data)

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
        }
        account_line_obj.create(partner_line_data)
        invoice_id.action_post()

        previous.allow_create = False
        if not previous.partner_id:
          raise ValidationError((
            "No tiene un cliente ligado al contrato"))
        if previous.partner_id:
          partner_id = previous.partner_id
          partner_id.write({'name' : previous.name})
        previous.state = 'contract'
        # Se crea el árbol de comisiones
        previous.create_commision_tree(invoice_id=invoice_id)

        # ************* MODIFICACIÖN PARA REAFILIIACIONES *************************
        # lines_prev = []
        # for line in previous.commission_tree:
        #   lines_prev.append(line.job_id.name + ' -> ' + str(line.corresponding_commission)  + ' / ' + str(line.remaining_commission) + ' / ' + str(line.commission_paid) + ' / ' + str(line.actual_commission_paid))
        
        # Para modificar el árbol de contratos dependiendo de las opciones del tipo de traspaso            
        amount_fide = sum(previous.commission_tree.filtered(lambda x: x.job_id.name in ['FIDEICOMISO']).mapped('corresponding_commission'))
        amount_as = sum(previous.commission_tree.filtered(lambda x: x.job_id.name in ['ASISTENTE SOCIAL']).mapped('corresponding_commission'))
        plus_amount_fide = sum(previous.commission_tree.filtered(lambda x: x.job_id.name not in ['PAPELERIA','FIDEICOMISO','ASISTENTE SOCIAL','IVA']).mapped('corresponding_commission'))
        fide_line_id = previous.commission_tree.filtered(lambda x: x.job_id.name in ['FIDEICOMISO'])
        as_line_id = previous.commission_tree.filtered(lambda x: x.job_id.name in ['ASISTENTE SOCIAL'])
        line_ids = previous.commission_tree.filtered(lambda x: x.job_id.name not in ['PAPELERIA','FIDEICOMISO','IVA'])       
        
        transfer_amount = 0
        # Traspaso sin comisión
        if previous.trasnsfer_type == 'without_commission':        
          # 
          line_ids.corresponding_commission = 0
          line_ids.remaining_commission = 0
          # Comisiones correspondientes
          fide_line_id.corresponding_commission = fide_line_id.remaining_commission = amount_fide + plus_amount_fide + amount_as       
        # Traspaso con comisión de 200 ó 400
        if previous.trasnsfer_type in ('commission_200', 'commission_400'):
          transfer_amount = 0

          if previous.trasnsfer_type == 'commission_200':
            transfer_amount = 200
          elif previous.trasnsfer_type == 'commission_400':
            transfer_amount = 400
          #
          line_ids.corresponding_commission = 0
          line_ids.remaining_commission = 0
          # Comisión correspondientes
          as_line_id.corresponding_commission = as_line_id.remaining_commission = transfer_amount
          fide_line_id.corresponding_commission = fide_line_id.remaining_commission = amount_fide + plus_amount_fide + amount_as - transfer_amount          
        # Traspaso con comisión especificada
        if previous.trasnsfer_type == 'commission_rest':
          #
          if previous.commission_rest_amount < 0:
            raise ValidationError("Especifique un monto mayor a cero en el monto de comisión.")
                    
          transfer_amount = previous.commission_rest_amount                             
          # Comisión correspondientes
          as_line_id.corresponding_commission = as_line_id.remaining_commission = transfer_amount
          fide_line_id.corresponding_commission = fide_line_id.remaining_commission = amount_fide + amount_as - transfer_amount          

        # Modificar linea de IVA asistente social para ajustar al nuevo monto y iva de fideicomiso
        if previous.company_id.apply_taxes and previous.company_id.is_iva_a_commission_agent and previous.trasnsfer_type != 'without':
          # Modificar la línea de IVA ASISTENTE SOCIAL
          iva_as_line = previous.commission_tree.filtered(lambda x: x.job_id.name in ['IVA ASISTENTE SOCIAL'])
          iva_as_line_corresponding_commission = iva_as_line.corresponding_commission

          if not iva_as_line:
            raise ValidationError("Error al modificar árbol con traspaso: No se encontró la rama IVA ASISTENTE SOCIAL")
          iva_as_commission = round(transfer_amount * 0.16, 2)
          iva_as_line.write({'corresponding_commission': iva_as_commission, 'remaining_commission': iva_as_commission})

          # Actualizar el monto de fideicomiso
          if previous.trasnsfer_type == 'commission_rest':
            new_fide_commission = fide_line_id.corresponding_commission + iva_as_line_corresponding_commission - iva_as_commission
            fide_line_id.write({'corresponding_commission': new_fide_commission, 'remaining_commission': new_fide_commission})
          else:
            new_fide_commission = fide_line_id.corresponding_commission - iva_as_commission
            fide_line_id.write({'corresponding_commission': new_fide_commission, 'remaining_commission': new_fide_commission})

        # lines = []
        # for line in previous.commission_tree:
        #   lines.append(line.job_id.name + ' -> ' + str(line.corresponding_commission)  + ' / ' + str(line.remaining_commission) + ' / ' + str(line.commission_paid) + ' / ' + str(line.actual_commission_paid))
        # if previous.trasnsfer_type != 'without':
        #   raise ValidationError(str(previous.excedent) + "\n" + str(lines_prev) + "\n" + str(lines))
        
        # **************************************************************************
        return invoice_id

  def reconcile_all(self, reconcile={}):
    account_move_line_obj = self.env['account.move.line']
    reconcile_model = self.env['account.partial.reconcile']
    if reconcile.get('debit_move_id'):
      if reconcile.get('initial_payment'):
        line = account_move_line_obj.browse(reconcile.get('initial_payment'))
        data = {
          'debit_move_id' : reconcile.get('debit_move_id'),
          'credit_move_id' : reconcile.get('initial_payment'),
          'amount' : abs(line.balance),
        }
        reconcile_model.create(data)
      if reconcile.get('excedent'):
        line = account_move_line_obj.browse(reconcile.get('excedent'))
        data = {
          'debit_move_id' : reconcile.get('debit_move_id'),
          'credit_move_id' : reconcile.get('excedent'),
          'amount' : abs(line.balance)
        }
        reconcile_model.create(data)

      if reconcile.get('pabs'):
        line = account_move_line_obj.browse(reconcile.get('pabs'))
        data = {
          'debit_move_id' : reconcile.get('debit_move_id'),
          'credit_move_id' : reconcile.get('pabs'),
          'amount' : abs(line.balance)
        }
        reconcile_model.create(data)
  
  #
  def update_payments(self):   
    for contract in self:
      # Para cada pago del contrato
      for payment in contract.payment_ids:
        if payment.reference == 'payment' and payment.state != 'cancelled':
          payment.action_draft()
          payment.post()
      # Para cada factura del contrato
      for invoice in contract.refund_ids:
        if invoice.type == 'out_invoice':
          if invoice.invoice_outstanding_credits_debits_widget != 'false':        
            outstandings = json.loads(invoice.invoice_outstanding_credits_debits_widget)
            content = outstandings.get('content')     
            for o in content:
              invoice.js_assign_outstanding_line(o.get('id'))  
    return True

  #Crear contrato y pagos (Papeleria, Excedente y Bono)
  def create_contract(self, vals=False):

    account_obj = self.env['account.move']
    account_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)
    journal_obj = self.env['account.journal']
    sequence_obj = self.env['ir.sequence']
    payment_obj = self.env['account.payment']
    payment_method_obj = self.env['account.payment.method']

    comission_template_obj = self.env['pabs.comission.template']
    pricelist_obj = self.env['product.pricelist.item']

    contract_status = self.env['pabs.contract.status']
    contract_status_reason = self.env['pabs.contract.status.reason']

    try:
      reconcile = {}
      ### Pasando el contrato a activo
      contract_status_id = contract_status.search([
        ('status','=','ACTIVO')],limit=1)
      if contract_status_id:
        self.contract_status_item = contract_status_id.id

      contract_status_reason_id = contract_status_reason.search([
        ('reason','=','ACTIVO')],limit=1)
      
      if contract_status_reason_id:
        self.contract_status_reason = contract_status_reason_id.id

      if vals:
        if vals.get('lot_id'):
          previous = self.search([('lot_id','=',vals['lot_id'])],limit=1)

          #### COMIENZA VALIDACIÓN DE COMISIONES Validar que en la plantilla de comisiones el asistente tenga comisión asignada > $0 #####
          if previous.employee_id and previous.name_service:
            #Obtener el puesto de asistente social
            job_id = self.env['hr.job'].search([('name', '=', 'ASISTENTE SOCIAL'),('company_id','=',previous.company_id.id,)]).id

            #Obtener la lista de precios
            pricelist_id = pricelist_obj.search([('product_id','=',previous.name_service.id)])
            if not pricelist_id:
              raise ValidationError(("No se encontró la tarifa del plan {}".format(previous.product_id.name)))
            
            ### Para planes digitales de Cuernavaca se utilizará la plantilla del plan físico.
            # Se buscará la coincidencia de acuerdo a la referencia interna: Fisico = PL-00006, Digital PL-00096
            if 'DIGITAL' in previous.name_service.name:
              physical_default_code = previous.name_service.default_code.replace('9', '0', 1)
              product_template = self.env['product.template'].search([
                ('company_id', '=', previous.company_id.id),
                ('default_code', '=', physical_default_code)
              ])

              if not product_template:
                raise ValidationError('No se encontró el producto con referencia interna {}'.format(physical_default_code))

              pricelist_id = pricelist_obj.search([('product_tmpl_id','=', product_template.id)])
              if not pricelist_id:
                raise ValidationError(("No se encontró la tarifa del plan físico {}".format(self.product_id.name)))

            #Obtener la plantilla de comisiones
            _logger.warning('empleado: {}\nplan: {}'.format(previous.employee_id.barcode, pricelist_id.product_tmpl_id.name))
            comission_template = comission_template_obj.search([
              ('employee_id', '=', previous.employee_id.id),
              ('plan_id', '=', pricelist_id.id),
              ('job_id', '=', job_id)])

            if not comission_template:
              raise ValidationError("No se encontró la plantilla de comisiones del asistente")

            # Se buscan todos los registros en los que el lot_id corresponda (para saber si es solicitud de Buen fin)
            bf = False
            move_line_ids = self.env['stock.move.line'].search([('lot_id','=',previous.lot_id.id)])
            for movl in move_line_ids:
              # Si se especificó un agente social para el buen fin
              if movl.move_id.asistente_social_bf:    
                bf = True          
                break
            if comission_template.comission_amount <= 0 and not bf:
              raise ValidationError(("El A.S {} tiene asignado ${} en su plantilla de comisiones. Debe asignarle un monto mayor a cero".format(comission_template.comission_agent_id.name, comission_template.comission_amount)))
            
            ### Regresar pricelist_id a valor original
            if 'DIGITAL' in previous.name_service.name:
              pricelist_id = pricelist_obj.search([('product_id','=',previous.name_service.id)])
              
          ### TERMINA VALIDACION COMISIONES
            

          if not previous.payment_scheme_id and not vals.get('payment_scheme_id'):
            raise ValidationError("El contrato no tiene asignado un esquema de pago")

          #Asignar asistente de venta PRODUCCION
          vals['sale_employee_id'] = previous.employee_id
          # Se buscan todos los registros en los que el lot_id corresponda
          move_line_ids = self.env['stock.move.line'].search([('lot_id','=',previous.lot_id.id)])
          for movl in move_line_ids:
            # Si se especificó un agente social para el buen fin
            if movl.move_id.asistente_social_bf:
              # Se busca el empleado y si se encuentra se asigna como Agente de ventas en el contrato
              employee_id = self.env['hr.employee'].search([('local_location_id','=',movl.move_id.asistente_social_bf.id)], limit = 1)
              if employee_id:
                vals['sale_employee_id'] = employee_id
              break

          #Validar fecha de creación
          fecha_creacion = 0
          if vals.get('invoice_date'):
            fecha_creacion = vals.get('invoice_date')
          else:
            fecha_creacion = previous.invoice_date
          self.validate_date(str(fecha_creacion))

          # Se busca el cobrador NINGUNO por barcode
          ning_id = self.env['hr.employee'].search([('barcode','=','NING'),('company_id','=',previous.company_id.id)])
          if not ning_id:
            raise ValidationError(("No se puede encontrar el cobrador NINGUNO para asignar al pre-contrato."))
          
          if not previous.debt_collector:
            vals['debt_collector'] = ning_id.id

          #Actualizar campos asignados hasta el momento
          previous.write(vals)

          invoice_id = self.create_invoice(previous)

          # **************************** BONO PARA ASISTENTE ***********************
          # Si no es reafiliación y toma comisión no es mayor que 0 y la compañia usa bono de AS
          if not previous.reaffiliation and previous.toma_comision <= 0 and previous.company_id.bonus_as:
            # Se busca el puesto BONO ASSITENTE
            job_bono_as_id = self.env['hr.job'].search([('name', '=', 'BONO ASISTENTE'),('company_id','=',previous.company_id.id,)])
            if job_bono_as_id:
                # Se busca el bono del AS
                bono_as_ids = self.env['pabs.bonus.as'].search([('plan_id','=',previous.name_service.id)], order="min_value")
                bono = 0
                for bon_rec in bono_as_ids:
                  if previous.initial_investment >= bon_rec.min_value and previous.initial_investment <= bon_rec.max_value:
                    bono = bon_rec.bonus
                # Si le corresponde bono
                if bono:
                  # Se recorre el árbol para determinar el punto de insercción
                  order = 0
                  comission_agent_id = previous.sale_employee_id.id
                  for nodo in previous.commission_tree:
                    if nodo.job_id.name == 'PAPELERIA':
                      order = nodo.pay_order
                    if nodo.job_id.name == 'RECOMENDADO':
                      order = nodo.pay_order  
                    if nodo.job_id.name == 'ASISTENTE SOCIAL':
                      order = nodo.pay_order
                      break
                  #                                    
                  if order == 0:
                    raise ValidationError("No se puede determinar un orden para el BONO AS")  
                
                  # Se actualiza el pay_order a partir del punto de insercción
                  update = False            
                  for nodo in previous.commission_tree:
                    if update:
                      nodo.pay_order += 1
                    elif nodo.pay_order == order:
                      update = True
                  # Se inserta el registro en el árbol
                  valores = {
                    'pay_order':order + 1,
                    'job_id': job_bono_as_id.id,
                    'comission_agent_id': comission_agent_id,
                    'corresponding_commission': bono,
                    'remaining_commission': bono,
                    'commission_paid': 0,
                    'actual_commission_paid': 0,
                    'contract_id': previous.id
                  }
                  self.env['pabs.comission.tree'].create(valores)
            else:
              raise ValidationError("No existe el puesto BONO ASISTENTE")
            pass
          # ************************************************************************

          account_id = invoice_id.partner_id.property_account_receivable_id.id

          journal_id = self.env['account.journal'].search([
            ('company_id', '=', previous.company_id.id),
            ('name', '=', 'VENTAS'),
            ('type', '=', 'sale')
          ])

          if not journal_id:
            raise ValidationError("No se encontró el diario VENTAS")
          
          currency_id = 33

          for line in invoice_id.line_ids:
            if line.debit > 0:
              reconcile.update({'debit_move_id' : line.id})     

          #Buscar diario de efectivo
          cash_journal_id = journal_obj.search([('company_id','=', previous.company_id.id), ('type','=','cash'), ('name','=','EFECTIVO')],limit=1)
          if not cash_journal_id:
            raise ValidationError("No se encontró el diario EFECTIVO")

          #Buscar método de pago
          payment_method_id = payment_method_obj.search([('payment_type','=','inbound'),('code','=','manual')],limit=1)
          if not payment_method_id:
            raise ValidationError("No se encontró el método de pago, favor de comunicarse con sistemas")

          ### CREANDO PAGO POR INVERSIÓN INICIAL
          if previous.stationery:
            payment_data = {
              'payment_reference' : 'Inversión inicial',
              'reference' : 'stationary',
              'way_to_pay' : 'cash',
              'communication' : 'Inversión inicial',
              'payment_type' : 'inbound',
              'partner_type' : 'customer',
              'contract' : previous.id,
              'partner_id' : previous.partner_id.id,
              'amount' : previous.stationery,
              'currency_id' : currency_id,
              'payment_date' : previous.invoice_date,
              'journal_id' : cash_journal_id.id,
              'payment_method_id' : payment_method_id.id,
            }
            initial_payment_id = payment_obj.create(payment_data)
            initial_payment_id.with_context(stationery=True).post()
            
            if initial_payment_id.move_line_ids:
              for obj in initial_payment_id.move_line_ids:
                if obj.credit > 0:
                  reconcile.update({
                    'initial_payment' : obj.id})

          ### CREANDO PAGO POR EXCEDENTE
          if previous.excedent:
            excedent_data = {
              'payment_reference' : 'Excedente Inversión Inicial',
              'reference' : 'surplus',
              'way_to_pay' : 'cash',
              'communication' : 'Excedente Inversión Inicial',
              'payment_type' : 'inbound',
              'partner_type' : 'customer',
              'contract' : previous.id,
              'partner_id' : previous.partner_id.id,
              'amount' : previous.excedent,
              'currency_id' : currency_id,
              'payment_date' : previous.invoice_date,
              'journal_id' : cash_journal_id.id,
              'payment_method_id' : payment_method_id.id,
            }
            excedent_payment_id = payment_obj.create(excedent_data)
            excedent_payment_id.with_context(excedent=True).post()
            if excedent_payment_id.move_line_ids:
              for line2 in excedent_payment_id.move_line_ids:
                if line2.credit > 0:
                  reconcile.update({
                    'excedent' : line2.id})

          ### NOTA DE CREDITO POR BONO PABS
          _logger.warning("El bono por inversión inicial es: {}".format(previous.investment_bond))
          if previous.investment_bond > 0:

            # FISCAL
            if previous.company_id.apply_taxes:
              #Buscar impuesto a agregar
              iva_tax = self.env['account.tax'].search([('name','=','IVA'), ('company_id','=', previous.company_id.id)])
              
              if not iva_tax:
                raise ValidationError("No se encontró el impuesto con nombre IVA")

              #Buscar linea de repartición de impuesto para facturas
              iva_repartition_line = iva_tax.refund_repartition_line_ids.filtered_domain([
                ('repartition_type','=','tax'), 
                ('refund_tax_id','=', iva_tax.id), 
                ('company_id','=', previous.company_id.id)
              ])

              if not iva_repartition_line:
                raise ValidationError("No se encontró la repartición de facturas rectificativas del impuesto {}".format(iva_tax.name))
              if len(iva_repartition_line) > 1:
                raise ValidationError("Se definió mas de una linea (sin incluir la linea base) en la repartición de facturas rectificativas del impuesto {}".format(iva_tax.name))

            #Encabezado
            refund_data = {
              'date' : previous.invoice_date,
              'commercial_partner_id' : previous.partner_id.id,
              'partner_id' : previous.partner_id.id,
              'ref' : 'Bono por inversión inicial',
              'type' : 'out_refund',
              'journal_id' : journal_id.id,
              'state' : 'draft',
              'currency_id' : currency_id,
              'invoice_date' : previous.invoice_date,
              'auto_post' : False,
              'contract_id' : previous.id,
              'invoice_user_id' : self.env.user.id,
              'reversed_entry_id' : invoice_id.id,
            }
            refund_id = account_obj.create(refund_data)

            if refund_id:
              # Buscar producto Bono por inversión inicial
              product_id = self.env['product.template'].search([('company_id','=',previous.company_id.id),('name','=','BONO POR INVERSION INICIAL')])
              if not product_id:
                raise ValidationError("No se encontró el producto BONO POR INVERSION INICIAL")

              product_product = self.env['product.product'].search([('product_tmpl_id', '=', product_id.id)])
              if not product_product:
                raise ValidationError("Problema el producto BONO POR INVERSION INICIAL: No se encontró la relación product_template({}) en la tabla product_product".format(product_id.id))

              account_id = product_id.property_account_income_id or product_id.categ_id.property_account_income_categ_id
              if not account_id:
                raise ValidationError("No se encontró la cuenta en los campos product_id.property_account_income_id o product_id.categ_id.property_account_income_categ_id")

              # Llenar datos de Linea principal de débito
              line_data = {
                'move_id' : refund_id.id,
                'account_id' : account_id.id,
                'quantity' : 1,
                'price_unit' : previous.investment_bond,
                'debit' : previous.investment_bond,
                'product_uom_id' : product_id.uom_id.id,
                'partner_id' : previous.partner_id.id,
                'amount_currency' : 0,
                'product_id' : product_product.id,
                'is_rounding_line' : False,
                'exclude_from_invoice_tab' : False,
                'name' : product_id.description_sale or product_id.name,
              }

              # FISCAL
              if previous.company_id.apply_taxes:
                line_data.update({
                  'tax_exigible' : True,
                  'tax_ids' : [(4, iva_tax.id, 0)],
                  'debit' : round(previous.investment_bond / (1 + iva_tax.amount/100), 2),
                })
              line = account_line_obj.create(line_data)

              # FISCAL
              # Llenar datos para línea de IVA
              if previous.company_id.apply_taxes:
                iva_data = {
                  'move_id' : refund_id.id,
                  'account_id' : iva_repartition_line.account_id.id,
                  'quantity' : 1,
                  'price_unit' : previous.investment_bond,
                  'debit' : round(previous.investment_bond - round( (previous.investment_bond / (1 + iva_tax.amount/100)), 2), 2),
                  'tax_base_amount' : round(previous.investment_bond - round( (previous.investment_bond / (1 + iva_tax.amount/100)), 2), 2),
                  'product_uom_id' : product_id.uom_id.id,
                  'partner_id' : previous.partner_id.id,
                  'amount_currency' : 0,
                  'product_id' : product_product.id,
                  'is_rounding_line' : False,
                  'exclude_from_invoice_tab' : True,
                  'name' : iva_tax.name,
                  'tax_line_id' : iva_tax.id,
                  'tax_group_id' : iva_tax.tax_group_id.id,
                  'tax_repartition_line_id' : iva_repartition_line.id,
                }

                line = account_line_obj.create(iva_data)

              ### CONTRAPARTIDA DEL DOCUMENTO #Linea de crédito
              partner_line_data = {
                'move_id' : refund_id.id,
                'account_id' : refund_id.partner_id.property_account_receivable_id.id,
                'quantity' : 1,
                'date_maturity' : previous.invoice_date,
                'amount_currency' : 0,
                'partner_id' : previous.partner_id.id,
                'tax_exigible' : False,
                'is_rounding_line' : False,
                'exclude_from_invoice_tab' : True,
                'credit' : previous.investment_bond,
              }
              line = account_line_obj.create(partner_line_data)

              ### VALIDANDO NOTA DE CRÉDITO
              reconcile.update({'pabs' : line.id})
              refund_id.with_context(investment_bond=True).action_post()

        _logger.info("Se creó la factura del contrato")
        if previous.name == 'Nuevo Contrato' or 'PCD' in previous.name:
          contract_name = pricelist_id.sequence_id._next()
          previous.name = contract_name
        else:
          contract_name = previous.name
        previous.partner_id.write({'name' : contract_name, 'company_id' : previous.company_id.id})
        self.reconcile_all(reconcile)

        ### Proceso extra de Afiliacion electrónica (Crear poliza de caja transito) ###
        if previous.sale_type in ('digital', 'digital_reafiliation'):
          econ_obj = self.env['pabs.electronic.contract']

          ### Buscar registro de corte
          corte = self.env['pabs.econtract.move'].search([
            ('id_contrato', '=', previous.id)
          ])

          if not corte:
            raise ValidationError("No se encontró el registro de corte")

          ### Validar cuentas para creación de póliza
          info_de_cuentas = {}
          info_de_cuentas = econ_obj.ValidarCuentas(previous.company_id.id, info_de_cuentas)

          if not info_de_cuentas:
            raise ValidationError("No se encontraron las cuentas para la poliza de transito")
          
          ### Generar póliza de transito
          id_poliza_transito = econ_obj.CrearPoliza(previous.company_id.id, previous.invoice_date, previous.name, previous.stationery, previous.initial_investment - previous.stationery, previous.sale_employee_id.warehouse_id.analytic_account_id.id, info_de_cuentas)

          ### Ligar póliza al registro de cierre
          corte.write({'id_poliza_caja_transito': id_poliza_transito})

    except Exception as e:
      self._cr.rollback()
      raise ValidationError(e)

  #################################################
  ### OVERWRITE DEL METODO WRITE
  #################################################
  def write(self, vals):
    ### Al cambiar el estatus o el motivo actualizar el campo de ultima fecha de estatus
    if vals.get('contract_status_item') or vals.get('contract_status_reason'):
      self.date_of_last_status = datetime.today()

    ##### Al cambiar estatus #####
    if vals.get('contract_status_item'):
      lista_de_estatus = self.env['pabs.contract.status'].search([])
      nuevo_estatus = lista_de_estatus.filtered(lambda x: x.id == vals['contract_status_item'])

      ### Si se quita la suspensión temporal quitar la fecha de reactivación
      if self.contract_status_item.status and "TEMPORAL" not in nuevo_estatus.status and "TEMPORAL" in self.contract_status_item.status:
        self.reactivation_date = None

      ### Actualizar detalle de servicio si se pasó a estatus REALIZADO
      if nuevo_estatus.status == "REALIZADO":
        self.service_detail = 'realized'

    ### Actualizar detalle de servicio si se pasó a motivo REALIZADO POR COBRAR
    if vals.get('contract_status_reason'):
      motivo_realizado_por_cobrar = self.env['pabs.contract.status.reason'].search([('reason', '=', 'REALIZADO POR COBRAR')])

      if not motivo_realizado_por_cobrar:
        raise ValidationError("No existe el motivo REALIZADO POR COBRAR")
      
      if vals['contract_status_reason'] == motivo_realizado_por_cobrar.id:
        self.service_detail = 'made_receivable'

    full_name = ''
    if vals.get('partner_name') or self.partner_name:
      full_name = full_name + (vals.get('partner_name') or self.partner_name)
    if vals.get('partner_fname') or self.partner_fname:
      full_name = full_name + ' ' + (vals.get('partner_fname') or self.partner_fname)
    if vals.get('partner_mname') or self.partner_mname:
      full_name = full_name + ' ' + (vals.get('partner_mname') or self.partner_mname)
    vals['full_name'] = full_name    
    res = super(PABSContracts, self).write(vals)
    ### Si se modificó el campo del cobrador
    if vals.get('debt_collector'):
      if self.env['hr.employee'].browse(vals.get('debt_collector')).barcode != 'NING':
        self.assign_collector_date = fields.Date.today() 
    return res 

  #Agregar comentario como nota interna
  def save_comment(self):
    if len(self.new_comment.strip()) == 0:
      raise ValidationError("No se ha escrito un comentario")

    val = {
      'user_id' : self.env.user.id,
      'date' : fields.Datetime.now(),
      'comment' : self.new_comment,
      'contract_id' : self.id,
    }

    self.env['pabs.contract.comments'].create(val)

    values = {
      'body': "<p>" + self.new_comment + "</p>",
      'model': self._name,
      'message_type': 'comment',
      'no_auto_thread': False,
      'res_id': self.id
    }
    
    self.env['mail.message'].create(values)
    self.new_comment = ""

   # Calcular fecha de vencimiento
  @api.depends('payment_amount', 'way_to_payment', 'date_first_payment')
  def calcular_vencimiento_y_atraso(self):
    for rec in self:
      if rec.state == 'contract':
        #Obtener información del contrato
        monto_pago = rec.payment_amount
        forma_pago = rec.way_to_payment
        fecha_primer_abono = rec.date_first_payment

        if fecha_primer_abono == False or forma_pago == False or monto_pago == False:
          rec.contract_expires = None
          rec.late_amount = 0
          return

        #Obtener cantidad entregada en bono de inversión inicial
        bonos_por_inversion = self.env['account.move'].search([
          ('partner_id','=',rec.partner_id.id),
          ('type','=', 'out_refund'),
          ('ref','=', 'Bono por inversión inicial')
        ])
        total_bono = sum(reg.amount_total for reg in bonos_por_inversion) or 0

        #Cantidad a programar (no se toma en cuenta recibos de enganche: inversion, excedente y bono)
        saldo_a_plazos = rec.product_price - rec.initial_investment - total_bono
        abonado = rec.paid_balance - rec.initial_investment - total_bono

        lista_pagos = []
        monto_atrasado = 0

        #
        ##
        ### Proceso exclusivo para primer pago #####
        indice = 1

        #Calcular importe a pagar
        importe_a_pagar = 0

        if saldo_a_plazos >= monto_pago:
          importe_a_pagar = monto_pago
        else:
          importe_a_pagar = saldo_a_plazos

        #Calcular importe restante
        importe_restante = 0
        
        if abonado >= importe_a_pagar:
          importe_restante = 0
          abonado = abonado - importe_a_pagar
        else:
          importe_restante = importe_a_pagar - abonado
          abonado = 0

        #Calcular importe_pagado
        importe_pagado = importe_a_pagar - importe_restante

        #Sumar al monto atrasado
        if fecha_primer_abono < fields.Date.today():
          monto_atrasado = monto_atrasado + importe_restante

        pago = {
          "numero_de_pago": indice, 
          "fecha_pago": fecha_primer_abono,
          "importe_a_pagar": importe_a_pagar,
          "importe_restante": importe_restante,
          "importe_pagado": importe_pagado,
          "saldo_restante": saldo_a_plazos,
          "monto_atrasado": monto_atrasado
        }

        lista_pagos.append(pago)

        saldo_a_plazos = saldo_a_plazos - importe_a_pagar
        indice = indice + 1

        fecha_pago_anterior = fecha_primer_abono
        
        #
        ##
        ### Proceso exclusivo para los demas pagos #####
        while saldo_a_plazos > 0:

          #Calcular importe a pagar
          importe_a_pagar = 0

          if saldo_a_plazos >= monto_pago:
            importe_a_pagar = monto_pago
          else:
            importe_a_pagar = saldo_a_plazos

          #Calcular importe restante
          importe_restante = 0
          
          if abonado >= importe_a_pagar:
            importe_restante = 0
            abonado = abonado - importe_a_pagar
          else:
            importe_restante = importe_a_pagar - abonado
            abonado = 0

          #Calcular importe_pagado
          importe_pagado = importe_a_pagar - importe_restante

          #Calcular siguiente fecha
          fecha_pago = ""
          if forma_pago == 'weekly':
            fecha_pago = fecha_pago_anterior + timedelta(days=7)
            fecha_pago_anterior = fecha_pago
          elif forma_pago == 'biweekly':
            pass
            fecha_pago = rec.add_one_biweek(fecha_pago_anterior, fecha_primer_abono.day)
            fecha_pago_anterior = fecha_pago
          elif forma_pago == 'monthly':
            fecha_pago = rec.add_one_month(fecha_pago_anterior, fecha_primer_abono.day)
            fecha_pago_anterior = fecha_pago

          #Sumar al monto atrasado
          if fecha_pago < fields.Date.today():
            monto_atrasado = monto_atrasado + importe_restante

          pago = {
            "numero_de_pago": indice, 
            "fecha_pago": fecha_pago,
            "importe_a_pagar": importe_a_pagar,
            "importe_restante": importe_restante,
            "importe_pagado": importe_pagado,
            "saldo_restante": saldo_a_plazos,
            "monto_atrasado": monto_atrasado
          }

          lista_pagos.append(pago)
          
          saldo_a_plazos = saldo_a_plazos - importe_a_pagar
          indice = indice + 1

        #retornar valores de actualización
        fecha_vencimiento = fecha_pago_anterior.strftime("%Y-%m-%d")
        
        #Actualizaciones a los campos
        rec.contract_expires = fecha_vencimiento
        #rec.late_amount = monto_atrasado
      else:
        rec.contract_expires = fields.Date.today()

  @api.depends('payment_amount', 'way_to_payment', 'date_first_payment')
  def calculo_rapido_del_monto_atrasado(self):
    # ('weekly','Semanal'),
    # ('biweekly','Quincenal'),
    # ('monthly', 'Mensual')]
    for rec in self:
      if rec.state == 'contract':
        
        if rec.balance <= 0:
          rec.late_amount = 0
          return

        #Obtener cantidad entregada en bono de inversión inicial
        total_bono = sum(rec.refund_ids.filtered(lambda r: r.type == 'out_refund' and r.state == 'posted').mapped('amount_total'))

        #Obtener cantidad por traspasos
        traspasos = rec.transfer_balance_ids.filtered(lambda x: x.move_id.state == 'posted')
        total_traspasos = 0
        if len(traspasos) > 0:
            total_traspasos = sum(traspasos.mapped('debit'))

        #Obtener monto abonado menos bonos y traspasos
        abonado = rec.paid_balance - rec.initial_investment - total_bono - total_traspasos
        monto_atrasado = 0

        fecha_hoy = date.today()
        fecha_primer_abono = rec.date_first_payment

        if fecha_hoy < fecha_primer_abono:
          rec.late_amount = 0
          return
          
        ### Forma de pago: SEMANAL
        if rec.way_to_payment == 'weekly':
          dias_transcurridos = fecha_hoy - fecha_primer_abono
          semanas = 0

          if dias_transcurridos.days % 7 != 0:
            semanas = math.ceil(dias_transcurridos.days/7)
          else:
            semanas = dias_transcurridos.days/7

          estimado_abonado = semanas * rec.payment_amount  
          monto_atrasado = estimado_abonado - abonado

        ### Forma de pago: QUINCENAL
        elif rec.way_to_payment == 'biweekly':
          meses = (fecha_hoy.year - fecha_primer_abono.year) * 12 + (fecha_hoy.month - fecha_primer_abono.month)
          quincenas = meses * 2

          periodo_quincena = 0 #Utilizado en excel de donde se originó este proceso
          dia_segunda_quincena = 0

          #La primer quincena esta antes del dia 14
          if fecha_primer_abono.day <= 14:
            periodo_quincena = 1
            dia_segunda_quincena = fecha_primer_abono.day + 14

            if fecha_hoy.day >= dia_segunda_quincena:
              quincenas = quincenas + 2
            else:
              quincenas = quincenas + 1
          #La primer quincena esta después del dia 14
          else:
            periodo_quincena = 2
            dia_segunda_quincena = fecha_primer_abono.day - 14
            if fecha_hoy.day < fecha_primer_abono.day:
              pass #No es necesario cambiar el número de quincenas
            else:
              quincenas = quincenas + 1

          estimado_abonado = quincenas * rec.payment_amount  
          monto_atrasado = estimado_abonado - abonado

        ### Forma de pago: MENSUAL
        elif rec.way_to_payment == 'monthly':
          meses = (fecha_hoy.year - fecha_primer_abono.year) * 12 + (fecha_hoy.month - fecha_primer_abono.month)

          if fecha_hoy.day >= fecha_primer_abono.day:
            meses = meses + 1

          estimado_abonado = meses * rec.payment_amount  
          monto_atrasado = estimado_abonado - abonado
        
        ### Otra forma de pago???
        else:
          monto_atrasado = 99999

        ###Asignar monto atrasado
        if monto_atrasado < 0:
          monto_atrasado = 0
        elif monto_atrasado > rec.balance:
          monto_atrasado = rec.balance
        rec.late_amount = monto_atrasado
      else:
        rec.late_amount = 0

  def add_one_month(self, orig_date, dia_primer_abono):

    ### Validar cambio de año ###
    # advance year and month by one month
    new_year = orig_date.year
    new_month = orig_date.month + 1
    # note: in datetime.date, months go from 1 to 12
    if new_month > 12:
        new_year = new_year + 1
        new_month = new_month - 12

    last_day_of_month = calendar.monthrange(new_year, new_month)[1]
    #new_day = min(orig_date.day, last_day_of_month) #Linea original
    
    new_day = min(dia_primer_abono, last_day_of_month) #Para mantener el día mas próximo al día del primer abono

    return orig_date.replace(year=new_year, month=new_month, day=new_day)

  def add_one_biweek(self, orig_date, dia_primer_abono):
    #Si el dia es menor o igual a 14 se calculará en el mes actual (ejemplo si la quincena uno cae en dia 2, la quincena dos caerá en dia 16)
    if orig_date.day <= 14:
      new_year = orig_date.year
      new_month = orig_date.month
      new_day = orig_date.day + 14

      if dia_primer_abono >= 28:
        last_day_of_month = calendar.monthrange(new_year, new_month)[1]
        new_day = min(dia_primer_abono, last_day_of_month) #Para mantener el día mas próximo al día del primer abono

      return orig_date.replace(year=new_year, month=new_month, day=new_day)
    
    #Si el día es mayor o igual a 15 se calculará con el mes siguiente (ejemplo si la quincena uno cae en dia 31, la quincena dos caerá en dia 14)
    if orig_date.day >= 15:
      
      ### Validar cambio de año ###
      # advance year and month by one month
      new_year = orig_date.year
      new_month = orig_date.month + 1
    
      # note: in datetime.date, months go from 1 to 12
      if new_month > 12:
          new_year = new_year + 1
          new_month = new_month - 12

      if orig_date.day >= 28:
        new_day = 14
      else:
        new_day = orig_date.day - 14

      return orig_date.replace(year=new_year, month=new_month, day=new_day)

  #Calcular dias sin abonar
  def calcular_dias_sin_abonar(self):
    for rec in self:
      if rec.state == 'contract':
        days = 0
        today = fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General')).date()
        #Obtener registro del último pago de cobranza
        ultimo_abono_cobranza = self.payment_ids.filtered(lambda r: r.state == 'posted' and r.reference == 'payment')
        if ultimo_abono_cobranza:
          ultimo_abono_cobranza = ultimo_abono_cobranza.sorted(key=lambda r: r.date_receipt if r.date_receipt else r.payment_date )
          days = (today - ultimo_abono_cobranza[-1].date_receipt).days
          rec.days_without_payment = days
          return days
        if rec.date_first_payment:
          if rec.date_first_payment < today:
            days = (today - rec.date_first_payment).days
            rec.days_without_payment = days
            return days
        rec.days_without_payment = days
        return days
      else:
        rec.days_without_payment = 0
        return 0

  def create_contracts(self, cantidad):
    contract_obj = self.env['pabs.contract']
    contract_ids = contract_obj.search([('state','=','precontract')], limit=cantidad, order="name")
    _logger.warning('Contratos a crear: {}'.format(len(contract_ids)))
    for contract_id in contract_ids:
      lot_id = contract_id.lot_id.id
      _logger.warning('Siguiente solicitud: {}'.format(lot_id))
      self.create_contract(vals={'lot_id' : lot_id})

  ### Función utilizada en un sincronizador de eCobro para pasar un contrato a Suspensión temporal
  @api.model
  def Cambiar_estatus(self, company_id, contrato, motivo, fecha_reactivacion, comentario):
    try:
      ### Validar valores de entrada
      if not company_id or not contrato or not motivo or not fecha_reactivacion:
        return {'correcto': 0, 'msj': 'No se enviaron todos los parámetros'}
      
      try:
        fecha = datetime.strptime(fecha_reactivacion, '%Y-%m-%d').date()

        if fecha < datetime.today().date():
          return {'correcto': 0, 'msj': 'La fecha de reactivación no puede ser menor al dia de hoy'.format(fecha_reactivacion)}
      except Exception as ex:
        return {'correcto': 0, 'msj': 'La fecha {} no es válida: {}'.format(fecha_reactivacion, ex)}

      if len(comentario) > 1000:
        comentario = comentario[0:999]

      ### Buscar valores de Odoo
      estatus_susp = self.env['pabs.contract.status'].search([('status', '=', 'SUSP. TEMPORAL')])
      if not estatus_susp:
        return {'correcto': 0, 'msj': 'No se encontró el estatus SUSP. TEMPORAL'}
      
      motivo_susp = self.env['pabs.contract.status.reason'].search([
        ('status_id', '=', estatus_susp.id),
        ('reason', '=', motivo)
      ])
      
      if not motivo_susp:
        return {'correcto': 0, 'msj': 'No se encontró el motivo {}'.format(motivo)}
      
      estatus_validos = self.env['pabs.contract.status'].search([('status', 'in', ('ACTIVO', 'SUSP. TEMPORAL'))])

      con = self.search([
        ('state', '=', 'contract'),
        ('company_id', '=', company_id),
        ('name', '=', contrato)
      ])

      if not con:
        return {'correcto': 0, 'msj': 'No se encontró el contrato {}'.format(contrato)}
      
      if len(con) > 1:
        return {'correcto': 0, 'msj': 'Existe mas de un contrato'.format(contrato)}
      
      if con.contract_status_item.id not in estatus_validos.ids:
        return {'correcto': 0, 'msj': 'El contrato no está actualmente en estatus ACTIVO o SUSP. TEMPORAL'.format(contrato)}
      
      ### Actualizar datos en base
      con.write({
        'contract_status_item': estatus_susp.id,
        'contract_status_reason': motivo_susp.id,
        'reactivation_date': fecha_reactivacion
      })

      val = {
        'user_id' : self.env.user.id,
        'date' : fields.Datetime.now(),
        'comment' : comentario,
        'contract_id' : con.id
      }

      self.env['pabs.contract.comments'].create(val)

      values = {
        'body': "<p>" + comentario + "</p>",
        'model': 'pabs.contract',
        'message_type': 'comment',
        'no_auto_thread': False,
        'res_id': con.id
      }
      
      self.env['mail.message'].create(values)

      _logger.info("Suspension temporal generada: {}".format(contrato))
      return {'correcto': 1, 'msj': ''}
    
    except Exception as ex:
      return {'correcto': 0, 'msj': 'Error de Odoo {}'.format(ex)}
    
  @api.model
  def update_contract_data(self, company_id, contract_name, dict):
    con = self.search([
      ('company_id', '=', company_id),
      ('name', '=', contract_name)
    ])

    if not con:
      return {"status": 0, "msj": "No se encontró el contrato {}".format(contract_name)}
    
    try:
      update_data = {}
      result = []  #1 = correcto, 0 = error

      ### Fachada domicilio
      if 'url_fachada_domicilio' in dict.keys():
        if str(dict['url_fachada_domicilio']) != con.url_fachada_domicilio:
          update_data.update({'url_fachada_domicilio': str(dict['url_fachada_domicilio'])})
          result.append({'status': 1, 'msj': 'actualizado'})
        else:
          result.append({'status': 1, 'msj': 'mismos datos'})
      ### Estatus Verificacion suspendido por cancelar
      elif 'vsxc' in dict.keys():
        status_vsxc = self.env['pabs.contract.status'].search([
          ('status', '=', 'VERIFICACION SC')
        ])
        
        if not status_vsxc:
          result.append({'status': 0, 'msj': 'No se encontró el estatus VERIFICACION SC'})
        else:
          if status_vsxc.id == con.contract_status_item.id:
            result.append({'status': 1, 'msj': 'mismos datos'})
          else:
            if con.contract_status_item.status in ['CANCELADO','PAGADO','REALIZADO','REALIZADO PERCAPITA', 'SUSP. PARA CANCELAR', 'VERIFICACION SC', 'TRASPASO']:
              result.append({'status': 0, 'msj': 'Estatus no permitido: {}'.format(con.contract_status_item.status)})
            else:
              reason_vsxc = self.env['pabs.contract.status.reason'].search([
                ('status_id', '=', status_vsxc.id),
                ('reason', '=', str(dict['vsxc']))
              ])

              if not reason_vsxc:
                reason_vsxc = self.env['pabs.contract.status.reason'].search([
                  ('status_id', '=', status_vsxc.id)
                ], limit=1)
              
              update_data.update({'contract_status_item': status_vsxc.id, 'contract_status_reason': reason_vsxc.id})
              result.append({'status': 1, 'msj': 'actualizado'})

              comentario = ""
              if 'comentario' in dict.keys():
                comentario = dict['comentario']

              if comentario:
                val = {
                  'user_id' : self.env.user.id,
                  'date' : fields.Datetime.now(),
                  'comment' : comentario,
                  'contract_id' : con.id
                }

                self.env['pabs.contract.comments'].create(val)

                values = {
                  'body': "<p>" + comentario + "</p>",
                  'model': 'pabs.contract',
                  'message_type': 'comment',
                  'no_auto_thread': False,
                  'res_id': con.id
                }
                
                self.env['mail.message'].create(values)

      if update_data:
        con.write(update_data)
        return result
      elif result:
        return result
      else:
        return {'status': 0, 'msj': 'No se actualizó ningún dato'}
      
    except Exception as ex:
      return {'status': 0, 'msj': '{}'.format(ex)}