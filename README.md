# Qalisa's Odoo modules / addons

Odoo addons and modules specifically developped for Qalisa's customers.

## About imported modules
- `prt_report_attachment_preview` was sourced by another maintainer, but kept here for coherence. All rights reserved.

## Debugging & Developping 

### About Odoo configuration behavior
Using `--without-demo` option arg to Odoo's `/usr/bin/odoo` in `docker-compose.yml` will prevent few features to work, such as :
- Auto-addition of custom gold taxes (`fr_numismatics_taxes`) 
- Auto-apply of French CoA (`fr_startup_enforced`)

### To connect to Odoo
Use `admin:admin` as default credentials to Odoo.