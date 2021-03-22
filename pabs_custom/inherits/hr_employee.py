# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

OPTIONS = [
  ('true','Si'),
  ('false','No')]

RELATIONSHIP = [
  ('son','Hijo(a)'),
  ('spouse','Esposo(a)'),
  ('father','Padre'),
  ('mother','Madre')]

class HrEmployee(models.Model):
  _inherit = 'hr.employee'
  
  # Declaración de campos
  employee_status = fields.Many2one(comodel_name='hr.employee.status',
    string='Estatus')

  barcode = fields.Char(groups=False)

  first_name = fields.Char(string='Nombre',
    tracking=True,
    required=True)

  last_name = fields.Char(string='Apellido',
    tracking=True,
    required=True)

  warehouse_id = fields.Many2one(comodel_name='stock.warehouse',
    string='Oficina',
    tracking=True)

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
    string='Parentezco')

  second_beneficiary = fields.Char(string='Nombre del beneficiario',
    tracking=True)

  second_beneficiary_birthdate = fields.Date(string='Fecha de Nacimiento',
    tracking=True)

  second_beneficiary_relationship = fields.Selection(selection=RELATIONSHIP,
    tracking=True,
    string='Parentezco')

  date_of_admission = fields.Date(string="Fecha de ingreso", tracking=True)

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
      duplicated = self.search([('barcode','=',vals.get('barcode'))])
      deb_collector = job_obj.search([
        ('name','=','COBRADOR')],limit=1)
      if not deb_collector:
        raise ValidationError((
          "No se encontró el puesto de cobrador"))
      if duplicated:
        raise ValidationError((
          "No puedes dar de alta el código de empleado {} por que ya existe".format(vals.get('barcode'))))
      if vals.get('job_id'):
        job_ids = job_obj.search([
          ('name','in',('PRESIDENTE','DIRECTOR NACIONAL','DIRECTOR REGIONAL','GERENTE SR','GERENTE JR','COORDINADOR','GERENTE DE OFICINA','ASISTENTE SOCIAL'))])
        if vals.get('job_id') in job_ids.ids:
          ### validación para seleccionar automáticamente las ubicaciones correspondientes
          if vals.get('warehouse_id'):
            warehouse_id = warehouse_obj.browse(vals.get('warehouse_id'))
            view_location_id = warehouse_id.view_location_id
            ### Buscar la ubicación de contratos
            contract_location = location_obj.search([
              ('contract_location','=',True)], limit=1)
            ### Buscar la ubicación de solicitudes
            request_location = location_obj.search([
              ('location_id','=',view_location_id.id),
              ('office_location','=',True)],limit=1)
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
            if newEmployee['department_id'] == sales_dept_id:
              self.env['pabs.comission.template'].create_comission_template(newEmployee['id'])
        elif vals.get('job_id') == deb_collector.id:
          newEmployee = super(HrEmployee, self).create(vals)
          comission_debt_collector_obj.create({
            'debt_collector_id' : newEmployee.id,
          })
        else:
          newEmployee = super(HrEmployee, self).create(vals)
      else:
        newEmployee = super(HrEmployee, self).create(vals)
    else:
      newEmployee = super(HrEmployee, self).create(vals)
    return newEmployee

  def name_get(self):
    ### EL formato en el cual mostrará la relación de hr.employee ejem. "V0001 - Eduardo Serrano"
    result = []
    for record in self:
      result.append((record.id, "{} - {}".format(record.barcode,record.name)))
    return result

  def write(self, vals):
    ### Declaración de objetos
    warehouse_obj = self.env['stock.warehouse']
    picking_type_obj = self.env['stock.picking.type']
    ### GUARDAMOS EL ALMACÉN ANTERIOR
    last_warehouse_id = self.warehouse_id
    ### VERIFICAMOS SI NO HUBO MODIFICACIÓN DE OFICINA
    if vals.get('warehouse_id'):
      ### NOS INSTANCIAMOS SOBRE EL ALMACÉMN
      warehouse_id = warehouse_obj.browse(vals.get('warehouse_id'))
      ### CAMBIAMOS LA UBICACIÓN LOCAL DE ALMACÉN
      self.local_location_id.write({'location_id' :warehouse_id.view_location_id.id})
      ### ENVIAMOS AL MÉTODO ORIGINAL LA NUEVA UBICACIÓN DE SOLICITUDES
      vals.update({
        'request_location_id' : warehouse_id.lot_stock_id.id
      })
      ### BUSCAMOS TODAS LAS OPERACIONES
      picking_type_ids = picking_type_obj.search(['|',
        ('default_location_src_id','=',self.local_location_id.id),
        ('default_location_dest_id','=',self.local_location_id.id)])
      ### RECORREMOS TODAS LAS OPERACIONES
      for picking_type_id in picking_type_ids:
        ### SI LA UBICACIÓN LOCAL ES LA DE ORIGEN
        if picking_type_id.default_location_src_id.id == self.local_location_id.id:
          name = '{} -> {}'.format(self.barcode, warehouse_id.name)
          ### ESCRIBIMOS EL ALMACÉN, LA UBICACIÓN DESTINO Y LE CAMIAMOS EL NOMBRE
          picking_type_id.write({
            'warehouse_id' : warehouse_id.id,
            'default_location_dest_id' : warehouse_id.wh_receipt_stock_id.id,
            'name' : name})
        ### SI LA UBICACIÓN LOCAL ES LA DE DESTINO
        elif picking_type_id.default_location_dest_id.id == self.local_location_id.id:
          name = '{} -> {}'.format(warehouse_id.name,self.barcode)
          ### ESCRIBIMOS EL ALMÁCÉN LA UBICACIÓN ORIGEN Y LE CAMBIAMOS EL NOMBRE
          picking_type_id.write({
            'warehouse_id' : warehouse_id.id,
            'default_location_src_id' : warehouse_id.lot_stock_id.id,
            'name' : name})
        ### BUSCAMOS LA SECUENCIA DE ESE PICKING
        sequence_id = picking_type_id.sequence_id
        ### REMPLAZAMOS TODO LO QUE TENGA QUE VER CON EL ALMACÉN ANTERIOR POR EL NUEVO
        sequence_name = sequence_id.name.replace(last_warehouse_id.name, warehouse_id.name)
        prefix_name = sequence_id.name.replace(last_warehouse_id.code, warehouse_id.code)
        ### ESCRIBIMOS LA INFORMACIÓN NUEVA
        sequence_id.write({
          'name' : sequence_name,
          'prefix' : prefix_name,
        })
    return super(HrEmployee, self).write(vals)

  @api.model
  def _name_search(self, name='', args=None, operator="ilike", limit=100):
    if args is None:
      args = []
    domain = args + ['|', ('barcode', operator, name), ('name', operator, name)]
    return super(HrEmployee, self).search(domain, limit=limit).name_get()
    