odoo.define('merge_docx.ext_report', function (require) {
'use strict';

var ActionManager = require('web.ActionManager');

ActionManager.include({
    _executeReportAction: function (action, options) {
        var self = this;
        if (action.report_type === 'docx') {
            return self._triggerDownload(action, options, 'docx');
        }
        return this._super(action, options);
    },  
    _makeReportUrls: function (action) {
        var self = this;
        var reportUrls = this._super(action);
        reportUrls.docx = '/report/docx_to_x/' + action.report_name;

        // We may have to build a query string with `action.data`. It's the place
        // were report's using a wizard to customize the output traditionally put
        // their options.
        if (action.report_type === 'docx'){
            if (_.isUndefined(action.data) || _.isNull(action.data) ||
                (_.isObject(action.data) && _.isEmpty(action.data))) {
                if (action.context.active_ids) {
                    var activeIDsPath = '/' + action.context.active_ids.join(',');
                    reportUrls = _.mapObject(reportUrls, function (value) {
                        return value += activeIDsPath;
                    });
                }
            } else {
                var serializedOptionsPath = '?options=' + encodeURIComponent(JSON.stringify(action.data));
                serializedOptionsPath += '&context=' + encodeURIComponent(JSON.stringify(action.context));
                reportUrls = _.mapObject(reportUrls, function (value) {
                    return value += serializedOptionsPath;
                });
            }
        }
        return reportUrls
    },
});

});