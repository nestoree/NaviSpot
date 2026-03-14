import customtkinter as ctk
from PIL import Image
from io import BytesIO
import requests
import json
import os
import threading
from pygame import mixer

# --- CONFIGURACIÓN Y MÓDULOS ---
from api_client import NavidromeAPI
from login import LoginFrame
from sidebar import SidebarFrame

CONFIG_FILE = "config.json"

class NaviSpot(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("NaviSpoti")
        self.geometry("1300x850")
        self.configure(fg_color="#121212")
        
        mixer.init()

        self.api = None
        self.playlist = []
        self.current_index = 0
        self.is_shuffled = False
        self.is_repeat = False

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                self.show_main_player(config)
            except:
                self.show_login()
        else:
            self.show_login()

    def show_login(self):
        self.login_view = LoginFrame(self, on_login_success=self.show_main_player)

    def show_main_player(self, config):
        for widget in self.winfo_children():
            widget.destroy()
        
        self.api = NavidromeAPI(config)
        self.setup_ui()
        self.load_content()
        self.update_ui_loop()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. SIDEBAR
        self.sidebar = SidebarFrame(
            self, 
            on_home_click=self.load_content, 
            on_artists_click=self.show_artists
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 2. VISTA DE CONTENIDO (Scroll)
        self.content_view = ctk.CTkScrollableFrame(self, fg_color="#121212", corner_radius=0)
        self.content_view.grid(row=0, column=1, sticky="nsew")
        self.content_view.columnconfigure((0, 1, 2, 3), weight=1)

        # 3. PLAYER BAR
        self.player_bar = ctk.CTkFrame(self, height=110, fg_color="#181818", corner_radius=0)
        self.player_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.player_bar.grid_columnconfigure(0, weight=0, minsize=350)
        self.player_bar.grid_columnconfigure(1, weight=1)
        self.player_bar.grid_columnconfigure(2, weight=0, minsize=350)

        # Info Canción
        self.info_container = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        self.info_container.grid(row=0, column=0, sticky="w", padx=20)
        self.mini_cover = ctk.CTkLabel(self.info_container, text="", width=56, height=56, fg_color="#282828")
        self.mini_cover.pack(side="left", padx=(0, 12))
        self.track_info = ctk.CTkLabel(self.info_container, text="Selecciona música", anchor="w", justify="left", font=("Arial", 12, "bold"))
        self.track_info.pack(side="left")

        # Controles
        self.center_frame = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        self.center_frame.grid(row=0, column=1, sticky="nsew")

        btn_f = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        btn_f.pack(pady=(15, 0))

        self.btn_shuffle = ctk.CTkButton(btn_f, text="🔀", width=40, font=("Arial", 20), fg_color="transparent", command=self.toggle_shuffle)
        self.btn_shuffle.pack(side="left", padx=10)
        ctk.CTkButton(btn_f, text="⏮", width=40, font=("Arial", 18), command=self.prev_song).pack(side="left")
        self.btn_play = ctk.CTkButton(btn_f, text="▶", width=50, height=50, corner_radius=25, fg_color="white", text_color="black", font=("Arial", 18, "bold"), command=self.toggle_playback)
        self.btn_play.pack(side="left", padx=15)
        ctk.CTkButton(btn_f, text="⏭", width=40, font=("Arial", 18), command=self.next_song).pack(side="left")
        self.btn_repeat = ctk.CTkButton(btn_f, text="🔁", width=40, font=("Arial", 20), fg_color="transparent", command=self.toggle_repeat)
        self.btn_repeat.pack(side="left", padx=10)

        # Slider Tiempo
        time_f = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        time_f.pack(fill="x", padx=60)
        self.lbl_now = ctk.CTkLabel(time_f, text="0:00", font=("Arial", 11), text_color="#b3b3b3")
        self.lbl_now.pack(side="left", padx=5)
        self.slider = ctk.CTkSlider(time_f, from_=0, to=100, height=12, progress_color="#1DB954", command=self.seek_track)
        self.slider.pack(side="left", fill="x", expand=True)
        self.lbl_total = ctk.CTkLabel(time_f, text="0:00", font=("Arial", 11), text_color="#b3b3b3")
        self.lbl_total.pack(side="left", padx=5)

        # Volumen
        vol_f = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        vol_f.grid(row=0, column=2, sticky="e", padx=30)
        ctk.CTkLabel(vol_f, text="🔊").pack(side="left", padx=8)
        self.vol_slider = ctk.CTkSlider(vol_f, width=120, from_=0, to=1, command=self.set_volume_log)
        self.vol_slider.pack(side="left")
        self.vol_slider.set(0.6)
        mixer.music.set_volume(0.36)

    # --- LÓGICA DE VISTAS ---

    def load_content(self):
        self._clear_content()
        ctk.CTkLabel(self.content_view, text="Inicio", font=("Arial", 24, "bold")).grid(row=0, column=0, columnspan=4, pady=(20, 10), padx=20, sticky="w")
        
        albums = self.api.get_albums(size=32)
        for i, album in enumerate(albums):
            self._create_album_card(album, (i//4)+1, i%4)

    def _create_album_card(self, album, r, c):
        title = album.get('title') or album.get('name') or "Desconocido"
        img_url = self.api.get_url("getCoverArt.view", f"&id={album['id']}&size=200")
        
        try:
            img = ctk.CTkImage(Image.open(BytesIO(requests.get(img_url).content)), size=(190, 190))
        except: img = None

        card = ctk.CTkFrame(self.content_view, fg_color="transparent")
        card.grid(row=r, column=c, padx=15, pady=20)

        img_btn = ctk.CTkButton(
            card, image=img, text="", 
            width=190, height=190, corner_radius=8,
            fg_color="#181818", hover_color="#282828",
            command=lambda a=album: self.show_album_details(a)
        )
        img_btn.pack()
        img_btn._image_ref = img

        # Botón Play Flotante (Corregido con fondo camuflado)
        play_ov = ctk.CTkButton(
            card, text="▶", width=48, height=48, corner_radius=24,
            fg_color="#1DB954", hover_color="#1ed760", text_color="black",
            font=("Arial", 20, "bold"), border_width=0,
            bg_color="#282828" # Coincide con el hover de la imagen para ocultar el cuadro
        )
        play_ov.configure(command=lambda a=album: self.play_album(a))

        def on_enter(e):
            play_ov.place(relx=0.82, rely=0.68, anchor="center")

        def on_leave(e):
            # Verificamos si realmente salimos de la tarjeta
            x, y = self.winfo_pointerxy()
            widget = self.winfo_containing(x, y)
            if widget not in [img_btn, play_ov]:
                play_ov.place_forget()

        img_btn.bind("<Enter>", on_enter)
        img_btn.bind("<Leave>", on_leave)
        play_ov.bind("<Leave>", on_leave)

        ctk.CTkLabel(card, text=self.truncate_text(title, 20), font=("Arial", 13, "bold")).pack(pady=(8,0))
        ctk.CTkLabel(card, text=self.truncate_text(album.get('artist', ''), 22), font=("Arial", 11), text_color="gray").pack()

    def show_album_details(self, album):
        self._clear_content()
        header = ctk.CTkFrame(self.content_view, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=30)
        
        img_url = self.api.get_url("getCoverArt.view", f"&id={album['id']}&size=300")
        try:
            img = ctk.CTkImage(Image.open(BytesIO(requests.get(img_url).content)), size=(230, 230))
        except: img = None
        
        ctk.CTkLabel(header, image=img, text="").pack(side="left", padx=(0, 25))
        info = ctk.CTkFrame(header, fg_color="transparent")
        info.pack(side="left", fill="y")
        ctk.CTkLabel(info, text="ÁLBUM", font=("Arial", 12, "bold")).pack(anchor="w")
        ctk.CTkLabel(info, text=album.get('title') or album.get('name'), font=("Arial", 42, "bold")).pack(anchor="w")
        ctk.CTkLabel(info, text=f"{album.get('artist')} • {album.get('year', '')}", font=("Arial", 14, "bold")).pack(anchor="w", pady=10)

        actions = ctk.CTkFrame(self.content_view, fg_color="transparent")
        actions.pack(fill="x", padx=30, pady=10)
        ctk.CTkButton(actions, text="▶", width=56, height=56, corner_radius=28, fg_color="#1DB954", text_color="black", font=("Arial", 22), command=lambda a=album: self.play_album(a)).pack(side="left")
        ctk.CTkButton(actions, text="Volver", width=100, command=self.load_content).pack(side="left", padx=20)

        tracks = self.api.get_album_tracks(album['id'])
        for i, track in enumerate(tracks):
            t_f = ctk.CTkFrame(self.content_view, fg_color="transparent", height=45)
            t_f.pack(fill="x", padx=30, pady=2)
            btn = ctk.CTkButton(t_f, text="", fg_color="transparent", hover_color="#2a2a2a", command=lambda idx=i, tl=tracks: self._play_specific_track(idx, tl))
            btn.place(relwidth=1, relheight=1)
            ctk.CTkLabel(t_f, text=str(i+1), width=30, text_color="gray").pack(side="left", padx=10)
            ctk.CTkLabel(t_f, text=track['title'], font=("Arial", 13)).pack(side="left")
            dur = track.get('duration', 0)
            ctk.CTkLabel(t_f, text=f"{dur//60}:{dur%60:02d}", text_color="gray").pack(side="right", padx=20)

    def show_artists(self):
        self._clear_content()
        ctk.CTkLabel(self.content_view, text="Artistas", font=("Arial", 24, "bold")).grid(row=0, column=0, pady=20, padx=20, sticky="w")
        
        def task():
            idx = self.api.get_artists()
            all_a = [a for i in idx for a in i['artist']]
            all_a.sort(key=lambda x: x['name'].lower())
            self.after(0, lambda: self._render_artist_list(all_a))
        threading.Thread(target=task).start()

    def _render_artist_list(self, artists):
        row, col = 1, 0
        for artist in artists:
            card = ctk.CTkFrame(self.content_view, fg_color="transparent")
            card.grid(row=row, column=col, padx=15, pady=20)
            img_url = self.api.get_url("getCoverArt.view", f"&id={artist['id']}&size=170")
            try:
                img = ctk.CTkImage(Image.open(BytesIO(requests.get(img_url).content)), size=(170, 170))
            except: img = None
            btn = ctk.CTkButton(card, image=img, text="", width=170, height=170, fg_color="transparent", corner_radius=85, command=lambda a=artist: self.load_artist_albums(a))
            btn.pack(); btn._image_ref = img 
            ctk.CTkLabel(card, text=self.truncate_text(artist['name'], 18), font=("Arial", 13, "bold")).pack(pady=8)
            col += 1
            if col > 3: col = 0; row += 1

    def load_artist_albums(self, artist):
        self._clear_content()
        ctk.CTkButton(self.content_view, text="← Volver", command=self.show_artists).pack(pady=10, padx=20, anchor="w")
        albums = self.api.get_artist_albums(artist['id'])
        grid_f = ctk.CTkFrame(self.content_view, fg_color="transparent")
        grid_f.pack(fill="both", expand=True)
        for i, album in enumerate(albums):
            self._create_album_card_in_artist(album, grid_f, i//4, i%4)

    def _create_album_card_in_artist(self, album, parent, r, c):
        title = album.get('title') or album.get('name') or "Desconocido"
        img_url = self.api.get_url("getCoverArt.view", f"&id={album['id']}&size=180")
        try:
            img = ctk.CTkImage(Image.open(BytesIO(requests.get(img_url).content)), size=(180, 180))
        except: img = None
        card = ctk.CTkFrame(parent, fg_color="transparent")
        card.grid(row=r, column=c, padx=15, pady=20)
        btn = ctk.CTkButton(card, image=img, text="", fg_color="transparent", command=lambda a=album: self.show_album_details(a))
        btn.pack(); btn._image_ref = img 
        ctk.CTkLabel(card, text=self.truncate_text(title, 20), font=("Arial", 13, "bold")).pack()

    # --- REPRODUCCIÓN ---

    def play_album(self, album):
        self.playlist = self.api.get_album_tracks(album['id'])
        if self.playlist:
            self.current_index = 0
            self.play_track()

    def _play_specific_track(self, index, track_list):
        self.playlist = track_list
        self.current_index = index
        self.play_track()

    def play_track(self):
        track = self.playlist[self.current_index]
        self.track_info.configure(text=f"{track['title'][:22]}\n{track['artist'][:25]}")
        url = self.api.get_url("getCoverArt.view", f"&id={track['id']}&size=60")
        try:
            img = ctk.CTkImage(Image.open(BytesIO(requests.get(url).content)), size=(56,56))
            self.mini_cover.configure(image=img); self.mini_cover._image_ref = img
        except: pass

        audio_url = self.api.get_url("stream.view", f"&id={track['id']}")
        with open("temp_song.mp3", "wb") as f: f.write(requests.get(audio_url).content)
        mixer.music.load("temp_song.mp3")
        mixer.music.play()
        self.btn_play.configure(text="⏸")
        dur = track.get('duration', 0)
        self.slider.configure(to=dur); self.slider.set(0)
        self.lbl_total.configure(text=f"{dur//60}:{dur%60:02d}")

    def toggle_playback(self):
        if not self.playlist: return
        if self.btn_play.cget("text") == "⏸":
            mixer.music.pause(); self.btn_play.configure(text="▶")
        else:
            mixer.music.unpause(); self.btn_play.configure(text="⏸")

    def seek_track(self, val):
        if self.playlist:
            mixer.music.play(start=float(val))

    def update_ui_loop(self):
        if mixer.music.get_busy() and self.btn_play.cget("text") == "⏸":
            pos = self.slider.get() + 1
            if pos <= self.slider.cget("to"):
                self.slider.set(pos)
                self.lbl_now.configure(text=f"{int(pos)//60}:{int(pos)%60:02d}")
        
        if not mixer.music.get_busy() and self.playlist and self.btn_play.cget("text") == "⏸":
            if self.slider.get() >= self.slider.cget("to") - 2:
                if self.is_repeat: self.play_track()
                else: self.next_song()
        self.after(1000, self.update_ui_loop)

    def next_song(self):
        if not self.playlist: return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play_track()

    def prev_song(self):
        if not self.playlist: return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.play_track()

    def toggle_shuffle(self):
        self.is_shuffled = not self.is_shuffled
        self.btn_shuffle.configure(text_color="#1DB954" if self.is_shuffled else "white")

    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat
        self.btn_repeat.configure(text_color="#1DB954" if self.is_repeat else "white")

    def set_volume_log(self, val): mixer.music.set_volume(float(val)**2)
    def truncate_text(self, t, m): return t[:m]+"..." if len(t)>m else t
    def _clear_content(self):
        for widget in self.content_view.winfo_children(): widget.destroy()

if __name__ == "__main__":
    app = NaviSpot(); app.mainloop()