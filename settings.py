import customtkinter as ctk
from PIL import Image
from io import BytesIO
import requests
import os

class SettingsFrame(ctk.CTkFrame): # <-- Cambiado de ScrollableFrame a Frame normal
    def __init__(self, master, api, on_logout):
        # Usamos transparent para que se vea el fondo del contenedor principal
        super().__init__(master, fg_color="transparent")
        self.api = api
        self.on_logout = on_logout
        
        self.username = getattr(api, 'user', "Usuario")
        self.server_url = getattr(api, 'base_url', "Servidor")

        self.setup_ui()

    def setup_ui(self):
        # TÍTULO PRINCIPAL - Con más margen lateral
        ctk.CTkLabel(self, text="Configuración", font=("Arial", 32, "bold")).pack(anchor="w", pady=(30, 40), padx=50)

        # --- SECCIÓN: TU MÚSICA MÁS ESCUCHADA ---
        self._create_section_title("Tu música más escuchada")
        
        # Contenedor de estadísticas - Ahora con fill="x" para que sea ancho
        stats_container = ctk.CTkFrame(self, fg_color="#181818", corner_radius=12)
        stats_container.pack(fill="x", padx=50, pady=10)

        frequent = self.api.get_albums(size=5, type="frequent")
        if frequent:
            for album in frequent:
                self._create_mini_row(stats_container, album)
        else:
            ctk.CTkLabel(stats_container, text="Aún no hay suficientes datos de escucha", text_color="gray", font=("Arial", 13)).pack(pady=30)

        # --- SECCIÓN: CUENTA ---
        self._create_section_title("Cuenta")
        acc_container = ctk.CTkFrame(self, fg_color="#181818", corner_radius=12)
        acc_container.pack(fill="x", padx=50, pady=10)

        self._create_info_row(acc_container, "Usuario conectado", self.username)
        self._create_info_row(acc_container, "URL del servidor", self.server_url)

        # --- SECCIÓN: PREFERENCIAS ---
        self._create_section_title("Preferencias de reproducción")
        pref_container = ctk.CTkFrame(self, fg_color="#181818", corner_radius=12)
        pref_container.pack(fill="x", padx=50, pady=10)
        
        self._create_switch(pref_container, "Normalizar volumen")
        self._create_switch(pref_container, "Autoreproducción", default_on=True)
        self._create_dropdown(pref_container, "Calidad de streaming", ["Alta (320kbps)", "Normal", "Baja"])

        # BOTÓN CERRAR SESIÓN - Separado del fondo
        ctk.CTkButton(
            self, text="Cerrar sesión", fg_color="transparent", border_width=1, 
            border_color="#f15e6c", text_color="#f15e6c", hover_color="#3b1c1e",
            height=40, width=150, font=("Arial", 14, "bold"),
            command=self.logout_action
        ).pack(anchor="w", padx=50, pady=(50, 100))

    # --- FUNCIONES DE CREACIÓN (Ajustadas para ser anchas) ---

    def _create_mini_row(self, parent, album):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=10)
        
        # Intentamos sacar el título: primero buscamos 'name', luego 'title'
        album_name = album.get('name') or album.get('title') or "Álbum Desconocido"
        artist_name = album.get('artist', 'Artista Desconocido')

        # Portada
        img_url = self.api.get_url("getCoverArt.view", f"&id={album['id']}&size=60")
        try:
            img = ctk.CTkImage(Image.open(BytesIO(requests.get(img_url).content)), size=(50, 50))
        except: img = None

        img_lbl = ctk.CTkLabel(row, image=img, text="", width=50)
        img_lbl.pack(side="left")
        img_lbl._image_ref = img # Guardamos referencia para que no se borre
        
        txt_f = ctk.CTkFrame(row, fg_color="transparent")
        txt_f.pack(side="left", padx=20)
        
        # Título del álbum
        ctk.CTkLabel(txt_f, text=album_name, font=("Arial", 15, "bold")).pack(anchor="w")
        # Nombre del artista
        ctk.CTkLabel(txt_f, text=artist_name, font=("Arial", 12), text_color="gray").pack(anchor="w")

    def _create_section_title(self, text):
        ctk.CTkLabel(self, text=text, font=("Arial", 20, "bold")).pack(anchor="w", pady=(35, 15), padx=50)

    def _create_info_row(self, parent, label, value):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=25, pady=15)
        ctk.CTkLabel(f, text=label, font=("Arial", 15), text_color="#b3b3b3").pack(side="left")
        ctk.CTkLabel(f, text=value, font=("Arial", 15, "bold"), text_color="#1DB954").pack(side="right")

    def _create_switch(self, parent, text, default_on=False):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=25, pady=12)
        ctk.CTkLabel(f, text=text, font=("Arial", 15), text_color="#b3b3b3").pack(side="left")
        sw = ctk.CTkSwitch(f, text="", progress_color="#1DB954")
        sw.pack(side="right")
        if default_on: sw.select()

    def _create_dropdown(self, parent, text, values):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=25, pady=12)
        ctk.CTkLabel(f, text=text, font=("Arial", 15), text_color="#b3b3b3").pack(side="left")
        ctk.CTkOptionMenu(f, values=values, fg_color="#282828", button_color="#383838", width=160).pack(side="right")

    def logout_action(self):
        if os.path.exists("config.json"): os.remove("config.json")
        self.on_logout()
