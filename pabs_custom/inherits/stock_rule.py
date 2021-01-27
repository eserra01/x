# -*- coding: utf-8 -*-
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class StockRule(models.Model):
  _inherit = 'stock.rule'

  def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values):
    print('-------------------------------_get_stock_move_values-------------------------------')
    ''' Returns a dictionary of values that will be used to create a stock move from a procurement.
    This function assumes that the given procurement has a rule (action == 'pull' or 'pull_push') set on it.
    :param procurement: browse record
    :rtype: dictionary
    '''
    group_id = False
    if self.group_propagation_option == 'propagate':
      group_id = values.get('group_id', False) and values['group_id'].id
    elif self.group_propagation_option == 'fixed':
      group_id = self.group_id.id

    date_expected = fields.Datetime.to_string(
      fields.Datetime.from_string(values['date_planned']) - relativedelta(days=self.delay or 0)
    )
    # it is possible that we've already got some move done, so check for the done qty and create
    # a new move with the correct qty
    qty_left = product_qty

    sale_order = self.env['sale.order'].search([
      ('name', '=', origin)], limit=1)

    move_values = {
      'name': name[:2000],
      'company_id': self.company_id.id or self.location_src_id.company_id.id or self.location_id.company_id.id or company_id.id,
      'product_id': product_id.id,
      'product_uom': product_uom.id,
      'product_uom_qty': qty_left,
      'partner_id': self.partner_address_id.id or (values.get('group_id', False) and values['group_id'].partner_id.id) or False,
      'location_id': self.location_src_id.id,
      'location_dest_id': location_id.id,
      'move_dest_ids': values.get('move_dest_ids', False) and [(4, x.id) for x in values['move_dest_ids']] or [],
      'rule_id': self.id,
      'procure_method': self.procure_method,
      'origin': origin,
      'picking_type_id': self.picking_type_id.id,
      'group_id': group_id,
      'route_ids': [(4, route.id) for route in values.get('route_ids', [])],
      'warehouse_id': self.propagate_warehouse_id.id or self.warehouse_id.id,
      'date': date_expected,
      'date_expected': date_expected,
      'propagate_cancel': self.propagate_cancel,
      'propagate_date': self.propagate_date,
      'propagate_date_minimum_delta': self.propagate_date_minimum_delta,
      'description_picking': product_id._get_description(self.picking_type_id),
      'priority': values.get('priority', "1"),
      'delay_alert': self.delay_alert,
      'series': sale_order.application_number
    }

    print('move_values2222', move_values)
    for field in self._get_custom_move_fields():
      print('---------------------forforfor------------------------------')
      if field in values:
        print('---------------------ififif------------------------------')
        move_values[field] = values.get(field)
    print('move_values3333', move_values)
    return move_values
    