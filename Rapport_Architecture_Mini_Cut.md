# Rapport d'Architecture et Stratégie Technique : Projet "Mini Cut"

## 1. 🎯 Analyse du Besoin & Architecture Globale

**Proposition de valeur :** "Mini Cut" est un outil SaaS tout-en-un de curation et de téléchargement de contenu vidéo (YouTube, Instagram, TikTok sans filigrane). Il permet d'extraire des portions spécifiques de vidéos sans avoir à télécharger le fichier complet.

**Architecture Recommandée : Découplée (Client-Server) avec Traitement Asynchrone**
Une architecture Serverless classique (comme les API routes de Next.js) n'est pas adaptée en raison des timeouts stricts imposés par les hébergeurs (10 à 60 secondes en général).
*   **Solution :** Un Front-end réactif qui communique avec un Back-end dédié (via long polling ou WebSockets). Des "Workers" traitent les téléchargements et les découpes complexes via FFmpeg en arrière-plan pour ne pas bloquer la requête utilisateur.

---

## 2. 🛠️ Stack Technique Recommandée (Gratuite & Performante)

*   **Front-end : Next.js (React) + Tailwind CSS + Shadcn UI**
    *   *Avantages :* Routage optimal, excellente SEO pour l'acquisition organique, et création rapide d'interfaces d'édition (comme une timeline de découpage) avec des composants modernes et accessibles.
*   **Back-end & API : FastAPI (Python)**
    *   *Avantages :* Intégration native, fluide et asynchrone avec les standards open source de la vidéo comme `yt-dlp` (écrit en Python) et `FFmpeg`.
*   **Base de données : TiDB (PostgreSQL / MySQL compatible)**
    *   *Avantages :* Approche Serverless, performances impressionnantes avec un plan gratuit très généreux, idéal pour gérer les profils utilisateurs et l'historique de leurs quotas.
*   **Authentification & Sécurité : Clerk ou Auth.js**
    *   *Avantages :* Gestion simple et robuste des sessions et des quotas utilisateurs, une étape indispensable pour éviter l'abus de tes ressources serveurs par des utilisateurs non inscrits.
*   **Hébergement & Infra : Vercel (Front) + Koyeb (Back)**
    *   *Avantages :* Vercel assure un déploiement CDN mondial gratuit du front. Koyeb permet de déployer gratuitement un conteneur Docker (indispensable pour faire tourner les binaires de FFmpeg) pour le back-end.

---

## 3. 💰 Matrice des Coûts & Offres Gratuites (Free Tier)

| Brique / Technologie | Fournisseur | Limites du Plan Gratuit | Stratégie d'extension (Scale) |
| :--- | :--- | :--- | :--- |
| **Front-end Hosting** | **Vercel** | Bande passante 100GB/mois | Plan Pro (20$/mois) si très fort trafic. |
| **Back-end & Workers** | **Koyeb** | 1 instance Eco (512MB RAM) | Scaler vers un VPS abordable (~4€/mois) pour plus de puissance CPU. |
| **Base de données** | **TiDB Serverless** | 5 GB, 50M Request Units/mois | Évolutif à l'usage, les limites gratuites sont très larges pour démarrer. |
| **Authentification** | **Clerk** | 10 000 Utilisateurs (MAU) | La monétisation du SaaS couvrira les coûts au-delà de ce palier. |
| **Traitement Vidéo** | **yt-dlp / FFmpeg** | 100% Open Source | Implémenter une rotation d'IP/Proxies si des blocages surviennent. |

---

## 4. ⚡ Alternatives & Comparatif Rapide

### Alternative 1 : Le Monolithe (La "Vibe" Maker)
*   **Stack :** Laravel (PHP) + Livewire + Tailwind + VPS (ex: Hetzner).
*   **Avantages :** Un seul dépôt de code, et le système natif de Queues/Jobs est parfait pour orchestrer FFmpeg.
*   **Inconvénients :** Nécessite de payer un VPS dès le premier jour car les hébergeurs gratuits ne supportent généralement pas FFmpeg avec des processus de fond en PHP.

### Alternative 2 : L'approche "No-Backend" (API Tierces)
*   **Stack :** Next.js (100% Vercel) + API externes (ex: RapidAPI).
*   **Avantages :** Zéro maintenance serveur, déploiement extrêmement rapide.
*   **Inconvénients :** Dépendance totale à un tiers instable, plans gratuits très limités (souvent 50 requêtes/mois), les coûts explosent très vite.

---

## 5. 🗺️ Feuille de Route d'Exécution (Roadmap MVP)

1.  **Proof of Concept (Semaine 1) :**
    *   Créer un script Python local utilisant `yt-dlp` et `FFmpeg` pour télécharger et couper un extrait précis d'une vidéo YouTube.
    *   Valider le bypass des filigranes pour Instagram et TikTok.
2.  **API Backend (Semaine 1-2) :**
    *   Exposer le script Python via une route FastAPI.
    *   Mettre en place un processus de nettoyage automatique des fichiers `.mp4` générés (ex: suppression après 10 minutes).
    *   Créer le Dockerfile, dockeriser l'application et déployer sur Koyeb.
3.  **Front-end & Interface (Semaine 2-3) :**
    *   Initialiser le projet Next.js.
    *   Développer l'UI principale : un champ de saisie d'URL, la récupération des métadonnées (durée), et un composant de double slider pour délimiter l'extrait.
4.  **Sécurisation & Limitation (Semaine 3) :**
    *   Intégrer Clerk.
    *   Configurer la base de données (TiDB) pour limiter les requêtes quotidiennes des utilisateurs gratuits.

---

## 6. ⚠️ Pièges Techniques ("Tech Debt") à Éviter Absolument

*   **Le téléchargement complet inutile :** Ne pas streamer ou télécharger la vidéo entière si l'utilisateur n'en veut que 10 secondes. Utiliser les arguments de téléchargement partiel de `yt-dlp` combinés à `FFmpeg` pour économiser massivement la bande passante et la RAM du serveur.
*   **Le cauchemar de l'IP Ban :** YouTube bloque rapidement les adresses IP des serveurs Cloud (AWS, DigitalOcean, etc.) qui effectuent trop de requêtes automatisées. Prévoir l'utilisation de fichiers de cookies (`--cookies`) ou une infrastructure de rotation de proxies IPv6 à moyen terme.
*   **La fuite de stockage (Storage Leak) :** Si le backend ne nettoie pas rigoureusement les fichiers traités ou en échec d'encodage, l'espace disque (très limité en plan gratuit) saturera en quelques heures, faisant crasher l'API entière.
