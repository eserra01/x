# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

import openpyxl
import base64
from io import BytesIO
import logging

TIPOS = [
  ('complete', 'Cartera completa'),
  ('partial', 'Cartera parcial')  
]

_logger = logging.getLogger(__name__)

class TransferPortfolioPartners(models.Model):
  _name = 'pabs.transfer.portfolio.partners'
  _description = 'Traspaso de Cartera de Clientes'
  
  tipo = fields.Selection(TIPOS, string = "Tipo de transferencia", default="complete", required=True)

  collector_origin_id = fields.Many2one(comodel_name= 'hr.employee', string='Cobrador Origen')
  collector_dest_id = fields.Many2one(comodel_name='hr.employee', string='Cobrador Destino')
  
  file = fields.Binary(string="Archivo")
  file_name = fields.Char(string="Archivo")
  info = fields.Char(string="Resultados", default="Nota: El primer contrato debe estár en la celda A5 y el codigo de cobrador destino en columna K. No dejes filas en blanco entre los registros.")

  def transfer_parnters(self):
    con_obj = self.env['pabs.contract']
    id_compania = self.env.company.id
    pabs_log_obj = self.env['pabs.log']
    pabs_log = "" 

    ###############     TRANSFERENCIA COMPLETA     ###############
    if self.tipo == 'complete':

      ### Consultar contratos del cobrador de origen
      lista_contratos = con_obj.search([
        ('company_id', '=', id_compania),
        ('contract_status_item.status', 'in', ('REALIZADO POR COBRAR','SUSP. TEMPORAL','ACTIVO')),
        ('debt_collector', '=', self.collector_origin_id.id)
      ])

      if not lista_contratos:
        raise ValidationError(("El cobrador {} no tiene ningún contrato asignado".format(self.collector_origin_id.name)))
      
      ### Crear comentarios en contratos
      mail_obj = self.env['mail.message']

      cobrador_origen = "{} {}".format(self.collector_origin_id.barcode, self.collector_origin_id.name)
      cobrador_destino = "{} {}".format(self.collector_dest_id.barcode, self.collector_dest_id.name)

      #
      pabs_log += f"<p>Cambio de cobrador: {cobrador_origen}->{cobrador_destino}</p>"
      pabs_log += "<p>Contratos:</p>"
      cantidad_contratos = len(lista_contratos)
      i = 0
      for index, con in enumerate(lista_contratos, 1):
        _logger.info("{} de {}. Transfiriendo cartera completa: {} -> {}".format(index, cantidad_contratos, con.name, cobrador_destino))

        values = {
          'body': "<p>" + "Cambio de cobrador: {} -> {}".format(cobrador_origen, cobrador_destino) + "</p>",
          'model': 'pabs.contract',
          'message_type': 'comment',
          'no_auto_thread': False,
          'res_id': con.id
        }
        
        mail_obj.create(values)
        #        
        if i >= 20:
          i = 0
          pabs_log += "<br/>"
        i += 1
        pabs_log += f"{con.name}, "
      #
      pabs_log_obj.create({'detail': pabs_log, 'user_id': self.env.user.id,'topic_id': 'tdc'})

      ### Actualizar por sql
      ids = str(lista_contratos.ids)
      ids = ids.replace('[', '')
      ids = ids.replace(']', '')

      query = "UPDATE pabs_contract SET debt_collector = {}, assign_collector_date = CAST(NOW() AS DATE) WHERE id IN ({})".format(self.collector_dest_id.id, ids)

      _logger.info("Ejecutando query de transferencia de cartera: {}".format(cobrador_destino))
      self.env.cr.execute(query)

    ###############     TRANSFERENCIA PARCIAL     ###############
    elif self.tipo == 'partial':
      mail_obj = self.env['mail.message']

      ### Consultar cobradores
      lista_cobradores = []

      obj_cob = self.env['hr.employee'].search([
        ('company_id', '=', id_compania), 
        ('employee_status.name', '=', 'ACTIVO'),
        '|', ('job_id.name', 'ilike', 'COBRA'),
        ('job_id.name', 'ilike', 'SUPER')
      ])

      for cob in obj_cob:
        lista_cobradores.append({
          'id': cob.id,
          'codigo': cob.barcode,
          'nombre': cob.name
        })

      ### Leer archivo
      wb = openpyxl.load_workbook( 
      filename=BytesIO(base64.b64decode(self.file)), read_only=True)
      ws = wb.active
                
      records = ws.iter_rows(min_row=5, max_row=None, min_col=1, max_col=13, values_only=True)

      ### En esta iteración se crean los comentarios en los contratos y se construye una cadena sql de actualizacion
      query = ""
      for fila in records:
        pabs_log = ""
        numero_contrato = fila[0]
        codigo_cobrador = fila[10]

        if not numero_contrato:
          break
        
        if codigo_cobrador:
          ### Validar contrato
          con = con_obj.search([
            ('company_id', '=', id_compania),
            ('name', '=', numero_contrato)
          ])

          if not con:
            raise ValidationError("No se encontró el contrato {}".format(numero_contrato))
          
          ### Validar cobrador
          cob = next((x for x in lista_cobradores if codigo_cobrador == x['codigo']), 0)

          if not cob:
            raise ValidationError("No se encontró el cobrador {}\nVerifique que su estatus sea ACTIVO y su puesto sea COBRADOR o SUPERVISOR".format(codigo_cobrador))
          
          if codigo_cobrador != con.debt_collector.barcode:
            _logger.info("Transfiriendo cartera parcial: {} -> {} {}".format(numero_contrato, cob['codigo'], cob['nombre']))
            query = query + "UPDATE pabs_contract SET debt_collector = {}, assign_collector_date = CAST(NOW() AS DATE) WHERE id = {};".format(cob['id'], con['id'])

            ### Crear comentario en el contrato
            values = {
              'body': "<p>" + "Cambio de cobrador: {} {} -> {} {}".format(con.debt_collector.barcode, con.debt_collector.name, cob['codigo'], cob['nombre']) + "</p>",
              'model': 'pabs.contract',
              'message_type': 'comment',
              'no_auto_thread': False,
              'res_id': con.id
            }
            
            mail_obj.create(values)
            pabs_log += f"<p>Cambio de cobrador: {con.debt_collector.barcode} {con.debt_collector.name} -> {cob['codigo']} {cob['nombre']}</p>"
            pabs_log += f"<p>Contrato: {con.name}</p>"
            pabs_log_obj.create({'detail': pabs_log, 'user_id': self.env.user.id,'topic_id': 'tdc'})

      ### Actualizar por sql
      if query:
        _logger.info("Ejecutando query de transferencia de cartera parcial")
        self.env.cr.execute(query)