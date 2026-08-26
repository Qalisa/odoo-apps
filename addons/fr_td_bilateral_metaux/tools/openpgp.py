# -*- coding: utf-8 -*-
"""Chiffrement OpenPGP du fichier de dépôt, par appel à ``gpg``.

Le cahier des charges TD/bilatéral impose de chiffrer le fichier **après**
l'avoir compressé, avec une clé publique de la DGFiP, avant dépôt sur le
portail Télé-TD (§ 2.4.3.4). Deux clés distinctes existent — « clé de
chiffrement pour les fichiers de test » et « clé de chiffrement pour les
fichiers de production » — et « l'utilisation d'un type de clé qui ne
correspond pas à la nature du fichier conduit à son rejet lors de son
traitement par la DGFiP ».

Rien dans le contenu du fichier ne dit s'il est de test ou de production :
c'est le portail sur lequel on le dépose qui le décide. Le choix de la clé ne
se déduit donc de rien et doit être fait à la génération.

**Pourquoi le binaire plutôt qu'une bibliothèque.** ``gpg`` 2.4 est déjà dans
l'image Odoo ; ``python-gnupg`` n'y est pas, et n'est lui-même qu'une
enveloppe autour du même binaire. L'ajouter imposerait de reconstruire l'image
sans rien gagner.

**Trousseau jetable.** Chaque appel travaille dans un ``GNUPGHOME``
temporaire : rien n'est importé dans le trousseau du système, et deux
déclarations chiffrées en même temps ne se voient pas. Les clés manipulées
ici sont publiques — celles de la DGFiP, publiées sur impots.gouv.fr — il n'y
a aucun secret à protéger, seulement une identité à vérifier.

Aucun ``import odoo`` ici : la règle se teste en isolation.
"""

import io
import os
import shutil
import subprocess
import tempfile
import zipfile

GPG = '/usr/bin/gpg'

# Au-delà, ce n'est pas une clé : c'est un fichier envoyé par erreur.
TAILLE_MAX_CLE = 1024 * 1024


class ErreurChiffrement(Exception):
    """Le chiffrement n'a pas pu se faire, et le message dit pourquoi."""


def _gpg(args, homedir, entree=None):
    """Lance ``gpg`` dans un trousseau donné et rend (code, sortie, erreur)."""
    if not os.path.exists(GPG):
        raise ErreurChiffrement(
            "gpg est introuvable sur le serveur (%s). Le chiffrement du "
            "fichier DGFiP en dépend." % GPG)
    env = dict(os.environ, GNUPGHOME=homedir, LC_ALL='C')
    proc = subprocess.run(
        [GPG, '--batch', '--no-tty', '--quiet', '--yes'] + args,
        input=entree, capture_output=True, env=env, timeout=120,
    )
    return proc.returncode, proc.stdout, proc.stderr.decode('utf-8', 'replace')


def extraire_cle(donnees):
    """Matière de la clé, que la DGFiP la publie en ZIP ou en clair.

    Les deux clés se téléchargent depuis impots.gouv.fr sous forme d'archives
    ``cle_publique_chiffrement_dgfip_tiersdeclarants_{test,prod}.zip``. Plutôt
    que d'imposer de les dézipper à la main — geste où l'on se trompe de
    fichier — on accepte l'archive telle qu'elle est téléchargée.
    """
    if not donnees:
        raise ErreurChiffrement("Aucune clé fournie.")
    if len(donnees) > TAILLE_MAX_CLE:
        raise ErreurChiffrement(
            "Ce fichier fait %.1f Mo : ce n'est pas une clé publique."
            % (len(donnees) / 1048576.0))
    if not donnees.startswith(b'PK\x03\x04'):
        return donnees
    try:
        with zipfile.ZipFile(io.BytesIO(donnees)) as archive:
            membres = [n for n in archive.namelist()
                       if not n.endswith('/') and '__MACOSX' not in n]
            if not membres:
                raise ErreurChiffrement("L'archive ZIP est vide.")
            if len(membres) > 1:
                raise ErreurChiffrement(
                    "L'archive contient %s fichiers (%s) : extrayez la clé "
                    "et téléversez-la seule."
                    % (len(membres), ", ".join(membres[:4])))
            return archive.read(membres[0])
    except zipfile.BadZipFile:
        raise ErreurChiffrement("Archive ZIP illisible.")


def decrire_cle(donnees):
    """Identité de la clé, sans l'importer : empreinte, titulaire, dates.

    C'est ce qui permet de voir *laquelle* des deux clés est en place. Se
    tromper de clé ne produit aucune erreur au chiffrement — le rejet arrive
    plus tard, à la DGFiP, sur un dépôt qu'on croyait fait.
    """
    matiere = extraire_cle(donnees)
    with tempfile.TemporaryDirectory() as home:
        os.chmod(home, 0o700)
        code, sortie, erreur = _gpg(
            ['--with-colons', '--show-keys', '/dev/stdin'], home, entree=matiere)
    if code != 0:
        raise ErreurChiffrement(
            "Ce fichier n'est pas une clé publique OpenPGP lisible.\n%s"
            % erreur.strip()[:300])
    infos = {'fingerprint': '', 'uid': '', 'created': '', 'expires': ''}
    for ligne in sortie.decode('utf-8', 'replace').splitlines():
        champs = ligne.split(':')
        if champs[0] == 'pub' and not infos['created']:
            infos['created'], infos['expires'] = champs[5], champs[6]
        elif champs[0] == 'fpr' and not infos['fingerprint']:
            infos['fingerprint'] = champs[9]
        elif champs[0] == 'uid' and not infos['uid']:
            infos['uid'] = champs[9]
    if not infos['fingerprint']:
        raise ErreurChiffrement(
            "Aucune clé publique trouvée dans ce fichier.")
    return infos


def chiffrer(contenu, cle_publique):
    """Chiffre ``contenu`` pour le titulaire de ``cle_publique``.

    ``--trust-model always`` : la clé n'est signée par personne que nous
    connaissions, et il n'y a pas de toile de confiance à bâtir pour une clé
    qu'on est allé chercher soi-même sur le site de la DGFiP. Ce qui atteste
    la clé, c'est son empreinte, affichée dans la configuration.
    """
    matiere = extraire_cle(cle_publique)
    home = tempfile.mkdtemp()
    try:
        os.chmod(home, 0o700)
        code, _, erreur = _gpg(['--import', '/dev/stdin'], home, entree=matiere)
        if code != 0:
            raise ErreurChiffrement(
                "La clé publique n'a pas pu être chargée.\n%s"
                % erreur.strip()[:300])
        empreinte = decrire_cle(matiere)['fingerprint']
        code, chiffre, erreur = _gpg(
            ['--trust-model', 'always', '--recipient', empreinte,
             '--output', '-', '--encrypt', '/dev/stdin'], home, entree=contenu)
        if code != 0 or not chiffre:
            raise ErreurChiffrement(
                "Le chiffrement a échoué.\n%s" % erreur.strip()[:300])
        return chiffre
    finally:
        shutil.rmtree(home, ignore_errors=True)
