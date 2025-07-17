# Qalisa's Odoo modules / addons

Odoo addons and modules specifically developped for Qalisa's customers.

> [!NOTE]
> To mimic `odoo`'s official repo structure, there is no `main` / `master` repo; only major version tracked branches (`18-0`, `<major>-<minor>`...)

## About imported modules
- `prt_report_attachment_preview` and `psql_query_execute` were sourced by others developpers, but kept here for coherence. All rights apply with their sourcecode's respective licenses.

## Debugging & Developping 

### About Odoo configuration behavior
Using `--without-demo` option arg to Odoo's `/usr/bin/odoo` in `docker-compose.yml` will prevent few features to work, such as :
- Auto-addition of custom gold taxes (`fr_numismatics_taxes`) 
- Auto-apply of French CoA (`fr_startup_enforced`)

### To connect to Odoo
Use `admin:admin` as default credentials to Odoo.