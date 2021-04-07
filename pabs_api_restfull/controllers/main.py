# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request, Response
import json
import logging

_logger = logging.getLogger(__name__)


class APIREST(http.Controller):

  @http.route('/api/search', type='http', auth='none',methods=['POST'], csrf=False)
  def search_query(self, **kargs):
    response_header = {'Content-Type': 'application/json'}
    cr = request.cr
    if kargs.get('query'):
      try:
        cr.execute(kargs.get('query'))
        records = []
        headers = [d[0] for d in cr.description]
        for res in cr.fetchall():
          data = {}
          for ind, rec in enumerate(headers):
            data.update({
              headers[ind] : res[ind]
            })
          records.append(data)
          response = {
            'result' : records
          }
        return Response(json.dumps(response),headers=response_header)
      except Exception as e:
        return str(e)
    return Response("Petición Denegada", status=400)
