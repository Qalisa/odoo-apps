# Note: Instead of ":latest" tag or equivalent, we source here from a specific timestamped version of Odoo (eg, <major>.<minor>-<YYYYMMDD>),
#       as Odoo's team regularly fix (and introduce !) bugs, using "latest" would be a tracking risk.
FROM odoo:18.0-20250606

    # Switch to "root" to install modules...
    USER root

    # Fetch EQP Backup addon Python requirements list
    ADD https://raw.githubusercontent.com/Qalisa/eqp_odoo_addons/refs/heads/18.0/eqp_backups/requirements.txt ./requirements.txt

    # Install these requirements
    RUN pip install --break-system-packages -r ./requirements.txt

# Then, back to OG "odoo" user
USER odoo