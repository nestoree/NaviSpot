import customtkinter as ctk

class SidebarFrame(ctk.CTkFrame):
    def __init__(self, master, on_home_click, on_artists_click):
        super().__init__(master, width=220, fg_color="#000000", corner_radius=0)
        self.pack_propagate(False)
        
        ctk.CTkLabel(self, text="NaviSpot", font=("Arial", 24, "bold"), text_color="#1DB954").pack(pady=30, padx=20)

        # Botón Inicio
        self.btn_home = ctk.CTkButton(self, text="🏠  Inicio", font=("Arial", 14, "bold"),
                                      fg_color="transparent", anchor="w", hover_color="#282828",
                                      command=on_home_click)
        self.btn_home.pack(fill="x", padx=10, pady=5)

        # Botón Artistas (Nuevo)
        self.btn_artists = ctk.CTkButton(self, text="👤  Artistas", font=("Arial", 14, "bold"),
                                         fg_color="transparent", anchor="w", hover_color="#282828",
                                         command=on_artists_click)
        self.btn_artists.pack(fill="x", padx=10, pady=5)