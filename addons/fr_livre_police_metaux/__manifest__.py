# -*- coding: utf-8 -*-

{
    'name': "Livre de police - metaux precieux",
    'version': '18.0.1.32.0',
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

Ce que la désignation dit, et que le registre doit porter
--------------------------------------------------------

La description n'est exigée que là où l'article ne dit rien de l'objet, parce
que « 20 FRANCS OR » le décrit déjà mieux qu'une phrase saisie au comptoir.
L'argument ne tient que si cette désignation figure **au registre** — or elle
vivait sur l'avoir, et le registre, qui doit se lire seul, n'en gardait rien.
Une ligne de pièces s'y lisait « Or, 49 unités, 900 ‰ », ce qui ne désigne
aucun objet.

Chaque inscription porte donc la **désignation** de l'article, figée comme le
reste, couverte par le chiffre de contrôle et imprimée en tête de la colonne 3.
La description continue de ne recueillir que ce que la désignation n'a pas dit.

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

Le **mode de reglement** se saisit sur le devis de rachat, obligatoire des
qu'une ligne entre au registre : le modele officiel le range dans la meme
colonne que le prix, c'est-a-dire du cote de l'operation et non du reglement.
Le recueillir en amont evite au registre d'etre complete apres coup — et
permet de n'offrir que ce que la loi admet. « Lorsqu'un professionnel achete
des metaux a un particulier ou a un autre professionnel, le paiement est
effectue par cheque barre ou par virement a un compte ouvert au nom du
vendeur » (code monetaire et financier, art. L112-6) : la liste ne propose
donc pas les especes, quel que soit le montant.

Le registre s'ouvre depuis son propre menu, reserve a un droit nomme : la
consultation devra un jour laisser trace de « l'identifiant du consultant, la
date, l'heure et l'objet de la consultation » (arrete du 15 mai 2020, art. 3,
2°), et une trace ne vaut que si l'acces est accorde a des personnes.

Une inscription **ne se modifie pas et ne se supprime pas**. « Les
enregistrements informatiques crees pour les ouvrages d'occasion ne [peuvent]
etre modifies que par creation d'un nouvel enregistrement avec indication de
son motif » (CGI, ann. IV, art. 56 J sexdecies, 2° c). Un bouton
« Rectifier » ouvre un assistant preremli des valeurs d'origine : la
correction s'inscrit a la suite, sous son propre numero d'ordre, avec son
motif et un renvoi a l'inscription reprise. L'originale demeure, lisible telle
qu'elle a ete ecrite.

Par ricochet, une piece inscrite ne revient plus au brouillon et ses lignes ne
se suppriment plus : le registre a consigne ce qu'elle disait le jour du
rachat, et le laisser diverger sans trace serait pire que le refus.

Corriger une quantite
---------------------

Une quantite fausse se corrige comme le reste — par une rectification, jamais
par une sortie. Une sortie affirmerait que le metal est parti, sans acheteur
ni facture ; du metal qui n'a jamais ete detenu n'est parti nulle part, et
l'inscrire ainsi mettrait au registre une mention fausse pour en corriger une
autre.

Deux consequences en decoulent, et elles ne vont pas de soi.

**Le stock suit du meme geste.** Le registre et le stock disent la meme chose
de deux facons ; n'en corriger qu'une les fait diverger durablement.
L'ajustement d'inventaire est le chemin d'Odoo pour du metal absent — le meme
que la reprise emprunte en sens inverse.

**L'arithmetique du registre suit aussi.** Une rectification ne detient rien :
c'est l'inscription d'origine qui porte le numero d'ordre appose sur le lot
(art. R321-4), et c'est donc elle qui tient le stock, mais pour ce que dit sa
derniere rectification. Sans cette double regle, le meme metal existerait deux
fois et un lot corrige ne se solderait jamais. Une inscription ramenee a zero
n'est alors ni en stock ni sortie : son etat reste vide.

Quand c'est une reprise entiere qu'il faut reprendre, l'ecran **Rectifier les
quantites** le fait d'un seul geste : plusieurs inscriptions selectionnees
dans la liste du registre, un seul motif — elles procedent du meme constat —
et une nouvelle quantite par ligne. Le poids ne s'y saisit pas : il se deduit
a la proportion de l'inscrit, faute de quoi une inscription pourrait se
contredire elle-meme.

L'entree en stock suit la comptabilisation
------------------------------------------

Comptabiliser l'avoir inscrit le metal au registre, et **valide dans la
foulee la reception**. Sans cela le registre dit que le metal est entre
pendant que le stock dit qu'il n'est pas la — et c'est le stock qui a tort :
au comptoir, le metal a change de mains au moment meme ou le rachat s'est
arrete. Un lot absent du stock ne se revend pas, ne se transfere pas, et
n'apparait pas au poids detenu.

L'ordre inverse reste impossible : le lot prend le numero d'ordre de
l'inscription, et l'inscription nait a la comptabilisation. Receptionner
avant de comptabiliser est refuse, et le reste.

Deux cas laissent le bon en l'etat. Une **quantite partielle** ouvre un
assistant de reliquat : ce que le comptoir a reellement pris en main ne se
devine pas. Une **entree non inscrite sur le meme bon** — facturation
partielle — ferait entrer un metal dont l'achat n'est pas arrete. Ni l'un ni
l'autre n'empeche la comptabilisation : l'avoir est poste, le registre
inscrit, et la raison s'ecrit dans le fil de discussion de la piece. Le bon
reste « pret », comme avant.

La page du jour et son chiffre de controle
-----------------------------------------

Le texte decrit une chaine d'empreintes sans la nommer ainsi : « le repertoire
contenant ces informations [doit comprendre] un systeme d'identification des
pages par chiffre de controle, contenant un algorithme ou un systeme fonde
notamment sur la date de l'operation, reporte en fin et en tete des pages
imprimees quotidiennement » (CGI, ann. IV, art. 56 J sexdecies, 2° c).
Reporter le controle en pied d'une page et en tete de la suivante, c'est
chainer : retirer une ligne d'une page ancienne casse tous les controles
suivants.

Une page s'ouvre au premier rachat du jour, se scelle le soir — une tache
planifiee ferme celles des jours passes — et ne se rouvre plus. Un rachat
arrive apres la fermeture ouvre la page suivante, a la meme date.

**L'edition quotidienne** reprend les colonnes du modele officiel, en paysage,
avec le chiffre de controle en tete et en pied : c'est sur l'imprime que la
chaine se verifie.

**Le controle d'integrite** rejoue la chaine et imprime son constat. Il
verifie trois choses qui se cassent differemment : le contenu de chaque page,
son chainage a la precedente, et la continuite des numeros — une suppression
faite hors d'Odoo ne casse aucune empreinte, mais laisse un trou.

Le metal qui change d'etablissement
-----------------------------------

« Lorsque les personnes mentionnees a l'article R. 321-1 possedent plusieurs
etablissements ouverts au public, un registre est tenu pour chaque
etablissement » (c. pen., art. R321-6). Trois comptoirs, trois registres,
trois suites de numeros d'ordre.

Restait le mouvement entre eux. Un sachet part de Metz pour etre vendu depuis
Nancy : cote stock, deux bons ; cote registre, rien. La sortie de Metz
s'inscrivait comme une sortie ordinaire, muette sur sa destination, et Nancy
n'inscrivait aucune entree — le metal quittait un registre sans entrer dans
l'autre, et sa revente ulterieure ne s'inscrivait nulle part, faute d'entree a
laquelle la rattacher.

Un document **Transfert entre etablissements** tient desormais les deux bouts.
Il nomme l'agence d'arrivee, porte le **motif** du deplacement, et c'est lui
qui cree les deux bons de stock, les enchaine et les valide. Le passage se
fait par l'emplacement de transit inter-societes d'Odoo, seul chemin possible
— un emplacement de stock appartient a un etablissement, et rien ne relie
directement deux entrepots. Un bon qui emprunterait ce transit sans document
est refuse.

Le transfert ne se fait que par quelqu'un qui a acces aux deux etablissements :
sortir du registre de l'un pour entrer dans celui de l'autre, c'est en
repondre aux deux.

**Le sachet n'est pas reetiquete.** Il porte le numero d'ordre du comptoir de
rachat et le portera jusqu'a la fonte. Odoo, lui, exige que le nom d'un lot
soit unique par article dans une societe, et chaque agence repart de 000001 :
le lot transfere est donc qualifie — « METZ/000123 » — et cesse d'appartenir a
une societe. Le numero du comptoir est intact, une recherche sur « 000123 » le
retrouve, et c'est le **meme** enregistrement de lot qui traverse : rien n'est
recree a l'arrivee, la quantite sort d'un cote exactement comme elle entre de
l'autre.

L'entree a Nancy prend son propre numero d'ordre, dans la suite de Nancy. Elle
recopie ce qui decrit la marchandise et **rien de la personne** qui a vendu a
Metz : son nom, son domicile et sa piece d'identite restent au registre ou ils
ont ete recueillis. Ce qui tient leur place, c'est l'**origine** —
l'etablissement, le numero d'ordre et la date du rachat, figes a l'inscription
et redits en toutes lettres a la colonne « provenance ». La chaine remonte
donc au comptoir qui a achete, transfert apres transfert, et la vente finale a
un fondeur s'inscrit a Nancy en designant toujours Metz.

Le prix de l'entree est nul, et ce n'est pas un oubli : un transfert entre
etablissements d'un meme titulaire ne paie personne. Le prix d'achat vit a
l'inscription d'origine, que ces colonnes designent nommement.

Sa **date d'entree est celle de l'arrivee**, non celle du rachat a Metz : le
registre de Nancy dit quand ce metal est entre chez Nancy. Le raisonnement
inverse — un seul titulaire, donc une seule date — se contredirait lui-meme,
puisque si les trois etablissements n'en faisaient qu'un, ce transfert
n'aurait rien a inscrire nulle part. La date du rachat ne se perd pas : elle
demeure a la colonne « date du rachat » et dans la provenance.

Entre les deux validations, le metal est **en transit** : sorti d'un registre,
pas encore inscrit a l'autre. Ce n'est pas un trou, c'est l'etat reel de la
marchandise, et les deux inscriptions le disent.

Le stock d'ouverture
--------------------

Les comptoirs ont tenu leur registre a la main jusqu'ici. Le jour ou le
registre informatise prend la suite, le coffre n'est pas vide : il contient du
metal rachete sous l'ancien registre, dont les acquisitions sont consignees
la-bas, page apres page. Si ce metal n'entre pas, il n'existe pas — et sa
revente ne s'inscrira nulle part, faute d'entree a laquelle la rattacher.

Un document **Reprise de stock d'ouverture**, un par etablissement, le fait
entrer. Il inscrit au registre, cree le lot au numero d'ordre inscrit et pose
la quantite en stock, d'un seul geste : un ajustement d'inventaire fait a part
remplirait le stock sans rien inscrire, et le registre ne saurait plus rien de
ce metal.

**Ce n'est pas un achat.** Personne n'a vendu quoi que ce soit a
l'etablissement ce jour-la. Les colonnes du vendeur restent donc vides et le
prix est nul ; les remplir d'un vendeur fictif ferait dire au registre qu'une
operation a eu lieu, et masquerait ce qui doit se voir — que ces objets
viennent d'ailleurs. Ce que la colonne « provenance » porte, c'est le renvoi au
registre ou l'acquisition est consignee.

Le renvoi vaut dans les deux sens. Le registre manuscrit doit porter a sa
cloture la mention inverse — le stock reporte, la date, les numeros d'ordre
sous lesquels il l'a ete. Elle s'ecrit a la main, et ce module ne peut pas la
produire ; l'ecran la rappelle.

La maille est le **lot**, que l'art. R321-4 admet expressement : un stock
d'ouverture n'est pas detaille objet par objet, il est pese par nature et par
titre. Chaque ligne recoit un numero d'ordre, et ce numero doit figurer sur le
contenant des la reprise faite. Le lot se vide ensuite par ventes successives,
et le registre le suit — l'entree reste « sortie en partie » tant qu'il reste
du metal.

Le journal des consultations
----------------------------

« Les consultations du traitement automatise font l'objet d'un enregistrement
comprenant l'identifiant du consultant, la date, l'heure et l'objet de la
consultation. Ces informations sont conservees pendant un delai d'un an »
(arrete du 15 mai 2020, art. 3, 2°).

C'est la seule obligation du registre qui porte sur les **lectures**. L'objet
ne se devine pas : un logiciel sait qu'on ouvre le registre, il ne sait pas
pourquoi. Il se declare donc avant d'entrer, dans une liste courte. C'est une
friction assumee — sans elle, la mention exigee n'existerait pas.

L'edition du jour et le controle d'integrite se tracent seuls. Une URL saisie
a la main atteint la liste sans declaration : c'est pourquoi l'acces est
reserve a un groupe nomme plutot qu'ouvert au comptoir. Les libelles de colonnes sont ici des libelles d'ecran ; les
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
    # `sale_stock` fait naitre la reception d'un rachat et porte le lien du
    # mouvement vers la ligne de devis ; `stock` porte le lot qui prend le
    # numero d'ordre (c. penal, art. R321-4).
    'depends': ['sale', 'account', 'stock', 'sale_stock',
                'contacts_citizenship_id', 'fr_numismatics_metals'],
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
        'views/stock_picking_views.xml',
        'views/stock_lot_views.xml',
        'views/livre_police_ligne_views.xml',
        'views/livre_police_rectification_views.xml',
        'views/livre_police_rectification_quantite_views.xml',
        'views/livre_police_page_views.xml',
        'views/livre_police_transfert_views.xml',
        'views/livre_police_reprise_views.xml',
        'views/livre_police_controle_views.xml',
        'views/livre_police_consultation_views.xml',
        'report/livre_police_page_report.xml',
        'report/livre_police_controle_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fr_livre_police_metaux/static/src/description_toujours_visible.js',
            'fr_livre_police_metaux/static/src/livre_police_liste.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
