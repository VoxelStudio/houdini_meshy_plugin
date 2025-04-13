"""
Module principal du panel Python pour Meshy dans Houdini
"""

import os
import hou
from PySide2 import QtWidgets, QtCore
from typing import Optional

from .meshy_api import MeshyAPI

class MeshyWorker(QtCore.QThread):
    """Worker thread pour la génération de modèles"""
    progress = QtCore.Signal(int, str)  # (pourcentage, message)
    finished = QtCore.Signal(dict)  # résultat final
    error = QtCore.Signal(str)  # message d'erreur
    
    def __init__(self, api, prompt, node_context, save_path=None):
        super().__init__()
        self.api = api
        self.prompt = prompt
        self.node_context = node_context
        self.save_path = save_path
        self._is_cancelled = False
        
    def run(self):
        try:
            # Étape 1: Preview
            self.progress.emit(0, "Démarrage de la génération...")
            preview_result = self.api.text_to_3d_preview(self.prompt)
            preview_task_id = preview_result["result"]
            
            # Suivi du preview
            attempts = 0
            max_attempts = 150
            while attempts < max_attempts and not self._is_cancelled:
                status = self.api.get_job_status(preview_task_id)
                if status["status"] == "SUCCEEDED":
                    self.progress.emit(50, "Preview terminé, démarrage du raffinement...")
                    break
                elif status["status"] == "FAILED":
                    self.error.emit(f"Erreur lors du preview: {status.get('error', 'Erreur inconnue')}")
                    return
                    
                progress = (attempts / max_attempts) * 50  # 0-50% pour le preview
                self.progress.emit(int(progress), f"Génération du preview... {int(progress)}%")
                self.msleep(2000)  # Pause de 2 secondes
                attempts += 1
                
            if self._is_cancelled:
                return
                
            # Étape 2: Refine
            refine_result = self.api.text_to_3d_refine(preview_task_id)
            refine_task_id = refine_result["result"]
            
            # Suivi du refine
            attempts = 0
            while attempts < max_attempts and not self._is_cancelled:
                status = self.api.get_job_status(refine_task_id)
                if status["status"] == "SUCCEEDED":
                    self.progress.emit(100, "Raffinement terminé!")
                    status["prompt"] = self.prompt  # Ajouter le prompt pour le nom du fichier
                    self.finished.emit(status)
                    break
                elif status["status"] == "FAILED":
                    self.error.emit(f"Erreur lors du raffinement: {status.get('error', 'Erreur inconnue')}")
                    return
                    
                progress = 50 + (attempts / max_attempts) * 50  # 50-100% pour le refine
                self.progress.emit(int(progress), f"Raffinement en cours... {int(progress)}%")
                self.msleep(2000)
                attempts += 1
                
        except Exception as e:
            self.error.emit(f"Erreur: {str(e)}\n{traceback.format_exc()}")
            
    def cancel(self):
        self._is_cancelled = True

class MeshyPanel(QtWidgets.QWidget):
    """Panel principal pour l'interface Meshy"""
    
    def __init__(self):
        super().__init__()
        self.api = MeshyAPI()
        self.worker = None
        # Charger la configuration existante
        self.api.load_config()
        self.setup_ui()
        
        # Mettre à jour le statut de l'API
        self.update_api_status()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Layout principal
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        # Groupe Configuration API
        api_group = QtWidgets.QGroupBox("Configuration API Meshy")
        api_layout = QtWidgets.QVBoxLayout()
        
        # Layout pour la clé API
        api_key_layout = QtWidgets.QHBoxLayout()
        self.api_key_input = QtWidgets.QLineEdit()
        self.api_key_input.setPlaceholderText("Entrez votre clé API Meshy...")
        self.api_key_input.setText(self.api.api_key or "")
        api_key_layout.addWidget(self.api_key_input)
        
        # Bouton pour sauvegarder/vérifier la clé API
        self.save_api_button = QtWidgets.QPushButton("Sauvegarder")
        self.save_api_button.clicked.connect(self.save_api_key)
        api_key_layout.addWidget(self.save_api_button)
        
        api_layout.addLayout(api_key_layout)
        
        # Label pour le statut de l'API
        self.api_status_label = QtWidgets.QLabel("Statut API : Non configuré")
        api_layout.addWidget(self.api_status_label)
        
        # Layout pour les liens
        links_layout = QtWidgets.QVBoxLayout()
        
        # Lien pour obtenir une clé API avec réduction
        api_link = QtWidgets.QLabel('<a href="https://www.meshy.ai?via=Foxform3D" style="color: #FFA500; text-decoration: underline;">Obtenir une clé API avec 20% de réduction</a>')
        api_link.setOpenExternalLinks(True)
        links_layout.addWidget(api_link)
        
        # Lien vers la documentation
        doc_link = QtWidgets.QLabel('<a href="https://docs.meshy.ai" style="color: #FFA500; text-decoration: underline;">Documentation Meshy</a>')
        doc_link.setOpenExternalLinks(True)
        links_layout.addWidget(doc_link)
        
        api_layout.addLayout(links_layout)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Groupe Configuration Sauvegarde
        save_group = QtWidgets.QGroupBox("Configuration Sauvegarde")
        save_layout = QtWidgets.QVBoxLayout()
        
        # Checkbox pour utiliser $HIP
        self.use_hip_checkbox = QtWidgets.QCheckBox("Utiliser $HIP (dossier du projet Houdini)")
        self.use_hip_checkbox.setChecked(True)
        self.use_hip_checkbox.stateChanged.connect(self.toggle_save_path)
        save_layout.addWidget(self.use_hip_checkbox)
        
        # Layout pour le chemin de sauvegarde
        save_path_layout = QtWidgets.QHBoxLayout()
        self.save_path_input = QtWidgets.QLineEdit()
        self.save_path_input.setPlaceholderText("Chemin de sauvegarde des modèles...")
        self.save_path_input.setEnabled(False)  # Désactivé par défaut car $HIP est coché
        save_path_layout.addWidget(self.save_path_input)
        
        # Bouton parcourir
        browse_save_btn = QtWidgets.QPushButton("Parcourir")
        browse_save_btn.clicked.connect(self.browse_save_path)
        save_path_layout.addWidget(browse_save_btn)
        
        save_layout.addLayout(save_path_layout)
        save_group.setLayout(save_layout)
        layout.addWidget(save_group)
        
        # Groupe Text-to-3D
        text_group = QtWidgets.QGroupBox("Text to 3D")
        text_layout = QtWidgets.QVBoxLayout()
        
        # Zone de texte pour le prompt
        self.prompt_input = QtWidgets.QTextEdit()
        self.prompt_input.setPlaceholderText("Entrez votre description...")
        self.prompt_input.setMaximumHeight(100)
        text_layout.addWidget(self.prompt_input)
        
        # Bouton de génération
        self.generate_button = QtWidgets.QPushButton("Générer depuis le texte")
        self.generate_button.clicked.connect(self.text_to_3d_clicked)
        text_layout.addWidget(self.generate_button)
        
        text_group.setLayout(text_layout)
        layout.addWidget(text_group)
        
        # Groupe Image-to-3D
        image_group = QtWidgets.QGroupBox("Image to 3D")
        image_layout = QtWidgets.QVBoxLayout()
        
        # Layout pour le chemin de l'image
        image_path_layout = QtWidgets.QHBoxLayout()
        self.image_path_input = QtWidgets.QLineEdit()
        self.image_path_input.setPlaceholderText("Chemin de l'image...")
        image_path_layout.addWidget(self.image_path_input)
        
        # Bouton de sélection de fichier
        self.browse_image_button = QtWidgets.QPushButton("Parcourir")
        self.browse_image_button.clicked.connect(self.browse_image)
        image_path_layout.addWidget(self.browse_image_button)
        
        image_layout.addLayout(image_path_layout)
        
        # Bouton de génération depuis l'image
        self.generate_image_button = QtWidgets.QPushButton("Générer depuis l'image")
        self.generate_image_button.clicked.connect(self.generate_from_image)
        image_layout.addWidget(self.generate_image_button)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)

        # Groupe pour la texturation
        texture_group = QtWidgets.QGroupBox("Texturer la géométrie sélectionnée")
        texture_layout = QtWidgets.QVBoxLayout()

        # Description des textures souhaitées
        self.texture_prompt = QtWidgets.QTextEdit()
        self.texture_prompt.setPlaceholderText("Description des textures souhaitées...")
        self.texture_prompt.setMaximumHeight(100)
        texture_layout.addWidget(self.texture_prompt)

        # Style de texture
        style_layout = QtWidgets.QHBoxLayout()
        style_layout.addWidget(QtWidgets.QLabel("Style:"))
        self.style_combo = QtWidgets.QComboBox()
        self.style_combo.addItems(["Réaliste", "Cartoon", "Stylisé", "Peint à la main"])
        style_layout.addWidget(self.style_combo)
        texture_layout.addLayout(style_layout)

        # Bouton pour texturer
        self.texture_button = QtWidgets.QPushButton("Texturer la géométrie")
        self.texture_button.clicked.connect(self.texture_selected_geometry)
        texture_layout.addWidget(self.texture_button)

        texture_group.setLayout(texture_layout)
        layout.addWidget(texture_group)
        
        # Zone de statut
        self.status_label = QtWidgets.QLabel("Prêt")
        layout.addWidget(self.status_label)
        
        # Barre de progression
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Bouton d'annulation
        self.cancel_button = QtWidgets.QPushButton("Annuler")
        self.cancel_button.hide()
        self.cancel_button.clicked.connect(self.cancel_generation)
        layout.addWidget(self.cancel_button)
        
        # Ajouter un espace extensible à la fin
        layout.addStretch()
    
    def save_api_key(self):
        """Sauvegarde et vérifie la clé API"""
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            QtWidgets.QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez entrer une clé API"
            )
            return
        
        # Mettre à jour la clé API
        self.api.set_api_key(api_key)
        
        # Vérifier si la clé est valide
        if self.api.validate_api_key():
            # Sauvegarder la configuration
            self.api.save_config()
            QtWidgets.QMessageBox.information(
                self,
                "Succès",
                "Clé API validée et sauvegardée avec succès!"
            )
        else:
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur",
                "La clé API semble invalide. Veuillez vérifier votre clé."
            )
        
        # Mettre à jour le statut
        self.update_api_status()
    
    def update_api_status(self):
        """Met à jour l'affichage du statut de l'API"""
        if not self.api.api_key:
            self.api_status_label.setText("Statut API : Non configuré")
            self.api_status_label.setStyleSheet("color: red")
        elif self.api.validate_api_key():
            self.api_status_label.setText("Statut API : Connecté")
            self.api_status_label.setStyleSheet("color: green")
        else:
            self.api_status_label.setText("Statut API : Clé invalide")
            self.api_status_label.setStyleSheet("color: red")
    
    def browse_image(self):
        """Ouvre un dialogue pour sélectionner une image"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Sélectionner une image",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.image_path_input.setText(file_path)
    
    def text_to_3d_clicked(self):
        """Gestion du clic sur le bouton Text-to-3D"""
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            self.show_error("Veuillez entrer un prompt")
            return
            
        try:
            # Désactiver l'interface pendant le traitement
            self.disable_ui_controls()
            self.progress_bar.setValue(0)
            self.progress_bar.show()
            self.cancel_button.show()
            self.status_label.setText("Démarrage de la génération...")
            
            # Récupérer le contexte du nœud actuel
            node_context = hou.node("/obj")
            
            # Obtenir le chemin de sauvegarde
            save_path = self.get_save_path()
            
            # Création et démarrage du worker
            self.worker = MeshyWorker(self.api, prompt, node_context, save_path)
            self.worker.progress.connect(self.on_progress)
            self.worker.error.connect(self.on_error)
            self.worker.finished.connect(self.on_finished)
            self.worker.start()
            
        except Exception as e:
            self.show_error(f"Erreur lors de la génération : {str(e)}")
            self.reset_ui_state()
            
    def show_error(self, message):
        """Affiche une boîte de dialogue d'erreur"""
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Erreur")
        msg.exec_()
    
    def generate_from_image(self):
        """Génère un modèle 3D à partir d'une image"""
        if not self.api.api_key:
            QtWidgets.QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez d'abord configurer votre clé API Meshy"
            )
            return
            
        image_path = self.image_path_input.text().strip()
        if not image_path or not os.path.exists(image_path):
            QtWidgets.QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez sélectionner une image valide"
            )
            return
        
        try:
            self.status_label.setText("Génération en cours...")
            self.progress_bar.show()
            self.cancel_button.show()
            
            # Création et démarrage du worker
            self.worker = MeshyWorker(self.api, "", hou.node("/obj"), self.get_save_path())
            self.worker.progress.connect(self.on_progress)
            self.worker.error.connect(self.on_error)
            self.worker.finished.connect(self.on_finished)
            self.worker.start()
            
        except Exception as e:
            self.status_label.setText(f"Erreur: {str(e)}")
            self.progress_bar.hide()
            self.cancel_button.hide()
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur",
                f"Une erreur est survenue: {str(e)}"
            )

    def texture_selected_geometry(self):
        """Texture la géométrie sélectionnée dans Houdini"""
        if not self.api.api_key:
            QtWidgets.QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez d'abord configurer votre clé API Meshy"
            )
            return
            
        # Vérifier s'il y a une sélection
        selection = hou.selectedNodes()
        if not selection:
            QtWidgets.QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez sélectionner un node de géométrie"
            )
            return

        try:
            # Obtenir le premier node sélectionné
            node = selection[0]
            
            # Créer un dossier temporaire pour l'export
            temp_dir = hou.expandString("$HIP/temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, "temp_for_texture.fbx")
            
            # Exporter la géométrie en FBX
            # Note: Cette partie peut nécessiter des ajustements selon la version de Houdini
            hou.hipFile.exportFBX(temp_file, [node])
            
            # Préparer les paramètres
            prompt = self.texture_prompt.toPlainText().strip()
            style = self.style_combo.currentText().lower()
            
            self.status_label.setText("Texturation en cours...")
            self.progress_bar.show()
            self.cancel_button.show()
            
            # Création et démarrage du worker
            self.worker = MeshyWorker(self.api, prompt, node, self.get_save_path())
            self.worker.progress.connect(self.on_progress)
            self.worker.error.connect(self.on_error)
            self.worker.finished.connect(self.on_finished)
            self.worker.start()
            
        except Exception as e:
            self.status_label.setText(f"Erreur: {str(e)}")
            self.progress_bar.hide()
            self.cancel_button.hide()
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur",
                f"Une erreur est survenue: {str(e)}"
            )

    def on_progress(self, value, message):
        """Mise à jour de la progression"""
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{message}")
        self.status_label.setText(message)
        
    def on_error(self, message):
        """Gestion des erreurs"""
        self.progress_bar.hide()
        self.cancel_button.hide()
        self.status_label.setText(f"Erreur: {message}")
        self.reset_ui_state()
        self.show_error(message)
        
    def on_finished(self, result):
        """Gestion de la fin de la génération"""
        try:
            # Import du modèle dans Houdini avec le chemin personnalisé
            self.api.import_model_to_houdini(result, hou.node("/obj"), self.get_save_path())
            self.progress_bar.hide()
            self.cancel_button.hide()
            self.status_label.setText("Modèle généré et importé avec succès!")
            self.reset_ui_state()
        except Exception as e:
            self.on_error(str(e))
        
    def cancel_generation(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
            self.progress_bar.hide()
            self.cancel_button.hide()
            self.status_label.setText("Génération annulée")
            
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        super().closeEvent(event)

    def toggle_save_path(self, state):
        """Active/désactive le champ de chemin de sauvegarde selon l'état de la checkbox"""
        self.save_path_input.setEnabled(not state)
        if state:
            # Si $HIP est activé, on met à jour le chemin affiché
            hip = hou.expandString("$HIP")
            self.save_path_input.setPlaceholderText(f"$HIP ({hip})")
        else:
            self.save_path_input.setPlaceholderText("Chemin de sauvegarde des modèles...")
            
    def browse_save_path(self):
        """Ouvre un dialogue pour sélectionner le dossier de sauvegarde"""
        if self.use_hip_checkbox.isChecked():
            return
            
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier de sauvegarde",
            self.save_path_input.text() or hou.expandString("$HOME")
        )
        if folder_path:
            self.save_path_input.setText(folder_path)
            
    def get_save_path(self) -> str:
        """Retourne le chemin de sauvegarde actuel"""
        if self.use_hip_checkbox.isChecked():
            base_path = hou.expandString("$HIP")
        else:
            base_path = self.save_path_input.text().strip() or hou.expandString("$HOME")
        
        # Ajouter le sous-dossier meshy_models
        return os.path.join(base_path, "meshy_models")

    def reset_ui_state(self):
        """Réinitialise l'état de l'interface"""
        # Réactiver tous les contrôles
        self.prompt_input.setEnabled(True)
        self.generate_button.setEnabled(True)
        self.generate_image_button.setEnabled(True)
        self.texture_button.setEnabled(True)
        self.browse_image_button.setEnabled(True)
        self.save_api_button.setEnabled(True)
        
        # Cacher les éléments de progression
        self.progress_bar.hide()
        self.cancel_button.hide()
        
    def disable_ui_controls(self):
        """Désactive les contrôles pendant le traitement"""
        self.prompt_input.setEnabled(False)
        self.generate_button.setEnabled(False)
        self.generate_image_button.setEnabled(False)
        self.texture_button.setEnabled(False)
        self.browse_image_button.setEnabled(False)
        self.save_api_button.setEnabled(False)

def createInterface():
    """Fonction requise par Houdini pour créer le panel"""
    return MeshyPanel() 