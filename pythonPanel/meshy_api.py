"""
Module de gestion des interactions avec l'API Meshy.ai
"""

import os
import json
import time
import requests
from typing import Dict, Any, Optional

class MeshyAPI:
    """Classe principale pour interagir avec l'API Meshy"""
    
    def __init__(self, api_key: str = None):
        """Initialise la connexion avec l'API Meshy"""
        self.api_url = "https://api.meshy.ai/openapi/v1"  # Retour à l'URL qui fonctionnait
        self.set_api_key(api_key)
    
    def set_api_key(self, api_key: str = None) -> None:
        """Définit ou met à jour la clé API"""
        self.api_key = api_key
        
        # Réinitialiser la session avec la nouvelle clé
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            })
    
    def validate_api_key(self) -> bool:
        """Vérifie si la clé API est valide"""
        import sys
        def log(msg):
            print(msg, file=sys.stderr)
            sys.stderr.flush()

        if not self.api_key:
            log("❌ Pas de clé API fournie")
            return False
            
        try:
            # Utiliser text-to-texture comme endpoint de validation
            validation_url = f"{self.api_url}/text-to-texture"
            
            log("🔑 Validation de la clé API...")
            log(f"📡 URL: {validation_url}")
            log(f"🔒 Headers: {dict(self.session.headers)}")
            
            # Requête POST avec les paramètres requis
            data = {
                "object_prompt": "test object",
                "texture_prompt": "simple color"
            }
            response = self.session.post(validation_url, json=data)
            
            log(f"📊 Status code: {response.status_code}")
            log(f"📝 Réponse: {response.text[:200] if response.text else 'Pas de contenu'}")
            
            if response.status_code == 200:
                log("✅ Validation réussie!")
                return True
            elif response.status_code == 401:
                log("❌ Clé API non autorisée")
                return False
            elif response.status_code == 402:
                log("✅ Clé API valide (crédits insuffisants)")
                return True
            elif response.status_code == 400:
                # Si l'erreur 400 est due à la validation des paramètres,
                # cela signifie que l'authentification a réussi
                if "validation" in response.text.lower():
                    log("✅ Clé API valide (erreur de validation des paramètres)")
                    return True
                else:
                    log("❌ Erreur de requête")
                    return False
            else:
                log(f"⚠️ Statut inattendu: {response.status_code}")
                return False
                
        except Exception as e:
            log(f"❌ Erreur: {str(e)}")
            log(f"📋 Type d'erreur: {type(e)}")
            return False
    
    def save_config(self, config_dir: str = None) -> None:
        """Sauvegarde la configuration (dont la clé API) localement"""
        if config_dir is None:
            # Utiliser le dossier de configuration Houdini de l'utilisateur
            config_dir = os.path.expanduser("~/houdini20.5/meshy_plugin")
            
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, "config.json")
        
        with open(config_file, "w") as f:
            json.dump({"api_key": self.api_key}, f)
    
    def load_config(self, config_dir: str = None) -> None:
        """Charge la configuration depuis le fichier local"""
        if config_dir is None:
            config_dir = os.path.expanduser("~/houdini20.5/meshy_plugin")
            
        config_file = os.path.join(config_dir, "config.json")
        
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                self.set_api_key(config.get("api_key"))
        except:
            pass  # Fichier non trouvé ou invalide
    
    def text_to_3d(self, prompt: str) -> Dict[str, Any]:
        """Convertit un texte en modèle 3D via Meshy en utilisant le workflow preview/refine"""
        if not self.api_key:
            raise ValueError("Clé API non configurée")
            
        import sys
        def log(msg):
            print(msg, file=sys.stderr)
            sys.stderr.flush()

        # Étape 1 : Preview - Génération du mesh de base
        preview_endpoint = "https://api.meshy.ai/openapi/v2/text-to-3d"
        preview_data = {
            "mode": "preview",
            "prompt": prompt,
            "art_style": "realistic",
            "topology": "quad",
            "target_polycount": 30000,
            "should_remesh": True,
            "symmetry_mode": "auto"
        }
        
        log("🚀 Démarrage de la génération du preview...")
        preview_response = self.session.post(preview_endpoint, json=preview_data)
        preview_response.raise_for_status()
        preview_task_id = preview_response.json()["result"]
        
        # Attendre que la preview soit terminée (max 5 minutes)
        max_attempts = 150  # 5 minutes (2 secondes * 150)
        attempts = 0
        while attempts < max_attempts:
            status = self.get_job_status(preview_task_id)
            if status["status"] == "SUCCEEDED":
                log("✅ Preview terminé avec succès!")
                break
            elif status["status"] == "FAILED":
                raise ValueError(f"Preview échoué: {status.get('task_error', {}).get('message', 'Erreur inconnue')}")
            
            attempts += 1
            progress = (attempts / max_attempts) * 100
            log(f"⏳ Preview en cours... {progress:.1f}% (tentative {attempts}/{max_attempts})")
            time.sleep(2)
            
        if attempts >= max_attempts:
            raise TimeoutError("Le preview a dépassé le délai maximum de 5 minutes")
            
        # Étape 2 : Refine - Application des textures
        log("🎨 Démarrage du raffinement...")
        refine_data = {
            "mode": "refine",
            "preview_task_id": preview_task_id,
            "enable_pbr": True
        }
        
        refine_response = self.session.post(preview_endpoint, json=refine_data)
        refine_response.raise_for_status()
        refine_task_id = refine_response.json()["result"]
        
        # Attendre que le refine soit terminé (max 5 minutes)
        attempts = 0
        while attempts < max_attempts:
            status = self.get_job_status(refine_task_id)
            if status["status"] == "SUCCEEDED":
                log("✅ Raffinement terminé avec succès!")
                return status
            elif status["status"] == "FAILED":
                raise ValueError(f"Raffinement échoué: {status.get('task_error', {}).get('message', 'Erreur inconnue')}")
            
            attempts += 1
            progress = (attempts / max_attempts) * 100
            log(f"⏳ Raffinement en cours... {progress:.1f}% (tentative {attempts}/{max_attempts})")
            time.sleep(2)
            
        if attempts >= max_attempts:
            raise TimeoutError("Le raffinement a dépassé le délai maximum de 5 minutes")
    
    def image_to_3d(self, image_path: str) -> Dict[str, Any]:
        """Convertit une image en modèle 3D via Meshy"""
        if not self.api_key:
            raise ValueError("Clé API non configurée")
            
        endpoint = f"{self.api_url}/image-to-mesh"  # Endpoint cohérent
        
        with open(image_path, "rb") as image_file:
            files = {"image": ("image.png", image_file, "image/png")}
            response = self.session.post(endpoint, files=files)
        
        response.raise_for_status()
        return response.json()
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Vérifie le statut d'un job en cours"""
        if not self.api_key:
            raise ValueError("Clé API non configurée")
            
        endpoint = f"https://api.meshy.ai/openapi/v2/text-to-3d/{job_id}"
        
        response = self.session.get(endpoint)
        response.raise_for_status()
        return response.json()
    
    def download_model(self, url: str, output_path: str) -> str:
        """Télécharge un modèle 3D depuis l'URL fournie"""
        if not self.api_key:
            raise ValueError("Clé API non configurée")
            
        response = self.session.get(url, stream=True)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return output_path

    def texture_geometry(self, model_path: str, prompt: str = None, style: str = None) -> Dict[str, Any]:
        """Envoie une géométrie existante à Meshy pour la texturer"""
        if not self.api_key:
            raise ValueError("Clé API non configurée")
            
        endpoint = f"{self.api_url}/text-to-texture"  # Déjà dans le bon format
        
        # Préparer le fichier avec le bon format MIME
        with open(model_path, "rb") as model_file:
            files = {"model_file": ("model.obj", model_file, "application/octet-stream")}
            
            # Préparer les données selon la doc
            data = {}
            if prompt:
                data["texture_prompt"] = prompt  # Format cohérent
            if style:
                data["style"] = style
                
            response = self.session.post(
                endpoint,
                files=files,
                data=data
            )
        
        response.raise_for_status()
        return response.json()

    def text_to_3d_houdini(self, prompt: str, node_context) -> None:
        """Workflow complet de text-to-3D dans Houdini"""
        import hou
        import time
        import sys
        
        def log(msg):
            print(msg, file=sys.stderr)
            sys.stderr.flush()
            
        try:
            # Créer le dossier de destination dès le début
            output_dir = os.path.expanduser("~/houdini20.5/meshy_plugin/models")
            os.makedirs(output_dir, exist_ok=True)
            log(f"📁 Dossier de destination créé : {output_dir}")
            
            # Nom du fichier basé sur le prompt
            safe_name = prompt[:30].lower().replace(" ", "_")
            output_path = os.path.join(output_dir, f"{safe_name}.fbx")
            log(f"📄 Le modèle sera sauvegardé comme : {output_path}")
            
            # Créer un nœud Geometry pour recevoir le modèle
            geo_node = node_context.createNode("geo", "meshy_" + prompt[:20].lower().replace(" ", "_"))
            
            # Lancer la génération du modèle
            log(f"🎨 Génération du modèle 3D pour : {prompt}")
            result = self.text_to_3d(prompt)
            
            # Récupérer l'URL du modèle FBX
            model_url = result.get("model_urls", {}).get("fbx")
            if not model_url:
                raise ValueError("URL du modèle FBX non trouvée dans la réponse")
            
            log(f"🔗 URL du modèle obtenue : {model_url}")
                
            # Télécharger le modèle
            log(f"📥 Téléchargement du modèle vers : {output_path}")
            self.download_model(model_url, output_path)
            
            # Vérifier que le fichier existe
            if not os.path.exists(output_path):
                raise ValueError(f"Le fichier n'a pas été téléchargé : {output_path}")
            
            log(f"📦 Taille du fichier téléchargé : {os.path.getsize(output_path)} bytes")
            
            # Créer un nœud FBX pour importer le modèle
            fbx_node = geo_node.createNode("fbximport")
            fbx_node.parm("file").set(output_path)
            
            # Mettre à jour le nœud
            log("🔄 Import du modèle dans Houdini...")
            fbx_node.cook(force=True)
            
            # Positionner le nœud et le layout
            geo_node.layoutChildren()
            
            # Sélectionner le nouveau nœud
            geo_node.setSelected(True)
            
            log("✅ Modèle importé avec succès!")
            log(f"💾 Le modèle est sauvegardé dans : {output_path}")
            
        except Exception as e:
            log(f"❌ Erreur: {str(e)}")
            log(f"📋 Type d'erreur: {type(e)}")
            raise 