import logging
import requests
from odoo import models, api, fields, _
from odoo.exceptions import UserError
import time

_logger = logging.getLogger(__name__)

ALLOWED_TAXES = {
    'tva': 'TVA',     
    'tvab': 'TVAB',    
    'tvac': 'TVAC',    
    'tvad': 'TVAD',   
}


def _clean_str(val):
    """Nettoie les chaînes pour éviter les caractères invalides."""
    if isinstance(val, str):
        return val.encode("utf-8", errors="ignore").decode("utf-8")
    return val

def _truncate(s, n):
    s = _clean_str(s) or ""
    return s[:n]

class AccountMoveLine(models.Model):
    _inherit = 'account.invoice.line'
    fne_item_id = fields.Char(string="Item ID FNE", copy=False)

class AccountMove(models.Model):
    _inherit = 'account.invoice' 


    fne_sent = fields.Boolean(string="Certifier la facture", default=False,copy=False)
    fne_reference_dgi = fields.Char(string="Référence DGI", readonly=True, copy=False)
    fne_verification_url = fields.Char(string="Lien vérification DGI", readonly=True, copy=False)
    invoice_id_from_fne = fields.Char(string="ID FNE", readonly=True, copy=False)
    fne_warning = fields.Boolean(string="Avertissement FNE", readonly=True, copy=False)
    fne_balance_sticker = fields.Integer(string="Solde sticker FNE", readonly=True, copy=False)
    mode_paiement = fields.Selection(
        selection=[
            ('mobile-money', 'Mobile Money'),
            ('cash', 'Espèces'),
            ('transfer', 'Virement Bancaire'),
            ('check', 'Chèque'),
            ('deferred', 'A terme'),
            ('card', 'Carte Bancaire'),],
        string="Mode de paiement",
        default='mobile-money',
        help="Sélectionnez le mode de paiement pour la facture.",
    )
    
    # Reste de vos fonctions utilitaires inchangées
    def _detect_template(self):
        partner = self.partner_id
        if getattr(partner, 'x_is_government', False):
            return "B2G"
        if partner.country_id and partner.country_id.code and partner.country_id.code != (self.company_id.country_id.code or "CI"):
            return "B2F"
        if partner.vat:
            return "B2B"
        return "B2C"

    def _compute_custom_taxes(self):
        """Agrège les taxes non TVA (autres prélèvements) au niveau racine."""
        customs = {}
        for line in self.invoice_line_ids.filtered(lambda l: not l.display_type):
            for tax in line.tax_ids:
                tg = (tax.tax_group_id and tax.tax_group_id.name or "").upper()
                if "TVA" in tg:
                    continue
                key = (tax.name, tax.amount)
                customs[key] = {"name": _truncate(tax.name, 50), "amount": float(tax.amount)}
        return list(customs.values()) 
    
    def _compute_currency_block(self):
        """foreignCurrency/rate si devise ≠ devise société."""
        if self.currency_id and self.currency_id != self.company_currency_id:
            rate = self.company_currency_id._get_conversion_rate(
                self.company_currency_id, self.currency_id, self.company_id,
                self.invoice_date or fields.Date.context_today(self)
            ) or 0.0
            return self.currency_id.name or "", float(rate)
        return "", 0.0
    
    # -------------------------
    # Préparation des payloads
    # -------------------------
    def _prepare_payload_sale(self):
        return self._prepare_base_payload("sale")

    def _prepare_payload_purchase_agri(self):
        return self._prepare_base_payload("purchase")

    def _build_items(self):
        regime_fiscal = self.partner_id.regimeFiscal # Assurez-vous que regimeFiscal existe sur le partenaire
        taxe= ALLOWED_TAXES.get(regime_fiscal)
        _logger.info(f"[FNE] Régime fiscal pour {self.partner_id.name}: {regime_fiscal} -> Taxe: {taxe}")
        items = []
        for line in self.invoice_line_ids.filtered(lambda l: not l.display_type): # Ne traiter que les lignes non-display_type
            if self.move_type == 'out_invoice':
                taxes_list = [taxe] if taxe else [] # Ajouter la taxe uniquement si elle est définie
                items.append({
                    "reference": _clean_str(line.product_id.default_code or ""),
                    "description": _truncate(line.name or line.product_id.display_name or "Ligne", 255),
                    "quantity": float(line.quantity or 0),
                    "amount": float(line.price_unit or 0),
                    "discount": float(line.discount or 0),
                    "measurementUnit": _clean_str(line.product_uom_id and line.product_uom_id.name or "pcs"),
                    "taxes": taxes_list,
                })
            elif self.move_type == 'in_invoice':
                items.append({
                    "reference": _clean_str(line.product_id.default_code or ""),
                    "description": _truncate(line.name or line.product_id.display_name or "Ligne", 255),
                    "quantity": float(line.quantity or 0),
                    "amount": float(line.price_unit or 0),
                    "discount": float(line.discount or 0),
                    "measurementUnit": _clean_str(line.product_uom_id and line.product_uom_id.name or "pcs"),
                })
        return items

    def _prepare_base_payload(self, invoice_type):
        invoice = self  
        
        # --- MEILLEURE PRATIQUE : Lecture directe du paramètre ---
        config = self.env['ir.config_parameter'].sudo()
        point_de_vente = config.get_param('fne.point_de_vente', 'Default Point of Sale')
        footer= config.get_param('fne.footer', '<p>Merci pour votre confiance</p>')
        # --------------------------------------------------------

        # --- AJOUT DU LOGGING POUR LE DEBUGAGE (Point de Vente / Footer) ---
        _logger.info(f"[FNE DEBUG _prepare_base_payload]: Point de Vente = {point_de_vente}")
        # -------------------------------------------------------------------

        if not point_de_vente:
            raise UserError(_("Le point de vente n'est pas configuré pour le FNE."))

        items = self._build_items()
        _logger.info(f"[FNE] Items préparés pour {invoice.name}: {items}")
        if not items:
            raise UserError(_("Aucune ligne de facture valide pour l'envoi à la DGI."))

        
        template = "B2B" if invoice.partner_id.vat else "B2C"
        mode_paiement = invoice.mode_paiement or 'mobile-money'

        return {
            "invoiceType": invoice_type,
            "paymentMethod":_clean_str(mode_paiement or "mobile-money"),
            "template": template,
            "isRne": False,
            "rne": "",
            "clientNcc": _clean_str(invoice.partner_id.vat or ""),
            "clientCompanyName": _clean_str(invoice.partner_id.name or ""),
            "clientPhone": _clean_str(invoice.partner_id.phone or ""),
            "clientEmail": _clean_str(invoice.partner_id.email or ""),
            "clientSellerName": _clean_str(invoice.user_id.name or ""),
            "pointOfSale": point_de_vente,
            "establishment": "NEURONES TECHNOLOGIE",
            # "establishment": _clean_str(invoice.company_id.name or ""),
            "commercialMessage":_truncate("Condition de paiement : " + (getattr(self.invoice_payment_term_id, "name", "") or ""),140),
            "footer": _clean_str(footer),
            "foreignCurrency": "",
            "foreignCurrencyRate": 0,
            "items": items,
            "customTaxes": [custom_taxes for custom_taxes in self._compute_custom_taxes()],
            "discount": 0,
        }


    # -------------------------
    # Envoi à la DGI
    # -------------------------
    
    def _apply_sign_success(self, data):
        self.fne_sent = True
        self.fne_reference_dgi = data.get("reference") or False
        self.fne_verification_url = data.get("token") or False
        self.fne_warning = bool(data.get("warning"))
        self.fne_balance_sticker = int(data.get("balance_sticker") or 0)
        _logger.info(f'[FNE] Facture {self.name} certifiée avec succès. Réponse DGI : {data}')

        self.invoice_id_from_fne = data.get("id") or data.get("invoice", {}).get("id") or self.invoice_id_from_fne
        items = data.get("invoice", {}).get("items", [])
        
        # Mapping des ID d'items FNE aux lignes de facture Odoo par référence/produit (plus fiable)
        for fne_item in items:
            fne_item_id = fne_item.get("id")
            # Une implémentation plus robuste serait de mapper par la référence que vous avez envoyée
            # Mais en l'absence de référence unique, on se base sur l'ordre/description (moins fiable)
            # Puisque l'API retourne les items dans l'ordre, nous utilisons l'index comme fallback
            
            # Recherche de la ligne Odoo non-affichable
            try:
                line_index = items.index(fne_item)
                # Utiliser l'index pour trouver la ligne Odoo correspondante
                line = self.invoice_line_ids.filtered(lambda l: not l.display_type)[line_index]
                if fne_item_id:
                    line.fne_item_id = fne_item_id
                else:
                    _logger.warning(f"[FNE] Aucun ID trouvé pour l’item {line_index} de la facture {self.name}")
            except IndexError:
                 _logger.warning(f"[FNE] Pas assez d’items retournés par la DGI pour mapper toutes les lignes de la facture {self.name}")
            except Exception as e:
                _logger.warning(f"[FNE] Erreur de mapping d'item FNE pour {self.name}: {e}")
                
    
    
    def _request_fne(self, method, url, headers, json_body=None, retries=2, timeout=30):
        last_err = None
        for attempt in range(retries + 1):
            try:
                resp = requests.request(method, url, headers=headers, json=json_body, timeout=timeout)
                try:
                    data = resp.json()
                except ValueError:
                    data = {"raw_response": _truncate(resp.text, 200) } # Troncature pour les logs

                if resp.status_code in (200, 201):
                    return data
                if 500 <= resp.status_code < 600 and attempt < retries:
                    _logger.warning(f"[FNE] Tentative {attempt+1}/{retries+1} : Erreur 5xx. Nouvelle tentative dans {2 ** attempt}s.")
                    time.sleep(2 ** attempt)
                    continue
                raise UserError(_("FNE %s %s : %s - %s") % (method, url, resp.status_code, data))
            except requests.RequestException as e:
                last_err = e
                if attempt < retries:
                    _logger.warning(f"[FNE] Tentative {attempt+1}/{retries+1} : Erreur réseau. Nouvelle tentative dans {2 ** attempt}s.")
                    time.sleep(2 ** attempt)
                    continue
                raise UserError(_("Erreur réseau FNE %s %s : %s") % (method, url, str(e)))
        raise last_err # Devrait être atteint après la boucle
                
    def action_send_to_fne(self):
        self.ensure_one()
        
        # --- MEILLEURE PRATIQUE : Lecture directe du paramètre ---
        config = self.env['ir.config_parameter'].sudo()
        api_key = config.get_param('fne.api_key')
        mode = (config.get_param('fne.mode', 'test') or 'test').lower()
        base_url = (config.get_param('fne.test_url') if mode == 'test' else config.get_param('fne.prod_url')) or ""
        # --------------------------------------------------------

        # --- AJOUT DU LOGGING POUR LE DEBUGAGE (API Key / Mode / URL) ---
        _logger.info("FNE CONFIG DEBUG START ----------------------------------------------------------------")
        _logger.info(f"FNE PARAMETER: mode = {mode}")
        _logger.info(f"FNE PARAMETER: api_key (masked) = {api_key and '*******' or 'EMPTY'}")
        _logger.info(f"FNE PARAMETER: fne.test_url = {config.get_param('fne.test_url')}")
        _logger.info(f"FNE PARAMETER: fne.prod_url = {config.get_param('fne.prod_url')}")
        _logger.info(f"FNE PARAMETER: base_url FINAL = {base_url}")
        _logger.info("FNE CONFIG DEBUG END ------------------------------------------------------------------")

        if not base_url:
            raise UserError(_("L'URL de l'API FNE n'est pas configurée."))
        if not api_key:
            raise UserError(_("La clé API FNE n'est pas configurée."))

        headers = {
            'Authorization': f"Bearer {api_key}",
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        endpoint_sign = base_url.rstrip('/') + "/external/invoices/sign"

        for inv in self:
            try:
                if inv.fne_sent:
                    _logger.info("[FNE] %s déjà certifiée.", inv.name)
                    continue

                if inv.move_type in ('out_invoice',):
                    payload = inv._prepare_payload_sale()
                    _logger.info("[FNE] SIGN %s payload=%s", inv.name, payload)
                    data = inv._request_fne("POST", endpoint_sign, headers, json_body=payload)
                    inv._apply_sign_success(data)

                elif inv.move_type in ('in_invoice',):
                    payload = inv._prepare_payload_purchase_agri()
                    _logger.info("[FNE] SIGN (purchase) %s payload=%s", inv.name, payload)
                    data = inv._request_fne("POST", endpoint_sign, headers, json_body=payload)
                    inv._apply_sign_success(data)

                elif inv.move_type in ('out_refund',):
                    inv._post_refund_to_fne(headers, base_url)

                elif inv.move_type in ('in_refund', 'in_receipt'):
                    _logger.info("[FNE] %s ignorée (type %s). Ce type de document n'est pas géré par l'envoi FNE.", inv.name, inv.move_type)
                    continue

                else:
                    _logger.info("[FNE] %s ignorée (type %s).", inv.name, inv.move_type)

            except UserError as ue:
                _logger.error("[FNE] Erreur Utilisateur %s : %s", inv.name, ue.name)
                raise
            except Exception as e:
                _logger.exception("[FNE] Exception non gérée lors de l'envoi de %s", inv.name)
                raise

    # -------------------------
    # Hook post-validation
    # -------------------------
    def _post_refund_to_fne(self, headers, base_url):
        self.ensure_one()
        refund_move = self
        origin = refund_move.reversed_entry_id 
        if not origin:
            raise UserError(_("Facture d'origine introuvable pour l’avoir %s") % refund_move.name)

        if not origin.invoice_id_from_fne:
            raise UserError(_("ID FNE de la facture d'origine manquant pour l’avoir %s") % refund_move.name)
        
        _logger.info("[FNE] REFUND %s -> Recherche lignes originales de %s", refund_move.name, origin.name)

        items = []
        
        # CORRECTION LOGIQUE DE RECHERCHE D'ORIGINE : on se base sur les produits
        origin_lines_map = {
            line.product_id.id: line
            for line in origin.invoice_line_ids.filtered(lambda l: not l.display_type and l.fne_item_id)
        }
        
        for line in refund_move.invoice_line_ids.filtered(lambda l: not l.display_type):
            qty = abs(line.quantity or 0)
            if qty <= 0:
                continue
                
            orig_line = origin_lines_map.get(line.product_id.id)
            
            if not orig_line:
                raise UserError(_("Ligne d'origine introuvable ou ID FNE manquant pour le produit '%s' (avoir %s). Assurez-vous que le produit est le même que dans la facture originale.") % (line.product_id.display_name or line.name or '', refund_move.name))

            fne_item_id = orig_line.fne_item_id
            
            if not fne_item_id:
                # Cette condition est déjà filtrée par origin_lines_map, mais est laissée comme garde-fou
                raise UserError(_("ID FNE de l'item d'origine manquant pour la ligne '%s' (avoir %s)") % (line.name or '', refund_move.name))

            items.append({"id": fne_item_id, "quantity": float(qty)})

        if not items:
            raise UserError(_("Aucune ligne valable pour le refund FNE (quantités nulles ou produits non mappés)."))

        endpoint = base_url.rstrip('/') + f"/external/invoices/{origin.invoice_id_from_fne}/refund"
        body = {"items": items}
        _logger.info("[FNE] REFUND %s ENDPOINT: %s body=%s", refund_move.name, endpoint, body)

        data = self._request_fne("POST", endpoint, headers, json_body=body)
        refund_move.fne_sent = True
        refund_move.fne_reference_dgi = data.get("reference") or False
        refund_move.fne_verification_url = data.get("token") or False
        refund_move.fne_warning = bool(data.get("warning"))
        refund_move.fne_balance_sticker = int(data.get("balance_sticker") or 0)
        _logger.info(f'[FNE] Avoir {refund_move.name} certifié avec succès. Réponse DGI : {data}')
        return data
    
    # -------------------------
    # Hook post-validation
    # -------------------------
    @api.model
    def action_post(self):
        res = super().action_post()
        
        # --- MEILLEURE PRATIQUE : Lecture directe du paramètre ---
        config = self.env['ir.config_parameter'].sudo()
        # Lire la valeur stockée (qui est une chaîne 'True'/'False') et la comparer
        if config.get_param('fne.auto_send', 'False') == 'True':
            self.action_send_to_fne()
        # --------------------------------------------------------
        
        return res
    
    def action_open_fne_link(self):
        self.ensure_one()
        if self.fne_verification_url:
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': self.fne_verification_url,
            }
        else:
            raise UserError(_("Aucun lien de vérification DGI n'est disponible pour cette facture."))