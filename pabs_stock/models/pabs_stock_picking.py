# -*- coding: utf-8 -*-
from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

PABS_PICKING_TYPE = [
        ('going','Peticiones a AG'),
        ('ret','Retornos a AG'),
        ('request','Solicitudes a AG'),
        ('consumption','Baja de consumibles'), 
        ('adjust','Ajuste de consumibles'),
        ('adjust2','Baja urnas y ataúdes'),
        ('internal','Traspasos internos')]

class StockQuant(models.Model):
    _inherit = 'stock.quant'
    
    @api.constrains('quantity')
    def check_quantity(self):
        return True
        for quant in self:
            if float_compare(quant.quantity, 1, precision_rounding=quant.product_uom_id.rounding) > 0 and quant.lot_id and quant.product_id.tracking == 'serial':
                raise ValidationError(_('The serial number has already been assigned: \n Product: %s, Serial Number: %s') % (quant.product_id.display_name, quant.lot_id.name))


class PabsStockPicking(models.Model):
    _name = 'pabs.stock.picking'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Pabs picking stock"
    _order = 'id desc'

    name = fields.Char(string='Movimiento', copy=False,readonly=True, default='/')
    state = fields.Selection([('cancel','Cancelado'),('draft','Borrador'),('transit','En tránsito'),('done','Transferido')], tracking=True, string='Estado',readonly=True, default='draft')
    picking_type = fields.Selection(PABS_PICKING_TYPE, string='Tipo de operación', required=True, states={'draft': [('readonly', False)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]}, tracking=True)
    origin_location_id = fields.Many2one(string="Origen", comodel_name='stock.location', states={'draft': [('readonly', False)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]}, domain="[('pabs_stock_location','=',True)]", tracking=True)
    dest_location_id = fields.Many2one(string="Destino", comodel_name='stock.location', states={'draft': [('readonly', False)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]}, domain="[('pabs_stock_location','=',True)]", tracking=True)    
    origin_inventory_id = fields.Many2one(string='Inventario origen', comodel_name='stock.inventory', states={'draft': [('readonly', False)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    dest_inventory_id = fields.Many2one(string='Inventario destino', comodel_name='stock.inventory', states={'draft': [('readonly', False)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    transit_inventory_id = fields.Many2one(string='Inventario tránsito', comodel_name='stock.inventory', states={'draft': [('readonly', False)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    date_done = fields.Datetime(string='Fecha transferido',states={'draft': [('readonly', False)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]}, tracking=True)    
    notes = fields.Char(string="Notas", states={'draft': [('readonly', False)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]}, tracking=True)
    move_id = fields.Many2one(string="Póliza", comodel_name='account.move', tracking=True,)
    line_ids = fields.One2many(string="Productos", comodel_name='pabs.stock.picking.line', inverse_name='pabs_picking_id', states={'draft': [('readonly', False)], 'done': [('readonly', True)], 'cancel': [('readonly', True)], 'cancel': [('readonly', True)]})
    standard_price = fields.Float(string = "Costo total", compute='_get_standard_price', tracking=True)
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True, tracking=True) 

    def _get_standard_price(self):
        for rec in self:
            total = 0
            for line in rec.line_ids:
                total += line.product_id.standard_price * line.qty
            rec.standard_price = total
        return True

    def get_credentials(self, picking_type):
        #
        credentials_id = self.env['pabs.picking.type.user'].search([('user_id','=',self.env.user.id)], limit = 1)
        flag = False
        for credential in credentials_id:
            #
            if credential.going and picking_type == 'going':
                return True
            if credential.ret and picking_type == 'ret':
                return True
            if credential.request and picking_type == 'request':
                return True
            if credential.consumption and picking_type == 'consumption':
                return True
            if credential.adjust and picking_type == 'adjust':
                return True 
            if credential.adjust2 and picking_type == 'adjust2':
                return True
            if credential.internal and picking_type == 'internal':
                return True    
        return False

    def action_cancel(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError("Solo puede cancelar solicitudes en esatdo borrador.")
            rec.state = 'cancel'
        return True

    def action_done(self):              
        if not self.get_credentials(self.picking_type):
            raise ValidationError('No tiene permisos para realizar este tipo de operación.')
        config_id = self.env['pabs.stock.config'].search([('company_id','=',self.env.company.id),('config_type','=','primary')],limit=1)
        if not config_id:                    
            raise ValidationError('No existe una configuración para el control de almacén.')
        if not config_id.consumable_journal_id:
                raise ValidationError('No se han definido el diario para la póliza de consumibles.')       
        
        amls = []
        # TRASPASOS DE ALMACÉN CENTRAL A OFICINAS
        if self.picking_type in ['going']:                                          
            # Se validan existencias en ORIGEN
            if self.picking_type in ['going']:
                for line in self.line_ids:
                    qty_available = line.product_id.with_context({'location':self.origin_location_id.id}).qty_available
                    if qty_available < line.qty:
                        raise ValidationError('El producto {} no tiene existencias suficientes en el origen, solo pueden transferirse {} unidades.'.format(line.product_id.name,qty_available))
            
            # Se obtienen los valores para el ORIGEN
            vals = self.get_inventory_vals(self.origin_location_id, self.picking_type, self.line_ids)
            origin_inventory_id = self.env['stock.inventory'].create(vals)  
            # Se agregan los productos con las cantidades
            for line in self.line_ids:
                # Se agregan solo productos sin seguimiento por serie o lote   
                if line.product_id.tracking == 'none':                   
                    self.env['stock.inventory.line'].create(
                    {
                        'inventory_id': origin_inventory_id.id, 
                        'product_id': line.product_id.id, 
                        'product_qty': line.product_id.with_context({'location':self.origin_location_id.id}).qty_available - line.qty,                    
                        'prod_lot_id': line.prod_lot_id.id if line.prod_lot_id else False,
                        'location_id': self.origin_location_id.id
                    })
                    # Se validan las cuentas
                    if not line.product_id.categ_id.property_account_expense_categ_id:
                        raise ValidationError("No se ha definidio la cuenta de gastos del producto {} en la categoría {}".format(line.product_id.name,line.product_id.categ_id.name))
                    if not line.product_id.categ_id.consumble_account_stock_id:
                        raise ValidationError("No se ha definidio la cuenta de inventario del producto {} en la categoría {}".format(line.product_id.name,line.product_id.categ_id.name))
                                        
                    warehouse_id = self.env['stock.warehouse'].search([('company_id','=',self.env.company.id),('lot_stock_id','=',self.dest_location_id.id)],limit=1)
                    analytic_account_id = warehouse_id.analytic_account_id if warehouse_id else False
                    #
                    # Se agregan las lineas de la póliza de gastos
                    amls.append((0,0,{
                        'name': _(''),
                        'debit': 0.0,
                        'credit':  line.product_id.list_price * line.qty,
                        'account_id': line.product_id.categ_id.consumble_account_stock_id.id,
                    }))
                    amls.append((0,0,{
                        'name': _(line.product_id.name + ' ('+ str(line.qty) + ' unidades)'),
                        'debit':  line.product_id.list_price * line.qty,
                        'credit': 0.0,
                        'account_id': line.product_id.categ_id.property_account_expense_categ_id.id,
                        'analytic_account_id': analytic_account_id.id
                    }))                       
            
            # Se valida el inventario ORIGEN
            origin_inventory_id.action_start()
            origin_inventory_id.action_validate()
            self.origin_inventory_id = origin_inventory_id.id      

            # Se crea la póliza y se publica          
            move_row = self.env['account.move'].create({
                'journal_id':config_id.consumable_journal_id.id,
                'ref': 'Costo traspaso de consumibles',
                'line_ids': amls,
                'date': fields.Date.context_today(self)
            })          
            # Se publica la póliza
            move_row.post()
            # Se asocia la póliza al mov
            self.move_id = move_row.id                                                                               
         
        # TRASPASOS DE OFICINAS A ALMACÉN CENTRAL
        if self.picking_type in ['ret']:
            # Se obtienen los valores para incrementar en destino
            vals = self.get_inventory_vals(self.dest_location_id, self.picking_type, self.line_ids)
            dest_inventory_id = self.env['stock.inventory'].create(vals)  
            # Se agregan los productos con las cantidades
            for line in self.line_ids:
                # Se agregan solo productos sin seguimiento por serie o lote 
                if line.product_id.tracking == 'none':                                            
                    self.env['stock.inventory.line'].create(
                    {
                        'inventory_id': dest_inventory_id.id, 
                        'product_id': line.product_id.id, 
                        'product_qty': line.product_id.with_context({'location':self.dest_location_id.id}).qty_available + line.qty,                    
                        'prod_lot_id': line.prod_lot_id.id if line.prod_lot_id else False,
                        'location_id': self.dest_location_id.id
                    })
                    # Se validan las cuentas
                    if not line.product_id.categ_id.property_account_expense_categ_id:
                        raise ValidationError("No se ha definidio la cuenta de gastos del producto {} en la categoría {}".format(line.product_id.name,line.product_id.categ_id.name))
                    if not line.product_id.categ_id.consumble_account_stock_id:
                        raise ValidationError("No se ha definidio la cuenta de inventario del producto {} en la categoría {}".format(line.product_id.name,line.product_id.categ_id.name))
                    # Se agregan las lineas de la póliza de ingresos
                    amls.append((0,0,{
                        'name': _(''),
                        'debit': line.product_id.list_price * line.qty,
                        'credit':  0.0,
                        'account_id': line.product_id.categ_id.consumble_account_stock_id.id,
                    }))
                    amls.append((0,0,{
                        'name': _(line.product_id.name + ' ('+ str(line.qty) + ' unidades)'),
                        'debit':  0.0,
                        'credit': line.product_id.list_price * line.qty,
                        'account_id': line.product_id.categ_id.property_account_expense_categ_id.id,
                        'analytic_account_id': False
                    }))      
            # Se valida el inventario origen
            dest_inventory_id.action_start()
            dest_inventory_id.action_validate()
            self.dest_inventory_id = dest_inventory_id.id

            # Se crea la póliza y se publica          
            move_row = self.env['account.move'].create({
                'journal_id': config_id.consumable_journal_id.id,
                'ref': 'Costo traspaso de consumible (Reversa)',
                'line_ids': amls,
                'date': fields.Date.context_today(self)
            })          
            # Se publica la póliza
            move_row.post()  
            # Se asocia la póliza al mov
            self.move_id = move_row.id

        # CONSUMOS DE OFICINA
        if self.picking_type in ['consumption']:
        # Se valida  que todos los productos tengan existencias en el origen   
            for line in self.line_ids:
                qty_available= line.product_id.with_context({'location':self.origin_location_id.id}).qty_available
                if qty_available < line.qty:
                    raise ValidationError('El producto {} no tiene existencias suficientes en el origen, solo pueden consumirse {} unidades.'.format(line.product_id.name,qty_available))          

            # Se obtienen los valores para el inventario de la ubicación ORIGEN
            vals = self.get_inventory_vals(self.origin_location_id, self.picking_type, self.line_ids)
            origin_inventory_id = self.env['stock.inventory'].create(vals)  
            # Se agregan los productos con las cantidades
            for line in self.line_ids:
                if line.product_id.tracking != 'none':
                    # Se busca el quant
                    quant_id = self.env['stock.quant'].search(
                    [
                        ('product_id','=',line.product_id.id),
                        ('company_id','=',self.company_id.id),
                        ('location_id','=',self.origin_location_id.id),
                        ('lot_id','=',line.prod_lot_id.id),
                        ('quantity','>',0)
                    ])
                    if quant_id:
                        quant_id.sudo().location_id = self.dest_location_id.id     
                else:          
                    self.env['stock.inventory.line'].create(
                    {
                        'inventory_id': origin_inventory_id.id, 
                        'product_id': line.product_id.id, 
                        'product_qty': line.product_id.with_context({'location':self.origin_location_id.id}).qty_available - line.qty,                    
                        'prod_lot_id': line.prod_lot_id.id if line.prod_lot_id else False,
                        'location_id': self.origin_location_id.id
                    })   
            # Se valida el inventario 
            origin_inventory_id.action_start()
            origin_inventory_id.action_validate()
            self.origin_inventory_id = origin_inventory_id.id                       
        
        # AJUSTE DE CONSUMIBLES
        if self.picking_type in ['adjust']:
            # Se obtienen los valores para el inventario de la ubicación ORIGEN
            vals = self.get_inventory_vals(self.origin_location_id, self.picking_type, self.line_ids)
            origin_inventory_id = self.env['stock.inventory'].create(vals)            
            analytic_account_id = self.env.company.analytic_cost_account_id            
            
            # Se agregan los productos con las cantidades
            for line in self.line_ids:                
                self.env['stock.inventory.line'].create(
                {
                    'inventory_id': origin_inventory_id.id, 
                    'product_id': line.product_id.id, 
                    'product_qty': line.qty,         
                    'prod_lot_id': line.prod_lot_id.id if line.prod_lot_id else False,           
                    'location_id': self.origin_location_id.id
                })   
                # Se validan las cuentas
                if not line.product_id.categ_id.property_account_expense_categ_id:
                    raise ValidationError("No se ha definidio la cuenta de gastos del producto {} en la categoría {}".format(line.product_id.name,line.product_id.categ_id.name))
                if not line.product_id.categ_id.consumble_account_stock_id:
                    raise ValidationError("No se ha definidio la cuenta de inventario del producto {} en la categoría {}".format(line.product_id.name,line.product_id.categ_id.name))                
                #
                qty_available = line.product_id.with_context({'location':self.origin_location_id.id}).qty_available  

                # Si la cantidad disponible es menor a la especificada se crea una póliza de ingresos
                if qty_available < line.qty:
                    #                     
                    # Se agregan las lineas de la póliza de ingresos
                    amls.append((0,0,{
                        'name': _(''),
                        'debit': line.product_id.list_price * (line.qty - qty_available),
                        'credit':  0.0,
                        'account_id': line.product_id.categ_id.consumble_account_stock_id.id,
                    }))
                    amls.append((0,0,{
                        'name': _(line.product_id.name + ' ('+ str(line.qty - qty_available) + ' unidades)'),
                        'debit':  0.0,
                        'credit': line.product_id.list_price * (line.qty - qty_available),
                        'account_id': line.product_id.categ_id.property_account_expense_categ_id.id,
                        'analytic_account_id': analytic_account_id.id
                    }))   
                # Si la cantidad dsiponible es mayor a la especificada se crea póliza de gastos
                elif qty_available > line.qty:
                    # Se agregan las lineas de la póliza de gastos
                    amls.append((0,0,{
                        'name': _(''),
                        'debit': 0.0,
                        'credit':  line.product_id.list_price * (qty_available - line.qty),
                        'account_id': line.product_id.categ_id.consumble_account_stock_id.id,
                    }))
                    amls.append((0,0,{
                        'name': _(line.product_id.name + ' ('+ str(qty_available - line.qty) + ' unidades)'),
                        'debit':  line.product_id.list_price * (qty_available - line.qty),
                        'credit': 0.0,
                        'account_id': line.product_id.categ_id.property_account_expense_categ_id.id,
                        'analytic_account_id': analytic_account_id.id
                    }))   
                    pass

            # Se valida el inventario ORIGEN
            origin_inventory_id.action_start()
            origin_inventory_id.action_validate()
            self.origin_inventory_id = origin_inventory_id.id

            #
            if amls:
                # Se crea la póliza y se publica          
                move_row = self.env['account.move'].create({
                    'journal_id': config_id.consumable_journal_id.id,
                    'ref': 'Ajuste de consumibles',
                    'line_ids': amls,
                    'date': fields.Date.context_today(self)
                })          
                # Se publica la póliza
                move_row.post()
                # Se asocia la póliza al mov
                self.move_id = move_row.id  
        
        # AJUSTE DE URNAS Y ATAUDES
        if self.picking_type in ['adjust2']:
            # Se obtienen los valores para el inventario de la ubicación ORIGEN
            vals = self.get_inventory_vals(self.origin_location_id, self.picking_type, self.line_ids)
            origin_inventory_id = self.env['stock.inventory'].create(vals)  
            # Se agregan los productos con las cantidades
            for line in self.line_ids:         
                self.env['stock.inventory.line'].create(
                {
                    'inventory_id': origin_inventory_id.id, 
                    'product_id': line.product_id.id, 
                    'product_qty': 0,         
                    'prod_lot_id': line.prod_lot_id.id if line.prod_lot_id else False,           
                    'location_id': self.origin_location_id.id
                })
                # Se actualiza la cantidad transferida
                line.qty_done = line.qty

            # Se valida el inventario ORIGEN
            origin_inventory_id.action_start()
            origin_inventory_id.action_validate()
            self.origin_inventory_id = origin_inventory_id.id
        
        # TRASPASOS DE SOLICITUDES
        if self.picking_type in ['request']:
            #
            for i,line in enumerate(self.line_ids,1):     
                if not line.start_serie and not line.end_serie:
                    raise ValidationError("Debe especificar las serie inicial y final para el producto {} de la linea {}.".format(line.product_id.name,i))   

            lot_obj = self.env['stock.production.lot']
            # Se obtienen los valores para el inventario de la ubicación ORIGEN
            vals = self.get_inventory_vals(self.origin_location_id, self.picking_type, self.line_ids)
            origin_inventory_id = self.env['stock.inventory'].create(vals)  
            # Se agregan los productos con las cantidades
            for line in self.line_ids:     
                if line.product_id.tracking != 'none':
                    # Se obtiene cada solicitud en el rango especificado                                    
                    for serie in range(int(line.start_serie.name),int(line.end_serie.name) + 1,1):
                        lot = str(serie).zfill(len(line.start_serie.name))                                            
                        lot_id = lot_obj.search([('name','=',lot)], limit=1)
                        if lot_id:
                            # Se busca el quant con el lot_id
                            quant_id = self.env['stock.quant'].search(
                            [
                                ('product_id','=',line.product_id.id),
                                ('company_id','=',self.company_id.id),
                                ('location_id','=',self.origin_location_id.id),
                                ('lot_id','=',lot_id.id),
                                ('quantity','>',0)
                            ])
                            if quant_id:
                                quant_id.sudo().location_id = self.dest_location_id.id    
                            else:
                                raise ValidationError("No se encuentra existencias para la solicitud {}".format(lot))   
                        else:
                            raise ValidationError("No se encuentra la solicitud {}".format(lot))    
                                       
            # Se valida el inventario ORIGEN
            origin_inventory_id.action_start()
            origin_inventory_id.action_validate()
            self.origin_inventory_id = origin_inventory_id.id
        
        # TRASPASOS INTERNOS
        if self.picking_type in ['internal']:            
            # Se obtiene la configuración
            config_id = self.env['pabs.stock.config'].search([('company_id','=',self.env.company.id),('config_type','=','primary')],limit=1)
            if not config_id:                    
                raise ValidationError('No existe una configuración para el control de almacén.')
            if not config_id.transit_location_id:
                raise ValidationError('No se ha especificado una ubicación de tránsito en la configuración primaria.')            
            
            # Se definen origen y destino dependiendo del contexto             
            if self.env.context.get('receipt'):
                origin_location_id = config_id.transit_location_id
                dest_location_id = self.dest_location_id
            else:
                origin_location_id = self.origin_location_id
                dest_location_id = config_id.transit_location_id

            # Se valida  que todos los productos tengan existencias en el origen
            for line in self.line_ids:
                qty_available= line.product_id.with_context({'location':origin_location_id.id}).qty_available
                if qty_available < line.qty:
                    raise ValidationError('El producto {} no tiene existencias suficientes en el origen, solo pueden transferirse {} unidades.'.format(line.product_id.name,qty_available))          
                                                            
            # Se obtienen los valores para el inventario de la ubicación ORIGEN
            vals = self.get_inventory_vals(origin_location_id, self.picking_type, self.line_ids)
            origin_inventory_id = self.env['stock.inventory'].create(vals)  
            # Se agregan los productos con las cantidades
            for line in self.line_ids: 
                # Si no tiene seguimiento por serie
                if line.product_id.tracking == 'none':
                    qty = line.product_id.with_context({'location':origin_location_id.id}).qty_available - line.qty
                else:
                    qty = 0
                #
                self.env['stock.inventory.line'].create(
                {
                    'inventory_id': origin_inventory_id.id, 
                    'product_id': line.product_id.id, 
                    'product_qty': qty,
                    'prod_lot_id': line.prod_lot_id.id if line.prod_lot_id else False,
                    'location_id': origin_location_id.id
                })   
            # Se valida el inventario ORIGEN
            origin_inventory_id.action_start()
            origin_inventory_id.action_validate()
            if self.env.context.get('receipt'):
                self.dest_inventory_id = origin_inventory_id.id
            else:
                self.origin_inventory_id = origin_inventory_id.id

            # Se obtienen los valores para el inventario de la ubicación DESTINO
            vals = self.get_inventory_vals(dest_location_id, self.picking_type, self.line_ids)
            dest_inventory_id = self.env['stock.inventory'].create(vals)  
            # Se agregan los productos con las cantidades
            for line in self.line_ids:
                # Si no tiene seguimiento por serie
                if line.product_id.tracking == 'none':
                    qty = line.product_id.with_context({'location':dest_location_id.id}).qty_available + line.qty
                else:
                    qty = 1     
                self.env['stock.inventory.line'].create(
                {
                    'inventory_id': dest_inventory_id.id, 
                    'product_id': line.product_id.id, 
                    'product_qty': qty,
                    'prod_lot_id': line.prod_lot_id.id if line.prod_lot_id else False,
                    'location_id': dest_location_id.id
                })   
            # Se valida el inventario TRANSITO
            dest_inventory_id.action_start()
            dest_inventory_id.action_validate()
            if self.env.context.get('receipt'):
                self.dest_inventory_id = dest_inventory_id.id
            else:
                self.transit_inventory_id = dest_inventory_id.id
           
            # Se cambia el estatus
            if self.env.context.get('receipt'):
                self.state = 'done'
                self.date_done = fields.Date.context_today(self)
            else:
                self.state = 'transit'
            return True

        # Se actualiza el estatus del pabs.picking
        self.state = 'done'
        self.date_done = fields.Date.context_today(self)
        return True       
    
    def get_inventory_vals(self, location_id, picking_type, line_ids):        
        n = self.env['stock.inventory'].search_count([]) + 1
        if picking_type == 'going':
            name = 'Ajuste {}: {}->{}'.format(n,dict(PABS_PICKING_TYPE).get(picking_type),location_id.name)
        if picking_type == 'ret':
            name = 'Ajuste {}: {}->{}'.format(n,location_id.name,dict(PABS_PICKING_TYPE).get(picking_type))
        if picking_type in ['consumption','adjust','adjust2','request','internal']:
            name = 'Ajuste {}: {}({})'.format(n,dict(PABS_PICKING_TYPE).get(picking_type),location_id.name)
        #    
        vals  ={
            'name': name,
            'location_ids': [(6,0,[location_id.id])],
            'product_ids': [(6,0,line_ids.mapped('product_id.id'))],
            'company_id': self.company_id.id
        }
        return vals

    
    @api.model
    def create(self,vals):
        #   
        if not self.get_credentials(vals.get('picking_type')):
            raise ValidationError('No tiene permisos para realizar este tipo de operación.')   
        
        ### Validar que no existan lineas duplicadas (para productos con serie se evaluará id de producto y serie, para los demás solo producto)
        if vals.get('line_ids'):
            prod_ids = []
            for index, line in enumerate(vals.get('line_ids'), 1):
                product_id = line[2].get('product_id')
                lot_id = line[2].get('prod_lot_id')

                llave = {"product_id": product_id, "lot_id": lot_id}

                if llave not in prod_ids:
                    prod_ids.append(llave)
                else:
                    raise ValidationError("Existe una linea duplicada de producto por favor eliminela para poder continuar. Linea {}".format(index))
        #    
        res = super(PabsStockPicking, self).create(vals)   
        n = self.search_count([])
        today = fields.Date.context_today(self)
        res.name = str('Traspaso/{}/{}/{}').format(today.year,today.month,str(n))    
        return res

    ### Validar que no existan lineas duplicadas (para productos con serie se evaluará id de producto y serie, para los demás solo producto)
    def write(self,vals):
        #
        pick_line_obj = self.env['pabs.stock.picking.line']

        if not self.get_credentials(self.picking_type):
            raise ValidationError('No tiene permisos para realizar este tipo de operación.')   
        
        if vals.get('line_ids'):
            
            prod_ids = []
            for index, line in enumerate(vals.get('line_ids'), 1):
                
                llave = {}
                ### Datos de lineas existentes no modificadas: [4, 12, False]
                if line[0] == 4:
                    x = pick_line_obj.browse(line[1])
                    
                    if x.prod_lot_id:
                        llave = {"product_id": x.product_id.id, "lot_id": x.prod_lot_id.id}
                    else:
                        llave = {"product_id": x.product_id.id, "lot_id": None}
                ### Datos de lineas existentes modificadas: [1, 18, {"product_id": 99, "prod_lot_id": 001}]
                elif line[0] == 1:
                    x = pick_line_obj.browse(line[1])

                    if x.prod_lot_id:
                        llave = {"product_id": x.product_id.id, "lot_id": x.prod_lot_id.id}
                    else:
                        llave = {"product_id": x.product_id.id, "lot_id": None}

                    if "product_id" in line[2].keys():
                        llave.update({"product_id": line[2].get("product_id")})

                    if "prod_lot_id" in line[2].keys():
                        llave.update({"lot_id": line[2].get("prod_lot_id")})
                ### Datos de lineas nuevas: [0, 'virtual_226', {"product_id": 99, ...}]
                elif line[0] == 0:
                    llave = {"product_id": line[2].get('product_id'), "lot_id": line[2].get('prod_lot_id')}

                if llave:
                    if llave not in prod_ids:
                        prod_ids.append(llave)
                    else:
                        raise ValidationError("Existe una linea duplicada de producto por favor eliminela para poder continuar. Linea {}".format(index))
                
        #    
        res = super(PabsStockPicking, self).write(vals)
        return res

    @api.onchange('picking_type')
    def onchange_picking_type(self):
        for rec in self:
            #
            if rec.picking_type:
                #
                self.line_ids = False
                config_id = self.env['pabs.stock.config'].search([('company_id','=',self.env.company.id),('config_type','=','primary')],limit=1)
                if not config_id:                    
                    raise ValidationError('No existe una configuración para el control de almacén.')
                # Según el tipo de movimiento 
                if rec.picking_type in ['going']:
                    rec.origin_location_id = config_id.central_location_id.id
                    rec.dest_location_id = False                    
                if rec.picking_type == 'ret':
                    rec.dest_location_id = config_id.central_location_id.id
                    rec.origin_location_id = False
                if rec.picking_type == 'consumption':
                    rec.dest_location_id = config_id.scrap_location_id.id
                    rec.origin_location_id = False
                if rec.picking_type == 'adjust':
                    rec.origin_location_id = False
                    rec.dest_location_id = False
                if rec.picking_type in ['request']:
                    rec.origin_location_id = config_id.request_location_id.id
                    rec.dest_location_id = False
                if rec.picking_type == 'adjust2':
                    rec.origin_location_id = False
                    rec.dest_location_id = False
                if rec.picking_type == 'internal':
                    rec.origin_location_id = False
                    rec.dest_location_id = False
                #
                origin_ids = []
                for config_id in self.env['pabs.stock.config'].search([('company_id','=',self.env.company.id)]):                    
                    if config_id.central_location_id.id not in origin_ids:
                        origin_ids.append(config_id.central_location_id.id)              
                return {
                    'domain':
                    {
                        'origin_location_id': [('id','in',origin_ids)],                                           
                    }
                } 
               
class PabsStockPickingLine(models.Model):
    _name = 'pabs.stock.picking.line'
    _description = "Pabs picking stock line"

    product_id = fields.Many2one(string="Producto", comodel_name='product.product', required=True, domain="[('type','=','product'),('pabs_stock_product','=',True)]")
    qty_available = fields.Float(string="Disponible",)
    qty = fields.Float(string='Cantidad', default=1)
    qty_done = fields.Float(string='Transferido')
    start_serie  = fields.Many2one(comodel_name= 'stock.production.lot', string='Serie inicial', domain="[('id','=',0)]")
    end_serie  = fields.Many2one(comodel_name= 'stock.production.lot', string='Serie final', domain="[('id','=',0)]")
    product_tracking = fields.Selection(string='Tracking', related='product_id.tracking', readonly=True)
    prod_lot_id = fields.Many2one(
        'stock.production.lot', 'No. Serie', check_company=True,
        domain="[('product_id','=',product_id), ('company_id', '=', company_id)]")
    mortuary_id = fields.Many2one(string="Bitácora", comodel_name='mortuary')  
    pabs_picking_id = fields.Many2one(string="PABS Picking", comodel_name='pabs.stock.picking')
    company_id = fields.Many2one(comodel_name="res.company",string="Compañia",default=lambda self: self.env.company, copy=True, required=True) 

    def set_lots(self):
        if not self.pabs_picking_id.get_credentials(self.pabs_picking_id.picking_type):
            raise ValidationError('No tiene permisos para realizar este tipo de operación.')    
        return

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            # Si el tipo de operación es de SOLICTUDES      
            if rec.pabs_picking_id.picking_type == 'request':
                # Si seleccionan un producto
                if rec.product_id:                    
                    # Se obtiene la cantidad disponible en la ubicación origen           
                    rec.qty_available = rec.product_id.with_context(
                    {
                            'location': rec.pabs_picking_id.origin_location_id.id,
                            'company_owned':rec.pabs_picking_id.origin_location_id.company_id.id
                    }).qty_available
                    # Si el tipo de operación es de SOLCITUDES
                    if rec.pabs_picking_id.picking_type == 'request':                   
                        # Se obtienen los quants del producto y ubicación correspondientes
                        quant_ids = self.env['stock.quant'].search(
                            [
                                ('product_id','=',rec.product_id.id),
                                ('location_id','=',rec.pabs_picking_id.origin_location_id.id),
                                ('quantity','=',1),
                                ('reserved_quantity','=',0),
                                ('company_id','=',self.env.company.id),
                            ])
                        # Se obtienen los lotes de los quants
                        lot_ids = quant_ids.mapped('lot_id')                        
                        # Se devuelve el dominio 
                        return {
                            'domain':
                            {                           
                                'start_serie': [('id','in',lot_ids.ids)],
                                'end_serie': [('id','in',lot_ids.ids)],
                            }
                        }      
                # 
                return {
                    'domain':
                    {
                        'product_id': [('type','=','product'),('pabs_stock_product','=',False)],
                        'start_serie': [('id','=',0)],
                        'end_serie': [('id','=',0)],                     
                    }
                }      
             # Si el tipo de operación es AJUSTE DE URNAS y ATAÚDES      
            if rec.pabs_picking_id.picking_type == 'adjust2':
                # Si seleccionan un producto
                if rec.product_id:
                    #
                    rec.qty = 1       
                    # Se obtiene la cantidad disponible en la ubicación origen           
                    rec.qty_available = rec.product_id.with_context({'location': rec.pabs_picking_id.origin_location_id.id}).qty_available
                    # Si el tipo de operación es de SOLCITUDES
                    if rec.pabs_picking_id.picking_type == 'adjust2':                   
                        # Se obtienen los quants del producto y ubicación correspondientes
                        quant_ids = self.env['stock.quant'].search(
                            [
                                ('product_id','=',rec.product_id.id),
                                ('location_id','=',rec.pabs_picking_id.origin_location_id.id),
                                ('quantity','=',1),
                                ('reserved_quantity','=',0),
                                ('company_id','=',self.env.company.id),
                            ])
                        # Se obtienen los lotes de los quants
                        lot_ids = quant_ids.mapped('lot_id')                        
                        # Se devuelve el dominio 
                        return {
                            'domain':
                            {                           
                                'prod_lot_id': [('id','in',lot_ids.ids)],                               
                            }
                        }  
                return {                  
                    'domain':
                    {
                        'product_id': [
                            ('type','=','product'),
                            ('pabs_stock_product','=',True),
                            ('tracking','=','serial'),
                            ('categ_id.name','in',['ATAUDES','URNAS','ROSARIOS','PAQUETES'])],
                        'start_serie': [('id','=',0)],
                        'end_serie': [('id','=',0)],                     
                    }
                }

            # Si se seleccionó un producto
            if rec.product_id:                                                   
                rec.qty_available = rec.product_id.with_context({'location': rec.pabs_picking_id.origin_location_id.id}).qty_available               

    
    @api.onchange('start_serie','end_serie')
    def onchange_start_serie(self):
        for rec in self:                
            if rec.start_serie and rec.end_serie:
                qty = int(rec.end_serie) - int(rec.start_serie)
                if qty < 0:
                    rec.start_serie = rec.end_serie = 0                
                else:
                    rec.qty = qty + 1
    
    def set_lots(self):
        if self.pabs_picking_id.state != 'draft':
            raise ValidationError("Esta transferencia ya está validada o cancelada.")
        if self.pabs_picking_id.picking_type != 'request':
            raise ValidationError("Solo se pueden especificar series para el traspaso de solictudes.")
        # Se obtienen los quants del producto y ubicación correspondientes
        quant_ids = self.env['stock.quant'].search(
            [
                ('product_id','=',self.product_id.id),
                ('location_id','=',self.pabs_picking_id.origin_location_id.id),              
                ('quantity','=',1),
                ('reserved_quantity','=',0),
                ('company_id','=',self.env.company.id),
            ])
        # Se obtienen los lotes de los quants
        lot_ids = quant_ids.mapped('lot_id')
      
        vals = {
            'product_id': self.product_id.id,
            'pabs_stock_picking_line_id': self.id
        }
        wizard_id = self.env['set.lots.wizard'].create(vals)
        return {
            'name': _("Especificar lotes"),        
            'context': {'domain_start': lot_ids.ids},        
            'view_type': 'form',        
            'view_mode': 'form',        
            'res_model': 'set.lots.wizard', 
            'res_id': wizard_id.id,
            'views': [(False, 'form')],        
            'type': 'ir.actions.act_window',        
            'target': 'new',   
            }
        return action_id
    