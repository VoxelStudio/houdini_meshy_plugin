# Références API

## Meshy.ai API

### Base URL
```
https://api.meshy.ai
```

### Endpoints Principaux

#### Text-to-3D
- **Endpoint**: `/v1/meshy-4/text-to-3d`
- **Méthode**: POST
- **Paramètres**:
  - `prompt` (string): Description textuelle du modèle 3D
  - `style` (string, optionnel): Style de génération
  - `negative_prompt` (string, optionnel): Ce qu'il ne faut pas inclure

#### Image-to-3D
- **Endpoint**: `/v1/meshy-4/image-to-3d`
- **Méthode**: POST
- **Paramètres**:
  - `image` (file): Image source
  - `style` (string, optionnel): Style de génération

#### Get Job Status
- **Endpoint**: `/v1/jobs/{job_id}`
- **Méthode**: GET
- **Réponse**:
  - `status`: "pending" | "processing" | "completed" | "failed"
  - `model_url`: URL du modèle généré (si status = "completed")

## Houdini Python API (HOM)

### Importation
```python
import hou
```

### Fonctions Principales

#### Gestion des Nodes
```python
# Créer un node
node = hou.node("/obj").createNode("geo", "my_geo")

# Obtenir un node existant
node = hou.node("/obj/my_geo")

# Créer un node file pour importer
file_node = node.createNode("file", "import")
file_node.parm("file").set("path/to/file.fbx")
```

#### Gestion des Paramètres
```python
# Définir un paramètre
node.parm("scale").set(2.0)

# Obtenir un paramètre
scale = node.parm("scale").eval()
```

#### Layout et Organisation
```python
# Organiser les nodes
node.layoutChildren()

# Définir la position d'un node
node.setPosition([0, 0])
```

### Constantes Utiles
```python
# Chemins courants
hou.expandString("$HIP")  # Dossier du projet
hou.expandString("$TEMP") # Dossier temporaire
```

## Conventions de Code

### Python
- Utiliser des docstrings pour la documentation
- Suivre PEP 8 pour le style de code
- Utiliser le typage (type hints) pour les fonctions

### Houdini
- Préfixer les nodes générés avec un identifiant unique
- Organiser les nodes en sous-réseaux logiques
- Utiliser des noms explicites pour les paramètres

### Meshy
- Gérer les erreurs API avec try/except
- Vérifier les limites de taux (rate limits)
- Sauvegarder les job_id pour le suivi 