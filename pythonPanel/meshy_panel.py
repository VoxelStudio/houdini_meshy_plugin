"""
Module principal du panel Python pour Meshy dans Houdini
"""

import os
import hou
from PySide2 import QtWidgets, QtCore
from typing import Optional

from .meshy_api import MeshyAPI

class MeshyPanel(QtWidgets.QWidget):
    """Panel principal pour l'interface Meshy"""
    
    def __init__(self):
        super().__init__()
        self.api = MeshyAPI()
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
        save_api_btn = QtWidgets.QPushButton("Sauvegarder")
        save_api_btn.clicked.connect(self.save_api_key)
        api_key_layout.addWidget(save_api_btn)
        
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
        
        # Ajouter une ligne de séparation
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line)
        
        # Groupe Text-to-3D
        text_group = QtWidgets.QGroupBox("Text to 3D")
        text_layout = QtWidgets.QVBoxLayout()
        
        # Zone de texte pour le prompt
        self.prompt_input = QtWidgets.QTextEdit()
        self.prompt_input.setPlaceholderText("Entrez votre description...")
        self.prompt_input.setMaximumHeight(100)
        text_layout.addWidget(self.prompt_input)
        
        # Bouton de génération
        generate_text_btn = QtWidgets.QPushButton("Générer depuis le texte")
        generate_text_btn.clicked.connect(self.text_to_3d_clicked)
        text_layout.addWidget(generate_text_btn)
        
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
        browse_btn = QtWidgets.QPushButton("Parcourir")
        browse_btn.clicked.connect(self.browse_image)
        image_path_layout.addWidget(browse_btn)
        
        image_layout.addLayout(image_path_layout)
        
        # Bouton de génération depuis l'image
        generate_image_btn = QtWidgets.QPushButton("Générer depuis l'image")
        generate_image_btn.clicked.connect(self.generate_from_image)
        image_layout.addWidget(generate_image_btn)
        
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
        texture_btn = QtWidgets.QPushButton("Texturer la géométrie")
        texture_btn.clicked.connect(self.texture_selected_geometry)
        texture_layout.addWidget(texture_btn)

        texture_group.setLayout(texture_layout)
        layout.addWidget(texture_group)
        
        # Zone de statut
        self.status_label = QtWidgets.QLabel("Prêt")
        layout.addWidget(self.status_label)
        
        # Barre de progression
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
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
            # Récupérer le contexte du nœud actuel
            node_context = hou.node("/obj")
            
            # Lancer la génération et l'import
            self.api.text_to_3d_houdini(prompt, node_context)
            
        except Exception as e:
            self.show_error(f"Erreur lors de la génération : {str(e)}")
            
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
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Mode indéterminé
            
            # Appel à l'API
            response = self.api.image_to_3d(image_path)
            
            # TODO: Gérer la réponse et l'importation
            # Cette partie sera développée plus tard
            
            self.status_label.setText("Génération réussie!")
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            self.status_label.setText(f"Erreur: {str(e)}")
            self.progress_bar.setVisible(False)
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
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            # Envoyer à Meshy
            response = self.api.texture_geometry(
                temp_file,
                prompt=prompt if prompt else None,
                style=style
            )
            
            # TODO: Gérer la réponse et appliquer les textures
            # Cette partie sera développée plus tard
            
            self.status_label.setText("Texturation réussie!")
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            self.status_label.setText(f"Erreur: {str(e)}")
            self.progress_bar.setVisible(False)
            QtWidgets.QMessageBox.critical(
                self,
                "Erreur",
                f"Une erreur est survenue: {str(e)}"
            )

def createInterface():
    """Fonction requise par Houdini pour créer le panel"""
    return MeshyPanel() 