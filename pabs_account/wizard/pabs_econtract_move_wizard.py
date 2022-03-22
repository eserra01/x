# -*- coding: utf-8 -*-

from logging.config import valid_ident
from odoo import api, models, fields
from odoo.exceptions import ValidationError

from datetime import datetime
import requests
import logging
import json

import pytz
tz = pytz.timezone('America/Mexico_City')

_logger = logging.getLogger(__name__)

CUENTA_TRANSITO = "101.01.005"
NOMBRE_CUENTA_TRANSITO = "Caja transito"

CUENTA_CONTRATOS_ELECTRONICOS = "101.01.004"
NOMBRE_CUENTA_ELECTRONICOS = "Caja Contratos Electronicos"

CUENTA_CAJA_CONTRATOS = "101.01.002"

class PabsAccountMove(models.TransientModel):
    _name = 'pabs.econtract.move.wizard'
    _descripcion = "Generador de pólizas de Inversiones y Excedentes de afiliaciones electrónicas"

    fecha_inicio = fields.Date(string = 'Fecha inicial de Corte')
    fecha_fin = fields.Date(string = 'Fecha final de Corte')

    json_contratos = fields.Text(string="json_contratos")

    texto_cierres = fields.Text(string="Afiliaciones")
    
    cantidad_contratos = fields.Integer(string = "Cantidad de contratos")
    total_inversiones = fields.Float(string = "Total de inversiones")

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    @api.onchange('fecha_fin')
    def ConsultarAfiliaciones(self):

        if not self.fecha_inicio or not self.fecha_fin:
            self.cantidad_contratos = 0
            self.total_inversiones = 0
            return

        if self.fecha_inicio > self.fecha_fin:
            self.cantidad_contratos = 0
            self.total_inversiones = 0
            return {'warning': {'title': ('Atención'), 'message': "La fecha inicial no puede ser mayor que la fecha final"}}
        
        id_compania = self.env.company.id

        if not id_compania:
            raise ValidationError("No está asignada una compañia")

        ### Buscar contratos de la oficina en el cierre que no tenga la póliza generada ###
        lista_contratos = self.env['pabs.econtract.move'].search([
            ('company_id', '=', id_compania),
            ('fecha_hora_cierre', '>=', '{} 00:00:00'.format(self.fecha_inicio) ),
            ('fecha_hora_cierre', '<=', '{} 23:59:59'.format(self.fecha_fin) ),
            ('estatus', '=', 'cerrado'),
            ('id_poliza_caja_transito', '!=', False),
            ('id_poliza_caja_electronicos', '=', False)
        ])

        if not lista_contratos:
            self.cantidad_contratos = 0
            self.total_inversiones = 0
            return {'warning': {'title': ('Atención'), 'message': "No hay contratos"}}

        contratos = []
        texto_cierres = ""
        total_inversiones = 0
        for con in lista_contratos:
            contratos.append({
                'id_cierre': con.id,
                'contrato': con.id_contrato.name,
                'inversion': con.id_contrato.initial_investment
            })

            #texto_cierres = texto_cierres + "{}     ->     {}".format(con.id_contrato.name, con.id_contrato.initial_investment) + "\n"
            total_inversiones = total_inversiones + con.id_contrato.initial_investment
            
        #self.texto_cierres = texto_cierres
        self.cantidad_contratos = len(lista_contratos)
        self.total_inversiones = total_inversiones
        
        self.json_contratos = json.dumps(contratos)

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def btnCrearPolizas(self):
        _logger.info("Comienza creación de pólizas de cierre")

        json_contratos = json.loads(self.json_contratos)

        company = self.env['res.company'].browse(self.env.company.id)

        if not company:
            raise ValidationError("No se definió una compañía")

        ### Validación de cuentas ###
        id_cuenta_transito = self.env['account.account'].search([
            ('company_id', '=', company.id),
            ('code', '=', CUENTA_TRANSITO)
        ]).id

        if not id_cuenta_transito:
            raise ValidationError("No se encontró la cuenta {} - {}".format(CUENTA_TRANSITO, NOMBRE_CUENTA_TRANSITO))
            
        id_cuenta_electronicos = self.env['account.account'].search([
            ('company_id', '=', company.id),
            ('code', '=', CUENTA_CONTRATOS_ELECTRONICOS)
        ]).id

        if not id_cuenta_electronicos:
            raise ValidationError("No se encontró la cuenta {} - {}".format(CUENTA_CONTRATOS_ELECTRONICOS, NOMBRE_CUENTA_ELECTRONICOS))

        journal_id = company.account_journal_id.id

        if not journal_id:
            raise ValidationError("No se encontró el diario en la compañia")

        ### Iterar en lista de contratos ###
        cantidad_contratos = len(json_contratos)
        for index, con in enumerate(json_contratos): 
            _logger.info("{} de {}. {}".format(index + 1, cantidad_contratos, con['contrato']))

            id_poliza = self.CrearPoliza(company.id, journal_id, id_cuenta_transito, id_cuenta_electronicos, con)

            if id_poliza:
                ### Actualizar registro de cierre
                cierre = self.env['pabs.econtract.move'].browse(con['id_cierre'])
                cierre.write({
                    'estatus': 'confirmado',
                    'id_poliza_caja_electronicos': id_poliza
                })
                _logger.info("Se actualizó información de cierre")

#  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -

    def CrearPoliza(self, company_id, journal_id, id_cuenta_transito, id_cuenta_electronicos, con):
        ### Buscar si ya existe una poliza ###
        existe_poliza = self.env['account.move'].search([
            ('company_id', '=', company_id),
            ('ref', '=', con['contrato']),
            ('line_ids.account_id', '=', id_cuenta_electronicos),
            ('line_ids.debit', '>', 0)
        ])

        if len(existe_poliza) > 1:
            mensaje = "Existe mas de una póliza para el contrato {}".format(con['contrato'])
            _logger.warning(mensaje)
            raise ValidationError(mensaje)

        if existe_poliza:
            mensaje = "Ya existe la poliza para el contrato {}".format(existe_poliza.name)
            _logger.warning(mensaje)
            raise ValidationError(mensaje)

        ### Lineas del asiento ###
        apuntes = []
        apuntes.append([0,0,
        {
            'account_id': id_cuenta_transito,
            'name': con['contrato'],
            'debit': 0,
            'credit': con['inversion']
        }])

        apuntes.append([0,0,
        {
            'account_id': id_cuenta_electronicos,
            'name': con['contrato'],
            'debit': con['inversion'],
            'credit': 0
        }])

        ### Encabezado del asiento ###
        asiento = {
            'ref' : con['contrato'],
            'date' : datetime.now(tz).date(),
            'journal_id' : journal_id,
            'company_id' : company_id,
            'line_ids' : apuntes
        }

        # Crear póliza
        move = self.env['account.move'].create(asiento)
        
        # Validar póliza
        move.action_post()
        _logger.info("Se creó y validó póliza {}".format(move.id))

        return move.id