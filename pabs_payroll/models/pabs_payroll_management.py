# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.addons.pabs_payroll.models.pabs_payroll import WEEK, STATES
from datetime import datetime

HEADERS = [
  'Fecha de Ingreso',
  'Código',
  'Empleado',
  'Puesto',
  'Oficina',
  'Esquema',
  'Sueldo',
  'Séptimo día',
  'Horas extra',
  'Día festivo',
  'Comisión',
  'Retroactivo',
  'Comisión Garantía',
  'Apoyo Capacitación',
  'Bono Tip de Venta',
  'Sueldo asistencia',
  'Periodo de Apoyo',
  'Gratificación',
  'Bono por Recomendar',
  'Bono Inv inicial alta',
  'Bono por  Efectividad',
  'Prima dominical',
  'Prima vacacional',
  'Bono Productividad',
  'Apoyo de Gasolina',
  'APOYO RIF',
  'Bono mensual',
  'Vales despensa',
  'Préstamo caja ahorro',
  #'Dev. Descuento duplicado',
  'Prestamo empresa',
  'Apoyo cambio de plaza',
  'TOTAL PERCEPCIONES', # 32
  'IMSS',
  'Descuento por Tip de venta',
  'Caja de ahorro',
  'Préstamo caja de ahorro',
  'Préstamo PROBENSO',
  'Préstamo empresa',
  'Fondo de ahorro',
  'INFONAVIT',
  'Paquete Funerario',
  'Comisiones anticipadas',
  'TOTAL DEDUCCIONES', # 43
  '*NETO*'] #44

class PabsPayrollManagement(models.Model):
  _name = 'pabs.payroll.management'
  _description = 'Nómina Sección de Gerente'
  _rec_name = 'week_number'

  name = fields.Char(string='Folio')

  state = fields.Selection(selection=STATES,
    string='Estado',
    default='draft')

  user_id = fields.Many2one(comodel_name='res.users',
    string='Usuario',
    default=lambda self: self.env.user)

  week_number = fields.Selection(selection=WEEK,
    string='Semana',
    required=True,
    default=lambda self: self._calc_week_number())

  first_date = fields.Date(string='Fecha Inicio')

  end_date = fields.Date(string='Fecha Fin')

  perception_ids = fields.One2many(comodel_name='pabs.payroll.perceptions',
    inverse_name='payroll_id',
    string='Percepciones')

  deduction_ids = fields.One2many(comodel_name='pabs.payroll.deductions',
    inverse_name='payroll_id',
    string='Deducciones')

  record_count = fields.Integer(string='Enviados',
    compute='compute_record_count')

  def _calc_week_number(self):
    today = datetime.today()
    week_number = (int(today.strftime("%U")) - 1)
    if week_number < 10:
      week_number = str(week_number).zfill(2)
    else:
      week_number = str(week_number)
    self.week_number = week_number
    return week_number

  @api.onchange('week_number')
  def calc_dates(self):
    year = fields.Date.today().year
    registry_obj = self.env['pabs.payroll.registry']
    week_config_obj = self.env['week.number.config']
    year_config_obj = self.env['week.year']
    year_id = year_config_obj.search([
      ('name','=',year)],limit=1)
    if not year_id:
      raise ValidationError((
        "No se ha configurado el año en curso, favor de comunicarse con sistemas"))
    for rec in self:
      if rec.week_number:
        record = week_config_obj.search([
          ('number_week','=',rec.week_number),
          ('year','=',year_id.id)])
        if not record:
          rec.first_date = False
          rec.end_date = False
          return {
            'warning': {
              'title': ("Error en busqueda de Semana"),
              'message': "No se encontró coincidencias para la {}".format(
              dict(rec._fields['week_number'].selection).get(rec.week_number))
            }
          }
        rec.first_date = record.first_date
        rec.end_date = record.end_date
      count = registry_obj.search_count([
        ('week_number','=', self.week_number)])
      self.record_count = count
    count = registry_obj.search_count(['&',
      ('payroll_id','!=',False),
      ('payroll_contract_id','!=',False),
      ('payroll_collection_id','!=',False),
      ('week_number','=', self.week_number)])
    self.record_count = count

  def get_external_records(self):
    return {
      'name': "Nómina {}".format(dict(self._fields['week_number'].selection).get(self.week_number)),
      'type': 'ir.actions.act_window',
      'view_type': 'form',
      'domain' : [('week_number','=',self.week_number)],
      'view_mode': 'tree',
      'res_model': 'pabs.payroll.registry',
      'view_id': self.env.ref('pabs_payroll.tree_payroll_registry').id,
    }

  def compute_record_count(self):
    ### DECLARACION DE OBJETOS
    registry_obj = self.env['pabs.payroll.registry']
    count = registry_obj.search_count(['&',
      ('payroll_id','!=',False),
      ('payroll_contract_id','!=',False),
      ('payroll_collection_id','!=',False),
      ('week_number','=', self.week_number)])
    self.record_count = count
    return count

  @api.model
  def create(self, vals):
    week_config_obj = self.env['week.number.config']
    year_config_obj = self.env['week.year']
    year = fields.Date.today().year
    year_id = year_config_obj.search([
      ('name','=',year)],limit=1)
    record = week_config_obj.search([
      ('number_week','=',vals['week_number']),
      ('year','=',year_id.id)])
    vals['first_date'] = record.first_date
    vals['end_date'] = record.end_date
    return super(PabsPayrollManagement, self).create(vals)

  def update_records(self):
    ### LIMPIANDO LISTAs
    self.perception_ids = [(5,0,0)]
    self.deduction_ids = [(5,0,0)]
    ### DECLARANDO OBJETOS
    employee_obj = self.env['hr.employee']
    payroll_obj = self.env['pabs.payroll']
    payroll_contract_obj = self.env['pabs.payroll.contract']
    payroll_collection_obj = self.env['pabs.payroll.collection']
    comission_output_obj = self.env['pabs.comission.output']

    ### BUSCAMOS A TODOS LOS EMPLEADOS
    employee_ids = employee_obj.search([
      ('barcode','not in',('FIDE','PAPE','BON_INV','C8999','C0003','TRASP','DEPO','COPNO','REMAN','OXXO',False))]
    ).sorted(
      key=lambda r: r.job_id.id,reverse = True)
    ### ARRAY LIMPIO PARA INGRESAR LOS VALORES
    employees = []
    deductions = []

    all_comissions = comission_output_obj.search([
      ('payment_date','>=',self.first_date),
      ('payment_date','<=',self.end_date)])

    ### RECORREMOS EMPLEADO POR EMPLEADO
    for employee_id in employee_ids:
      
      ########## PERCEPCIONES #############
      comissions = sum(all_comissions.filtered(
        lambda r: r.comission_agent_id.id == employee_id.id
        ).mapped('actual_commission_paid'))

      ### SI TIENEN SUELDO SE AGREGA AL ARRAY
      employee_data = {
        'employee_id' : employee_id.id,
        'salary' : employee_id.salary_base or 0,
        'commission' : comissions or 0
      }
      ### BUSCAMOS LAS COMISIONES 


      ### BUSCAMOS LOS APOYOS
      payroll_sec_id = payroll_obj.search([
        ('state','=','to review'),
        ('week_number','=', self.week_number),
        ('warehouse_id','=',employee_id.warehouse_id.id)])
      ### SI ENCONTRAMOS LA INFORMACION
      if payroll_sec_id:
        ### FILTRAMOS LOS REGISTROS Y MAPEAMOS EL VALOR
        records = payroll_sec_id.support_ids.filtered(
          lambda r: r.employee_id.id == employee_id.id)
        ### VALOR DE AYUDAS
        supports = records.mapped('five_hundred_support')
        ### VALOR DE BONO POR PRODUCTIVIDAD
        productivity = records.mapped('productivity_bonus')
        ### AGREGAMOS EL VALOR AL DICCIONARIO DE DATOS
        employee_data.update({
          'support_training' : supports[0] if supports else 0,
          'productivity_bonus' : productivity[0] if productivity else 0,
        })
        ### FILTRAMOS LOS REGISTROS Y MAPEAPOS EL VALOR DE INVERSION ALTA
        inv_high = payroll_sec_id.high_investment_ids.filtered(
          lambda r: r.employee_id.id == employee_id.id)
        ### VALOR POR INVERSIÓN ALTA
        inv_high_value = inv_high.mapped('total')
        ### AGREGAMOS EL VALOR DE INVERSION ALTA AL DICCIONARIO DE DATOS
        employee_data.update({
          'inv_investment' : inv_high_value[0] if inv_high_value else 0,
        })
      ### BUSCAMOS LA INFORMACIÓN DE CONTRATOS DE SUELDOS..
      payroll_contract_id = payroll_contract_obj.search([
        ('state','=','to review'),
        ('week_number','=',self.week_number),
        ('warehouse_id','=',employee_id.warehouse_id.id)])
      ### SI ENCONTRAMOS LA INFORMACION
      if payroll_contract_id:
        ### FILTRAMOS LOS REGISTROS Y MAPEAMOS EL SUELDO..
        contract_salary = payroll_contract_id.salary_ids.filtered(
          lambda r: r.employee_id.id == employee_id.id).mapped('salary')
        ### AGREGAMOS EL VALOR AL DICCIONARIO DE DATOS
        employee_data.update({
          'salary_assistant' : contract_salary[0] if contract_salary else 0,
        })
      ### GUARDAMOS TODA LA INFORMACION EN UN ARRAY
      employees.append([0,0,employee_data])
      contract_discount = 0

      ############# DEDUCCIONES ##############################

      ### RECORREMOS LOS CONTRATOS DONDE EL ASISTENTE ES PROPIETARIO
      for contract in employee_id.own_contracts:
        ### SI ES DESCUENTO VÍA NOMINA
        if contract.payroll_discount:
          ### SI EL PAGO ES SEMANAL
          if contract.way_to_payment == 'weekly':
            contract_discount += contract.payment_amount
          ### SI EL PAGO ES QUINCENAL
          elif contract.way_to_payment == 'biweekly':
            contract_discount += (contract.payment_amount / 2)
          ### SI EL PAGO ES MENSUAL
          elif contract.way_to_payment == 'monthly':
            contract_discount += (contract.payment_amount / 4)
          ### SI NO ESTA ESTABLECIDO UNA FORMA DE PAGO
          else:
            contract_discount += 0
      ### AGREGAMOS LA INFORMACION A UN ARRAY DE DEDUCCIONES
      deductions.append([0,0,{
        'employee_id' : employee_id.id,
        'funeral_package' : contract_discount
      }])
    self.perception_ids = employees
    self.deduction_ids = deductions

  def print_report(self):
    ### DEFINIMOS SI ES NOMINA O PRENOMINA
    type_file = "Nómina" if self.state == 'to review' else "Pre Nomina"
    ### DEFINIMOS LA SEMANA A LA QUE PERTENECE
    week = dict(self._fields['week_number'].selection).get(self.week_number)
    title = "{} de {}".format(type_file, week)
    data = {
      "title" : title,
    }
    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_payroll.prepayroll_report_xlsx').report_action(self, data=data)

  ### GENERAMOS UN CONTRAINT PARA EVITAR QUE SE DUPLIQUEN REGISTROS
  _sql_constraints = [
    ('unique_payroll_management',
      'UNIQUE(week_number)',
      'No se puede crear el registro: solo puede existir un registro por Semana'),
    ]

class PayrollReportXLS(models.AbstractModel):
  _name = 'report.pabs_payroll.pabs_payroll_xlsx_report'
  _inherit = 'report.report_xlsx.abstract'

  ### GENERAMOS EL REPORTE EN XLSX
  def generate_xlsx_report(self, workbook, data, rec):
    ### SI SE ENVIÓ EL TITULO
    if data.get('title'):
      ### AGREGAMOS EL NOMBRE A LA HOJA
      sheet = workbook.add_worksheet(data.get('title'))
    ### SI NO
    else:
      ### SOLAMENTE ESCRIBIMOS LA HOJA CON EL NOMBRE DE "NOMINA"
      sheet = workbook.add_worksheet("Nómina")

    ### ESTILOS DE CELDAS
    bold_format = workbook.add_format({'bold': True,'border' : True})
    total_format = workbook.add_format({'bold': True,'border' : True, 'font_color' : '#2978F8', 'text_wrap': True})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy', 'text_wrap': True})
    money_format = workbook.add_format({'num_format': '$#,##0.00', 'text_wrap': True})
    acumulated_format = workbook.add_format({'num_format': '$#,##0.00', 'bold' : True, 'bottom': True, 'text_wrap': True})

    ### ESCRIBIMOS LOS ENCABEZADOS DE LA TABLA
    for row, row_data in enumerate(HEADERS):
      ### SI SON TOTALES
      if row in(31,42,43):
        sheet.write(0,row,row_data,total_format)
      ### SI NO
      else:
        sheet.write(0,row,row_data,bold_format)

    ### TRAEMOS LOS REGISTROS
    perceptions = rec.perception_ids
    deductions = rec.deduction_ids

    for index, line in enumerate(perceptions):
      index += 1
      employee_id = line.employee_id
      ### FECHA DE INGRESO
      sheet.write(index, 0, employee_id.date_of_admission or '', date_format)
      ### CÓDIGO
      sheet.write(index, 1, employee_id.barcode or '')
      ### EMPLEADO
      sheet.write(index, 2, employee_id.name or '')
      ### PUESTO
      sheet.write(index, 3, employee_id.job_id.name or '')
      if employee_id.job_id.name == 'ASISTENTE SOCIAL':
        office_name = employee_id.warehouse_id.name
      else:
        office_name = employee_id.department_id.name
      ### OFICINA
      sheet.write(index, 4, office_name or '')
      ### ESQUEMA
      sheet.write(index, 5, employee_id.payment_scheme.name or '')
      ### SUELDO
      sheet.write(index, 6, employee_id.salary_base or '', money_format)
      ### SEPTIMO DÍA
      sheet.write(index, 7, line.seventh_day or '', money_format)
      ### HORAS EXTRA
      sheet.write(index, 8, line.extra or '', money_format)
      ### DIA FESTIVO
      sheet.write(index, 9, line.fest_day or '', money_format)
      ### COMISION
      sheet.write(index, 10, line.commission or '', money_format)
      ### RETROACTIVO
      sheet.write(index, 11, line.retroactive or '', money_format)
      ### COMISION GARANTIA
      sheet.write(index, 12, line.waranty_commission or '', money_format)
      ### APOYO CAPACITACION
      sheet.write(index, 13, line.support_training or '', money_format)
      ### BONO TIPO DE VENTA
      sheet.write(index, 14, line.bond_tip_sale or '', money_format)
      ### SUELDO ASISTENCIA
      sheet.write(index, 15, line.salary_assistant or '', money_format)
      ### PERIODO DE APOYO
      sheet.write(index, 16, line.support_period or '', money_format)
      ### GRATIFICACION
      sheet.write(index, 17, line.gratification or '', money_format)
      ### BONO POR RECOMENDAR
      sheet.write(index, 18, line.referral_bonus or '', money_format)
      ### INV ALTA
      sheet.write(index, 19, line.inv_investment or '', money_format)
      ### BONO POR EFECTIVIDAD
      sheet.write(index, 20, line.effective_bonus or '', money_format)
      ### PRIMA DOMINICAL
      sheet.write(index, 21, line.sunday_premium or '', money_format)
      ### PRIMA VACACIONAL
      sheet.write(index, 22, line.vacation_pay or '', money_format)
      ### BONO PRODUCTIVIDAD
      sheet.write(index, 23, line.productivity_bonus or '', money_format)
      ### APOYO DE GASOLINA
      sheet.write(index, 24, line.fuel_support or '', money_format)
      ### APOYO RIF
      sheet.write(index, 25, line.rif_support or '', money_format)
      ### BONO MENSUAL
      sheet.write(index, 26, line.monthly_bouns or '', money_format)
      ### VALES DE DESPENSA
      sheet.write(index, 27, line.food_allowances or '', money_format)
      ### PRESTAMO CAJA AHORRO
      sheet.write(index, 28, line.loan or '', money_format)
      ### PRESTAMO EMPRESA
      sheet.write(index, 29, line.loan_company or '', money_format)
      ### APOYO CAMBIO DE PLAZA
      sheet.write(index, 30, line.change or '', money_format)
      ### TOTAL PERCEPCIONES
      sheet.write(index, 31, line.total or '', money_format)

      ### BUSCAMOS LAS DEDUCIONES
      deduction = deductions.filtered(
        lambda r: r.employee_id.id == employee_id.id)
      ### IMSS
      sheet.write(index, 32, deduction.imss or '', money_format)
      ### DESCUENTO POR TIP DE VENTA
      sheet.write(index, 33, deduction.discount_tip_sale or '', money_format)
      ### CAJA DE AHORRO
      sheet.write(index, 34, deduction.saving_bank or '', money_format)
      ### PRESTAMO CAJA DE AHORRO
      sheet.write(index, 35, deduction.sparkasse_loan or '', money_format)
      ### PRESTAMO PROBENSO
      sheet.write(index, 36, deduction.probenso_loan or '', money_format)
      ### PRESTAMO EMPRESA
      sheet.write(index, 37, deduction.company_loan or '', money_format)
      ### FONDO DE AHORRO
      sheet.write(index, 38, deduction.saving_fund or '', money_format)
      ### INFONAVIT
      sheet.write(index, 39, deduction.infonavit or '', money_format)
      ### PAQUETE FUNERARIO
      sheet.write(index, 40, deduction.funeral_package or '', money_format)
      ### COMISIONES ANTICIPADAS
      sheet.write(index, 41, deduction.anticipated_sales_comission or '', money_format)
      ### TOTAL DEDUCCIONES
      sheet.write(index, 42, deduction.total or '', money_format)
      ### NETO
      neto = (line.total - deduction.total)
      sheet.write(index, 43, neto, money_format)
    index +=1
    ### INSERTAMOS TOTALES
    sheet.write_formula(index, 6, '=SUM(G1:G%s)' % index, acumulated_format)
    sheet.write_formula(index, 7, '=SUM(H1:H%s)' % index, acumulated_format)
    sheet.write_formula(index, 8, '=SUM(I1:I%s)' % index, acumulated_format)
    sheet.write_formula(index, 9, '=SUM(J1:J%s)' % index, acumulated_format)
    sheet.write_formula(index, 10, '=SUM(K1:K%s)' % index, acumulated_format)
    sheet.write_formula(index, 11, '=SUM(L1:L%s)' % index, acumulated_format)
    sheet.write_formula(index, 12, '=SUM(M1:M%s)' % index, acumulated_format)
    sheet.write_formula(index, 13, '=SUM(N1:N%s)' % index, acumulated_format)
    sheet.write_formula(index, 14, '=SUM(O1:O%s)' % index, acumulated_format)
    sheet.write_formula(index, 15, '=SUM(P1:P%s)' % index, acumulated_format)
    sheet.write_formula(index, 16, '=SUM(Q1:Q%s)' % index, acumulated_format)
    sheet.write_formula(index, 17, '=SUM(R1:R%s)' % index, acumulated_format)
    sheet.write_formula(index, 18, '=SUM(S1:S%s)' % index, acumulated_format)
    sheet.write_formula(index, 19, '=SUM(T1:T%s)' % index, acumulated_format)
    sheet.write_formula(index, 20, '=SUM(U1:U%s)' % index, acumulated_format)
    sheet.write_formula(index, 21, '=SUM(V1:V%s)' % index, acumulated_format)
    sheet.write_formula(index, 22, '=SUM(W1:W%s)' % index, acumulated_format)
    sheet.write_formula(index, 23, '=SUM(X1:X%s)' % index, acumulated_format)
    sheet.write_formula(index, 24, '=SUM(Y1:Y%s)' % index, acumulated_format)
    sheet.write_formula(index, 25, '=SUM(Z1:Z%s)' % index, acumulated_format)
    sheet.write_formula(index, 26, '=SUM(AA1:AA%s)' % index, acumulated_format)
    sheet.write_formula(index, 27, '=SUM(AB1:AB%s)' % index, acumulated_format)
    sheet.write_formula(index, 28, '=SUM(AC1:AC%s)' % index, acumulated_format)
    sheet.write_formula(index, 29, '=SUM(AD1:AD%s)' % index, acumulated_format)
    sheet.write_formula(index, 30, '=SUM(AE1:AE%s)' % index, acumulated_format)
    sheet.write_formula(index, 31, '=SUM(AF1:AF%s)' % index, acumulated_format)
    sheet.write_formula(index, 32, '=SUM(AG1:AG%s)' % index, acumulated_format)
    sheet.write_formula(index, 33, '=SUM(AH1:AH%s)' % index, acumulated_format)
    sheet.write_formula(index, 34, '=SUM(AI1:AI%s)' % index, acumulated_format)
    sheet.write_formula(index, 35, '=SUM(AJ1:AJ%s)' % index, acumulated_format)
    sheet.write_formula(index, 36, '=SUM(AK1:AK%s)' % index, acumulated_format)
    sheet.write_formula(index, 37, '=SUM(AL1:AL%s)' % index, acumulated_format)
    sheet.write_formula(index, 38, '=SUM(AM1:AM%s)' % index, acumulated_format)
    sheet.write_formula(index, 39, '=SUM(AN1:AN%s)' % index, acumulated_format)
    sheet.write_formula(index, 40, '=SUM(AO1:AO%s)' % index, acumulated_format)
    sheet.write_formula(index, 41, '=SUM(AP1:AP%s)' % index, acumulated_format)
    sheet.write_formula(index, 42, '=SUM(AQ1:AQ%s)' % index, acumulated_format)
    sheet.write_formula(index, 43, '=SUM(AR1:AR%s)' % index, acumulated_format)
    sheet.freeze_panes(1, 3)
