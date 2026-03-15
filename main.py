import customtkinter as ctk
from PIL import Image
from io import BytesIO
import requests
import json
import os
import threading
import time
from pygame import mixer
import random

# --- CONFIGURACIÓN Y MÓDULOS ---
from api_client import NavidromeAPI
from login import LoginFrame
from sidebar import SidebarFrame
from profile import ProfileFrame
from settings import SettingsFrame

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
        self.current_playlist = []
        self.track_duration = 0
        self.current_cover_img = None
        self.slider_updating = False
        self.slider_dragging = False
        self.playback_position_offset = 0
        self.volume_syncing = False
        self.shuffle_history = []
        self.search_var = ctk.StringVar()

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.show_main_player(config)
            except Exception:
                self.show_login()
        else:
            self.show_login()

    def show_login(self):
        self.login_view = LoginFrame(self, on_login_success=self.show_main_player)

    def show_main_player(self, config):
        for widget in self.winfo_children():
            widget.destroy()
        self.config = config
        self.api = NavidromeAPI(self.config)
        self.setup_ui()
        self.load_content()
        self.restore_playback_state()
        self.update_ui_loop()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. SIDEBAR
        self.sidebar = SidebarFrame(
            self, 
            on_home_click=self.load_content, 
            on_artists_click=self.show_artists,
            on_settings_click=self.show_settings # <- Añade esta línea
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
        info_text_frame = ctk.CTkFrame(self.info_container, fg_color="transparent")
        info_text_frame.pack(side="left", fill="both", expand=True)
        self.track_title_label = ctk.CTkLabel(
            info_text_frame,
            text="Selecciona música",
            anchor="w",
            justify="left",
            font=("Arial", 12, "bold"),
            wraplength=250,
            width=270
        )
        self.track_title_label.pack(anchor="w")
        self.track_artist_label = ctk.CTkLabel(
            info_text_frame,
            text=" ",
            anchor="w",
            font=("Arial", 11),
            text_color="#b3b3b3"
        )
        self.track_artist_label.pack(anchor="w", pady=(2, 0))

        # Controles
        self.center_frame = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        self.center_frame.grid(row=0, column=1, sticky="nsew")

        btn_f = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        btn_f.pack(pady=(15, 0))
        button_style = dict(
            width=44,
            height=44,
            corner_radius=22,
            fg_color="transparent",
            hover_color="#282828",
            border_width=1,
            border_color="#2f2f2f",
            text_color="#d0d0d0",
            font=("Arial", 18)
        )
        self.btn_shuffle = ctk.CTkButton(btn_f, text="🔀", **button_style, command=self.toggle_shuffle)
        self.btn_shuffle.pack(side="left", padx=8)
        ctk.CTkButton(btn_f, text="⏮", command=self.prev_song, **button_style).pack(side="left", padx=8)
        self.btn_play = ctk.CTkButton(
            btn_f,
            text="▶",
            width=58,
            height=58,
            corner_radius=29,
            fg_color="#1DB954",
            text_color="black",
            font=("Arial", 22, "bold"),
            command=self.toggle_playback
        )
        self.btn_play.pack(side="left", padx=10)
        ctk.CTkButton(btn_f, text="⏭", command=self.next_song, **button_style).pack(side="left", padx=8)
        self.btn_repeat = ctk.CTkButton(btn_f, text="🔁", **button_style, command=self.toggle_repeat)
        self.btn_repeat.pack(side="left", padx=8)

        # Slider Tiempo
        time_f = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        time_f.pack(fill="x", padx=60)
        self.lbl_now = ctk.CTkLabel(time_f, text="0:00", font=("Arial", 11), text_color="#b3b3b3")
        self.lbl_now.pack(side="left", padx=5)
        self.slider = ctk.CTkSlider(time_f, from_=0, to=100, height=12, progress_color="#1DB954", command=self.on_slider_move)
        self.slider.pack(side="left", fill="x", expand=True)
        self.slider.bind("<ButtonPress-1>", self.on_slider_press)
        self.slider.bind("<ButtonRelease-1>", self.on_slider_release)
        self.lbl_total = ctk.CTkLabel(time_f, text="0:00", font=("Arial", 11), text_color="#b3b3b3")
        self.lbl_total.pack(side="left", padx=5)

        # Volumen
        vol_f = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        vol_f.grid(row=0, column=2, sticky="e", padx=30)
        ctk.CTkLabel(vol_f, text="🔊").pack(side="left", padx=8)
        self.vol_slider = ctk.CTkSlider(vol_f, width=120, from_=0, to=1, command=self.set_volume_log)
        self.vol_slider.pack(side="left")
        self.apply_saved_volume()

    # --- LÓGICA DE VISTAS ---

    def show_profile(self):
        """Muestra la vista de configuración del perfil"""
        self._clear_content()
        # Necesitamos pasarle el self.api.config para que lea el usuario y URL
        profile_view = ProfileFrame(self.content_view, config=self.api.config, on_logout=self.logout)
        profile_view.pack(fill="both", expand=True)

    def logout(self):
        """Cierra sesión, detiene la música y vuelve al login"""
        mixer.music.stop()
        for widget in self.winfo_children():
            widget.destroy()
        self.api = None
        self.show_login()

    def load_content(self, search_query=None):
        self._clear_content()
        self._render_search_bar()

        header_text = f"Resultados para \"{search_query}\"" if search_query else "Inicio"
        ctk.CTkLabel(
            self.content_view,
            text=header_text,
            font=("Arial", 24, "bold")
        ).grid(row=1, column=0, columnspan=4, pady=(0, 10), padx=20, sticky="w")

        if search_query:
            albums = self.api.search_albums(search_query, size=32)
        else:
            albums = self.api.get_albums(size=32)
        albums = self._sort_albums(albums)
        self._render_album_grid(albums, start_row=2)

    def _render_search_bar(self):
        bar = ctk.CTkFrame(self.content_view, fg_color="#1a1a1a", corner_radius=18, border_width=1, border_color="#282828")
        bar.grid(row=0, column=0, columnspan=4, sticky="ew", padx=20, pady=(20, 10))
        bar.grid_columnconfigure(0, weight=1)

        search_entry = ctk.CTkEntry(
            bar,
            textvariable=self.search_var,
            placeholder_text="Buscar álbum...",
            fg_color="#111111",
            border_color="#2e2e2e",
            corner_radius=14
        )
        search_entry.grid(row=0, column=0, sticky="ew", padx=(16, 8), pady=10)
        search_entry.bind("<Return>", lambda _: self.execute_search())

        ctk.CTkButton(bar, text="Buscar", width=110, command=self.execute_search).grid(row=0, column=1, padx=(0, 8), pady=10)
        ctk.CTkButton(bar, text="Ver todo", width=90, fg_color="transparent", border_width=1, command=lambda: self.execute_search(clear=True)).grid(row=0, column=2, padx=(0, 12), pady=10)

    def _render_album_grid(self, albums, start_row=2):
        for i, album in enumerate(albums):
            row = start_row + (i // 4)
            col = i % 4
            self._create_album_card(album, row, col)

    def execute_search(self, clear=False, *_):
        if clear:
            self.search_var.set("")
        query = self.search_var.get().strip()
        if clear or not query:
            self.load_content()
        else:
            self.load_content(search_query=query)

    def _sort_albums(self, albums):
        try:
            return sorted(albums, key=lambda album: (album.get("name") or album.get("title") or "").lower())
        except Exception:
            return albums

    def show_settings(self):
        self._clear_content()
        # Importante: Pasar el objeto API y usar pack expansivo
        settings_view = SettingsFrame(
            self.content_view, 
            api=self.api, 
            on_logout=self.logout
        )
        # El fill="both" y expand=True son vitales aquí
        settings_view.pack(fill="both", expand=True, padx=20)

    def logout(self):
        """Cierra sesión, detiene la música y vuelve al login"""
        mixer.music.stop()
        for widget in self.winfo_children():
            widget.destroy()
        self.api = None
        self.show_login()

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
        header.pack(fill="x", padx=30, pady=20)
        header.grid_columnconfigure(1, weight=1)

        cover_id = album.get('coverArt') or album.get('id')
        cover_img = self.fetch_cover_image(cover_id, size=200)
        cover_label = ctk.CTkLabel(
            header,
            image=cover_img,
            text="",
            width=200,
            height=200,
            fg_color="#1d1d1d",
            corner_radius=12
        )
        if cover_img:
            cover_label._image_ref = cover_img
        cover_label.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 24))

        info_frame = ctk.CTkFrame(header, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="nw")
        ctk.CTkLabel(
            info_frame,
            text=album.get('name') or album.get('title'),
            font=("Arial", 28, "bold"),
            anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            info_frame,
            text=album.get('artist'),
            font=("Arial", 18),
            text_color="gray",
            anchor="w"
        ).pack(anchor="w")

        tracks = self.api.get_tracks(album['id'])

        for i, track in enumerate(tracks):
            track_frame = ctk.CTkFrame(self.content_view, fg_color="transparent")
            track_frame.pack(fill="x", padx=20, pady=4)
            track_frame.grid_columnconfigure(1, weight=1)

            play_btn = ctk.CTkButton(
                track_frame,
                text="▶",
                width=36,
                height=36,
                corner_radius=18,
                fg_color="#1DB954",
                text_color="black",
                hover_color="#1ed760",
                command=lambda t=track: self.play_single_track(t, tracks)
            )
            play_btn.grid(row=0, column=0, padx=(0, 12), pady=8)

            ctk.CTkLabel(
                track_frame,
                text=f"{i+1}. {track.get('title')}",
                font=("Arial", 13),
                anchor="w",
                justify="left"
            ).grid(row=0, column=1, sticky="w")

    def show_artists(self):
        self._clear_content()
        ctk.CTkLabel(self.content_view, text="Artistas", font=("Arial", 24, "bold")).grid(row=0, column=0, pady=20, padx=20, sticky="w")
        
        def task():
            idx = self.api.get_artists()
            all_a = [a for i in idx for a in i['artist']]
            all_a.sort(key=lambda x: x['name'].lower())
            self.after(0, lambda: self._render_artist_list(all_a))
        threading.Thread(target=task).start()

    def play_single_track(self, track, playlist):
        self.current_playlist = playlist
        self.playlist = playlist
        self.current_index = next((i for i, t in enumerate(playlist) if t['id'] == track['id']), 0)
        self.current_track_id = track['id']
        self.play_track()

    def _render_artist_list(self, artists):
        row, col = 1, 0
        for artist in artists:
            card = ctk.CTkFrame(
                self.content_view,
                fg_color="#1a1a1a",
                corner_radius=24,
                border_width=1,
                border_color="#292929"
            )
            card.configure(width=260)
            card.grid_propagate(False)
            card.grid(row=row, column=col, padx=15, pady=14, sticky="nsew")
            card.grid_rowconfigure(1, weight=1)

            img_url = self.api.get_url("getCoverArt.view", f"&id={artist['id']}&size=200")
            try:
                img = ctk.CTkImage(Image.open(BytesIO(requests.get(img_url, timeout=5).content)), size=(180, 180))
            except Exception:
                img = None

            cover_holder = ctk.CTkFrame(
                card,
                fg_color="#111111",
                corner_radius=20,
                width=220,
                height=220
            )
            cover_holder.pack(padx=20, pady=(18, 8))
            cover_holder.pack_propagate(False)

            btn = ctk.CTkButton(
                cover_holder,
                image=img,
                text="",
                width=220,
                height=220,
                fg_color="transparent",
                hover_color="#1e1e1e",
                border_width=0,
                corner_radius=24,
                command=lambda a=artist: self.load_artist_albums(a)
            )
            btn.pack(expand=True, fill="both")
            if img:
                btn._image_ref = img

            ctk.CTkLabel(
                card,
                text=self.truncate_text(artist['name'], 24),
                font=("Arial", 14, "bold"),
                text_color="white"
            ).pack(padx=20, pady=(4, 0), anchor="w")

            ctk.CTkLabel(
                card,
                text="Ver discografía",
                font=("Arial", 11),
                text_color="#b1b1b1"
            ).pack(padx=20, pady=(0, 12), anchor="w")

            col += 1
            if col > 3:
                col = 0
                row += 1

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

    def fetch_cover_image(self, cover_id, size=200):
        if not cover_id: return None
        try:
            url = self.api.get_url("getCoverArt.view", f"&id={cover_id}&size={size}")
            response = requests.get(url, timeout=5)
            return ctk.CTkImage(Image.open(BytesIO(response.content)), size=(size, size))
        except Exception:
            return None

    # --- REPRODUCCIÓN ---

    def play_album(self, album):
        # Ahora sí, llamamos al método que acabamos de crear
        tracks = self.api.get_tracks(album['id'])
        
        if tracks:
            # Guardamos la lista y ponemos la primera canción
            self.current_playlist = tracks
            self.shuffle_history.clear()
            self.playlist = tracks
            self.current_index = 0
            self.current_track_id = tracks[0]['id']
            self.play_track()
        else:
            print("No se encontraron canciones en este álbum.")

    def _play_specific_track(self, index, track_list):
        self.current_playlist = track_list
        self.shuffle_history.clear()
        self.playlist = track_list
        self.current_index = index
        self.current_track_id = track_list[index]['id']
        self.play_track()

    def play_track(self, resume=False):
        if not self.current_track_id: return

        try:
            mixer.music.stop()
            mixer.music.unload()
            
            audio_url = self.api.get_url("stream.view", f"&id={self.current_track_id}")
            response = requests.get(audio_url)
            
            with open("temp_song.mp3", "wb") as f:
                f.write(response.content)
            
            mixer.music.load("temp_song.mp3")
            mixer.music.play()
            if resume and self.playback_position_offset > 0:
                try:
                    mixer.music.set_pos(self.playback_position_offset)
                except Exception:
                    pass
            else:
                self.playback_position_offset = 0
            self.btn_play.configure(text="⏸")

            self.playlist = self.current_playlist
            track_data = next((t for t in self.current_playlist if t['id'] == self.current_track_id), None)
            if track_data:
                self.refresh_player_info(track_data, position=self.playback_position_offset)

        except Exception as e:
            print(f"❌ Error en play_track: {e}")

    def toggle_playback(self):
        if not self.playlist: return
        if self.btn_play.cget("text") == "⏸":
            mixer.music.pause()
            self.btn_play.configure(text="▶")
            self.save_playback_position()
        else:
            if not mixer.music.get_busy():
                self.play_track(resume=True)
            else:
                mixer.music.unpause()
                self.btn_play.configure(text="⏸")

    def on_slider_move(self, val):
        if self.slider_updating or self.slider_dragging:
            return
        try:
            position = float(val)
        except ValueError:
            return
        self.lbl_now.configure(text=self.format_time(int(position)))

    def on_slider_press(self, _event):
        self.slider_dragging = True

    def on_slider_release(self, _event):
        self.slider_dragging = False
        self.seek_track(self.slider.get())

    def seek_track(self, val):
        if self.slider_updating or not self.current_track_id:
            return
        try:
            position = float(val)
        except ValueError:
            return
        self.playback_position_offset = position
        self.config['last_position'] = float(position)
        self.persist_config()
        was_paused = self.btn_play.cget("text") == "▶"
        mixer.music.stop()
        mixer.music.play(start=0.0)
        try:
            mixer.music.set_pos(position)
        except Exception:
            pass
        if was_paused:
            mixer.music.pause()
            self.btn_play.configure(text="▶")
        else:
            self.btn_play.configure(text="⏸")
        self._update_slider_position(position)

    def update_ui_loop(self):
        if mixer.music.get_busy():
            pos_ms = mixer.music.get_pos()
            if pos_ms >= 0:
                slider_to = self.slider.cget("to")
                pos = self.playback_position_offset + (pos_ms / 1000)
                if slider_to > 0 and pos <= slider_to and not self.slider_dragging:
                    self.slider_updating = True
                    self.slider.set(pos)
                    self.slider_updating = False
                self.lbl_now.configure(text=self.format_time(int(pos)))
        
        if not mixer.music.get_busy() and self.playlist and self.btn_play.cget("text") == "⏸":
            slider_to = self.slider.cget("to")
            if self.slider.get() >= max(slider_to - 0.5, 0):
                if self.is_repeat: self.play_track()
                else: self.next_song()
        self.after(1000, self.update_ui_loop)

    def next_song(self):
        if not self.playlist: return
        if self.is_shuffled and len(self.playlist) > 1:
            self.shuffle_history.append(self.current_index)
            next_index = random.randrange(len(self.playlist))
            while next_index == self.current_index:
                next_index = random.randrange(len(self.playlist))
            self.current_index = next_index
        else:
            self.current_index = (self.current_index + 1) % len(self.playlist)
        self.current_track_id = self.playlist[self.current_index]['id']
        self.play_track()

    def prev_song(self):
        if not self.playlist: return
        if self.is_shuffled and self.shuffle_history:
            self.current_index = self.shuffle_history.pop()
        else:
            self.current_index = (self.current_index - 1) % len(self.playlist)
        self.current_track_id = self.playlist[self.current_index]['id']
        self.play_track()

    def toggle_shuffle(self):
        self.is_shuffled = not self.is_shuffled
        self.btn_shuffle.configure(text_color="#1DB954" if self.is_shuffled else "#b3b3b3")
        if not self.is_shuffled:
            self.shuffle_history.clear()

    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat
        self.btn_repeat.configure(text_color="#1DB954" if self.is_repeat else "white")

    def set_volume_log(self, val):
        if self.volume_syncing:
            return
        try:
            volume = float(val)
        except ValueError:
            return
        mixer.music.set_volume(volume ** 2)
        self.config['volume'] = volume
        self.persist_config()

    def apply_saved_volume(self):
        if not self.config:
            saved = 0.6
        else:
            saved = self.config.get("volume", 0.6)
        self.volume_syncing = True
        self.vol_slider.set(saved)
        mixer.music.set_volume(saved ** 2)
        self.volume_syncing = False
        if self.config.get("volume") != saved:
            self.config['volume'] = saved
            self.persist_config()

    def truncate_text(self, t, m): return t[:m]+"..." if len(t)>m else t

    def _clear_content(self):
        for widget in self.content_view.winfo_children():
            widget.destroy()

    def persist_config(self):
        if not self.config:
            return
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando config: {e}")

    def restore_playback_state(self):
        try:
            track_info = self.config.get("last_track")
            if not track_info:
                return
            album_id = track_info.get("albumId") or track_info.get("album_id")
            if not album_id:
                return
            tracks = self.api.get_tracks(album_id)
            if not tracks:
                return
            self.current_playlist = tracks
            self.playlist = tracks
            track_id = track_info.get("id")
            self.current_index = next((i for i, t in enumerate(tracks) if t['id'] == track_id), 0)
            self.current_track_id = track_id
            self.playback_position_offset = float(self.config.get("last_position", 0))
            self.refresh_player_info(
                tracks[self.current_index],
                position=self.playback_position_offset,
                save_state=False
            )
            self.btn_play.configure(text="▶")
        except Exception as exc:
            print(f"📀 No se pudo restaurar estado de reproducción: {exc}")

    def _update_slider_position(self, position):
        slider_to = self.slider.cget("to")
        safe_pos = max(0, min(position or 0, slider_to or 0))
        self.slider_updating = True
        self.slider.set(safe_pos)
        self.slider_updating = False
        self.playback_position_offset = safe_pos
        self.lbl_now.configure(text=self.format_time(int(safe_pos)))
        self.lbl_total.configure(text=self.format_time(self.track_duration))

    def save_playback_position(self):
        self.playback_position_offset = self.slider.get()
        self.config['last_position'] = float(self.playback_position_offset)
        self.persist_config()

    def refresh_player_info(self, track_data, position=0, save_state=True):
        title = track_data.get('title', 'Desconocido')
        artist = track_data.get('artist', 'Artista')
        self.track_title_label.configure(text=self.truncate_text(title, 28))
        self.track_artist_label.configure(text=self.truncate_text(artist, 24))

        cover_id = track_data.get('coverArt') or track_data.get('albumId')
        if cover_id:
            try:
                cover_url = self.api.get_url("getCoverArt.view", f"&id={cover_id}&size=200")
                cover_img = ctk.CTkImage(Image.open(BytesIO(requests.get(cover_url, timeout=5).content)), size=(56, 56))
                self.mini_cover.configure(image=cover_img, text="")
                self.current_cover_img = cover_img
            except Exception:
                self.mini_cover.configure(image=None, text="")
        else:
            self.mini_cover.configure(image=None, text="")

        duration_value = track_data.get('duration') or track_data.get('seconds') or track_data.get('time')
        self.track_duration = self.parse_duration(duration_value)
        slider_max = self.track_duration if self.track_duration > 0 else 1
        self.slider.configure(from_=0, to=slider_max)
        self._update_slider_position(position)

        if save_state:
            self.config['last_track'] = {
                "id": track_data.get('id'),
                "albumId": track_data.get('albumId'),
                "title": track_data.get('title'),
                "artist": track_data.get('artist')
            }
            self.config['last_position'] = float(self.playback_position_offset)
            self.persist_config()

    def format_time(self, seconds):
        seconds = int(seconds or 0)
        minutes, secs = divmod(seconds, 60)
        return f"{minutes}:{secs:02d}"

    def parse_duration(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

if __name__ == "__main__":
    app = NaviSpot(); app.mainloop()
