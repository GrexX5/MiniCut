# Product Requirements Document (PRD) - Mini Cut

## 1. 📝 Aperçu du Projet
**Nom du produit :** Mini Cut
**Vision :** Fournir l'outil le plus rapide et le plus simple pour extraire des portions précises de vidéos YouTube et télécharger des contenus Instagram/TikTok sans filigrane, le tout depuis une interface web fluide.
**Cible :** Créateurs de contenu, community managers, monteurs vidéo, et utilisateurs des réseaux sociaux cherchant à archiver ou remixer du contenu.

## 2. 🎯 Objectifs
* **Simplicité :** L'utilisateur doit pouvoir obtenir sa vidéo en moins de 3 clics après avoir collé son lien.
* **Rapidité :** Le traitement d'un extrait de 15 secondes ne doit pas nécessiter le téléchargement préalable d'une vidéo source de 2 heures.
* **Accessibilité :** Fonctionner parfaitement sur desktop et mobile.
* **Viabilité :** Maintenir des coûts d'infrastructure proches de zéro durant la phase de lancement (MVP).

## 3. ✨ Fonctionnalités Clés (MVP)

### 3.1. Gestion des URLs et Détection
* **Champ de saisie universel :** Un seul input pour coller le lien.
* **Détection automatique :** Le système identifie automatiquement la source (YouTube, Instagram, TikTok) et adapte le traitement en conséquence.
* **Bypass de filigrane :** Téléchargement natif de la source pure pour TikTok et Instagram.

### 3.2. Interface de Découpage (Clipping)
* **Récupération des métadonnées :** Affichage instantané du titre, de la miniature et de la durée totale de la vidéo.
* **Timeline interactive :** Un double slider (curseurs de début et de fin) permettant de définir précisément la portion à conserver.
* **Saisie manuelle (Optionnel) :** Champs inputs temporels (HH:MM:SS) pour une précision à la seconde près.

### 3.3. Système de Traitement et Téléchargement
* **Traitement Asynchrone :** Feedback visuel (loader/progress bar) pendant que le backend télécharge et coupe la vidéo.
* **Bouton de téléchargement direct :** Une fois le traitement terminé, la vidéo est servie sous forme de fichier `.mp4` prêt à être enregistré.

### 3.4. Gestion Utilisateurs (Auth & Quotas)
* **Authentification simple :** Inscription / Connexion via Google ou Email.
* **Système de Quotas :** 
  * Utilisateurs non inscrits : 0 ou 1 essai gratuit (pour l'acquisition).
  * Utilisateurs gratuits (inscrits) : Limités à X téléchargements ou découpes par jour.

## 4. 🛤️ Parcours Utilisateur (User Flow)
1. **Landing Page :** L'utilisateur arrive sur la page d'accueil de Mini Cut.
2. **Input :** Il colle le lien URL de la vidéo.
3. **Fetching :** L'application interroge l'API, récupère et affiche les infos de la vidéo.
4. **Action (Choix) :**
   * *Option A :* Il clique sur "Télécharger la vidéo complète" (si applicable/autorisé).
   * *Option B :* Il ajuste les curseurs pour sélectionner un extrait de 10 à 30 secondes, puis clique sur "Couper & Télécharger".
5. **Processing :** Un écran de chargement s'affiche.
6. **Delivery :** Le fichier final est mis à disposition, le compteur de quota de l'utilisateur est décrémenté.

## 5. 🛠️ Exigences Techniques (Non-Fonctionnelles)
* **Frontend :** Next.js (React), Tailwind CSS. Interface responsive et optimisée SEO.
* **Backend :** FastAPI (Python) pour une intégration native avec `yt-dlp` et `ffmpeg`.
* **Database :** TiDB (Serverless) pour stocker les profils et les quotas.
* **Sécurité :** Nettoyage automatique des fichiers `.mp4` du serveur après 10 minutes pour éviter la saturation du stockage. Implémentation d'un Rate Limiting strict sur les routes de l'API.

## 6. 🚀 Fonctionnalités Futures (V2 - Post MVP)
* **Extraction Audio :** Option pour télécharger uniquement la piste audio (`.mp3`).
* **Batch Download :** Possibilité de coller plusieurs liens et de les traiter en file d'attente.
* **Export Cloud :** Envoi direct du fichier découpé vers Google Drive ou Dropbox.
* **Sous-titres automatiques :** Ajout d'une surcouche IA (ex: Whisper) pour générer des sous-titres sur les extraits découpés.
