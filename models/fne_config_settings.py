# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)
class ResConfigSettings(models.TransientModel):
    """Configuration FNE intégrée dans les paramètres généraux"""
    _inherit = 'res.config.settings'

    # ⚠️ NE PAS utiliser config_parameter dans Odoo 11 si ça ne fonctionne pas
    # On va gérer manuellement avec get_values() et set_values()
    
    fne_api_key = fields.Char(
        string="API Key FNE",
        help="Clé API fournie par la DGI pour l'accès au service FNE"
    )
    
    fne_mode = fields.Selection(
        [
            ('test', 'Test'),
            ('prod', 'Production')
        ],
        string="Mode",
        default='test',
        help="Environnement d'exécution (Test ou Production)"
    )
    
    fne_auto_send = fields.Boolean(
        string="Envoi automatique après validation",
        default=False,
        help="Si coché, les factures seront automatiquement envoyées à la DGI après validation"
    )
    
    fne_test_url = fields.Char(
        string="URL Test",
        default="http://54.247.95.108/ws",
        help="URL de l'API FNE en environnement de test"
    )
    
    fne_prod_url = fields.Char(
        string="URL Production",
        default="https://www.services.fne.dgi.gouv.ci/ws",
        help="URL de l'API FNE en environnement de production"
    )
    
    fne_point_de_vente = fields.Char(
        string="Point de Vente",
        help="Identifiant du point de vente pour le FNE (ex: SIEGE NEURONES)"
    )
    
    fne_establishment = fields.Char(
        string="Établissement",
        help="Nom de l'établissement (ex: NEURONES TECHNOLOGIES SA)"
    )
    
    fne_footer = fields.Html(
        string="Pied de page FNE",
        default="<p>Merci pour votre confiance</p>",
        help="Message HTML affiché en pied de page sur les factures certifiées"
    )

    @api.model
    def get_values(self):
        """
        Récupération des valeurs depuis ir.config_parameter
        Cette méthode est appelée lors de l'ouverture du formulaire de configuration
        """
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        # Récupérer chaque paramètre depuis ir.config_parameter
        res.update(
            fne_api_key=ICPSudo.get_param('fne.api_key', default=''),
            fne_mode=ICPSudo.get_param('fne.mode', default='test'),
            fne_auto_send=ICPSudo.get_param('fne.auto_send', default='False') == 'True',
            fne_test_url=ICPSudo.get_param('fne.test_url', default='http://54.247.95.108/ws'),
            fne_prod_url=ICPSudo.get_param('fne.prod_url', default='https://www.services.fne.dgi.gouv.ci/ws'),
            fne_point_de_vente=ICPSudo.get_param('fne.point_de_vente', default=''),
            fne_establishment=ICPSudo.get_param('fne.establishment', default=''),
            fne_footer=ICPSudo.get_param('fne.footer', default='<p>Merci pour votre confiance</p>'),
        )
        
        return res

    @api.multi
    def set_values(self):
        """
        Sauvegarde des valeurs dans ir.config_parameter
        Cette méthode est appelée lors du clic sur "Appliquer" ou "Enregistrer"
        """
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        # Sauvegarder chaque paramètre dans ir.config_parameter
        ICPSudo.set_param('fne.api_key', self.fne_api_key or '')
        ICPSudo.set_param('fne.mode', self.fne_mode or 'test')
        ICPSudo.set_param('fne.auto_send', 'True' if self.fne_auto_send else 'False')
        ICPSudo.set_param('fne.test_url', self.fne_test_url or 'http://54.247.95.108/ws')
        ICPSudo.set_param('fne.prod_url', self.fne_prod_url or 'https://www.services.fne.dgi.gouv.ci/ws')
        ICPSudo.set_param('fne.point_de_vente', self.fne_point_de_vente or '')
        ICPSudo.set_param('fne.establishment', self.fne_establishment or '')
        ICPSudo.set_param('fne.footer', self.fne_footer or '<p>Merci pour votre confiance</p>')
        
        # Log pour debug
  
        _logger.info("=" * 70)
        _logger.info("[FNE CONFIG] Paramètres sauvegardés avec succès:")
        _logger.info(f"  - Mode: {self.fne_mode}")
        _logger.info(f"  - API Key: {'*' * 10 if self.fne_api_key else 'Non configurée'}")
        _logger.info(f"  - Point de vente: {self.fne_point_de_vente}")
        _logger.info(f"  - Établissement: {self.fne_establishment}")
        _logger.info(f"  - Auto send: {self.fne_auto_send}")
        _logger.info("=" * 70)
