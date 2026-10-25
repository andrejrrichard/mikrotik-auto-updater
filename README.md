# MikroTik Auto Updater

Outil Python de mise à jour automatique de routeur(s) MikroTik.

## 🎯 Objectif

Ce script se connecte à une liste de routeurs MikroTik via leur API REST, lit leur version de RouterOS installée, la compare avec la dernière version disponible (via le flux RSS officiel de MikroTik), et déclenche la mise à jour si nécessaire de RouterOS et RouterBOARD.

## ✨ Fonctionnalités

- Lecture de la version cible depuis le flux RSS officiel.
- Connexion sécurisée aux routeurs via HTTPS (certificats auto-signés tolérés).
- Comparaison fiable entre version installée et version cible (internet).
- Synchronisation automatique du channel de mise à jour (stable, testing, long-term).
- Mise à jour de RouterOS et RouterBOARD.
- Traitement séquentiel de plusieurs routeurs.
- Gestion des erreurs par routeur (un échec n'arrête pas les autres).

## 🔐 Sécurité

L'utilisateur API des routeurs doit avoir les policies minimales : api, rest-api, read, write, reboot.
L'accès à l'API REST doit être restreint à l'adresse IP du PC de gestion (via le champ address du service www-ssl).

## ⚠️ Limitations connues

Le script suppose que le PC exécutant le script a accès à internet pour lire le flux RSS.
Le script suppose que le routeur a accès à internet pour obtenir le package à mettre à jour.

## Helper

# 1. Créer le groupe avec les policies minimales
/user group add name=api-updater policy=api,rest-api,read,write,reboot,policy,test,local,!telnet,!ssh,!ftp,!winbox,!password,!web,!sniff,!sensitive,!romon

# 2. Créer l'utilisateur et l'assigner au groupe
/user add name=updater group=api-updater password="VotreMotDePasseFort" comment="Compte pour script de mise à jour"

# 3. Créer un certificat auto-signé pour l'IP de gestion du routeur
/certificate add name=cert-gestion common-name=192.168.88.1 days-valid=3650
/certificate sign cert-gestion

# 4. Assigner le certificat au service www-ssl
/ip service set www-ssl certificate=cert-gestion

# 5. Restreindre l'accès à votre PC de gestion uniquement
/ip service set www-ssl address=192.168.88.2/32

# 6. Activer le service et redémarrer pour appliquer
/ip service enable www-ssl
/ip service set www-ssl disabled=yes
/ip service set www-ssl disabled=no