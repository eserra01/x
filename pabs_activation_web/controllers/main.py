# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request, Response
import json
import logging

_logger = logging.getLogger(__name__)

class ActivationWeb(http.Controller):

  @http.route('/main/activation', auth="user", type="http")
  def get_main_page(self):
    company_obj = request.env['res.company'].sudo()
    company_ids = company_obj.search([])
    values = []
    for company_id in company_ids:
      values.append('<option value="{}">{}</option>'.format(company_id.id, company_id.name))
    return request.render('pabs_activation_web.main_page_activation', {'company_ids': values})

  @http.route('/main/company', auth="none", type='http', methods=['POST'],csrf=False)
  def get_company_values(self, **kargs):
    ### Encabezado
    response_header = {'Content-Type': 'application/json'}
    ### Declaración de objetos
    municipality_obj = request.env['res.locality']
    neighborhood_obj = request.env['colonias']
    ### Sí el post viene con compañia
    if kargs.get('company_id'):
      company_id = int(kargs.get('company_id'))
      data = {}
      municipality_rec = []
      neighborhood_rec = []
      municipality_ids = municipality_obj.sudo().search([
        ('company_id','=',company_id)])
      for municipality_id in municipality_ids:
        municipality_rec.append({
          'id' : municipality_id.id,
          'name' : municipality_id.name,
        })
      data.update({'municipality_id' : municipality_rec})
      neighborhood_ids = neighborhood_obj.sudo().search([
        ('company_id','=',company_id)])
      for neighborhood_id in neighborhood_ids:
        neighborhood_rec.append({
          'id' : neighborhood_id.id,
          'name' : neighborhood_id.name,
        })
      data.update({'neighborhood_id' : neighborhood_rec})
      response = {'result' : data}
      return Response(json.dumps(response),headers=response_header)
    return Response({"error" : []}, status=400)

  @http.route("/main/check/serie", auth="none",type="http", methods=['POST'], csrf=False)
  def check_serie(self, **kargs):
    response_header = {'Content-Type': 'application/json'}
    ### DECLARACION DE OBJETOS
    lot_obj = request.env['stock.production.lot'].sudo()
    stock_quant_obj = request.env['stock.quant'].sudo()
    payment_scheme_obj = request.env['pabs.payment.scheme'].sudo()
    contract_obj = request.env['pabs.contract'].sudo()

    salary_id = payment_scheme_obj.search([
      ('name','=','SUELDO')])

    message = ""
    result = {}

    ### VALIDAMOS LA INFORMACIÓN ENVIADA POR EL POST
    if kargs.get('company_id'):
      company_id = int(kargs.get('company_id'))
    if kargs.get('lot_id'):
      lot_name = kargs.get('lot_id');
    else:
      lot_name = ''
    ### BUSCAMOS LA SOLICITUD
    lot_id = lot_obj.search([
      ('company_id','=',company_id),
      ('name','=',lot_name)])
    if not lot_id:
      message = "No se encontró la solicitud"
      response = {'result' : {'message' : message}}
      return Response(json.dumps(response),headers=response_header)
    ### BUSCAMOS SI NO TIENE UNA ACTIVACIÓN PREVIA
    contract_id = contract_obj.search([
      ('company_id','=',company_id),
      ('lot_id','=',lot_id.id)])
    if contract_id:
      message = "El número de serie cuenta con una activación previa: {}".format(contract_id.activation_code)
      response = {'result' : {'message' : message}}
      return Response(json.dumps(response),headers=response_header)
    ### GUARDAMOS EL ASISTENTE QUE LA TIENE ASIGNADA
    employee_id = lot_id.employee_id
    if not employee_id:
      message = message + "No se encuentra asignada a un asistente\n"
      response = {'result' : {'message' : message}}
      return Response(json.dumps(response),headers=response_header)
    else:
      employee_name = "{} - {}".format(employee_id.barcode, employee_id.name) or False
      result.update({'employee' : employee_name})
    if employee_id.payment_scheme.id == salary_id.id:
      scheme_data = []
      scheme_ids = payment_scheme_obj.search([])
      for scheme_id in scheme_ids:
        scheme_data.append({
          'id' : scheme_id.id,
          'name' : scheme_id.name,
        })
      result.update({"schemes" : scheme_data})
    product_id = lot_id.product_id
    if not product_id:
      message = message + "No se encontró el servicio\n"
      response = {'result' : {'message' : message}}
      return Response(json.dumps(response),headers=response_header)
    else:
      product_name = product_id.name or False
      result.update({'product' : product_name})
    ### BUSCAMOS SU UBICACIÓN
    quant_id = stock_quant_obj.search([
      ('company_id','=',company_id),
      ('quantity','>=',1),
      ('lot_id','=',lot_id.id)],order="id desc", limit=1)
    if quant_id.location_id.consignment_location:
      response = {'result' : result}
      return Response(json.dumps(response),headers=response_header)
    else:
      message =  message + "La solicitud no puede ser activada por que se encuentra cancelada\n"
      response = {'result' : {'message' : message}}
      return Response(json.dumps(response),headers=response_header)

  @http.route("/main/activation/set", auth="none", type='http', methods=['POST'],csrf=False)
  def set_activation(self, **kargs):
    response_header = {'Content-Type': 'application/json'}
    ### DECLARACIÓN DE OBJETOS
    contract_obj = request.env['pabs.contract'].sudo()
    production_lot_obj = request.env['stock.production.lot'].sudo()
    if kargs:
      company_id = int(kargs.get('company_id'))
      lot_id = production_lot_obj.search([
        ('name','=',kargs.get('lot_id')),('company_id','=',company_id)],limit=1)
      kargs.update({
        'lot_id' : lot_id.id,
        'municipality_id' : int(kargs.get('municipality_id')),
        'neighborhood_id' : int(kargs.get('neighborhood_id')),
        'company_id' : company_id
      })
    contract_id = contract_obj.with_user(request.env.context['uid']).with_context(force_company=company_id).create(kargs)
    if contract_id:
      response = {'result' : {'activation_code' : contract_id.activation_code}}
      return Response(json.dumps(response),headers=response_header)
    response = {'result' : {'message' : 'No se pudo activar, favor de verificar son sistemas'}}
    return Response(json.dumps(response),headers=response_header)
