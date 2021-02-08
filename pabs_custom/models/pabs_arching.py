# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

STATES = [
  ('open','Abierto'),
  ('closed','Cerrado')]

class PabsArching(models.Model):
  _name = 'pabs.arching'

  name = fields.Char(string='Folio')
  create_uid = fields.Integer(string='Usuario', default=lambda self: self.env.user.id)
  user_name = fields.Char(String="Secretaria", default=lambda self: self.env.user.partner_id.name)
  # warehouse_user_ids = fields.One2many(comodel_name='stock.warehouse', inverse_name='id', string='Oficinas del usuario', default = lambda self: self.env.user.warehouse_ids)

  #Caja texto donde se coloca el código para elegir al asistente
  code = fields.Char(string='Código del asistente', required=True)

  employee_id = fields.Many2one(comodel_name='hr.employee', string='Asistente')
  employee_code = fields.Char(related='employee_id.barcode', string='Código')
  
  warehouse_id = fields.Integer(related="employee_id.warehouse_id.id", store=True, string="Codigo oficina")
  warehouse_name = fields.Char(related="employee_id.warehouse_id.name", store=True, string="Oficina")

  #Ubicación del asistente
  agent_location_id = fields.Integer(related="employee_id.local_location_id.id", store=True, string="Id de ubicacion")
  
  state = fields.Selection(selection=STATES, string='Estado', default='open')

  create_date = fields.Datetime(string="Fecha de apertura")
  closing_date = fields.Datetime(string="Fecha de cierre")

  effectiveness = fields.Float(string="Efectividad", digits=(3,2), store=True)

  #Solicitudes en poder del asistente
  solicitudes = fields.Char(string="Solicitudes en poder del asistente")
  cantidad_solicitudes = fields.Integer(string="Solicitudes en poder del asistente")

  #Solicitudes pertenecientes al arqueo (escaneadas y no escaneadas)
  line_ids = fields.One2many(comodel_name='pabs.arching.line', inverse_name='arching_id', string='Solicitudes')
  cantidad_escaneadas = fields.Integer(string="Solicitudes escaneadas")

  #PENDIENTE Caja texto donde se coloca la solicitud que se registrará
  #solicitud = fields.Char(string="Solicitud", store=False)

##########################################
#####             METODOS            #####
##########################################
  #Al escribir el código del asistente
  @api.onchange('code')
  def check_employee_in_office(self):
    if not self.code:
      return

    employee_obj = self.env['hr.employee'].search([('barcode','=', self.code.upper())])

    if not employee_obj:
      raise ValidationError("El asistente {} no existe".format(self.code))
    
  ### Solo permitir elegir empleados de la oficina a las que tiene la secretaria tiene acceso
    #Obtener almacenes asignados al usaurioc
    allowed_warehouses_obj = self.env.user.warehouse_ids

    if not allowed_warehouses_obj:
      raise ValidationError("Tu usuario no tiene acceso a ninguna oficina")
    
    #Validar que la secretaria tenga acceso a la oficina a la que está asignada el asistente
    if employee_obj.warehouse_id.id not in allowed_warehouses_obj.ids:
      raise ValidationError("Tu usuario no tiene acceso a la oficina: {}".format(employee_obj.warehouse_id.name))
  ### 

    #Si el asistente ya tiene un arqueo abierto impedir crear otro
    arching_ids = self.env['pabs.arching'].search_count([('code', '=', self.code), ('state','=','open')])
    if arching_ids > 0:
      raise ValidationError("El asistente {} ya tiene un arqueo abierto. Cierre primero ese arqueo antes de abrir uno nuevo".format(self.code))

    #Llenar información del formulario
    self.employee_id = employee_obj.id
    self.warehouse_id = employee_obj.warehouse_id.id
    self.warehouse_name = employee_obj.warehouse_id.name
    
    #Consultar las solicitudes en poder del asistente
    #Si el usuario edita la lista de solicitudes escaneadas se actualiza esta lista
    self.consultar_solicitudes_asistente()

    self.name = self.code + "_" + datetime.today().strftime("%d-%m-%y")
    self.user_id = self.env.user.id

  def consultar_solicitudes_asistente(self):
    #Obtener las solicitudes en poder del asistente
    listado_solicitudes = self.env['stock.quant'].search([('location_id','=', self.agent_location_id), ('quantity','=','1')])
    
    conteo_solicitudes = 0
    self.solicitudes = ""

    for solicitud in listado_solicitudes:
      if self.solicitudes:
        self.solicitudes = self.solicitudes + str(solicitud.lot_id.name) + ", "
      else:
        self.solicitudes = str(solicitud.lot_id.name) + ", "
      conteo_solicitudes = conteo_solicitudes + 1

    self.cantidad_solicitudes = conteo_solicitudes

  #Al modificar el listado de solicitudes escaneadas
  @api.onchange('line_ids')
  def _onchange_(self):
    #Al editar las solicitudes escaneadas consultar de nuevo las solicitudes en poder del asistente
    self.consultar_solicitudes_asistente()

    ### Calcular efectividad
    conteo_solicitudes_presentadas = 0
    for solicitud in self.line_ids:
      if solicitud.state == 'presented':
        conteo_solicitudes_presentadas = conteo_solicitudes_presentadas + 1
    self.cantidad_escaneadas = conteo_solicitudes_presentadas

    if self.cantidad_solicitudes > 0:
      self.effectiveness = (self.cantidad_escaneadas / self.cantidad_solicitudes) * 100

  #Al cerrar el arqueo
  def close_arching(self):
    #Cambiar estatus a cerrado
    self.write({'state':'closed', 'closing_date': datetime.today()})

  ###Insertar solicitudes faltantes a la lista
    #Consultar lista de solicitudes en poder del asistente
    listado_solicitudes = self.env['stock.quant'].search([('location_id','=', self.agent_location_id), ('quantity','=','1')])

    lista_solicitudes_faltantes = []
    #Evaluar cada solicitud y si no se encuentra en la lista agregarla
    for solicitud in listado_solicitudes:
      if solicitud.lot_id.id not in self.line_ids.lot_id.ids:

        #Consultar si la solicitud está activada
        contract_obj = self.env['pabs.contract'].search([('lot_id','=', solicitud.lot_id.id)])

        activated = False
        if contract_obj.activation_code:
          activated = True

        #Llenar datos de solicitud faltante
        sol = {'arching_id': self.id,
          'lot_id': solicitud.lot_id.id,
          #'scan_date':'',
          'activated': activated,
          'state':'missing'
        }

        lista_solicitudes_faltantes.append(sol)

    if len(lista_solicitudes_faltantes) > 0:
      self.env['pabs.arching.line'].create(lista_solicitudes_faltantes)

  #COMPLETADO - Imprimir reporte desde botón y mostrar sólo cuando el arqueo está cerrado.
  #COMPLETADO Limitar registros en vista de lista: solo mostrar los asistentes que pertenecen a la oficina del usuario  

  #PENDIENTE Validar que sea escaneado no escrito ni copiado #PREGUNTAR A LALO

  #Método para aumentar la altura de la página
  def change_size_page(self, items):
    paper_format = self.env['report.paperformat'].search([('name', '=', 'Arqueo termico')])
    if len(items) > 1:
        paper_format.page_height = 140 + (len(items) * 10)