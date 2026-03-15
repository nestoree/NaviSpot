# 🎵 NaviSpot (v1.5-alpha)
NaviSpot es un reproductor de escritorio inspirado en Spotify que se conecta a servidores Navidrome/Subsonic para traer tu biblioteca musical a una experiencia moderna y personalizada. Está escrito en Python con `customtkinter` para la interfaz, `requests` para hablar con la API y `pygame` para reproducir audio localmente.

## ¿Qué hace?
- Abre sesión con tu servidor Navidrome usando URL/usuario/contraseña y guarda ese estado (más la última canción, posición y volumen) en `config.json`.
- Muestra una cuadrícula de álbumes ordenada alfabéticamente con portada, título truncado y un botón de reproducir flotante para arrancar cualquier disco fácilmente.
- Permite buscar álbumes, navegar por artistas y abrir el detalle de un álbum con portada grande, lista de canciones y botones de reproducción en cada pista.
- Incluye un reproductor persistente en la parte inferior: portada en miniatura, título/autor truncados, controles shuffle/repetir, barra de progreso operativa y volumen logarítmico.
- Guarda y restaura el estado (track activo, posición del slider y volumen) cada vez que cierras la app para reanudar donde la dejaste.

## Tecnologías principales
- `customtkinter`: elementos gráficos con estilo oscuro (frames, botones, sliders).
- `pygame.mixer`: decodificador y control de reproducción (play, pause, seek, volumen).
- `requests`: llamadas HTTP seguras a la API de Navidrome/Subsonic.
- `Pillow`: carga de portadas y miniaturas para los widgets con imágenes.

## Estado actual y roadmap
| Componentes | Estado |
| --- | --- |
| Login + persistencia (`config.json`) | Funciona, pero todavía se pueden pulir errores de escritura/lectura. |
| Grid de álbumes + búsqueda | Implementado con truncado y orden alfabético. |
| Vista de álbum + controles por pista | Listas de canciones con botones de play directos. |
| Reproductor inferior | Tiene shuffle, repeat, slider y volumen, aunque ahora se están afinando el seek y el estilo visual. |
| Librería de artistas | Renderiza tarjetas con imágenes cuadradas y enlaces a discografía. |
| Funciones futuras | Letras, playlists, descargas y temas personalizados son objetivos a medio plazo. |

## Instalación
1. Clona el proyecto:
   ```powershell
   git clone https://github.com/nestoree/NaviSpot
   cd NaviSpot
   ```
2. Instala Python 3.10+ y las dependencias:
   ```powershell
   pip install customtkinter Pillow requests pygame
   ```
3. Ejecuta la aplicación:
   ```powershell
   python main.py
   ```

## Configuración inicial
1. Al abrir por primera vez verás el formulario de login.
2. Introduce la URL del servidor (`http://mi-servidor:4533`), tu usuario y la contraseña.
3. El cliente valida la conexión con `ping.view` y guarda los datos (sin exponer la contraseña en texto plano) en `config.json`. Ese archivo también almacena el volumen, la última canción y la posición del slider para restaurar la sesión.

## Uso diario
* Usa la barra de búsqueda o desplázate por la pantalla principal para encontrar álbumes.
* Despliega un álbum para ver su portada grande y reproducir canciones individuales con el botón `▶`.
* Controla la reproducción desde la barra inferior: shuffle, repetir, barra de progreso (arrastrable) y slider de volumen cuadrático.
* Ve a “Artistas” para explorar por intérpretes y volver rápidamente a la vista previa de álbumes.
* En “Configuración” puedes ver tus credenciales guardadas y cerrar sesión si necesitas reconfigurar el servidor.

## Desarrollo y contribuciones
* Para aportar, abre un issue o envía un pull request con descripciones claras y casos de prueba.
* El código principal vive en `main.py`, mientras que `login.py`, `sidebar.py`, `settings.py` y `profile.py` segmentan cada vista.
* Respeta el estilo oscuro, los tamaños fijos de tarjetas y la filosofía de minimizar saltos inesperados en la UI (truncar textos largos, mantener imágenes cuadradas, preservar el layout del reproductor).

Gracias por acompañar este proyecto en sus primeras etapas. Cada prueba, reporte y mejora gráfica ayuda a hacerlo más pulido.
