# Ce module porte des données — un groupe et la liste des menus qu'il commande
# — et un correctif qui ne peut pas s'écrire en données : deux règles d'Odoo
# sont `noupdate`, et se réattribuent donc par le code.

from .hooks import post_init_hook
