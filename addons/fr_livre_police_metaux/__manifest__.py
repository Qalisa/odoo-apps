# -*- coding: utf-8 -*-

{
    'name': "Livre de police - metaux precieux",
    'version': '18.0.1.4.0',
    'summary': """
Description obligatoire des objets rachetes, article par article.
""",
    'description': """
Livre de police - metaux precieux
=================================

Le registre d'objets mobiliers exige de chaque objet acquis « la nature, la
provenance et la description » (art. R321-3 3° du code pénal). Le modèle
officiel du registre intitule la colonne « DESCRIPTION PRÉCISE de l'objet
(nature, dimensions, style, signature et éventuellement signes distinctifs) et
indication de sa provenance » (arrêté du 15 mai 2020, annexe I, colonne 3).

Cette description n'existe nulle part ailleurs : elle ne se déduit ni de
l'article, ni du montant, ni du poids. Elle se recueille au comptoir, devant
les objets, et une fois le vendeur reparti elle est perdue.

Ce module la rend **obligatoire**, sur les seuls articles qui la réclament.
Le choix se fait article par article, dans sa fiche : un rachat d'or au
gramme désigne des objets à décrire, une remise ou un arrondi n'en désigne
aucun.

Deux mentions, deux portées
---------------------------

L'article R321-3 3° tient la provenance et la description dans la même
phrase, et le modèle officiel du registre dans la même colonne. Elles ne
manquent pourtant pas de la même façon.

La **provenance** n'est jamais donnée par la désignation de l'article : elle
est déclarée par le vendeur, et rien d'autre ne la fournit. Elle est donc due
de **tout article inscrit au registre**, et suit la case « Soumis au livre de
police » de fr_numismatics_metals. Elle ne s'écrit nulle part aujourd'hui :
elle prend une colonne, remplie depuis une liste administrable — « Bijoux
personnels », « Héritage ou succession », « Achat antérieur »… Le comptoir
peut en créer une à la volée, mais pas une simple variante d'écriture d'une
valeur existante : « héritage » serait renvoyé vers « Héritage ou
succession ».

La **description** est déjà donnée par la désignation dès que l'article
désigne un type catalogué : « 20 FRANCS OR » dit la nature, le diamètre, le
millésime et l'effigie mieux qu'une phrase saisie au comptoir. Elle n'est
donc exigée que là où l'article ne dit rien de l'objet — or au gramme, lot de
pièces, argent en vrac — et c'est ce que déclare la case sur la fiche. Elle
se met là où le comptoir la met déjà (voir plus bas).

Une provenance déjà portée par une pièce comptabilisée ne se renomme plus.
Elle s'archive — les pièces passées gardent la leur (art. R321-6 et
R321-6-1).

Le sens de la quantité désigne le rachat
----------------------------------------

Un rachat se saisit ici comme une **ligne de quantité négative** sur un devis :
l'établissement ne vend pas, il achète. Selon le solde du document, cette
ligne devient soit une ligne d'avoir en quantité positive, soit une ligne de
facture en quantité négative. Les deux font entrer un objet, et les deux sont
donc contrôlées.

Une quantité négative sur un avoir, à l'inverse, ne fait entrer aucun objet :
c'est une correction, et elle n'est pas contrôlée.

Pas de champ dédié
------------------

La description se met là où le comptoir la met déjà : dans le champ
« Description » de la ligne, sous la désignation de l'article — « 18k Or
750 ‰(gr) ⏎ 1 BAGUE ». Ce champ est pré-rempli par Odoo avec le nom de
l'article, donc jamais vide : ce qui est contrôlé, c'est ce que le libellé
**ajoute** à cette désignation.

Une ligne renommée sans être décrite ne passe pas : « 20 FRANCS OR
(Non-Scellé) » nomme une variante, il ne désigne aucun objet particulier.

Les deux mentions sont exigées deux fois : à la confirmation du devis et à
la comptabilisation de la pièce. La ligne incomplète passe en rouge pendant
la saisie, pour que le manque se voie avant le refus.

La qualité du vendeur
---------------------

Le registre comporte aussi « les nom, prénoms, qualité et domicile de chaque
personne qui a vendu » (art. R321-3 1°), et « les nom, prénoms, qualité et
domicile du représentant » lorsque le vendeur est une personne morale (2°).
Le modèle officiel intitule la colonne « NOM, PRENOM ou dénomination sociale
du vendeur […], qualité ou profession, domicile ou siège social » (arrêté du
15 mai 2020, annexe I, colonne 2).

Cette qualité prend elle aussi une liste administrable — « Retraité(e) »,
« Salarié(e) », « Gérant(e) »… — et se saisit sur la fiche contact, avec
l'état civil et la pièce d'identité.

**Le champ n'est pas obligatoire d'un vendeur particulier.** La mention l'est
au registre, le champ ne l'est pas dans Odoo : rien ne bloque l'enregistrement
d'un contact ni la confirmation d'un devis. C'est un choix d'exploitation — le
comptoir doit pouvoir avancer sur une fiche incomplète — et l'obligation est
rappelee sous le champ, la ou la saisie se fait.

Le representant d'une societe
-----------------------------

Une societe ne se presente pas au comptoir : quelqu'un vient pour elle. Le
registre ne se contente donc pas de la raison sociale — il veut savoir **qui**
a remis les objets, et **a quel titre**.

CE QUE LE DROIT EXIGE — « lorsqu'il s'agit d'une personne morale, la
denomination et le siege de celle-ci ainsi que les nom, prenoms, qualite et
domicile du representant » (art. R321-3 2° du code penal).

Le client d'un tel rachat reste **la societe** : c'est elle qui vend, c'est
elle qui est payee, et c'est sa denomination que l'avoir porte. La personne se
designe juste en dessous, dans un champ **Representant** limite aux personnes
physiques rattachees a ce client.

Son **poste** s'affiche a cote, en **lecture seule**. C'est le champ standard
« Poste » (`function`) de la fiche contact, et non la liste administrable du
vendeur particulier : Odoo y range deja la fonction d'un contact dans sa
societe — gerant, mandataire, salarie —, et c'est exactement ce que le 2°
appelle la qualite du representant. La liste, elle, sert a une profession
(« Retraite(e) »), qui ne dit rien du lien avec une personne morale.

Il appartient a la personne, pas au devis : le corriger depuis un document le
changerait retroactivement pour tous ses rachats passes. Il se saisit sur la
fiche contact, et un encadre le rappelle quand il manque.

Enfin, **choisir un contact de societe comme client le remplace par sa
societe**, la personne rejoignant aussitot le champ que le registre lui
reserve. Le comptoir cherche la personne qu'il a devant lui ; l'avoir doit
porter le nom de celle qui a vendu.

Le representant suit le devis jusqu'a la piece comptable. Si le comptoir a
saisi le contact comme client plutot que la societe, la facturation bascule le
client sur la societe et laisse la personne dans son propre champ : l'avoir
nomme qui a vendu, le registre nomme qui s'est presente.

**Ici, la qualite bloque.** Ce n'est pas une inegalite de traitement : d'une
personne physique, la qualite complete une identite que la piece d'identite
etablit deja ; du representant, elle *est* le lien avec la societe, et rien
d'autre au document ne l'etablit. Le comptoir peut avancer sans savoir qu'un
vendeur est retraite ; il ne peut pas consigner qu'une societe a vendu sans
dire qui l'engageait.

Le refus tombe a la confirmation du devis et a la comptabilisation de la
piece, comme pour la provenance et la description. Un avertissement s'affiche
pendant la saisie, pour que le manque se voie avant le refus.

**Ce que ce module ne verifie pas** : le *domicile* du representant, que le
meme 2° exige. Il n'a pas de place distincte dans Odoo — un contact rattache a
une societe herite de l'adresse de celle-ci, qui est son siege et non le
domicile de la personne. Exiger un domicile sans champ pour le porter
n'apporterait rien.

Le registre lui-meme
--------------------

Recueillir les mentions ne suffit pas a tenir un registre. Tant qu'elles
vivent sur l'avoir et sur la fiche contact, le registre les **relit** : changer
le nom d'un vendeur ou corriger son adresse reecrit ses rachats passes, sans
trace et sans intention. Le code penal veut l'inverse — d'un registre tenu par
traitement automatise, il exige qu'il garantisse « l'integrite, l'intangibilite
et la securite des donnees enregistrees » (art. R321-6-1).

Ce module materialise donc le registre : **une ligne par lot entre**, ecrite a
la comptabilisation de l'avoir, qui ne relit plus rien ensuite. Les colonnes
suivent l'ordre du modele officiel (arrete du 15 mai 2020, annexe I), puis
viennent les mentions propres aux metaux precieux que ce modele ne porte pas —
poids, titre, date de sortie (CGI, ann. IV, art. 56 J quindecies).

Chaque ligne recoit un **numero d'ordre** continu par societe. « Chaque objet
expose a la vente ou detenu en stock est affecte d'un numero d'ordre. […] Le
numero d'ordre est porte sur le registre et figure de maniere apparente sur
chaque objet ou lot d'objets » (art. R321-4). La maille est donc le **lot**,
que le meme article admet expressement — et le comptoir doit porter ce numero
sur le sachet.

Le registre s'ouvre depuis son propre menu, reserve a un droit nomme : la
consultation devra un jour laisser trace de « l'identifiant du consultant, la
date, l'heure et l'objet de la consultation » (arrete du 15 mai 2020, art. 3,
2°), et une trace ne vaut que si l'acces est accorde a des personnes.

**Ce que ce module ne fait pas encore** : refuser l'ecriture et n'admettre la
rectification que par un nouvel enregistrement motive ; sceller une page par
jour avec son chiffre de controle ; editer le registre du jour ; tracer les
consultations. Les libelles de colonnes sont ici des libelles d'ecran ; les
intitules exacts du modele officiel viendront avec l'edition imprimee.
""",

    'category': 'Accounting/Localizations',
    'author': 'Qalisa',
    'license': "AGPL-3",
    'website': 'https://odoo-docs.qalisa.fr/',
    # `contacts_citizenship_id` porte deja l'etat civil et la piece
    # d'identite du vendeur : la qualite se saisit dans le meme groupe, au
    # meme moment, et non dans un bloc concurrent.
    # `fr_numismatics_metals` porte « Soumis au livre de police », qui dit
    # quels articles entrent au registre : la provenance suit cette case et
    # n'en reclame pas une seconde.
    'depends': ['sale', 'account', 'contacts_citizenship_id',
                'fr_numismatics_metals'],
    'data': [
        'security/livre_police_security.xml',
        'security/ir.model.access.csv',
        'data/livre_police_provenance_data.xml',
        'data/livre_police_qualite_data.xml',
        'views/livre_police_provenance_views.xml',
        'views/livre_police_qualite_views.xml',
        'views/res_partner_views.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/livre_police_ligne_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fr_livre_police_metaux/static/src/description_toujours_visible.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
