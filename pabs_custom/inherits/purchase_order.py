# -*- coding: utf-8 -*-

from odoo import fields, models, api
from re import findall as regex_findall, split as regex_split
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
  _inherit = 'purchase.order'

  picking_type_id = fields.Many2one(comodel_name='stock.picking.type', default=False)

  ### Btn que confirma el pedido de compra
  def button_confirm(self):
    if self.amount_total <= 0:
      raise ValidationError((
        "No puedes validar un documento en 0"))
    ### Genera su proceso natural
    res = super(PurchaseOrder, self).button_confirm()
    ### Se recorre todas las lineas del pedido
    for line in self.order_line:
      ### Se agrega el valor de número de serie a la órden de entrega
      line.move_ids.next_serial = line.since
      ### Se agrega la cantidad a generar
      line.move_ids.next_serial_count = line.product_qty
      ### Se asigna la entrada
      line.move_ids.action_assign_serial_show_details()
      ### Valida si el producto tiene "seguimiento por número de serie" y lo confirma
    return res

  @api.model
  def create(self, vals):
    total = 0
    if not vals.get('order_line'):
      raise ValidationError((
        "No puedes crear un registro sin ningún producto"))
    for line in vals.get('order_line'):
      total += (line[2]['product_qty'] * line[2]['price_unit'])
    if total <= 0:
      raise ValidationError((
        "No puedes crear un registro con un total menor o igual que 0"))
    return super(PurchaseOrder, self).create(vals)

class PurchaseOrderLine(models.Model):
  _inherit = "purchase.order.line"

  ### Declaración de campos
  tracking = fields.Selection([
    ('serial', 'By Unique Serial Number'),
    ('lot', 'By Lots'),
    ('none', 'No Tracking')], 
    string="Tracking",
    related='product_id.product_tmpl_id.tracking',
    store=False)

  since = fields.Char(string='Serie')

  ### Cuando seleccionas un producto se antepone el prefijo de acuerdo al producto
  """@api.onchange('product_id')
  @api.onchange('product_id')
  def calc_serie(self):
    pricelist_item_obj = self.env['product.pricelist.item']
    if self.product_id:
      if self.product_id.tracking == 'serial':
        item_id = pricelist_item_obj.search([('product_id','=',self.product_id.id)],
          order="create_date desc",limit=1)
        if item_id:
          self.since = item_id.prefix_request"""

  @api.onchange('since','product_qty')
  def validate_serie(self):
    pricelist_item_obj = self.env['product.pricelist.item']
    if self.product_id:
      if self.product_id.tracking == 'serial':
        item_id = pricelist_item_obj.search([
          ('product_id','=',self.product_id.id)], 
          order="create_date desc",limit=1)
        if item_id and self.since:
          prefix = item_id.prefix_request
          if self.since[0:6] != prefix[0:6]:
            raise ValidationError((
              "Favor de verificar el prefijo de las solicitudes"))
          elif len(self.since) > 12 or len(self.since) < 12:
            raise ValidationError((
              "El número de serie contiene {} digitos y debería tener 12 digitos, favor de verificarlo".format(len(self.since))))
          ### VALIDAR TODOS LOS NÚMEROS DE SERIE
          caught_initial_number = regex_findall("\d+", self.since)
          initial_number = caught_initial_number[-1]
          padding = len(initial_number)
          # We split the serial number to get the prefix and suffix.
          splitted = regex_split(initial_number, self.since)
          # initial_number could appear several times in the SN, e.g. BAV023B00001S00001
          prefix = initial_number.join(splitted[:-1])
          suffix = splitted[-1]
          initial_number = int(initial_number)
          for i in range(0, int(self.product_qty)):
            self.validate_exist_serie(self.product_id,'%s%s%s' % (
              prefix,
              str(initial_number + i).zfill(padding),
              suffix))
  
  def validate_exist_serie(self, product_id, serie):
    lot_obj = self.env['stock.production.lot']
    serie = lot_obj.search([
      ('name','=',serie),
      ('product_id','=',product_id.id)])
    if serie:
      raise ValidationError((
        "El número de serie {} ya está dado de alta en el sistema, favor de verificarlo".format(serie.name)))
          