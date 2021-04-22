# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from re import findall as regex_findall, split as regex_split

REASONS = [
  ('full_name','Nombre completo del Promotor'),
  ('incorrect_request','Solicitud Incorrecta'),
  ('initial_investment_wrong', 'Alterada la inv. inicial'),
  ('it_is_already','Ya esta dado de alta'),
  ('incomplete_documents','Documentos incompletos'),
  ('headline_signature','Firma del titular'),
  ('autorize_transfer','Falta autorización para traspaso'),
  ('missing_reg_or_modif', 'Falta alta o modif. de oficina de promotor'),
  ('data_missing_on_req','Faltan datos en croquis o solicitud'),
  ('other','Otros'),
  ('nothing','Ninguno'),
  ('package_has_no_cost','No tiene costo del paquete'),
  ('activation_code_altered','Código de activacion con pluma o alterado'),
  ('payment_amount_doesnot_correspond','No corresponde monto del abono'),
  ('data_dont_match','Datos no coinciden sistema y contrato')
]

class StockMove(models.Model):
  _inherit = 'stock.move'

  return_reasons = fields.Selection(selection=REASONS,
    string='Motivo de regreso')
  
  ### Declaración de campos XMARTS
  series_start = fields.Char(
    string="Serie inicio")

  series_end = fields.Char(
    string="Serie fin")

  series = fields.Char(
    string="Serie")

  papeleria = fields.Float(
    string="Papeleria")

  inversion_inicial = fields.Float(
    string="Inversión inicial")

  toma_comision = fields.Float(
    string="Toma comisión")

  forma_pago = fields.Selection([
    ('efectivo', 'Efectivo'),
    ('deposito', 'Deposito'),
    ('tarjeta_bancaria', 'Tarjeta bancaria'),
    ('pagare','Pagaré'),
    ('cheque', 'Cheque'),
    ('bono_pabs', 'Bono PABS'),
  ], string="Forma de pago")

  origen_solicitud = fields.Selection([
    ('cambaceo', 'Cambaceo'),
    ('cancelada', 'Cancelada'),
    ('servicio', 'Servicio'),
    ('referido', 'Referido'),
    ('reafiliacion', 'Reafiliacion'),
    ('medios_electronicos', 'Medios electronicos'),
    ('directo', 'Directo'),
    ('sobrantes', 'Sobrantes'),
    ('extravio', 'Extravio'),
  ], string="Origen de solicitud")

  referencia = fields.Char(
    string="Referencia")

  codigo_de_activacion_valid = fields.Char(
    string="Activación")

  amount_received = fields.Float(string='Importe recibido',
    compute="_calc_amount_received")

  ### Termina Declaración de campos XMARTS

  @api.onchange('inversion_inicial','toma_comision')
  def _calc_amount_received(self):
    for rec in self:
      if not rec.origen_solicitud in ('cancelada','extravio','sobrantes'):
        res = (float(rec.inversion_inicial) - float(rec.toma_comision))
        """if res < rec.papeleria:
          raise ValidationError((
            "El importe recibido debe ser mayor o igual a la papelería"))"""
        rec.amount_received = res
      else:
        rec.amount_received = 0


  ### Candado para evitar que se dupliquen series por error y siempre se generen las cantidades solicitadas
  def action_assign_serial_show_details(self):
    if len(self.move_line_nosuggest_ids) == self.next_serial_count:
      return self.action_show_details()
    elif len(self.move_line_nosuggest_ids) < self.next_serial_count:
      self.move_line_nosuggest_ids.unlink()
    elif len(self.move_line_nosuggest_ids) > self.next_serial_count:
      self.move_line_nosuggest_ids.unlink()
    return super(StockMove, self).action_assign_serial_show_details()

  ### Métodos XMARTS
  @api.onchange('series_start', 'series_end')
  def onchange_serie(self):
    pricelist_item_obj = self.env['product.pricelist.item']
    lot_obj = self.env['stock.production.lot']
    # print("-------------------------------------onchange series_start y series_end---------------------------------------------")
    for record in self:
      record.product_uom_qty = 0
      if record.series_start and record.series_end:
        if '-' in record.series_start and '-' in record.series_end:
          if record.series_end.split('-')[1].isnumeric() and record.series_start.split('-')[1].isnumeric():
            if int(record.series_end.split('-')[1]) >= int(record.series_start.split('-')[1]):
              record.product_uom_qty = int(record.series_end.split('-')[1]) - int(record.series_start.split('-')[1]) + 1
        elif record.series_start.isnumeric() and record.series_end.isnumeric():
          if int(record.series_end) >= int(record.series_start.isnumeric()):
            record.product_uom_qty = int(record.series_end) - int(record.series_start) + 1
      ### Calculando el producto al cual hace referencia la serie
      if record.series_start:
        product_prefix = record.series_start[0:6]
        pricelist_id = pricelist_item_obj.search([
            ('prefix_request','=',product_prefix),('company_id','=',self.company_id.id)],
            order="create_date desc",limit=1)
        if not pricelist_id:
          raise ValidationError((
            'No se pudo validar a que prefijo hace referencia "{}" favor de verificarlo con sistemas'.format(product_prefix)))
        record.product_id = pricelist_id.product_id.id or False
        ### VALIDAR TODOS LOS NÚMEROS DE SERIE
        caught_initial_number = regex_findall("\d+", record.series_start)
        initial_number = caught_initial_number[-1]
        padding = len(initial_number)
        # We split the serial number to get the prefix and suffix.
        splitted = regex_split(initial_number, record.series_start)
        # initial_number could appear several times in the SN, e.g. BAV023B00001S00001
        prefix = initial_number.join(splitted[:-1])
        suffix = splitted[-1]
        initial_number = int(initial_number)
        for i in range(0, int(record.product_uom_qty)):
          self.validate_location_serie(record.picking_id.location_id,'%s%s%s' % (
            prefix,
            str(initial_number + i).zfill(padding),
            suffix))

  @api.onchange('codigo_de_activacion_valid')
  def validation_activation_code(self):
    lot_obj = self.env['stock.production.lot']
    contract_obj = self.env['pabs.contract']
    for rec in self:
      if rec.codigo_de_activacion_valid:
        lot_id = lot_obj.search([
          ('name','=',rec.series),('company_id','=',self.company_id.id)],limit=1)
        if not lot_id:
          raise ValidationError((
            "No se encontró la solicitud"))
        contract_id = contract_obj.search([
          ('lot_id','=',lot_id.id),('company_id','=',self.company_id.id)],limit=1)
        if not contract_id:
          raise ValidationError((
            "La solicitud {} No ha sido activado previamente".format(rec.series)))
        if contract_id.activation_code != rec.codigo_de_activacion_valid:
          raise ValidationError((
            "El número de activación no es correcto, favor de intentarlo nuevamente"))


  def validate_location_serie(self, location_id, serie):
    lot_obj = self.env['stock.production.lot']
    quant_obj = self.env['stock.quant']
    lot_id = lot_obj.search([
      ('name','=',serie),('company_id','=',self.company_id.id)],limit=1)
    if not lot_id:
      raise ValidationError((
        'No se encontro la solicitud {} en el sistema'.format(serie)))
    quant_id = quant_obj.search([
      ('lot_id','=',lot_id.id),('company_id','=',self.company_id.id)],limit=1,order="id desc")
    if location_id != quant_id.location_id:
      raise ValidationError((
        'La solicitud {} no se encuentra en el almacén indicado, se encuentra en {}\n favor de verificarlo'.format(
          serie,quant_id.location_id.name_get()[0][1])))


  @api.onchange('series')
  def onchange_series(self):
    move_obj = self.env['stock.move']
    quant_obj = self.env['stock.quant']
    contract_obj = self.env['pabs.contract']
    location_id = False
    
    for rec in self:
      cont = 0
      ### Validar que no se esté duplicando la linea que se está capturando
      if rec.series:
        for obj_line in rec.picking_id.move_ids_without_package:
          if rec.series == obj_line.series:
            cont+=1
            if cont > 2:
              raise ValidationError((
                "No se puede agregar la línea por que ya fue agregada previamente"))
      line = move_obj.search([
        ('series','=',rec.series),
        ('company_id','=',self.company_id.id),
        ('origen_solicitud','in',('cancelada','extravio'))],limit=1)
      if line:
        raise ValidationError((
          "La solicitud {} no puede ser ingresada por que está {}".format(rec.series,dict(rec._fields['origen_solicitud'].selection).get(rec.origen_solicitud))))
      mode_prod = self.env['stock.production.lot'].search(
        [('name', '=', str(rec.series)),('company_id','=',self.company_id.id)], limit=1)        
      if rec.series and rec.picking_id.type_transfer == 'ov-as':
        if rec.picking_id.location_dest_id.consignment_location:
          for prodc in mode_prod:
            quant_id = quant_obj.search([
              ('lot_id','=',prodc.id),('company_id','=',self.company_id.id)],limit=1,order="id desc")
            if quant_id.location_id != rec.location_id:
              raise ValidationError((
                "La solicitud {} no se encuentrá en el almacén indicado, se encuentra en {}\nfavor de verificarlo".format(
                  quant_id.lot_id.name, quant_id.location_id.name_get()[0][1])))
            rec.product_id = prodc.product_id
            rec.product_uom_qty = 1
      elif rec.series and rec.picking_id.type_transfer == 'as-ov':
        if rec.picking_id.employee_id:
          location_id = rec.picking_id.employee_id.local_location_id
        if rec.picking_id.location_dest_id.received_location:
          for prodc in mode_prod:
            quant_id = quant_obj.search([
              ('lot_id','=',prodc.id),
              ('company_id','=',self.company_id.id),
              ('quantity','>',0)], order="in_date desc", limit=1)
            if quant_id:
              if quant_id.location_id != location_id:
                raise ValidationError((
                  "La solicitud {} no se encuentra asignada al A.S {}, se encuentra en {}".format(rec.series, rec.picking_id.employee_id.name, quant_id.location_id.name)))
            rec.product_id = prodc.product_id
            rec.product_uom_qty = 1
            ### VALIDAR SI ESTA ACTIVADA LA SOLICITUD
            contract_id = contract_obj.search([
              ('company_id','=',self.company_id.id),
              ('lot_id','=',mode_prod.id),
              ('activation_code','!=',False)])
            if not contract_id:
              raise ValidationError((
                "La solicitud {} no se encuentra con una activación previa".format(rec.series)))
        else:
          raise ValidationError((
            "No se encontró la ubicación de recibidos"))

  ### Método de xmarts limpiado
  def _update_reserved_quantity(self,need,available_quantity,
    location_id,lot_id=None,package_id=None,owner_id=None,strict=True):
    self.delete()
    for rec in self:
      series_start = ''
      if rec.picking_id.type_transfer == 'ac-ov':
        if rec.series_start:
          series_start = rec.series_start
        else:
          raise ValidationError(_('Es necesario agregar una serie de inicio en el producto %s.') % (rec.product_id.name))
      elif rec.picking_id.type_transfer == 'ov-as' or rec.picking_id.type_transfer == 'as-ov' or rec.picking_id.type_transfer == 'as-cont':
        series_start = rec.series
      if series_start != '':
        self.env['transf.operaciones'].create({
          'name': rec.picking_id.name,
          'id_user': self.env.user.id,
          'id_producto': rec.product_id.id,
          'serie_start': series_start,
          'demanda': rec.product_uom_qty,
          'type_transfer': rec.picking_id.type_transfer,
        })
    res = super(StockMove, self)._update_reserved_quantity(
      need, available_quantity, location_id, lot_id, package_id, owner_id, strict)
    self.delete()
    return res

  def delete(self):
    cr = self.env.cr
    cr2 = self.env.cr
    sql1 = 'DELETE FROM det_operaciones d WHERE d.transf_operaciones IN (SELECT tr.id FROM transf_operaciones AS tr WHERE id_user=%s)' % (int(self.env.user.id))
    cr.execute(sql1)
    sql2 = 'DELETE FROM transf_operaciones WHERE id_user=%s' % (int(self.env.user.id))
    cr2.execute(sql2)

  def _get_new_picking_values(self):
    print('----------------------stock_move  _get_new_picking_valuessssss-----------------------------------')
    """ return create values for new picking that will be linked with group
    of moves in self.
    """
    origins = self.filtered(lambda m: m.origin).mapped('origin')
    origins = list(dict.fromkeys(origins)) # create a list of unique items
    # Will display source document if any, when multiple different origins
    # are found display a maximum of 5
    if len(origins) == 0:
      origin = False
    else:
      origin = ','.join(origins[:5])
      if len(origins) > 5:
        origin += "..."
    partners = self.mapped('partner_id')
    partner = len(partners) == 1 and partners.id or False
    return {
      'origin': origin,
      'company_id': self.mapped('company_id').id,
      'user_id': False,
      'move_type': self.mapped('group_id').move_type or 'direct',
      'partner_id': partner,
      'picking_type_id': self.mapped('picking_type_id').id,
      'location_id': self.mapped('location_id').id,
      'location_dest_id': self.mapped('location_dest_id').id,
      'type_transfer': 'ventas',
    }

  @api.onchange('origen_solicitud')
  def onchange_origen_solicitud(self):
    pricelist_item_obj = self.env['product.pricelist.item']
    if self.origen_solicitud in ('cancelada', 'sobrantes', 'extravio'):
      self.papeleria = 0
      self.invercion_inicial = 0
      self.toma_comision = 0
    else:
      if self.product_id:
        if self.product_id.tracking == 'serial':
          item_id = pricelist_item_obj.search([('product_id','=',self.product_id.id),('company_id','=',self.company_id.id)],
            order="create_date desc",limit=1)
          if item_id:
            self.papeleria = item_id.stationery

  @api.onchange('product_id')
  def onchange_product_id_papeleria(self):
    pricelist_item_obj = self.env['product.pricelist.item']
    if self.picking_id.type_transfer == 'as-ov':
      if self.product_id:
        if self.product_id.tracking == 'serial':
          item_id = pricelist_item_obj.search([('product_id','=',self.product_id.id),('company_id','=',self.company_id.id)],
            order="create_date desc",limit=1)
          if item_id:
            self.papeleria = item_id.stationery

  def _action_confirm(self, merge=True, merge_into=False):
    """ Confirms stock move or put it in waiting if it's linked to another move.
    :param: merge: According to this boolean, a newly confirmed move will be merged
    in another move of the same picking sharing its characteristics.
    """
    move_create_proc = self.env['stock.move']
    move_to_confirm = self.env['stock.move']
    move_waiting = self.env['stock.move']

    to_assign = {}
    for move in self:
      # if the move is preceeded, then it's waiting (if preceeding move is done, then action_assign has been called already and its state is already available)
      if move.move_orig_ids:
        move_waiting |= move
      else:
        if move.procure_method == 'make_to_order':
          move_create_proc |= move
        else:
          move_to_confirm |= move
      if move._should_be_assigned():
        key = (move.group_id.id, move.location_id.id, move.location_dest_id.id)
        if key not in to_assign:
          to_assign[key] = self.env['stock.move']
        to_assign[key] |= move

    # create procurements for make to order moves
    procurement_requests = []
    for move in move_create_proc:
      values = move._prepare_procurement_values()
      origin = (move.group_id and move.group_id.name or (move.origin or move.picking_id.name or "/"))
      procurement_requests.append(self.env['procurement.group'].Procurement(
        move.product_id, move.product_uom_qty, move.product_uom,
        move.location_id, move.rule_id and move.rule_id.name or "/",
        origin, move.company_id, values))
    self.env['procurement.group'].run(procurement_requests)

    move_to_confirm.write({'state': 'confirmed'})
    (move_waiting | move_create_proc).write({'state': 'waiting'})

    # assign picking in batch for all confirmed move that share the same details
    for moves in to_assign.values():
      moves._assign_picking()
    self._push_apply()
    self._check_company()
    # if merge:
    #     return self._merge_moves(merge_into=merge_into)
    return self

  @api.model
  def create(self, vals):
    picking_obj = self.env['stock.picking']
    move_line_obj = self.env['stock.move.line']
    lot_obj = self.env['stock.production.lot']
    pricelist_item_obj = self.env['product.pricelist.item']
    product_obj = self.env['product.product']
    picking_id = picking_obj.browse(vals.get('picking_id'))
    if picking_id.type_transfer == 'as-ov':
      if vals.get('product_id'):
        product_id = product_obj.browse(vals.get('product_id'))
        if product_id.tracking == 'serial':
          item_id = pricelist_item_obj.search([('product_id','=',product_id.id),('company_id','=',vals.get('company_id'))],
            order="create_date desc",limit=1)
          if item_id:
            vals['papeleria'] = item_id.stationery
    res = super(StockMove, self).create(vals)
    if vals.get('picking_id'):
      if picking_id.type_transfer in ('ov-as','as-ov'):
        lot_id = lot_obj.search([('name','=',res.series),('company_id','=',vals.get('company_id'))],limit=1)
        data = {
          'picking_id' : picking_id.id,
          'move_id': res.id,
          'product_id': res.product_id.id,
          'product_uom_id' : res.product_id.uom_id.id,
          'qty_done' : 1,
          'lot_id' : lot_id.id or False,
          'location_id' : picking_id.location_id.id,
          'location_dest_id' : picking_id.location_dest_id.id,
          'state' : 'assigned',
          'reference' : res.reference,
        }
        move_line_obj.create(data)
        lot_id.employee_id = picking_id.employee_id.id or False
        ### SI EL MOVIMIENTO ES OFICINA DE VENTAS - ASISTENTE
        if picking_id.type_transfer == 'ov-as':
          location_id = picking_id.location_id
        ### SI NO, VIENE DEL ASISTENTE A LA OFICINA DE VENTAS
        else:
          location_id = picking_id.location_dest_id
        ### SI HAY UBICACIÓN
        if location_id:
          ### BUSCA EL ALMACÉN AL QUE PERTENECE LA TRANSFERENCIA
          warehouse_id = picking_id.location_id.get_warehouse()
          ### SI SE ENCONTRÓ EL ALMACÉN
          if warehouse_id:
            ### PONE LA SOLICITUD EN EL ALMACÉN DE LA TRANSFERENCIA
            lot_id.warehouse_id = warehouse_id.id
        res.state = 'assigned'
      if picking_id.type_transfer == 'ac-ov':
        ### VALIDAR TODOS LOS NÚMEROS DE SERIE
        caught_initial_number = regex_findall("\d+", res.series_start)
        initial_number = caught_initial_number[-1]
        padding = len(initial_number)
        # We split the serial number to get the prefix and suffix.
        splitted = regex_split(initial_number, res.series_start)
        # initial_number could appear several times in the SN, e.g. BAV023B00001S00001
        prefix = initial_number.join(splitted[:-1])
        suffix = splitted[-1]
        initial_number = int(initial_number)
        for i in range(0, int(res.product_uom_qty)):
          serie = '{}{}{}'.format(prefix,str(initial_number + i).zfill(padding),suffix)
          lot_id = lot_obj.search([('name','=',serie),('company_id','=',vals.get('company_id'))],limit=1) or False
          data = {
            'picking_id' : picking_id.id,
            'move_id': res.id,
            'product_id': res.product_id.id,
            'product_uom_id' : res.product_id.uom_id.id,
            'qty_done' : 1,
            'lot_id' : lot_id.id,
            'location_id' : picking_id.location_id.id,
            'location_dest_id' : picking_id.location_dest_id.id,
            'state' : 'assigned',
            'reference' : res.reference,
          }
          move_line_obj.create(data)
        res.state = 'assigned'
    return res
