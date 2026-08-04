# Note: Instead of ":latest" tag or equivalent, we source here from a specific timestamped version of Odoo (eg, <major>.<minor>-<YYYYMMDD>),
#       as Odoo's team regularly fix (and introduce !) bugs, using "latest" would be a tracking risk.
# 2025-04 builds (18.0-20250415) shipped a regression in account.move._compute_narration that wiped `narration`
# on sale documents when `account.use_invoice_terms` was off (erasing quotation terms copied by sale._prepare_invoice).
# Fixed since 18.0-20250606; pinned below to a verified-fixed, recent build.
FROM odoo:18.0-20260803

    # Switch to "root" to install modules...
    USER root

    # Fetch EQP Backup addon Python requirements list
    ADD https://raw.githubusercontent.com/Qalisa/eqp_odoo_addons/refs/heads/18.0/eqp_backups/requirements.txt ./requirements.txt

    # Install these requirements
    RUN pip install --break-system-packages -r ./requirements.txt

# Then, back to OG "odoo" user
USER odoo