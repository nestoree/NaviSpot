import customtkinter as ctk

class SidebarFrame(ctk.CTkFrame):
    # Añadimos on_settings_click a los parámetros
    def __init__(self, master, on_home_click, on_artists_click, on_settings_click):
        super().__init__(master, width=240, fg_color="#000000", corner_radius=0)
        self.pack_propagate(False)

        # Logo
        ctk.CTkLabel(self, text="🎵 NaviSpot", font=("Arial", 24, "bold"), text_color="white").pack(pady=(30, 30), padx=20, anchor="w")

        # Botones Principales
        self.btn_home = ctk.CTkButton(self, text="🏠 Inicio", fg_color="transparent", text_color="white", hover_color="#282828", font=("Arial", 16, "bold"), anchor="w", command=on_home_click)
        self.btn_home.pack(pady=5, padx=15, fill="x")

        self.btn_artists = ctk.CTkButton(self, text="🎤 Artistas", fg_color="transparent", text_color="#b3b3b3", hover_color="#282828", font=("Arial", 16, "bold"), anchor="w", command=on_artists_click)
        self.btn_artists.pack(pady=5, padx=15, fill="x")

        # --- NUEVO: Separador y Botón de Configuración abajo del todo ---
        
        # Un frame vacío que se expande para empujar la configuración hacia abajo
        ctk.CTkFrame(self, fg_color="transparent").pack(expand=True, fill="both")

        self.btn_settings = ctk.CTkButton(self, text="⚙️ Configuración", fg_color="transparent", text_color="#b3b3b3", hover_color="#282828", font=("Arial", 14, "bold"), anchor="w", command=on_settings_click)
        self.btn_settings.pack(pady=20, padx=15, fill="x")
