# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil import tz

HEADERS = [
  {'name': 'Código', 'width': 10},
  {'name':'Nombre', 'width': 50},
  {'name':'No. de pago', 'width': 20},
  {'name':'Fecha de pago', 'width': 15},
  {'name':'Contrato', 'width': 15},
  {'name':'Importe', 'width': 15},
  {'name':'Empresa', 'width': 15}
]

class PabsCommissionAS(models.TransientModel):
  _name = 'pabs.commissions.as'
  _description = 'Reporte de comisiones de asistente social por periodo'

  start_date = fields.Date(string='Fecha Inicial', required=True)
  end_date = fields.Date(string='Fecha Final', required=True)
  all = fields.Boolean(string="Todos los asistentes", default=True)
  agent_id = fields.Many2one(string='Agente', comodel_name='hr.employee')

  def generate_xlsx_report(self):
    data = {
      'ids': self.ids,
      'model': self._name,
      'form': 
      {
        'date_start': self.start_date,
        'date_end': self.end_date,
        'all': self.all,
        'agent_id': self.agent_id.id
      },
    }
    ### RETORNAMOS EL REPORTE
    return self.env.ref('pabs_reports.pabs_commissions_as_xlsx').report_action(self, data=data)

##########################################################
########## VERSION ODOO 13 (DETALLADO POR PAGO) ##########
##########################################################

class PabsCommissionsASReportXLSX(models.AbstractModel):
  _name = 'report.pabs_reports.pabs_commissions_as_xlsx'
  _inherit = 'report.report_xlsx.abstract'
  _description = ''

  def generate_xlsx_report(self, workbook, data, lines):
    fecha_inicial = data['form']['date_start']
    fecha_final = data['form']['date_end']
    id_empleado = data['form']['agent_id']
    all_employees = data['form']['all']

    ### Obtener razones sociales por prefijo
    razones = self.env['pabs.companies.by.contract'].search([
        ('company_id', '=', self.env.company.id)
    ])

      # Ordenar para evaluar las opciones mas específicas primero
    razones = razones.sorted(key = lambda x: len(x.prefix_contract), reverse = True)

    ### Consultar datos
    consulta = """
      SELECT 
        per.barcode as codigo,
        per.name as comisionista, 
        abo.name as abono,
        abo.payment_date as fecha_oficina,
        con.name as contrato,
        com.actual_commission_paid as comision
      FROM account_payment as abo
      INNER JOIN pabs_comission_output as com on abo.id = com.payment_id
      INNER JOIN pabs_contract as con on abo.contract = con.id
      INNER JOIN hr_employee AS per ON com.comission_agent_id = per.id
      INNER JOIN hr_job AS car ON com.job_id = car.id
        WHERE abo.state IN ('posted','sent','reconciled')
        AND car.name NOT IN ('PAPELERIA', 'IVA')
        AND com.actual_commission_paid > 0
        AND con.company_id = {}
        AND abo.payment_date BETWEEN '{}' AND '{}'
        zzid_empleadozz
          ORDER BY abo.payment_date, con.name
      """.format(self.env.company.id, fecha_inicial, fecha_final)

    if all_employees:
      consulta = consulta.replace('zzid_empleadozz', '')
    else:
      consulta = consulta.replace('zzid_empleadozz', 'AND per.id = {}'.format(id_empleado))

    self.env.cr.execute(consulta)

    contratos = []
    for res in self.env.cr.fetchall():
      contratos.append({
        'codigo': res[0],
        'nombre': res[1],
        'abono': res[2],
        'fecha_oficina': res[3],
        'contrato': res[4],
        'importe': res[5]
      })

    ### Generar Excel
    sheet = workbook.add_worksheet("Comisiones de asistente social")

    bold_format = workbook.add_format({'bold': True})
    date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
    money_format = workbook.add_format({'num_format': '$#,##0.00'})
      
    fila = 0
    sheet.write(fila, 1,"Comisiones por agente del {} al {}".format(fecha_inicial, fecha_final))

    fila = 2
    for index, val in enumerate(HEADERS):
      sheet.write(fila, index,val.get('name'), bold_format)
      sheet.set_column(fila, index, val.get('width'))

    for con in contratos:
      fila = fila + 1

      sheet.write(fila, 0, con['codigo'])
      sheet.write(fila, 1, con['nombre'])
      sheet.write(fila, 2, con['abono'])
      sheet.write(fila, 3, con['fecha_oficina'], date_format)
      sheet.write(fila, 4, con['contrato'])
      sheet.write(fila, 5, con['importe'], money_format)

      for raz in razones:
        if raz.prefix_contract in con['contrato']:
          sheet.write(fila, 6, raz.pabs_company.name)
          break

  # def METODO_ANTERIOR(self, workbook, data, lines):
    
  #   date_start = data['form']['date_start']
  #   date_end = data['form']['date_end']
    
  #   # SALIDAS ENTRE DOS FECHAS
  #   # Consultar id de cargo papeleria
  #   cargo_papeleria = self.env['hr.job'].search([('name','=','PAPELERIA')])
  #   cargo_iva = self.env['hr.job'].search([('name','=','IVA')])

  #   if data['form']['all']:
  #     agente = "Todos"
  #     commission_ids = self.env['pabs.comission.output'].search([
  #       ('payment_date', '>=', date_start), 
  #       ('payment_date', '<=', date_end),
  #       ('payment_status', 'in', ['posted','sent','reconciled']),
  #       ('actual_commission_paid', '!=', 0),
  #       ('job_id', 'not in', [cargo_papeleria.id, cargo_iva.id])
  #       ]
  #     )
  #   else:     
  #      agente = '-'     
  #      commission_ids = self.env['pabs.comission.output'].search([
  #       ('payment_date', '>=', date_start), 
  #       ('payment_date', '<=', date_end),
  #       ('payment_status', 'in', ['posted','sent','reconciled']),
  #       ('actual_commission_paid', '!=', 0),
  #       ('job_id', 'not in', [cargo_papeleria.id, cargo_iva.id]),
  #       ('comission_agent_id','=',data['form']['agent_id'])
  #       ]
  #     )

  #   ### GENERAMOS LA HOJA
  #   sheet = workbook.add_worksheet("Comisiones de asistente social")

  #   ### AGREGAMOS FORMATOS
  #   bold_format = workbook.add_format({'bold': True})
  #   date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
  #   money_format = workbook.add_format({'num_format': '$#,##0.00'})

      
  #   sheet.write(0, 1,"Comisiones por agente del %s al %s"%(date_start,date_end))
  #   sheet.write(1, 1,"Agente: %s"%(agente))
  #   row = 4
  #   ### INSERTAMOS LOS ENCABEZADOS PARA EL FORMATO
  #   for index, val in enumerate(HEADERS):
  #     sheet.write(row-1, index,val.get('name'), bold_format)
  #     sheet.set_column(row-1, index, val.get('width'))

  #   total = 0
  #   ### INSERTAMOS LA INFORMACIÓN 
  #   for commission in commission_ids:
  #     ### GENERAMOS LOS INDEX
  #     count = 0
  #     total += commission.actual_commission_paid
  #     ### ESCRIBIMOS 
  #     sheet.write(row, 0, commission.comission_agent_id.barcode or "")
  #     sheet.write(row, 1, commission.comission_agent_id.name or "")
  #     sheet.write(row, 2, commission.payment_id.name or "")
  #     sheet.write(row, 3, str(commission.payment_id.payment_date) or "")
  #     sheet.write(row, 4, commission.payment_id.contract.name or "")
  #     sheet.write(row, 5, commission.actual_commission_paid or "")
  #     # count+=1
  #     row+=1
    
  #   if not data['form']['all']:
  #     sheet.write(row, 4, "Total", bold_format)
  #     sheet.write(row, 5, total or "", )