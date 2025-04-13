# Meshy Houdini Plugin

Plugin Houdini permettant d'intégrer les fonctionnalités de Meshy.ai directement dans Houdini.

## Fonctionnalités

- Génération de modèles 3D à partir de texte
- Texturing de géométries existantes
- Interface utilisateur intégrée dans Houdini
- Sauvegarde automatique des modèles générés

## Installation

1. Clonez ce dépôt dans un dossier local
2. Ajoutez le chemin du dossier à votre `PYTHONPATH` Houdini
3. Redémarrez Houdini
4. Créez un nouveau Python Panel et sélectionnez "Meshy Interface"

## Configuration

1. Obtenez une clé API sur [Meshy.ai](https://meshy.ai)
2. Entrez votre clé API dans l'interface du plugin
3. La clé sera sauvegardée localement pour les futures sessions

## Utilisation

1. Ouvrez le panneau Meshy dans Houdini
2. Entrez votre prompt ou sélectionnez une géométrie à texturer
3. Cliquez sur "Générer" ou "Texturer"
4. Le modèle/la texture sera automatiquement importé dans votre scène

## Auteur

Kevin @ FoxForm3D

## Licence

MIT License 