# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

OPTIONS = [
  ('true','Si'),
  ('false','No')]

RELATIONSHIP = [
  ('son','Hijo(a)'),
  ('spouse','Esposo(a)'),
  ('father','Padre'),
  ('mother','Madre')]

RESCISSION_REASONS = [
  ('RETIRO VOLUNTARIO','RETIRO VOLUNTARIO'),
  ('ABANDONO DE TRABAJO','ABANDONO DE TRABAJO'),
  ('FALTA DE PROBIDAD','FALTA DE PROBIDAD'),
  ('FALTA A LA MORAL','FALTA A LA MORAL'),
  ('INSUBORDINACION','INSUBORDINACIÓN'),
  ('BAJA PRODUCTIVIDAD','BAJA PRODUCTIVIDAD'),
  ('RESICION ART.47','RESICION ART.47'),
  ('DEMANDA LABORAL','DEMANDA LABORAL'),
  ('CAMBIO DE PLAZA','CAMBIO DE PLAZA'),
  ('BAJA POR PENSION','BAJA POR PENSIÓN'),
  ('BAJA POR M40','BAJA POR M40'),
  ('CAMBIO DE AREA','CAMBIO DE AREA'),
  ('NO CONTRATABLE','NO CONTRATABLE'),
  ('AUSENTISMO','AUSENTISMO'),
  ('PLANTA NO OTORGADA','PLANTA NO OTORGADA'),
  ('REINGRESO PENDIENTE','REINGRESO PENDIENTE'),
  ('NO INGRESA','NO INGRESA'),
  ('DANO A EQUIPO','DAÑO A EQUIPO'),
  ('NO FIRMA CONTRATO','NO FIRMA CONTRATO'),
  ('DOC. PENDIENTE','DOC. PENDIENTE'),
  ('DEF. DEL COLABORADOR','DEF. DEL COLABORADOR'),
  ('DESPIDO','DESPIDO'),
  ('RESCISION LABORAL','RESCISIÓN LABORAL'),
  ('MAL ASIGNADO','MAL ASIGNADO'),
  ('FALLECIMIENTO','FALLECIMIENTO'),
  ('AJUSTE DE PLATILLA','AJUSTE DE PLATILLA')]

EMPRESAS = [('pabs','PABS'),('funeraria','FUNERARIA'),('diremovil','DIREMOVIL')]

class HrEmployee(models.Model):
  _inherit = 'hr.employee'
  
  # Declaración de campos
  employee_status = fields.Many2one(comodel_name='hr.employee.status',
    string='Estatus')
  
  employee_status_date = fields.Date(string='Fecha cambio de estatus')

  barcode = fields.Char(string="Código de empleado",groups=False)

  first_name = fields.Char(string='Nombre',
    tracking=True,
    required=True)

  last_name = fields.Char(string='Apellido',
    tracking=True,
    required=True)

  warehouse_id = fields.Many2one(comodel_name='stock.warehouse',
    string='Oficina',
    tracking=True)
  
  company_type_id = fields.Many2one(comodel_name='type.company',string="Tipo de compañía",related='warehouse_id.type_company')

  view_location_id = fields.Many2one(comodel_name='stock.location',
    string='Ubicación de vista',
    store=False,
    related="warehouse_id.view_location_id")

  local_location_id = fields.Many2one(comodel_name='stock.location',
    string='Ubicación del empleado',
    tracking=True)

  request_location_id = fields.Many2one(comodel_name='stock.location',
    string='Ubicación de solicitudes',
    tracking=True)

  contract_location_id = fields.Many2one(comodel_name='stock.location',
    string='Ubicación de contratos',
    tracking=True)

  street = fields.Char(string='Calle',
    tracking=True)

  number = fields.Char(string='Número',
    tracking=True)

  city = fields.Char(string='Ciudad',
    tracking=True)

  state_id = fields.Many2one(comodel_name='res.country.state',
    tracking=True,
    string='Estado')

  country_id = fields.Many2one(comodel_name='res.country',
    tracking=True,
    string='´País')

  municipality_id = fields.Many2one(comodel_name='res.locality',
    string='Municipio',
    tracking=True)

  neighborhood_id = fields.Many2one(comodel_name='colonias',
    string='Colonia',
    tracking=True)

  zip = fields.Char(string='Código postal',
    tracking=True,
    size=5)

  request = fields.Selection(selection=OPTIONS,
    tracking=True,
    default="false",
    string='Solicitud')

  birth_certificate = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Acta de nacimiento')

  identification = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Identificación')

  photos = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Fotos')

  proof_address = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Comprobante de domicilio')

  letter_recomendation = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Carta de Recomendación')

  criminal_record = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Carta de antecedentes penales')

  individual_contract = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Contrato Individual')

  confidentiality_contract = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Contrato de confidencialidad')

  responsive_letter = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Carta responsiva')

  promissory_note = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Pagaré')

  voluntary_resignation = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Renuncia voluntaría')  

  new_voluntary_resignation = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Nueva renuncia voluntaría')

  address_sheet = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Hoja de domicilio y teléfono')

  worker_card = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Carnet de trabajador')

  nss = fields.Char(string='NSS',
    tracking=True)

  curp = fields.Char(string='CURP',
    tracking=True)

  notice_privacy = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Aviso de privacidad')

  no_debit_letter = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Carta de no adeudo')

  welcome = fields.Selection(selection=OPTIONS,
    default="false",
    tracking=True,
    string='Bienvenida')

  payment_scheme = fields.Many2one(comodel_name='pabs.payment.scheme',
  tracking=True,
  string="Esquema de pago")

  rfc = fields.Char(string='RFC',
    tracking=True)

  category = fields.Char(string='Categoría',
    tracking=True)

  recluitment_id = fields.Many2one(comodel_name='pabs.recluitment.origin',
    string='Origen de reclutamiento',
    tracking=True)

  induction_id = fields.Many2one(comodel_name='pabs.recluitment.induction',
    string='Inducción impartida por',
    tracking=True)

  comment = fields.Text(string='Comentarios',
    tracking=True)

  first_payment = fields.Date(string='Fecha de inicio de esquema de pago',
    tracking=True)

  fist_beneficiary = fields.Char(string='Nombre del beneficiario',
    tracking=True)

  first_beneficiary_birthdate = fields.Date(string='Fecha de Nacimiento',
    tracking=True)

  fist_beneficiary_relationship = fields.Selection(selection=RELATIONSHIP,
    tracking=True,
    string='Parentesco')

  second_beneficiary = fields.Char(string='Nombre del beneficiario',
    tracking=True)

  second_beneficiary_birthdate = fields.Date(string='Fecha de Nacimiento',
    tracking=True)

  second_beneficiary_relationship = fields.Selection(selection=RELATIONSHIP,
    tracking=True,
    string='Parentesco')

  date_of_admission = fields.Date(string="Fecha de ingreso", tracking=True)

  salary_contract_number = fields.Integer(string="Contratos a sueldo",copy=False)

  recommended_id = fields.Char(string='Recomendador')

  code_extension = fields.Char(string='Extensión de código')

  rescission_reason = fields.Selection(selection=RESCISSION_REASONS, tracking=True, string='Motivo rescisión')

  pabs_company = fields.Selection(selection=EMPRESAS, string='Empresa')

  pabs_location = fields.Char(string='Ubicación')

  # Calculo de nombre completo
  @api.onchange('first_name','last_name')
  def calc_full_name(self):
    for obj in self:
      full_name = ''
      if obj.first_name:
        full_name = full_name + obj.first_name
      if obj.last_name:
        full_name = "{} {}".format(full_name,obj.last_name)
      obj.name = full_name

  @api.model
  def create(self, vals):
    ### Declaración de objetos
    warehouse_obj = self.env['stock.warehouse']
    location_obj = self.env['stock.location']
    job_obj = self.env['hr.job']
    comission_debt_collector_obj = self.env['pabs.comission.debt.collector']
    ### Validaciones con el código de empleado
    if vals.get('barcode'):
      ### cambia el código de empleado a mayusculas para mantener un estándar
      vals['barcode'] = vals['barcode'].upper()
    
    ### Validar que no se repitan los códigos de empleado
    duplicated = None
    if self.env.context.get('migration'):
      duplicated = self.search([
        ('barcode','=',vals.get('barcode')),
        ('period_type','=',vals.get('period_type'))
      ])
    else:
      duplicated = self.search([('barcode','=',vals.get('barcode'))])

    deb_collector = job_obj.search([
      ('name','=','COBRADOR')],limit=1)
    if not deb_collector:
      raise ValidationError((
        "No se encontró el puesto de cobrador"))
    if duplicated:
      raise ValidationError((
        "No puedes dar de alta el código de empleado {} por que ya existe".format(vals.get('barcode'))))
    job_ids = job_obj.search([
      ('name','in',('PRESIDENTE','DIRECTOR NACIONAL','DIRECTOR REGIONAL','GERENTE SR','GERENTE JR','COORDINADOR','GERENTE DE OFICINA','ASISTENTE SOCIAL'))])
    if vals.get('job_id') in job_ids.ids:
      ### validación para seleccionar automáticamente las ubicaciones correspondientes
      if vals.get('warehouse_id'):
        warehouse_id = warehouse_obj.browse(vals.get('warehouse_id'))
        view_location_id = warehouse_id.view_location_id
        ### Buscar la ubicación de contratos
        contract_location = location_obj.search([('contract_location','=',True)], limit=1)
        ### Buscar la ubicación de solicitudes
        request_location = location_obj.search([('location_id','=',view_location_id.id),('office_location','=',True)],limit=1)
        ### Sí encuentra una ubicación de solicitudes
        if request_location:
          vals['request_location_id'] = request_location.id
        else:
          ### Mensaje de error para validar si está bien configurada la ubicación de solicitudes
          raise ValidationError((
            "No se pudo encontrar el almacén de solicitudes, favor de ponerse en contacto con sistemas"))
        ### Sí encuentra una ubicación de contratos.
        if contract_location:
          vals['contract_location_id'] = contract_location.id
        else:
          ### Mensaje de error para validar si está bien configurada la ubicación de contratos
          raise ValidationError((
            "No se pudo encontrar el almacén de contratos, favor de ponerse en contacto con sistemas"))
        ### Generando valores para la creación de su ubicación
        location_val = {
          'name': vals.get('barcode'),
          'location_id': view_location_id.id,
          'usage': 'internal',
          'consignment_location' : True
        }
        ### Método para crear la ubicación
        local_location = location_obj.sudo().create(location_val)
        ### Agregarlo al diccionario para anexarlo
        vals['local_location_id'] = local_location.id

        #Insertar registro de empleado
        newEmployee = super(HrEmployee, self).create(vals)

        #Solo crear plantilla cuando el empleado es del departamento de ventas
        sales_dept_id = self.env['hr.department'].search([('name','=','VENTAS')], limit = 1)
        _logger.warning("Departamento Emp:{}\nDept:{}".format(newEmployee.department_id.id,sales_dept_id.id))
        if newEmployee.department_id.name == 'VENTAS':
          self.env['pabs.comission.template'].create_comission_template(newEmployee.id)
        return newEmployee
    elif vals.get('job_id') == deb_collector.id:
      newEmployee = super(HrEmployee, self).create(vals)
      comission_debt_collector_obj.create({
        'debt_collector_id' : newEmployee.id,
      })
      
      newEmployee.write({'ecobro_id': str(newEmployee.id)})
      return newEmployee
    else:
      return super(HrEmployee, self).create(vals)

  def name_get(self):
    ### EL formato en el cual mostrará la relación de hr.employee ejem. "V0001 - Eduardo Serrano"
    result = []
    for record in self:
      result.append((record.id, "{} - {}".format(record.barcode,record.name)))
    return result

  def write(self, vals):
    ### Declaración de objetos
    warehouse_obj = self.env['stock.warehouse']
    location_obj = self.env['stock.location']
    picking_type_obj = self.env['stock.picking.type']
    job_obj = self.env['hr.job']
    ### BUSCAMOS EL JOB ID
    asistant_job_id = job_obj.search([('name','=','ASISTENTE SOCIAL')])
    ### SI NO ESTA
    if not asistant_job_id:
      ### ENVIAMOS MENSAJE DE ERROR
      raise ValidationError((
        "No se encontró el puesto de trabajo de asistente social"))
    if vals.get('warehouse_id'):
      warehouse_id = warehouse_obj.browse(vals.get('warehouse_id'))
      if self.local_location_id:
        local_location_id = location_obj.browse(self.local_location_id.id)
        local_location_id.write({'location_id' : warehouse_id.view_location_id.id})
      vals['request_location_id'] = warehouse_id.lot_stock_id.id
    return super(HrEmployee, self).write(vals)

  @api.onchange('employee_status')
  def _onchange_employee_status(self):
    for rec in self:
      rec.employee_status_date = fields.Date.today()

  @api.model
  def _name_search(self, name='', args=None, operator="ilike", limit=100):
    if args is None:
      args = []
    domain = args + ['|', ('barcode', operator, name), ('name', operator, name)]
    return super(HrEmployee, self).search(domain, limit=limit).name_get()
    