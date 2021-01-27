# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.tools.float_utils import float_compare, float_is_zero
from odoo.exceptions import UserError, ValidationError

class StockQuants(models.Model):
  _inherit = 'stock.quant'

  ### Métodos XMARTS
  @api.model
  def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, strict=False):
    self = self.sudo()
    rounding = product_id.uom_id.rounding
    quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
    # print("_update_reserved_quantityyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy ", quants.lot_id.name, "  quantity= ", quants.quantity, "  reserved_quantity= ", quants.reserved_quantity)
    # raise ValidationError(_('hola javi'))
    lista = quants
    transf_oper = self.env['transf.operaciones'].search([('id_user', '=', self.env.user.id)])
    series_start = ''
    trasfe_id = 0
    type_transfer = ''
    for tras in transf_oper:
      # print("transf_operrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr ", tras.id_producto.name)
      if product_id.id == tras.id_producto.id:
        series_start = tras.serie_start
        # print("111111111111111111111111111111111111111 ", series_start)
    if str(series_start) != '' and str(series_start) != 'False':
      cont = 0
      for lot in quants:
        if str(lot.lot_id.name) == str(series_start):
          cont += 1
          max_quantity_on_quan = lot.quantity - lot.reserved_quantity
          if float_compare(max_quantity_on_quan, 0, precision_rounding=rounding) <= 0:
            raise ValidationError(_('Ya ha sido utilizada la serie %s en el producto %s.') % (series_start, product_id.name))
      if cont == 0:
        raise ValidationError(_('No se encuentra la serie %s en el producto %s.') % (series_start, product_id.name))
    for trasfe in transf_oper:
      if product_id.id == trasfe.id_producto.id and str(trasfe.serie_start) == str(series_start):
        count = 0
        if trasfe.type_transfer == 'sucursal':
          while int(count) < int(trasfe.demanda):
            if '-' in series_start:
              letter = series_start.split('-')[0]
              number = series_start.split('-')[1]
              new_serie = letter + '-' + str(int(number) + int(count)).zfill(len(number))
              for lo in quants:
                if str(lo.lot_id.name) == str(new_serie):
                  max_quantity_on_qua = lo.quantity - lo.reserved_quantity
                  if float_compare(max_quantity_on_qua, 0, precision_rounding=rounding) <= 0:
                    raise ValidationError(_('Ya ha sido utilizada la serie %s en el producto %s.') % (new_serie, product_id.name))
              count += 1
            else:
              new_serie = str(int(series_start) + count).zfill(len(series_start))
              for lo in quants:
                if str(lo.lot_id.name) == str(new_serie):
                  max_quantity_on_qua = lo.quantity - lo.reserved_quantity
                  if float_compare(max_quantity_on_qua, 0, precision_rounding=rounding) <= 0:
                    raise ValidationError(_('Ya ha sido utilizada la serie %s en el producto %s.') % (new_serie, product_id.name))
              count += 1
        if trasfe.type_transfer == 'sucursal':
          contad = 0
          while int(contad) < int(trasfe.demanda):
            trasfe_id = trasfe.id
            if '-' in series_start:
              lette = series_start.split('-')[0]
              numbe = series_start.split('-')[1]
              new_seri = lette + '-' + str(int(numbe) + int(contad)).zfill(len(numbe))
              contad += 1
              self.env['det.operaciones'].create({
                'transf_operaciones': trasfe.id,
                'serie': new_seri})
            else:
              new_seri = str(int(series_start) + contad).zfill(len(series_start))
              contad += 1
              self.env['det.operaciones'].create({
                'transf_operaciones': trasfe.id,
                'serie': new_seri})
        else:
          trasfe_id = trasfe.id
          type_transfer = trasfe.type_transfer
          # print("333333333333333333333333333333333333333333333 ", series_start, "  id= ", trasfe_id)
          self.env['det.operaciones'].create({
            'transf_operaciones': trasfe.id,
            'serie': series_start})
    reserved_quants = []
    if float_compare(quantity, 0, precision_rounding=rounding) > 0:
      # if we want to reserve
      available_quantity = self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
      if float_compare(quantity, available_quantity, precision_rounding=rounding) > 0:
        raise UserError(_('It is not possible to reserve more products of %s than you have in stock.') % product_id.display_name)
    elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
        # if we want to unreserve
      available_quantity = sum(quants.mapped('reserved_quantity'))
      if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
        raise UserError(_('It is not possible to unreserve more products of %s than you have in stock.') % product_id.display_name)
    else:
      return reserved_quants
    det_oper = self.env['det.operaciones'].search([('transf_operaciones', '=', int(trasfe_id))])
    for det_op in det_oper:
      available_quantityy, quantityy, buscar_serie = self.buscar_serie(lista, det_op.serie, quantity, rounding, available_quantity, type_transfer)
      quantity = quantityy
      available_quantity = available_quantityy
      for re in buscar_serie:
        reserved_quants.append((re['lot_'], re['max_quantity_on_quan']))
    if len(det_oper) == 0:
      print("lllllllllllllllllllllllllllll")
      for quant in quants:
        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
          max_quantity_on_quant = quant.quantity - quant.reserved_quantity
          if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
            continue
          max_quantity_on_quant = min(max_quantity_on_quant, quantity)
          quant.reserved_quantity += max_quantity_on_quant
          reserved_quants.append((quant, max_quantity_on_quant))
          quantity -= max_quantity_on_quant
          available_quantity -= max_quantity_on_quant
        else:
          max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
          quant.reserved_quantity -= max_quantity_on_quant
          reserved_quants.append((quant, -max_quantity_on_quant))
          quantity += max_quantity_on_quant
          available_quantity += max_quantity_on_quant

        if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity, precision_rounding=rounding):
          break
      return reserved_quants
    return reserved_quants

  def buscar_serie(self, lista, serie, quantity, rounding, available_quantity, type_transfer):
    raise ValidationError((
      "lot_id: {}".format(lot_id)))
    reserved_quants = []
    for lot_ in lista:
      if str(lot_.lot_id.name) == str(serie):
        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
          max_quantity_on_quan = lot_.quantity - lot_.reserved_quantity
          if float_compare(max_quantity_on_quan, 0, precision_rounding=rounding) <= 0:
            continue
          max_quantity_on_quan = min(max_quantity_on_quan, quantity)
          lot_.reserved_quantity += max_quantity_on_quan
          print("jjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj ", lot_.reserved_quantity)
          reserved_quants.append({'lot_': lot_, 'max_quantity_on_quan': max_quantity_on_quan})
          quantity -= max_quantity_on_quan
          available_quantity -= max_quantity_on_quan
        else:
          print("oooooooooooooooooooooooo ", lot_.reserved_quantity)
          max_quantity_on_quan = min(lot_.reserved_quantity, abs(quantity))
          lot_.reserved_quantity -= max_quantity_on_quan
          reserved_quants.append(({'lot_': lot_, 'max_quantity_on_quan': -max_quantity_on_quan}))
          quantity += max_quantity_on_quan
          available_quantity += max_quantity_on_quan
        if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity, precision_rounding=rounding):
          break
    return available_quantity, quantity, reserved_quants
    