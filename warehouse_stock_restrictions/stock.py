# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import Warning

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


