# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    """Configuration FNE intégrée dans les paramètres généraux"""
    _inherit = 'res.config.settings'
    # ❌ NE PAS mettre _name quand on fait _inherit

    # Utiliser config_parameter pour la liaison automatique avec ir.config_parameter
    fne_api_key = fields.Char(
        string="API Key FNE",
        config_parameter='fne.api_key',
        help="Clé API fournie par la DGI pour l'accès au service FNE"
    )
    
    fne_mode = fields.Selection(
        [
            ('test', 'Test'),
            ('prod', 'Production')
        ],
        string="Mode",
        default='test',
        config_parameter='fne.mode',
        help="Environnement d'exécution (Test ou Production)"
    )
    
    fne_auto_send = fields.Boolean(
        string="Envoi automatique après validation",
        default=False,
        config_parameter='fne.auto_send',
        help="Si coché, les factures seront automatiquement envoyées à la DGI après validation"
    )
    
    fne_test_url = fields.Char(
        string="URL Test",
        default="http://54.247.95.108/ws",
        config_parameter='fne.test_url',
        help="URL de l'API FNE en environnement de test"
    )
    
    fne_prod_url = fields.Char(
        string="URL Production",
        default="https://www.services.fne.dgi.gouv.ci/ws",
        config_parameter='fne.prod_url',
        help="URL de l'API FNE en environnement de production"
    )
    
    fne_point_de_vente = fields.Char(
        string="Point de Vente",
        config_parameter='fne.point_de_vente',
        help="Identifiant du point de vente pour le FNE (ex: SIEGE NEURONES)"
    )
    
    fne_footer = fields.Html(
        string="Pied de page FNE",
        default="<p>Merci pour votre confiance</p>",
        config_parameter='fne.footer',
        help="Message HTML affiché en pied de page sur les factures certifiées"
    )

    # ============================================================================
    # MÉTHODE ALTERNATIVE SI config_parameter NE FONCTIONNE PAS DANS VOTRE VERSION
    # ============================================================================
    # Si vous rencontrez des problèmes avec config_parameter, 
    # décommentez les méthodes ci-dessous et supprimez config_parameter des champs
    
    # @api.model
    # def get_values(self):
    #     """Récupération des valeurs depuis ir.config_parameter"""
    #     res = super(ResConfigSettings, self).get_values()
    #     ICPSudo = self.env['ir.config_parameter'].sudo()
    #     
    #     res.update(
    #         fne_api_key=ICPSudo.get_param('fne.api_key', ''),
    #         fne_mode=ICPSudo.get_param('fne.mode', 'test'),
    #         fne_auto_send=ICPSudo.get_param('fne.auto_send', 'False') == 'True',
    #         fne_test_url=ICPSudo.get_param('fne.test_url', 'http://54.247.95.108/ws'),
    #         fne_prod_url=ICPSudo.get_param('fne.prod_url', 'https://www.services.fne.dgi.gouv.ci/ws'),
    #         fne_point_de_vente=ICPSudo.get_param('fne.point_de_vente', ''),
    #         fne_footer=ICPSudo.get_param('fne.footer', '<p>Merci pour votre confiance</p>'),
    #     )
    #     return res
    #
    # @api.multi
    # def set_values(self):
    #     """Sauvegarde des valeurs dans ir.config_parameter"""
    #     super(ResConfigSettings, self).set_values()
    #     ICPSudo = self.env['ir.config_parameter'].sudo()
    #     
    #     ICPSudo.set_param('fne.api_key', self.fne_api_key or '')
    #     ICPSudo.set_param('fne.mode', self.fne_mode or 'test')
    #     ICPSudo.set_param('fne.auto_send', 'True' if self.fne_auto_send else 'False')
    #     ICPSudo.set_param('fne.test_url', self.fne_test_url or 'http://54.247.95.108/ws')
    #     ICPSudo.set_param('fne.prod_url', self.fne_prod_url or 'https://www.services.fne.dgi.gouv.ci/ws')
    #     ICPSudo.set_param('fne.point_de_vente', self.fne_point_de_vente or '')
    #     ICPSudo.set_param('fne.footer', self.fne_footer or '<p>Merci pour votre confiance</p>')
