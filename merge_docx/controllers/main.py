# -*- encoding: utf-8 -*-
import json

from werkzeug.urls import url_decode
import time
from odoo.tools.safe_eval import safe_eval

from odoo.http import request, serialize_exception as _serialize_exception
from odoo.addons.web.controllers.main import content_disposition
from odoo import http
from odoo.tools import html_escape
from odoo.addons.web.controllers.main import ReportController as RC


class ReportControllerExtend(RC):
    @http.route([
        '/report/<converter>/<reportname>',
        '/report/<converter>/<reportname>/<docids>',
    ], type='http', auth='user', website=True)
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter == 'docx_to_x':
            report = request.env['ir.actions.report']._get_report_from_name(reportname)
            context = dict(request.env.context)
            doc_ids = docids
            if doc_ids:
                doc_ids = [int(i) for i in doc_ids.split(',')]
            if data.get('options'):
                data.update(json.loads(data.pop('options')))
            if data.get('context'):
                # Ignore 'lang' here, because the context in data is the one from the webclient *but* if
                # the user explicitely wants to change the lang, this mechanism overwrites it.
                data['context'] = json.loads(data['context'])
                if data['context'].get('lang'):
                    del data['context']['lang']
                context.update(data['context'])
            mimetype, out, report_name, ext = report.with_context(context).render_any_docs(doc_ids, data=data)
            """
            filename = "%s.%s" % (report.name, ext)
            if ext == 'pdf':
                pdfhttpheaders = [('Content-Type', mimetype), ('Content-Length', len(out))]
            else:
                pdfhttpheaders = [('Content-Type', mimetype), ('Content-Length', len(out)),
                                  ('Content-Disposition', content_disposition(filename))]"""
            pdfhttpheaders = [('Content-Type', mimetype), ('Content-Length', len(out))]
            return request.make_response(out, headers=pdfhttpheaders)
        return super(ReportControllerExtend, self).report_routes(reportname, docids, converter, **data)

    @http.route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token, context=None):
        requestcontent = json.loads(data)
        url, type = requestcontent[0], requestcontent[1]
        try:
            if type == 'qweb-docx_to_x':
                converter = 'docx_to_x'
                default_output_file = 'docx'

                pattern = '/report/docx_to_x/'
                reportname = url.split(pattern)[1].split('?')[0]

                docids = None
                if '/' in reportname:
                    reportname, docids = reportname.split('/')

                if docids:
                    # Generic report:
                    response = self.report_routes(reportname, docids=docids, converter=converter, context=context)
                else:
                    # Particular report:
                    data = url_decode(url.split('?')[1]).items()  # decoding the args represented in JSON
                    response = self.report_routes(reportname, converter=converter, context=context, **dict(data))

                report = request.env['ir.actions.report']._get_report_from_name(reportname)
                extension = report.output_file or default_output_file
                filename = "%s.%s" % (report.name, extension)

                if docids:
                    ids = [int(x) for x in docids.split(",")]
                    obj = request.env[report.model].browse(ids)
                    if report.print_report_name and not len(obj) > 1:
                        report_name = safe_eval(report.print_report_name, {'object': obj, 'time': time})
                        filename = "%s.%s" % (report_name, extension)
                response.headers.add('Content-Disposition', content_disposition(filename))
                response.set_cookie('fileToken', token)
                return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': "Odoo Server Error",
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
        return super(ReportControllerExtend, self).report_download(data, token, context)
