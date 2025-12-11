# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    """Configuration FNE intégrée dans les paramètres généraux"""
    _inherit = 'res.config.settings'
    # ❌ NE PAS mettre _name = 'fne.config.settings'

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
