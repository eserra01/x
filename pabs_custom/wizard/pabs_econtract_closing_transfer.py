# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import datetime

class PabsEcontractClosingTransfer(models.TransientModel):
  _name = 'pabs.econtract.closing.transfer'
  _description = 'Corte de afiliaciones electrónicas'

  warehouse_id = fields.Many2one(comodel_name='stock.warehouse', required=True, string='Oficina')
  date_closing = fields.Date(string='Fecha de cierre', required=True, default=fields.Date.today())

  def ImprimirCierre(self):
    if not self.warehouse_id:
      raise ValidationError("Elige una oficina")

    ### Consultar registros de corte ###
    cierres = self.env['pabs.econtract.move'].search([
      ('company_id', '=', self.env.company.id),
      ('id_contrato.lot_id.warehouse_id.id', '=', self.warehouse_id.id),
      ('estatus', '=', 'cerrado'),
      ('fecha_hora_cierre', '>=', datetime(self.date_closing.year, self.date_closing.month, self.date_closing.day, 0, 0, 0) ), 
      ('fecha_hora_cierre', '<=', datetime(self.date_closing.year, self.date_closing.month, self.date_closing.day, 23, 59, 59) )
    ])

    if not cierres:
      raise ValidationError("No hay afiliaciones")

    cierres = cierres.sorted(key=lambda x: x.id_asistente.name and x.id_contrato.name)

    ### Llenar datos que se enviarán al reporte ###
    detalle_contratos = []
    total_inversiones = 0
    for indice, con in enumerate(cierres):
      detalle_contratos.append({
        'indice': indice + 1,
        'codigo': con.id_asistente.barcode,
        'asistente': con.id_asistente.name,
        'plan': con.id_contrato.name_service.name,
        'contrato': con.id_contrato.name,
        'inversion_inicial': con.id_contrato.initial_investment,
        'tipo_digital': dict(con.id_contrato._fields['digital_type'].selection).get(con.id_contrato.digital_type),
      })

      total_inversiones = total_inversiones + con.id_contrato.initial_investment

    cantidad_contratos = len(cierres)

    nombre_almacen = self.warehouse_id.name
    fecha = self.date_closing

    data = {
      'create_uname' : self.env.user.name,
      'detalle_contratos': detalle_contratos,
      'cantidad_contratos': cantidad_contratos,
      'total_inversiones': total_inversiones,
      'nombre_almacen': nombre_almacen,
      'fecha': fecha
    }

    ### Llamar reporte ###
    return self.env.ref('pabs_custom.pabs_econtract_closing_transfer_action').report_action(self, data = data)

class PabsEcontractClosingTransferReport(models.Model):
  _name = 'report.pabs_custom.pabs_econtract_closing_transfer_action'

  @api.model
  def _get_report_values(self, docids, data):
    return {
      'create_uname' : data['create_uname'],
      'detalle_contratos' : data['detalle_contratos'],
      'cantidad_contratos' : data['cantidad_contratos'],
      'total_inversiones' : data['total_inversiones'],
      'nombre_almacen' : data['nombre_almacen'],
      'fecha' : data['fecha']
    }