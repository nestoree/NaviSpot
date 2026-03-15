import hashlib
import random
import requests
from urllib.parse import quote

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

    def get_albums(self, size=40, type="random"):
        try:
            # Ahora usamos el parámetro 'type' en la URL
            url = self.get_url("getAlbumList2.view", f"&type={type}&size={size}")
            r = requests.get(url, timeout=10)
            data = r.json()
            
            if 'subsonic-response' in data and 'albumList2' in data['subsonic-response']:
                # Si no hay álbumes de ese tipo, 'album' no existirá en la respuesta
                return data['subsonic-response']['albumList2'].get('album', [])
            return []
        except Exception as e:
            print(f"Error cargando álbumes ({type}): {e}")
            return []

    def search_albums(self, query, size=40):
        if not query:
            return []
        try:
            encoded = quote(query)
            url = self.get_url("search2.view", f"&query={encoded}&albumCount={size}")
            r = requests.get(url, timeout=10)
            data = r.json()
            search_result = data['subsonic-response'].get('searchResult2', {})
            albums = search_result.get('album', [])
            if isinstance(albums, dict):
                return [albums]
            return albums or []
        except Exception as e:
            print(f"Error buscando álbumes: {e}")
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

    def get_top_songs(self, size=5):
        # 'frequent' devuelve lo más escuchado en la API de Subsonic
        return self._make_request("getAlbumList2.view", f"&type=frequent&size={size}")

    def get_top_artists(self, size=5):
        # Obtenemos artistas y los ordenamos por importancia o frecuencia si el servidor lo soporta
        # Nota: Algunos servidores requieren lógica extra, pero 'getTopSongs' es el estándar
        res = self._make_request("getTopSongs.view", f"&count={size}")
        return res if res else []

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
    def get_tracks(self, album_id):
        try:
            # Usamos getAlbum.view para obtener los detalles de un álbum y sus canciones
            r = requests.get(self.get_url("getAlbum.view", f"&id={album_id}"), timeout=10)
            data = r.json()
            
            if 'subsonic-response' in data and 'album' in data['subsonic-response']:
                # Navidrome devuelve las canciones dentro de una lista llamada 'song'
                return data['subsonic-response']['album'].get('song', [])
            return []
        except Exception as e:
            print(f"Error cargando canciones del álbum: {e}")
            return []
