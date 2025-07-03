# track specific version (odoo do fix bugs regularly !)
FROM odoo:18.0-20250606

# switch to root to install modules...
USER root

# fetch Backup module Python requirements
ADD https://raw.githubusercontent.com/Qalisa/eqp_odoo_addons/refs/heads/18.0/eqp_backups/requirements.txt ./requirements.txt

# Install requirements
RUN pip install --break-system-packages -r ./requirements.txt

# back to Odoo
USER odoo