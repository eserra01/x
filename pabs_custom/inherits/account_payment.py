# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

WAY_TO_PAY = [
  ('cash','Efectivo'),
  ('transfer', 'Transferencia'),
  ('credit_card','Tarjeta de Crédito/Débito')]

REFERENCE =[('payment','Abono'),
  ('stationary','Papelería'),
  ('surplus','Excedente'),
  ('transfer','Traspaso'),
  ('payment_mortuary','Cobro Funeraria'),
  ('setlement_service_done', 'LCP por servicio realizado'),
  ('payment_expense','Pago de gasto')]

TYPE_CARD =[('tdc','Tarjeta de Crédito'),
  ('tdd','Tarjeta Débito')]

DESTINO_DE_PAGO_FUNERARIA =[
  ('directo', 'Servicio directo'),
  ('adicionales', 'Adicionales')
]

class account_Payment(models.Model):
    _inherit = 'account.payment'

    date_receipt = fields.Date(string="Fecha Recibo")

    reference = fields.Selection(selection  = REFERENCE, string="Referencia",required = True)

    ecobro_receipt = fields.Char(string="Recibo Ecobro")

    debt_collector_code = fields.Many2one(comodel_name = 'hr.employee' ,string="Cobrador")

    contract = fields.Many2one(comodel_name = 'pabs.contract',string= "Contrato")

    way_to_pay =  fields.Selection(selection=WAY_TO_PAY,
      string = 'Forma de pago',
      required = True)

    payment_date = fields.Date(string="Fecha Cobranza")

    type_card_payment = fields.Selection(selection = TYPE_CARD,
      string= "Tipo de tarjeta")

    card_number = fields.Char(string = "Número de tarjeta", size = 4)

    card_expiration_date = fields.Date(string='Fecha de expiración')

    card_expiration_month = fields.Char(string = "Mes de vencimiento", size = 2)
    card_expiration_year = fields.Char(string = "Año de vencimiento", size = 4)

    number_phone = fields.Char(string = "Número de teléfono")

    authorization_number = fields.Char(string = "Número de autorización")

    transfer_date = fields.Date(string = "Fecha de transferencia")

    transfer_reference = fields.Char(string = "Referencia")

    comission_output_ids = fields.One2many(comodel_name="pabs.comission.output", inverse_name="payment_id", string="Salidas de comisiones")

    destino_de_pago_funeraria =  fields.Selection(selection = DESTINO_DE_PAGO_FUNERARIA, string = 'Destino de pago funeraria')

    def ripcord_query(self, company_id, date_start, date_end):
      #
      cr = self._cr
      query = """
      SELECT SUM(A.amount),C.name as cobrador,C.barcode 
      FROM account_payment A INNER JOIN account_journal B ON A.journal_id = B.id 
      INNER JOIN hr_employee C ON A.debt_collector_code = C.id 
      WHERE B.company_id = %s AND 
      A.payment_type = 'inbound' AND 
      A.state = 'posted' AND 
      A.payment_date BETWEEN '%s' AND '%s' 
      GROUP BY C.barcode,C.name ORDER BY C.barcode ASC;
      """%(company_id, date_start, date_end)     
      cr.execute(query)
      dict = cr.dictfetchall()    
      return dict
     


    def post(self):
      contract_status_obj = self.env['pabs.contract.status']
      contract_status_reason_obj = self.env['pabs.contract.status.reason']
      ### Estatus Activo
      status_active_id = contract_status_obj.search([
        ('ecobro_code','=',1)],limit=1)
      ### BUSCAMOS LA RAZÓN DE ACTIVO
      status_reason_id = contract_status_reason_obj.search([
        ('reason','=','ACTIVO'),
        ('status_id','=',status_active_id.id)])
      comission_tree_obj = self.env['pabs.comission.tree'].with_context(
        force_company=self.contract.company_id.id)
      res = super(account_Payment, self).post()
      context = self._context
      IdPago = self.id
      if self.contract:
        if self.reference in ('payment','stationary','surplus'):
          CodigoCobrador = self.debt_collector_code.barcode
          NumeroContrato = self.contract.id
          MontoPago = self.amount or 0
          if context.get('stationery'):
            comission_tree_obj.CrearSalidasEnganche(
              IdPago=IdPago, NumeroContrato=NumeroContrato, 
              MontoPago=MontoPago, TipoPago='Papeleria')
          elif context.get('excedent'):
            comission_tree_obj.CrearSalidas(
              IdPago=IdPago, NumeroContrato=NumeroContrato,
              CodigoCobrador=CodigoCobrador, MontoPago=MontoPago,
              EsExcedente=True)
          else:
            comission_tree_obj.CrearSalidas(
              IdPago=IdPago, NumeroContrato=NumeroContrato,
              CodigoCobrador=CodigoCobrador, MontoPago=MontoPago,
              EsExcedente=False)
          ### VALIDAMOS SI EL CONTRATO ESTA EN ESTATUS DIFERENTE DE ACTIVO
          if self.contract.contract_status_item.id != status_active_id.id:
            ### PONEMOS LOS CONTRATOS EN ACTIVO
            self.contract.contract_status_item = status_active_id.id
            self.contract.contract_status_reason = status_reason_id.id
        if self.reference == 'transfer':
          CodigoCobrador = self.debt_collector_code.barcode
          NumeroContrato = self.contract.id
          MontoPago = self.amount or 0
          comission_tree_obj.CrearSalidasEnganche(
            IdPago=self.id, NumeroContrato=NumeroContrato,
            MontoPago=MontoPago, TipoPago='Transfer')
      return res

    def disassociate_payment(self):
      reconcile_model = self.env['account.partial.reconcile'].sudo()
      if self.move_line_ids:
        for obj in self.move_line_ids:
          if obj.credit > 0:
            reconcile_id = reconcile_model.search([
              ('credit_move_id','=',obj.id)])
            if reconcile_id:
              reconcile_id.unlink()

    def cancel(self):
      comission_tree_obj = self.env['pabs.comission.tree']
      self.disassociate_payment()
      res = super(account_Payment, self).cancel()
      IdPago = self.id
      if self.contract and self.comission_output_ids:
        NumeroContrato = self.contract.id
        comission_tree_obj.RevertirSalidas(
          IdPago=IdPago,NumeroContrato=NumeroContrato)
      return res 

    #Fields mortuary

    binnacle =fields.Many2one(comodel_name = 'mortuary',string= "Número de bitácora")

    user_create_payment = fields.Many2one(comodel_name = 'hr.employee' ,string="Persona que crea pago")
    
    balance_binnacle = fields.Float(string = "Saldo")

    date_of_death = fields.Date(string ="Fecha de defunción")

    place_of_death = fields.Char(string = "Lugar de fallecimiento")

    additional = fields.Char(string ="Adicionales")

    payment_person = fields.Char(string='Cliente que realizó el pago')

    @api.onchange('contract')
    def _onchange_contract(self):
      for rec in self:
        if rec.contract:
          rec.partner_id = rec.contract.partner_id.id

    @api.onchange('binnacle')
    def _onchange_binnacle(self):
      for rec in self:
        if rec.binnacle:
          rec.partner_id = rec.binnacle.partner_id.id
        
    _sql_constraints = [
      ('unique_ecobro_payment',
      'UNIQUE(ecobro_receipt, company_id)',
      'No se puede crear el registro: ya existe el pago en el sistema -> [ecobro_receipt, company_id]'),
    ]

    ########### Método modificado para operar parte fiscal 18/09/2021 ################
    def _prepare_payment_moves(self):
      ''' Prepare the creation of journal entries (account.move) by creating a list of python dictionary to be passed
      to the 'create' method.

      Example 1: outbound with write-off:

      Account             | Debit     | Credit
      ---------------------------------------------------------
      BANK                |   900.0   |
      RECEIVABLE          |           |   1000.0
      WRITE-OFF ACCOUNT   |   100.0   |

      Example 2: internal transfer from BANK to CASH:

      Account             | Debit     | Credit
      ---------------------------------------------------------
      BANK                |           |   1000.0
      TRANSFER            |   1000.0  |
      CASH                |   1000.0  |
      TRANSFER            |           |   1000.0

      :return: A list of Python dictionary to be passed to env['account.move'].create.
      '''
      all_move_vals = []
      for payment in self:
        company_currency = payment.company_id.currency_id
        move_names = payment.move_name.split(payment._get_move_name_transfer_separator()) if payment.move_name else None

        # Compute amounts.
        write_off_amount = payment.payment_difference_handling == 'reconcile' and -payment.payment_difference or 0.0
        if payment.payment_type in ('outbound', 'transfer'):
            counterpart_amount = payment.amount
            liquidity_line_account = payment.journal_id.default_debit_account_id
        else:
            counterpart_amount = -payment.amount
            liquidity_line_account = payment.journal_id.default_credit_account_id

        # Manage currency.
        if payment.currency_id == company_currency:
            # Single-currency.
            balance = counterpart_amount
            write_off_balance = write_off_amount
            counterpart_amount = write_off_amount = 0.0
            currency_id = False
        else:
            # Multi-currencies.
            balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.payment_date)
            write_off_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.payment_date)
            currency_id = payment.currency_id.id

        # Manage custom currency on journal for liquidity line.
        if payment.journal_id.currency_id and payment.currency_id != payment.journal_id.currency_id:
            # Custom currency on journal.
            if payment.journal_id.currency_id == company_currency:
                # Single-currency
                liquidity_line_currency_id = False
            else:
                liquidity_line_currency_id = payment.journal_id.currency_id.id
            liquidity_amount = company_currency._convert(
                balance, payment.journal_id.currency_id, payment.company_id, payment.payment_date)
        else:
            # Use the payment currency.
            liquidity_line_currency_id = currency_id
            liquidity_amount = counterpart_amount

        # Compute 'name' to be used in receivable/payable line.
        rec_pay_line_name = ''
        if payment.payment_type == 'transfer':
            rec_pay_line_name = payment.name
        else:
            if payment.partner_type == 'customer':
                if payment.payment_type == 'inbound':
                    rec_pay_line_name += _("Customer Payment")
                elif payment.payment_type == 'outbound':
                    rec_pay_line_name += _("Customer Credit Note")
            elif payment.partner_type == 'supplier':
                if payment.payment_type == 'inbound':
                    rec_pay_line_name += _("Vendor Credit Note")
                elif payment.payment_type == 'outbound':
                    rec_pay_line_name += _("Vendor Payment")
            if payment.invoice_ids:
                rec_pay_line_name += ': %s' % ', '.join(payment.invoice_ids.mapped('name'))

        # Compute 'name' to be used in liquidity line.
        if payment.payment_type == 'transfer':
            liquidity_line_name = _('Transfer to %s') % payment.destination_journal_id.name
        else:
            liquidity_line_name = payment.name

        ##### MODIFICACIONES FISCAL 17/09/2021 #####
        es_fiscal = payment.company_id.apply_taxes

        ### Proceso para empresa fiscal ###
        if es_fiscal:            
          
          # Buscar impuesto a aplicar: para funeraria se utiliza el impuesto con nombre "IVA FUNERARIA", para los demas tipos de pago se utiliza el impuesto con nombre "IVA"
          impuesto_IVA = 0
          if payment.reference == 'payment_mortuary':
            impuesto_IVA = self.env['account.tax'].search([('name','=','IVA FUNERARIA'), ('company_id','=', payment.company_id.id)])
            if not impuesto_IVA:
              raise ValidationError("No se encontró el impuesto con nombre IVA FUNERARIA")
          else:
            impuesto_IVA = self.env['account.tax'].search([('name','=','IVA'), ('company_id','=', payment.company_id.id)])
            if not impuesto_IVA:
              raise ValidationError("No se encontró el impuesto con nombre IVA")
            
          # Buscar cuenta a aplicar en linea de repartición de impuesto
          linea_de_impuesto = impuesto_IVA.invoice_repartition_line_ids.filtered_domain([
            ('repartition_type','=','tax'), 
            ('invoice_tax_id','=', impuesto_IVA.id), 
            ('company_id','=', payment.company_id.id)
          ])

          if not linea_de_impuesto:
            raise ValidationError("No se encontró la repartición de facturas del impuesto {}".format(impuesto_IVA.name))
          if len(linea_de_impuesto) > 1:
            raise ValidationError("Se definió mas de una linea (sin incluir la linea base) en la repartición de facturas del impuesto {}".format(impuesto_IVA.name))

          factor_iva = 1 + (impuesto_IVA.amount/100)

          ### Referencia: Cobro funeraria (Existen 2 destinos de pago: 1. directo y 2. adicionales)
          if payment.reference == 'payment_mortuary':

            # Buscar contra cuenta de IVA
            if not impuesto_IVA.inverse_tax_account:
              raise ValidationError("No se ha definido la contra cuenta de IVA en el impuesto IVA")
            
            ### 1. Con aplicación de IVA (SERVICIO DIRECTO)
            if payment.destino_de_pago_funeraria == 'directo':
              apuntes = [
                # Receivable / Payable / Transfer line. Subtotal = (Cantidad / 1.16)
                (0, 0, {
                    'name': rec_pay_line_name,
                    'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                    'currency_id': currency_id,
                    'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                    'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.commercial_partner_id.id,
                    'account_id': payment.destination_account_id.id,
                    'payment_id': payment.id,
                }),

                # Liquidity line.
                (0, 0, {
                    'name': liquidity_line_name,
                    'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                    'currency_id': liquidity_line_currency_id,
                    'debit': balance < 0.0 and -balance or 0.0,
                    'credit': balance > 0.0 and balance or 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.commercial_partner_id.id,
                    'account_id': liquidity_line_account.id,
                    'payment_id': payment.id,
                }),

                # IVA
                (0, 0, {
                    'name': impuesto_IVA.name,
                    'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                    'currency_id': liquidity_line_currency_id,
                    'debit': balance < 0.0 and round(-balance - round(-balance / factor_iva ,2) ,2) or 0.0,
                    'credit': balance > 0.0 and round( balance + round(balance / factor_iva ,2) ,2) or 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.commercial_partner_id.id,
                    'account_id': linea_de_impuesto.account_id.id,
                    'payment_id': payment.id,
                }),

                # Contra partida de IVA
                (0, 0, {
                    'name': impuesto_IVA.name,
                      'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                      'currency_id': currency_id,
                      'debit': balance + write_off_balance > 0.0 and round(balance + write_off_balance - round( (balance + write_off_balance) / factor_iva, 2), 2)  or 0.0,
                      'credit': balance + write_off_balance < 0.0 and round(-balance - write_off_balance - round( (-balance - write_off_balance) / factor_iva, 2), 2) or 0.0,
                      'date_maturity': payment.payment_date,
                      'partner_id': payment.partner_id.commercial_partner_id.id,
                      'account_id': impuesto_IVA.inverse_tax_account.id,
                      'payment_id': payment.id,
                }),
              ]
            ### 2. SIN APLICACIÓN DE IVA (Adicionales de funeraria)
            else:
              apuntes = [
              # Receivable / Payable / Transfer line.
              (0, 0, {
                  'name': rec_pay_line_name,
                  'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                  'currency_id': currency_id,
                  'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                  'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                  'date_maturity': payment.payment_date,
                  'partner_id': payment.partner_id.commercial_partner_id.id,
                  'account_id': payment.destination_account_id.id,
                  'payment_id': payment.id,
              }),
              # Liquidity line.
              (0, 0, {
                  'name': liquidity_line_name,
                  'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                  'currency_id': liquidity_line_currency_id,
                  'debit': balance < 0.0 and -balance or 0.0,
                  'credit': balance > 0.0 and balance or 0.0,
                  'date_maturity': payment.payment_date,
                  'partner_id': payment.partner_id.commercial_partner_id.id,
                  'account_id': liquidity_line_account.id,
                  'payment_id': payment.id,
              }),
            ]
          
          ### Construir los apuntes con IVA para los demas tipos de pago
          else:
            apuntes = [
              # Receivable / Payable / Transfer line. Subtotal = (Cantidad / 1.16)
              (0, 0, {
                  'name': rec_pay_line_name,
                  'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                  'currency_id': currency_id,
                  'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                  'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                  'date_maturity': payment.payment_date,
                  'partner_id': payment.partner_id.commercial_partner_id.id,
                  'account_id': payment.destination_account_id.id,
                  'payment_id': payment.id,
              }),

              # Liquidity line.
              (0, 0, {
                  'name': liquidity_line_name,
                  'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                  'currency_id': liquidity_line_currency_id,
                  'debit': balance < 0.0 and round(-balance / factor_iva ,2) or 0.0,
                  'credit': balance > 0.0 and round(balance / factor_iva ,2) or 0.0,
                  'date_maturity': payment.payment_date,
                  'partner_id': payment.partner_id.commercial_partner_id.id,
                  'account_id': liquidity_line_account.id,
                  'payment_id': payment.id,
              }),

              # IVA = Cantidad - subtotal
              (0, 0, {
                  'name': impuesto_IVA.name,
                  'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                  'currency_id': liquidity_line_currency_id,
                  'debit': balance < 0.0 and round(-balance - round(-balance / factor_iva ,2) ,2) or 0.0,
                  'credit': balance > 0.0 and round( balance + round(balance / factor_iva ,2) ,2) or 0.0,
                  'date_maturity': payment.payment_date,
                  'partner_id': payment.partner_id.commercial_partner_id.id,
                  'account_id': linea_de_impuesto.account_id.id,
                  'payment_id': payment.id,
              }),
            ]
        ### Sin aplicación de IVA ###
        ##### FIN MODIFICACIONES FISCAL #####
        else: 
          apuntes = [
            # Receivable / Payable / Transfer line.
            (0, 0, {
                'name': rec_pay_line_name,
                'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                'currency_id': currency_id,
                'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                'date_maturity': payment.payment_date,
                'partner_id': payment.partner_id.commercial_partner_id.id,
                'account_id': payment.destination_account_id.id,
                'payment_id': payment.id,
            }),
            # Liquidity line.
            (0, 0, {
                'name': liquidity_line_name,
                'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                'currency_id': liquidity_line_currency_id,
                'debit': balance < 0.0 and -balance or 0.0,
                'credit': balance > 0.0 and balance or 0.0,
                'date_maturity': payment.payment_date,
                'partner_id': payment.partner_id.commercial_partner_id.id,
                'account_id': liquidity_line_account.id,
                'payment_id': payment.id,
            }),
          ]

        # ==== 'inbound' / 'outbound' ====
        move_vals = {
            'date': payment.payment_date,
            'ref': payment.communication,
            'journal_id': payment.journal_id.id,
            'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
            'partner_id': payment.partner_id.id,
            'line_ids': apuntes,
        }

        if write_off_balance:
            # Write-off line.
            move_vals['line_ids'].append((0, 0, {
                'name': payment.writeoff_label,
                'amount_currency': -write_off_amount,
                'currency_id': currency_id,
                'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
                'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
                'date_maturity': payment.payment_date,
                'partner_id': payment.partner_id.commercial_partner_id.id,
                'account_id': payment.writeoff_account_id.id,
                'payment_id': payment.id,
            }))

        if move_names:
            move_vals['name'] = move_names[0]

        all_move_vals.append(move_vals)

        # ==== 'transfer' ====
        if payment.payment_type == 'transfer':
            journal = payment.destination_journal_id

            # Manage custom currency on journal for liquidity line.
            if journal.currency_id and payment.currency_id != journal.currency_id:
                # Custom currency on journal.
                liquidity_line_currency_id = journal.currency_id.id
                transfer_amount = company_currency._convert(balance, journal.currency_id, payment.company_id, payment.payment_date)
            else:
                # Use the payment currency.
                liquidity_line_currency_id = currency_id
                transfer_amount = counterpart_amount

            transfer_move_vals = {
                'date': payment.payment_date,
                'ref': payment.communication,
                'partner_id': payment.partner_id.id,
                'journal_id': payment.destination_journal_id.id,
                'line_ids': [
                    # Transfer debit line.
                    (0, 0, {
                        'name': payment.name,
                        'amount_currency': -counterpart_amount if currency_id else 0.0,
                        'currency_id': currency_id,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.commercial_partner_id.id,
                        'account_id': payment.company_id.transfer_account_id.id,
                        'payment_id': payment.id,
                    }),
                    # Liquidity credit line.
                    (0, 0, {
                        'name': _('Transfer from %s') % payment.journal_id.name,
                        'amount_currency': transfer_amount if liquidity_line_currency_id else 0.0,
                        'currency_id': liquidity_line_currency_id,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.commercial_partner_id.id,
                        'account_id': payment.destination_journal_id.default_credit_account_id.id,
                        'payment_id': payment.id,
                    }),
                ],
            }

            if move_names and len(move_names) == 2:
                transfer_move_vals['name'] = move_names[1]

            all_move_vals.append(transfer_move_vals)
      #raise ValidationError("{}".format(all_move_vals))
      return all_move_vals