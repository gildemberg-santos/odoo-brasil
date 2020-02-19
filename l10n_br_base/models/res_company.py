import re
import logging
import base64
from datetime import datetime
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

try:
    from OpenSSL import crypto
except ImportError:
    _logger.error('Cannot import OpenSSL.crypto', exc_info=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _compute_expiry_date(self):
        try:
            pfx = base64.decodestring(
                self.with_context(bin_size=False).l10n_br_certificate)
            pfx = crypto.load_pkcs12(pfx, self.l10n_br_cert_password)
            cert = pfx.get_certificate()
            end = datetime.strptime(
                cert.get_notAfter().decode(), '%Y%m%d%H%M%SZ')
            subj = cert.get_subject()
            self.l10n_br_cert_expire_date = end.date()
            if datetime.now() < end:
                self.l10n_br_cert_state = 'valid'
            else:
                self.l10n_br_cert_state = 'expired'
            self.l10n_br_cert_information = "%s\n%s\n%s\n%s" % (
                subj.CN, subj.L, subj.O, subj.OU)
        except crypto.Error:
            self.l10n_br_cert_state = 'invalid_password'
        except:
            self.l10n_br_cert_state = 'unknown'
            _logger.warning(
                _(u'Unknown error when validating certificate'),
                exc_info=True)

    l10n_br_certificate = fields.Binary('Certificado A1')
    l10n_br_cert_password = fields.Char('Senha certificado', size=64)

    l10n_br_cert_state = fields.Selection(
        [('not_loaded', u'Not loaded'),
         ('expired', u'Expired'),
         ('invalid_password', u'Invalid Password'),
         ('unknown', u'Unknown'),
         ('valid', u'Valid')],
        string=u"Cert. State", compute=_compute_expiry_date,
        default='not_loaded')
    l10n_br_cert_information = fields.Text(
        string=u"Cert. Info", compute=_compute_expiry_date)
    l10n_br_cert_expire_date = fields.Date(
        string=u"Cert. Expiration Date", compute=_compute_expiry_date)

    @api.onchange('cnpj_cpf')
    def onchange_mask_cnpj_cpf(self):
        if self.cnpj_cpf:
            val = re.sub('[^0-9]', '', self.cnpj_cpf)
            if len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
                self.cnpj_cpf = cnpj_cpf

    @api.onchange('zip')
    def onchange_mask_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                zip = "%s-%s" % (val[0:5], val[5:8])
                self.zip = zip
