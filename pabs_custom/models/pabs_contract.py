# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date
import logging
import calendar
from dateutil import tz
from odoo.addons.pabs_custom.externals.calcule import CalculeRFC, CalculeCURP

import math

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

class PABSContracts(models.Model):
  _name = 'pabs.contract'
  _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
  _description = 'Pre-Contrato'

#Datos del registro
  state = fields.Selection(selection=STATES,string='state',tracking=True,)

#Datos del pre_contrato
  lot_id = fields.Many2one(comodel_name='stock.production.lot', string='No. de Solicitud', tracking=True, required=True)

  type_view = fields.Selection(selection=TYPE, string='Tipo de vista')
  agent_id = fields.Char(string='Agente', required=True,tracking=True,)#, default=lambda self: self.env.user.name)
  captured = fields.Boolean(string='Capturado previamente')
  activation_code = fields.Char(string='Número de activación', tracking=True)
  street_toll = fields.Char(string ='Calle',tracking=True,)
  agent_id = fields.Char(string='Agente', required=True, default=lambda self: self.env.user.name,tracking=True,)
  name = fields.Char(string='Número de Contrato', default='Nuevo Contrato', tracking=True)
  activation_code = fields.Char(string='Número de activación', tracking=True)
  employee_id = fields.Many2one(comodel_name='hr.employee', related="lot_id.employee_id", tracking=True, string='Asistente activación')
  salary_scheme = fields.Boolean(string='Esquema de pago del empleado', related="employee_id.payment_scheme.allow_all",tracking=True)
  product_price = fields.Float(string='Costo', compute="calc_price",tracking=True)
  payment_scheme_id = fields.Many2one(comodel_name='pabs.payment.scheme', tracking=True, default=lambda self : self.env['pabs.payment.scheme'].search([],limit=1).id, string='Esquema de pago')
  contract_status = fields.Selection(selection=STATUS, string='Estatus de contrato', tracking=True)
  lot_id = fields.Many2one(comodel_name='stock.production.lot', string='No. de Solicitud', tracking=True, required=True)
  full_name = fields.Char(string="Nombre completo", tracking=True, compute="calc_full_name",store=True, index=True)
  partner_name = fields.Char(string='Nombre', required=True)
  partner_fname = fields.Char(string='Apellido paterno', required=True)
  partner_mname = fields.Char(string='Apellido materno', required=True)
  birthdate = fields.Date(string='Fecha de nacimiento', tracking=True, default=fields.Date.today(), required=True)
  phone = fields.Char(string='Teléfono', tracking=True, required=True)
  street = fields.Char(tracking=True, string='Calle / Número')
  name_service = fields.Many2one(comodel_name = 'product.product', tracking=True, related="lot_id.product_id", string='Servicio')
  street_toll = fields.Char(tracking=True, string = 'Calle')
  between_streets_toll = fields.Char(tracking=True, string ='Entre calles')
  vat = fields.Char(tracking=True, string='RFC', compute='_calc_rfc')
  new_entry = fields.Char(string='Nuevo Ingreso')

  #Datos del contrato
  name = fields.Char(string='Número de Contrato', default='Nuevo Contrato', tracking=True)
  product_price = fields.Float(tracking=True, string='Costo', compute="calc_price")
  sale_employee_id = fields.Many2one(tracking=True, comodel_name='hr.employee', string='Asistente venta')

  contract_status_item =  fields.Many2one(tracking=True, string="Estatus", comodel_name="pabs.contract.status")
  contract_status_name =  fields.Char(tracking=True, string="Nombre estatus", related="contract_status_item.status")
  contract_status_reason =  fields.Many2one(tracking=True, string="Motivo", comodel_name="pabs.contract.status.reason")
  date_of_last_status = fields.Datetime(tracking=True, string="Fecha estatus")
  reactivation_date = fields.Date(tracking=True, string="Fecha reactivación")

  name_service = fields.Many2one(tracking=True, comodel_name = 'product.product', related="lot_id.product_id", string='Servicio')
  product_code = fields.Char(tracking=True, string='Código de plan previsor', related="name_service.default_code")

  initial_investment = fields.Float(tracking=True, string ='Inversión inicial')
  stationery = fields.Float(tracking=True, string ='Papelería')
  excedent = fields.Float(tracking=True, string ='Excedente', compute='_calc_excedent')
  comission = fields.Float(tracking=True, string ='Comisión tomada')
  investment_bond = fields.Float(tracking=True, string ='Bono por inversión')
  amount_received = fields.Float(tracking=True, string='Importe recibido', compute='_calc_amount_received')

  debt_collector = fields.Many2one(tracking=True, comodel_name="hr.employee", string='Nombre del cobrador')
  payment_amount = fields.Float(tracking=True, string= 'Monto de pago')
  way_to_payment = fields.Selection(tracking=True, selection=WAY_TO_PAY,string = 'Forma de pago')
  date_first_payment = fields.Date(tracking=True, string='Fecha primer abono')
  status_of_contract = fields.Char(tracking=True, string="Estatus")
  contract_expires = fields.Date(tracking=True, string="Vencimiento contrato", compute ="calcular_vencimiento_y_atraso")
  days_without_payment = fields.Integer(tracking=True, string="Dias sin abonar", compute="calcular_dias_sin_abonar")
  late_amount = fields.Float(tracking=True, string="Monto atrasado", compute="calcular_vencimiento_y_atraso")
  comments = fields.Text(tracking=True, string='Comentarios de activación')
  service_detail = fields.Selection(tracking=True, selection=SERVICE, string='Detalle de servicio', default="unrealized", required="1")

  commission_tree = fields.One2many(tracking=True, comodel_name='pabs.comission.tree', inverse_name='contract_id', string="Arbol de comisiones")
  payment_ids = fields.One2many(tracking=True, comodel_name='account.payment', inverse_name='contract', string="Abonos")
  refund_ids = fields.One2many(tracking=True, comodel_name='account.move', inverse_name='contract_id', string="Notas")

#Datos del cliente
  full_name = fields.Char(tracking=True, string="Nombre completo", compute="calc_full_name")
  partner_name = fields.Char(tracking=True, string='Nombre', required=True)
  partner_fname = fields.Char(tracking=True, string='Apellido paterno', required=True)
  partner_mname = fields.Char(tracking=True, string='Apellido materno', required=True)
  birthdate = fields.Date(tracking=True, string='Fecha de nacimiento', default=fields.Date.today(), required=True)
  partner_id = fields.Many2one(tracking=True, comodel_name='res.partner', string='Cliente')
  vat = fields.Char(tracking=True, string='RFC',compute='_calc_rfc')

# Domicilio de casa
  street_name = fields.Char(tracking=True, string='Calle', required=True)
  street_number = fields.Char(tracking=True, string='Numero')
  between_streets = fields.Char(tracking=True, string='Entre calles')
  municipality_id = fields.Many2one(tracking=True, comodel_name='res.locality', required=True, string='Municipio')
  neighborhood_id = fields.Many2one(tracking=True, comodel_name='colonias', string='Colonia')
  phone = fields.Char(tracking=True, string='Teléfono', required=True)
  
# Domicilio de cobro
  street_name_toll = fields.Char(tracking=True, string = 'Calle')
  street_number_toll = fields.Char(tracking=True, string = 'Numero')
  between_streets_toll = fields.Char(tracking=True, string ='Entre calles')
  toll_municipallity_id = fields.Many2one(tracking=True, comodel_name='res.locality',string='Municipio')
  toll_colony_id = fields.Many2one(tracking=True, comodel_name='colonias',string='Colonia')
  phone_toll = fields.Char(tracking=True, string='Teléfono')

#Datos contables
  balance = fields.Float(tracking=True, string="Saldo", compute="_calc_balance")
  paid_balance = fields.Float(tracking=True, string="Abonado", compute="_calc_paid_balance")
  invoice_date = fields.Date(tracking=True, string='Fecha de creación', default=lambda r: r.calc_invoice_date())

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

  company_id = fields.Many2one(
    'res.company', 'Compañia', required=True,
    default=lambda s: s.env.company.id, index=True)

  transfer_balance_ids = fields.One2many(comodel_name='account.move.line',
    inverse_name='contract_id',
    string='Traspasos')

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
    else:
      return fields.Date.today()


  #Al elegir un estatus diferente borrar el motivo actual
  @api.onchange('contract_status_item')
  def check_status_reason(self):
    for rec in self:
      rec.contract_status_reason = None

  def _calc_balance(self):
    invoice_obj = self.env['account.move']
    for rec in self:
      invoice_ids = invoice_obj.search([
        ('type','=','out_invoice'),
        ('contract_id','=',rec.id)])
      result = sum(invoice_ids.mapped('amount_residual'))
      rec.balance = result

  #Abonado = Costo - Saldo
  def _calc_paid_balance(self):
    invoice_obj = self.env['account.move']
    for rec in self:
      #Obtener facturas del contrato
      invoice_ids = invoice_obj.search([('type','=','out_invoice'),('contract_id','=',rec.id)])
      Costo = sum(invoice_ids.mapped('amount_total'))
      Abonado = sum(invoice_ids.mapped('amount_residual'))
      rec.paid_balance = Costo - Abonado

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


  #Obtiene el saldo del contrato sumando el monto pendiente de las facturas
  def _calc_balance(self):
    invoice_obj = self.env['account.move']
    for rec in self:
      invoice_ids = invoice_obj.search([('type','=','out_invoice'),('contract_id','=',rec.id)])
      result = sum(invoice_ids.mapped('amount_residual'))
      rec.balance = result

  @api.onchange('invoice_date')
  def calc_first_payment(self):
    for rec in self:
      if rec.invoice_date:
        rec.date_first_payment = rec.invoice_date + timedelta(days=15)

  @api.onchange('amount_received','stationery')
  def _calc_excedent(self):
    for rec in self:
      rec.excedent = (float(rec.initial_investment) - float(rec.stationery))

  @api.onchange('initial_investment','comission')
  def _calc_amount_received(self):
    pabs_bonus_obj = self.env['pabs.bonus']
    for rec in self:
      rec.amount_received = (rec.initial_investment - rec.comission) or 0
      product_id = rec.name_service
      rec.investment_bond = 0
      bonus = pabs_bonus_obj.search([
        ('plan_id','=',product_id.id)], order="min_value")
      for bon_rec in bonus:
        if rec.initial_investment >= bon_rec.min_value and rec.initial_investment <= bon_rec.max_value:
          rec.investment_bond = bon_rec.bonus

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
  def create_partner(self, vals):
    partner_obj = self.env['res.partner']
    lot_obj = self.env['stock.production.lot']
    lot_id = lot_obj.browse(vals.get('lot_id'))
    if lot_id:
      partner_id = partner_obj.search([
        ('name','=',lot_id.name)])
      if partner_id:
        return partner_id
      else: 
        data = {
          'company_type' : 'person',
          'name' : lot_id.name,
        }
      return partner_obj.create(data)

  @api.model
  def create(self, vals):
    company_id = vals.get('company_id') or self.env.context.get('company_id') or False
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
      
    partner_id = self.create_partner(vals)
    vals['partner_id'] = partner_id.id
    vals['state'] = 'actived'
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

  #Domicilio de cobro
    self.street_name_toll = False
    self.street_number_toll = False
    self.between_streets_toll = False
    self.toll_municipallity_id = False
    self.toll_colony_id = False
    self.phone_toll = False

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

      #Domicilio de cobro
      self.street_name_toll = contract_id.street_name
      self.street_number_toll = contract_id.street_number
      self.between_streets_toll = contract_id.between_streets
      self.toll_municipallity_id = contract_id.municipality_id.id
      self.toll_colony_id = contract_id.neighborhood_id.id
      self.phone_toll = contract_id.phone

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

  @api.onchange('product_id')
  def calc_price(self):
    pricelist_obj = self.env['product.pricelist.item']
    for rec in self:
      if rec.name_service:
        pricelist_id = pricelist_obj.search([
          ('product_id','=',rec.name_service.id)], limit=1)
        if pricelist_id:
          self.product_price = pricelist_id.fixed_price
      
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
      ('lot_id','=',self.lot_id.id)],order="id desc", limit=1)
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
        contract_location = location_obj.search([
          ('contract_location','=',True)])
        contract_view_location = contract_location.location_id
        received_contract = location_obj.search([
          ('location_id','=',contract_view_location.id),
          ('received_location','=',True)])
        if not received_contract:
          raise ValidationError((
            "No se encuentra la ubicación de contratos"))
        if received_contract != location_id:
          raise ValidationError((
            "la solicitud {} no se encontró en la ubicación de contratos, se encuentra en {}".format(self.lot_id.name, location_id.name_get()[0][1])))
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

  #Crea el árbol de comisiones del contrato
  def create_commision_tree(self, invoice_id=False):
    ### Instanciaciones
    comission_template_obj = self.env['pabs.comission.template']
    comission_tree_obj = self.env['pabs.comission.tree']
    pricelist_obj = self.env['product.pricelist.item']
    ### VALIDA SI EXISTE EL EMPLEADO Y UN PLAN PARA GENERAR
    if self.employee_id and self.name_service:
      ### BUSCA LA LISTA DE PRECIOS
      pricelist_id = pricelist_obj.search([('product_id','=',self.name_service.id)])
      ### ENVIA MENSAJE SI NO ENCUENTRA LA LISTA DE PRECIOS
      if not pricelist_id:
        raise ValidationError(("No se encontró la información del plan {}".format(self.product_id.name)))
      ### BUSCA LA PLANTILLA DE LAS COMISIONES
      comission_template_id = comission_template_obj.search([
        ('employee_id','=',self.employee_id.id),
        ('plan_id','=',pricelist_id.id),
        ('comission_amount','>',0)],order="pay_order")
      ### ENVIA MENSAJE SI NO ENCUENTRA LA PLANTILLA
      if not comission_template_id:
        raise ValidationError(("El A.S {} no cuenta con un arbol de comisiones".format(self.employee_id.name)))

      ajuste_por_sueldo = 0
      contratoEsSueldo = (self.payment_scheme_id.name == "SUELDO")

      ### RECORRER TODAS LAS LINEAS DEL DETALLE DE LA PLANTILLA e insertar el registro
      for line in comission_template_id:
        if line.job_id.name != 'FIDEICOMISO':
          data = {
            'contract_id' : self.id,
            'pay_order' : line.pay_order,
            'job_id' : line.job_id.id,
            'comission_agent_id' : line.comission_agent_id.id,
            'corresponding_commission' : line.comission_amount,
            'remaining_commission' : line.comission_amount,
            'commission_paid' : 0,
            'actual_commission_paid' : 0,
          }
        else:
          data = {
            'contract_id' : self.id,
            'pay_order' : line.pay_order,
            'job_id' : line.job_id.id,
            'comission_agent_id' : line.comission_agent_id.id,
            'corresponding_commission' : line.comission_amount,
            'remaining_commission' : line.comission_amount,
            'commission_paid' : 0,
            'actual_commission_paid' : 0,
          }
        
        monto_comision = line.comission_amount

        if contratoEsSueldo and line.job_id.name == "ASISTENTE SOCIAL":
          ajuste_por_sueldo = monto_comision
          monto_comision = 0
        elif contratoEsSueldo and line.job_id.name == "FIDEICOMISO":
          monto_comision = monto_comision + ajuste_por_sueldo

        data = {
          'contract_id' : self.id,
          'pay_order' : line.pay_order,
          'job_id' : line.job_id.id,
          'comission_agent_id' : line.comission_agent_id.id,
          'corresponding_commission' : monto_comision,
          'remaining_commission' : monto_comision,
          'commission_paid' : 0,
          'actual_commission_paid' : 0,
        }
        comission_tree_obj.create(data)

  #Crea la factura
  def create_invoice(self, previous=False):
    account_obj = self.env['account.move']
    account_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)
    sequence_obj = self.env['ir.sequence']
    pricelist_obj = self.env['product.pricelist.item']
    if previous:
      journal_id = account_obj.with_context(
        default_type='out_invoice')._get_default_journal()
      currency_id = account_obj.with_context(
        default_type='out_invoice')._get_default_currency()
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
      }
      invoice_id = account_obj.create(data)
      if invoice_id:
        product_id = previous.name_service
        account_id = product_id.property_account_income_id or product_id.categ_id.property_account_income_categ_id

        line_data = {
          'move_id' : invoice_id.id,
          'account_id' : account_id.id,
          'quantity' : 1,
          'price_unit' : previous.product_price,
          'credit' : previous.product_price,
          'product_uom_id' : product_id.uom_id.id,
          'partner_id' : previous.partner_id.id,
          'amount_currency' : 0,
          'product_id' : product_id.id,
          'is_rounding_line' : False,
          'exclude_from_invoice_tab' : False,
          'name' : product_id.description_sale or product_id.name,
        }
        account_line_obj.create(line_data)

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
          #'price_unit' : (previous.product_price * -1),
          'debit' : previous.product_price,
        }
        account_line_obj.create(partner_line_data)
        invoice_id.action_post()
        previous.allow_create = False
        pricelist_id = pricelist_obj.search([
          ('product_id','=',previous.name_service.id)], limit=1)
        if not pricelist_id:
          raise ValidationError((
            "No se encontró una secuencia"))
        if not previous.partner_id:
          raise ValidationError((
            "No tiene un cliente ligado al contrato"))
        if previous.partner_id:
          partner_id = previous.partner_id
          partner_id.write({'name' : previous.name})
        previous.state = 'contract'
        previous.create_commision_tree(invoice_id=invoice_id)
        contract_name = pricelist_id.sequence_id._next()
        previous.name = contract_name
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
            raise ValidationError(("No se encontró la información del plan {}".format(previous.product_id.name)))

          #Obtener la plantilla de comisiones
          _logger.warning('empleado: {}\nplan: {}'.format(previous.employee_id.barcode, pricelist_id.product_tmpl_id.name))
          comission_template = comission_template_obj.search([
            ('employee_id', '=', previous.employee_id.id),
            ('plan_id', '=', pricelist_id.id),
            ('job_id', '=', job_id)])

          if not comission_template:
            raise ValidationError("No se encontró la plantilla de comisiones del asistente")

          if comission_template.comission_amount <= 0:
            raise ValidationError(("El A.S {} tiene asignado ${} en su plantilla de comisiones. Debe asignarle un monto mayor a cero".format(comission_template.comission_agent_id.name, comission_template.comission_amount)))
        ### TERMINA VALIDACION COMISIONES

        #Asignar asistente de venta PRODUCCION
        vals['sale_employee_id'] = previous.employee_id
        vals['invoice_date'] = self.calc_invoice_date()

        previous.write(vals)
        invoice_id = self.create_invoice(previous)
        account_id = invoice_id.partner_id.property_account_receivable_id.id
        journal_id = account_obj.with_context(
          default_type='out_invoice')._get_default_journal()
        currency_id = account_obj.with_context(
          default_type='out_invoice')._get_default_currency()
        for line in invoice_id.line_ids:
          if line.debit > 0:
            reconcile.update({'debit_move_id' : line.id})     
        ### CREANDO PAGO POR INVERSIÓN INICIAL
        if previous.stationery:
          cash_journal_id = journal_obj.search([
            ('type','=','cash')],limit=1)
          if not cash_journal_id:
            raise ValidationError((
              "No se encontró ningun diario de efectivo"))
          payment_method_id = payment_method_obj.search([
            ('payment_type','=','inbound'),
            ('code','=','manual')],limit=1)
          if not payment_method_id:
            raise ValidationError((
              "No se encontró el método de pago, favor de comunicarse con sistemas"))
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
            'currency_id' : currency_id.id,
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
          cash_journal_id = journal_obj.search([
            ('type','=','cash')],limit=1)
          if not cash_journal_id:
            raise ValidationError((
              "No se encontró ningun diario de efectivo"))
          payment_method_id = payment_method_obj.search([
            ('payment_type','=','inbound'),
            ('code','=','manual')],limit=1)
          if not payment_method_id:
            raise ValidationError((
              "No se encontró el método de pago, favor de comunicarse con sistemas"))
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
            'currency_id' : currency_id.id,
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
          refund_data = {
            'date' : previous.invoice_date,
            'commercial_partner_id' : previous.partner_id.id,
            'partner_id' : previous.partner_id.id,
            'ref' : 'Bono por inversión inicial',
            'type' : 'out_refund',
            'journal_id' : journal_id.id,
            'state' : 'draft',
            'currency_id' : currency_id.id,
            'invoice_date' : previous.invoice_date,
            'auto_post' : False,
            'contract_id' : previous.id,
            'invoice_user_id' : self.env.user.id,
            'reversed_entry_id' : invoice_id.id,
          }
          refund_id = account_obj.create(refund_data)
          if refund_id:
            product_id = self.env['product.template'].search([
              ('company_id','=',previous.company_id.id),
              ('name','=','BONO POR INVERSION INICIAL')])
            account_id = product_id.property_account_income_id or product_id.categ_id.property_account_income_categ_id

            line_data = {
              'move_id' : refund_id.id,
              'account_id' : account_id.id,
              'quantity' : 1,
              'price_unit' : previous.investment_bond,
              'debit' : previous.investment_bond,
              'product_uom_id' : product_id.uom_id.id,
              'partner_id' : previous.partner_id.id,
              'amount_currency' : 0,
              'product_id' : product_id.id,
              'is_rounding_line' : False,
              'exclude_from_invoice_tab' : False,
              'name' : product_id.description_sale or product_id.name,
            }
            line = account_line_obj.create(line_data)
            ### CONTRAPARTIDA DEL DOCUMENTO
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
      self.reconcile_all(reconcile)

  #################################################
  ### OVERWRITE DEL METODO WRITE
  #################################################
  def write(self, vals):
    ### Al cambiar el estatus o el motivo actualizar el campo de ultima fecha de estatus
    if vals.get('contract_status_item') or vals.get('contract_status_reason'):
      self.date_of_last_status = datetime.today()

    ### Al poner en suspensión temporal validar que la fecha de reactivación sea mayor al dia de hoy.
    if vals.get('reactivation_date') and fields.Date.to_date(vals.get('reactivation_date')) < fields.Date.today():
      raise ValidationError("La fecha de suspensión temporal debe ser mayor a la fecha actual")

    ### Si se quita la suspensión temporal quitar la fecha de reactivación
    if vals.get('contract_status_item') and vals.get('contract_status_item') != "SUSPENSION TEMPORAL" and self.contract_status_item.status == "SUSPENSION TEMPORAL":
      self.reactivation_date = None

    return super(PABSContracts, self).write(vals)

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
      #Obtener información del contrato
      monto_pago = rec.payment_amount
      forma_pago = rec.way_to_payment
      fecha_primer_abono = rec.date_first_payment

      if fecha_primer_abono == False or forma_pago == False or monto_pago == False:
        rec.contract_expires = None
        rec.late_amount = 0
        return

      saldo_a_plazos = rec.product_price - rec.initial_investment - rec.investment_bond
      abonado = rec.paid_balance - rec.initial_investment - rec.investment_bond #Abonos sin tomar en cuenta enganche

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
      rec.late_amount = monto_atrasado

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
      days = 0
      today = fields.Datetime.now().replace(tzinfo=tz.gettz('Mexico/General')).date()
      #Obtener registro del último pago de cobranza
      ultimo_abono_cobranza = self.payment_ids.filtered(lambda r: r.state == 'posted' and r.reference == 'payment')
      if ultimo_abono_cobranza:
        ultimo_abono_cobranza = ultimo_abono_cobranza.sorted(key=lambda r: r.date_receipt)
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

  def create_contracts(self):
    _logger.warning('El contrato')
    contract_obj = self.env['pabs.contract']
    contract_ids = contract_obj.search([
      ('state','=','precontract')],limit=400,order="name")
    for contract_id in contract_ids:
      lot_id = contract_id.lot_id.id
      _logger.warning('El contrato {}'.format(lot_id))
      self.create_contract(vals={'lot_id' : lot_id})