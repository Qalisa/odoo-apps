FROM odoo:18.0

USER root

# install requirements
ADD https://raw.githubusercontent.com/Qalisa/eqp_odoo_addons/refs/heads/18.0/eqp_backups/requirements.txt ./requirements.txt

RUN pip install --break-system-packages -r ./requirements.txt

USER odoo