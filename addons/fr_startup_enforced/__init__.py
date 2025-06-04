import logging

# Hooks pour l'initialisation
def post_configure_french_lang(env):    
    """Enforce French."""
    with env.cr.savepoint():
        _post_configure_french_lang(env)
    with env.cr.savepoint():
        _switch_fiscal_localization_to_france(env)

lang_to_activate = 'fr_FR'
lang_to_activate_base_code = 'fr'
lang_to_disable = 'en_US'

#
_logger = logging.getLogger(__name__)
def _post_configure_french_lang(env):
    try:
        #
        # Ensure French language (fr_FR) is activated if not already present
        #

        lang_obj = env['res.lang']
        to_activate = lang_obj.search([('code', '=', lang_to_activate)])
        if not to_activate:
            _logger.info(f"Activating French language ({lang_to_activate}).")
            to_activate._activate_lang(lang_to_activate)
        else:
            _logger.info(f"French language ({lang_to_activate}) is already activated.")

        # Get the default company
        company = env.ref("base.main_company")
        # Update the company's partner language if needed
        partner = company.partner_id
        if partner.lang != lang_to_activate:
            _logger.info(f"Updating company partner language to French ({lang_to_activate}).")
            partner.write({'lang': lang_to_activate})
        else:
            _logger.info(f"Company partner language is already set to French ({lang_to_activate}).")

        # Set the company's country to France if not already set
        french_country = env.ref(f'base.{lang_to_activate_base_code}')
        if company.country_id != french_country:
            _logger.info("Setting company country to France.")
            company.write({'country_id': french_country.id})
        else:
            _logger.info("Company country is already set to France.")

        # Update all user records to use French (fr_FR) as default language
        users = env['res.users'].with_context(active_test=False).search([])
        for user in users:
            if user.lang != lang_to_activate:
                _logger.info(f"Updating language for user '%s' to French ({lang_to_activate}).", user.name)
                user.write({'lang': lang_to_activate})
        _logger.info(f"All applicable user languages updated to French ({lang_to_activate}).")

        #
        # Disable old default language
        #
        
        to_disable = lang_obj.search([('code', '=', lang_to_disable)])
        if to_disable:
            _logger.info(f"Disabling default language ({lang_to_disable}).")
            to_disable.action_archive()
        else:
            _logger.info(f"Default language ({lang_to_disable}) is already activated.")

        #
        # Reload French language to ensure updated translations are applied (Required)
        #

        _logger.info(f"Reloading French language ({lang_to_activate}) translations.")

        # The _activate_lang method is used again to refresh the language data.
        mods = env['ir.module.module'].search([('state', '=', 'installed')])
        mods._update_translations(lang_to_activate)


    except Exception as e:
        _logger.exception("An error occurred while configuring French language: %s", e)
        raise


##
## Note: changes done here will be automatically reverted if setting up the database using "without_demo"
##
def _switch_fiscal_localization_to_france(env):
    chart_template = env['account.chart.template']
    company = env.ref("base.main_company")
    chart_template.try_loading(lang_to_activate_base_code, company, install_demo=False, force_create=True)
    print(f"Chart of accounts '{lang_to_activate_base_code}' loaded successfully for matching companies.", flush=True)
