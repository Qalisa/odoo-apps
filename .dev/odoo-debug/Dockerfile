# Note: prefer using "ghcr.io/qalisa/odoo:18-0" or its timestamped equivalent here, since it has appropriate required modules dependencies installed.
#       Using vanilla "odoo:<major>" is also possible.
FROM ghcr.io/qalisa/odoo:18-0-20250717

# install "DebugPy" to allow direct debugging of Odoo's python sourcecode while Odoo's running 
RUN pip3 install --break-system-packages -U debugpy
