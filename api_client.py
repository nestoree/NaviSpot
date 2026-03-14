import hashlib
import random
import requests

class NavidromeAPI:
    def __init__(self, config):
        self.base_url = config['url']
        self.user = config['user']
        self.password = config['pass']

    def get_auth(self):
        salt = str(random.randint(100, 999))
        token = hashlib.md5((self.password + salt).encode()).hexdigest()
        return f"u={self.user}&t={token}&s={salt}&v=1.16.1&c=pc_app&f=json"

    def get_url(self, endpoint, params=""):
        return f"{self.base_url}/rest/{endpoint}?{self.get_auth()}{params}"

    def get_albums(self, size=40):
        try:
            r = requests.get(self.get_url("getAlbumList.view", f"&type=random&size={size}"), timeout=10)
            data = r.json()
            # Navidrome a veces devuelve el objeto vacío si no hay conexión
            if 'subsonic-response' in data and 'albumList' in data['subsonic-response']:
                return data['subsonic-response']['albumList']['album']
            return []
        except Exception as e:
            print(f"Error cargando álbumes: {e}")
            return []
    
    def get_artist_albums(self, artist_id):
        try:
            r = requests.get(self.get_url("getArtist.view", f"&id={artist_id}"), timeout=10)
            data = r.json()
            album_data = data['subsonic-response']['artist'].get('album', [])
            # Forzar lista si solo viene un álbum
            if isinstance(album_data, dict): return [album_data]
            return album_data
        except Exception as e:
            print(f"Error: {e}"); return []

    def get_artist_image(self, artist_id, size=180):
            # Navidrome usa el mismo endpoint de CoverArt para los artistas usando su ID
            return self.get_url("getArtistInfo.view", f"&id={artist_id}&size={size}")

    def get_artists(self):
            try:
                r = requests.get(self.get_url("getArtists.view"), timeout=10)
                data = r.json()
                # Navegamos por el JSON de Subsonic para llegar a la lista
                return data['subsonic-response']['artists']['index']
            except Exception as e:
                print(f"Error cargando artistas: {e}")
                return []
            
    # ESTA ES LA FUNCIÓN QUE FALTABA:
    def get_album_tracks(self, album_id):
        try:
            r = requests.get(self.get_url("getAlbum.view", f"&id={album_id}"), timeout=10)
            data = r.json()
            return data['subsonic-response']['album']['song']
        except Exception as e:
            print(f"Error cargando canciones del álbum: {e}")
            return []