import customtkinter as ctk
import requests
import json
import os
from api_client import NavidromeAPI

CONFIG_FILE = "config.json"

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_login_success):
        super().__init__(master, fg_color="#121212")
        self.on_login_success = on_login_success
        self.pack(expand=True, fill="both")

        # UI
        ctk.CTkLabel(self, text="NaviSpot", font=("Arial", 32, "bold"), text_color="#1DB954").pack(pady=40)
        
        self.url_entry = ctk.CTkEntry(self, placeholder_text="URL del Servidor", width=300)
        self.url_entry.pack(pady=10)
        self.user_entry = ctk.CTkEntry(self, placeholder_text="Usuario", width=300)
        self.user_entry.pack(pady=10)
        self.pass_entry = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*", width=300)
        self.pass_entry.pack(pady=10)

        ctk.CTkButton(self, text="INICIAR SESIÓN", fg_color="#1DB954", text_color="black", 
                       font=("Arial", 14, "bold"), command=self.validate_login).pack(pady=30)
        
        self.error_lbl = ctk.CTkLabel(self, text="", text_color="red")
        self.error_lbl.pack()

    def validate_login(self):
        config = {
            "url": self.url_entry.get().rstrip('/'),
            "user": self.user_entry.get(),
            "pass": self.pass_entry.get()
        }
        test_api = NavidromeAPI(config)
        try:
            r = requests.get(test_api.get_url("ping.view"), timeout=5).json()
            if r['subsonic-response']['status'] == 'ok':
                with open(CONFIG_FILE, "w") as f:
                    json.dump(config, f)
                self.on_login_success(config)
            else:
                self.error_lbl.configure(text="Credenciales incorrectas")
        except:
            self.error_lbl.configure(text="Error de conexión")