# Détails Avancés des API

## Meshy.ai API

### Text-to-3D
- **Endpoint**: `/v1/meshy-4/text-to-3d`
- **Méthode**: POST
- **Headers requis**:
  ```python
  {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
  }
  ```
- **Corps de la requête**:
  ```python
  {
    "prompt": "a detailed 3D model of a dragon",
    "style": "realistic",  # Optionnel
    "negative_prompt": "low quality, blurry",  # Optionnel
    "output_format": "fbx"  # Optionnel, par défaut: fbx
  }
  ```
- **Réponse**:
  ```python
  {
    "job_id": "job_123",
    "status": "pending",
    "estimated_time": 120  # en secondes
  }
  ```

### Image-to-3D
- **Endpoint**: `/v1/meshy-4/image-to-3d`
- **Méthode**: POST
- **Headers requis**:
  ```python
  {
    "Authorization": "Bearer YOUR_API_KEY"
  }
  ```
- **Corps de la requête**:
  - `image`: Fichier image (formats supportés: PNG, JPG, JPEG)
  - `style`: Optionnel, style de génération
  - `output_format`: Optionnel, format de sortie

### Gestion des Jobs
- **Vérification du statut**:
  ```python
  GET /v1/jobs/{job_id}
  ```
- **Statuts possibles**:
  - `pending`: En attente
  - `processing`: En cours de traitement
  - `completed`: Terminé
  - `failed`: Échec
- **Réponse complète**:
  ```python
  {
    "status": "completed",
    "model_url": "https://...",
    "created_at": "2024-03-20T10:00:00Z",
    "completed_at": "2024-03-20T10:02:00Z"
  }
  ```

## Houdini Python API (HOM)

### Création de Nodes
```python
# Créer un node GEO
geo_node = hou.node("/obj").createNode("geo", "my_geo")

# Créer un node FILE pour l'import
file_node = geo_node.createNode("file", "import")
file_node.parm("file").set("path/to/model.fbx")

# Créer un node MATERIAL
mat_node = geo_node.createNode("material")
mat_node.parm("shop_materialpath").set("/mat/my_material")
```

### Gestion des Paramètres
```python
# Définir plusieurs paramètres
node.setParms({
    "scale": 2.0,
    "tx": 1.0,
    "ty": 0.0,
    "tz": 0.0
})

# Expressions Python dans les paramètres
node.parm("scale").setExpression("$F/24")  # Animation basée sur la frame

# Groupes de paramètres
node.setParmsInFolder("Transform", {
    "scale": 2.0,
    "rotate": [0, 45, 0]
})
```

### Organisation du Network
```python
# Définir la position d'un node
node.setPosition([0, 0])

# Organiser les nodes enfants
node.layoutChildren()

# Créer un sous-réseau
subnet = node.createNode("subnet", "my_subnet")
subnet.layoutChildren()
```

### Gestion des Erreurs
```python
try:
    node = hou.node("/obj/my_geo")
    if node is None:
        raise hou.NodeError("Node not found")
    # Opérations sur le node
except hou.NodeError as e:
    hou.ui.displayMessage(f"Erreur: {str(e)}")
except Exception as e:
    hou.ui.displayMessage(f"Erreur inattendue: {str(e)}")
```

### Chemins et Variables
```python
# Chemins courants
hip_path = hou.expandString("$HIP")  # Dossier du projet
temp_path = hou.expandString("$TEMP") # Dossier temporaire
home_path = hou.expandString("$HOUDINI_USER_PREF_DIR") # Préférences utilisateur

# Variables personnalisées
hou.putenv("MESHY_TEMP_DIR", f"{hip_path}/meshy_temp")
temp_dir = hou.getenv("MESHY_TEMP_DIR")
```

## Bonnes Pratiques

### Meshy
1. **Gestion des Rate Limits**:
   - Implémenter un système de file d'attente
   - Utiliser des délais exponentiels pour les retries
   - Sauvegarder les job_id pour éviter les doublons

2. **Optimisation des Requêtes**:
   - Compresser les images avant l'envoi
   - Utiliser des prompts précis et détaillés
   - Gérer les erreurs de réseau

### Houdini
1. **Organisation du Network**:
   - Utiliser des préfixes cohérents (ex: "meshy_")
   - Créer des sous-réseaux logiques
   - Documenter les nodes avec des notes

2. **Performance**:
   - Éviter les opérations coûteuses en temps réel
   - Utiliser le caching quand possible
   - Nettoyer les nodes temporaires 