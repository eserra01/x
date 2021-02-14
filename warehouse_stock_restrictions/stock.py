# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning

class ResUsers(models.Model):
    _inherit = 'res.users'

    restrict_locations = fields.Boolean('Restrict Location')

    warehouse_ids = fields.Many2many(
      'stock.warehouse',
      'warehouse_security_users',
      'user_id',
      'warehouse_id',
      'Warehouses')

    stock_location_ids = fields.Many2many(
        'stock.location',
        'location_security_stock_location_users',
        'user_id',
        'location_id',
        'Stock Locations')

    default_picking_type_ids = fields.Many2many(
        'stock.picking.type', 'stock_picking_type_users_rel',
        'user_id', 'picking_type_id', string='Default Warehouse Operations')

    @api.onchange('warehouse_ids')
    def _calc_locations_domain(self):
      ### Declaración de objetos
      location_obj = self.env['stock.location']
      picking_type_obj = self.env['stock.picking.type']
      ### Lista donde se guadarán los IDS
      view_location_ids = []
      ### Recorremos todos los almacenes
      for warehouse in self.warehouse_ids:
        ### Los agregamos a la lista
        view_location_ids.append(warehouse.view_location_id.id)
      res = {}
      ### Generando diccionario para dominio dinamico
      res['domain'] = {
        'stock_location_ids' : [('id','child_of',view_location_ids)]
      }
      ### IDS de las ubicacíones correspondientes a los almacenes seleccionados
      location_ids = location_obj.search([
        ('id','child_of',view_location_ids)]).ids
      ### Se rellena la información automáticamente
      self.stock_location_ids = [(6, 0, location_ids)]
      ### Buscamos todas las operaciones de esos almacenes
      picking_type_ids = picking_type_obj.search([
        ('warehouse_id','in',self.warehouse_ids.ids)]).ids
      ### Agregamos todas las operaciones a la lista
      self.default_picking_type_ids = [(6, 0, picking_type_ids)]
      return res


class stock_move(models.Model):
    _inherit = 'stock.move'
    @api.constrains('state', 'location_id', 'location_dest_id')
    def check_user_location_rights(self):
        #self.ensure_one()
        for obj in self:
          if obj.state == 'draft':
            return True
          user_locations = obj.env.user.stock_location_ids
          print(user_locations)
          print("Checking access %s" %obj.env.user.default_picking_type_ids)
          if obj.env.user.restrict_locations:
            message = _(
              'Invalid Location. You cannot process this move since you do '
              'not control the location "%s". '
              'Please contact your Adminstrator.')
            if obj.location_id not in user_locations:
              raise Warning(message % obj.location_id.name)
            elif obj.location_dest_id not in user_locations:
              raise Warning(message % obj.location_dest_id.name)

class StockPickingType(models.Model):
  _inherit = 'stock.picking.type'

  ### OMITIMOS QUE ANTEPONGA EL NOMBRE DEL ALMACÉN, PARA NO CAUSAR RUIDO AL USUARIO
  def name_get(self):
    ### EL formato en el cual mostrará la relación de hr.employee ejem. "V0001 - Eduardo Serrano"
    result = []
    for record in self:
      result.append((record.id, "{}".format(record.name)))
    return result

class HREmployee(models.Model):
  _inherit = 'hr.employee'

  @api.model
  def create(self, vals):
    users_obj = self.env['res.users'].sudo()
    res = super(HREmployee, self).create(vals)
    if res.warehouse_id:
      query = "select user_id from warehouse_security_users where warehouse_id = {}".format(res.warehouse_id.id)
      cr = self.env.cr.execute(query)
      raise ValidationError((
        "valor recibido: {}",format(cr.fetchall)))

