"""
Tienda de temas GNOME-Look con integración OCS
"""

import requests
import json
import time
import random
from pathlib import Path
import threading
from typing import List, Optional
from dataclasses import dataclass
from gi.repository import Gtk, Adw, Gdk, Gio, GLib, GdkPixbuf
import webbrowser
from ..utils.ocs_handler import ocs_handler

@dataclass
class ThemeItem:
    """Representa un tema de GNOME-Look usando OCS"""
    id: str
    name: str
    author: str
    description: str
    image_url: str
    download_url: str
    category: str
    downloads: int = 0
    rating: float = 0.0
    tags: List[str] = None
    version: str = ""
    last_updated: str = ""
    ocs_url: str = ""  # URL OCS para instalación

class GNOMELookStore:
    """Cliente para GNOME-Look.org usando API OCS"""
    
    def __init__(self):
        # API endpoints de GNOME-Look/OpenDesktop
        self.api_base = "https://www.opendesktop.org/api/v1"
        self.session = requests.Session()
        
        # Headers para la API
        self.session.headers.update({
            'User-Agent': 'GNOME-Theme-Loader/1.0',
            'Accept': 'application/json',
        })
        
        # Configuración
        self.timeout = 15
        self.max_retries = 3
        self.retry_delay = 2
        
        # Mapeo de categorías para la API
        self.category_mapping = {
            'all': '',
            'gtk': '101',      # GTK Themes
            'shell': '123',    # GNOME Shell Themes
            'icons': '132',    # Icon Themes
            'cursor': '108',   # Cursor Themes
            'grub': '109',     # GRUB Themes
            'wallpaper': '300' # Wallpapers
        }
        
        # Cache simple en memoria
        self._cache = {}
        self._cache_timeout = 300  # 5 minutos
        
        # Datos de respaldo para cuando la API no funcione
        self._fallback_themes = self._create_fallback_themes()
    
    def _create_fallback_themes(self) -> List[ThemeItem]:
        """Crear temas de respaldo para cuando la API no funcione"""
        return [
            ThemeItem(
                id="adwaita_dark",
                name="Adwaita Dark",
                author="GNOME Team",
                description="Tema oscuro oficial de GNOME con diseño moderno y minimalista",
                image_url="",
                download_url="https://www.gnome-look.org/p/1234/download",
                category="gtk",
                downloads=150000,
                rating=4.8,
                tags=["dark", "official", "modern"],
                version="42.0",
                last_updated="2024-01-15",
                ocs_url="ocs://install?url=https%3A//www.gnome-look.org/p/1234/download&type=themes&filename=adwaita_dark.tar.gz"
            ),
            ThemeItem(
                id="papirus_icons",
                name="Papirus Icons",
                author="Papirus Team",
                description="Pack de iconos coloridos y modernos para Linux",
                image_url="",
                download_url="https://www.gnome-look.org/p/9012/download",
                category="icons",
                downloads=120000,
                rating=4.7,
                tags=["icons", "colorful", "modern"],
                version="2024.01.20",
                last_updated="2024-01-20",
                ocs_url="ocs://install?url=https%3A//www.gnome-look.org/p/9012/download&type=icons&filename=papirus_icons.tar.gz"
            ),
            ThemeItem(
                id="breeze_cursors",
                name="Breeze Cursors",
                author="KDE Team",
                description="Cursores elegantes y suaves del proyecto KDE",
                image_url="",
                download_url="https://www.gnome-look.org/p/3456/download",
                category="cursor",
                downloads=25000,
                rating=4.6,
                tags=["cursors", "smooth", "kde"],
                version="5.27.0",
                last_updated="2024-01-05",
                ocs_url="ocs://install?url=https%3A//www.gnome-look.org/p/3456/download&type=cursors&filename=breeze_cursors.tar.gz"
            ),
            ThemeItem(
                id="yaru_theme",
                name="Yaru Theme",
                author="Ubuntu Team",
                description="Tema oficial de Ubuntu con colores vibrantes",
                image_url="",
                download_url="https://www.gnome-look.org/p/7890/download",
                category="gtk",
                downloads=85000,
                rating=4.5,
                tags=["ubuntu", "official", "vibrant"],
                version="22.04.1",
                last_updated="2024-01-12",
                ocs_url="ocs://install?url=https%3A//www.gnome-look.org/p/7890/download&type=themes&filename=yaru_theme.tar.gz"
            ),
            ThemeItem(
                id="arc_theme",
                name="Arc Theme",
                author="Horst3180",
                description="Tema elegante con esquinas redondeadas y colores suaves",
                image_url="",
                download_url="https://www.gnome-look.org/p/5678/download",
                category="gtk",
                downloads=95000,
                rating=4.7,
                tags=["elegant", "rounded", "smooth"],
                version="2024.01.10",
                last_updated="2024-01-10",
                ocs_url="ocs://install?url=https%3A//www.gnome-look.org/p/5678/download&type=themes&filename=arc_theme.tar.gz"
            )
        ]
    
    def _make_api_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Realizar petición a la API con reintentos"""
        url = f"{self.api_base}/{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                print(f"[STORE] Consultando API: {url} (intento {attempt + 1})")
                
                # Delay aleatorio para evitar rate limiting
                if attempt > 0:
                    delay = self.retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(delay)
                
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                
                # Verificar que la respuesta sea JSON válido
                content_type = response.headers.get('content-type', '')
                if 'application/json' not in content_type and 'text/html' in content_type:
                    print(f"[STORE] La API devolvió HTML en lugar de JSON")
                    return None
                
                try:
                    return response.json()
                except json.JSONDecodeError:
                    print(f"[STORE] Respuesta no es JSON válido")
                    return None
                
            except requests.exceptions.Timeout:
                print(f"[STORE] Timeout en intento {attempt + 1}")
            except requests.exceptions.ConnectionError:
                print(f"[STORE] Error de conexión en intento {attempt + 1}")
            except requests.exceptions.HTTPError as e:
                print(f"[STORE] Error HTTP {e.response.status_code} en intento {attempt + 1}")
                if e.response.status_code == 429:  # Rate limit
                    time.sleep(30)  # Esperar más tiempo
                elif e.response.status_code >= 500:  # Error del servidor
                    continue
                else:
                    break
            except Exception as e:
                print(f"[STORE] Error inesperado: {e}")
        
        print(f"[STORE] Falló después de {self.max_retries} intentos")
        return None
    
    def _parse_api_item(self, item: dict, category: str) -> Optional[ThemeItem]:
        """Parsear un item de la API a ThemeItem"""
        try:
            # Asegurar que los campos sean cadenas y no listas
            def safe_str(val):
                if isinstance(val, list):
                    return val[0] if val else ''
                return str(val) if val is not None else ''
            
            # Extraer información básica
            name = safe_str(item.get('name', ''))
            author = safe_str(item.get('username', ''))
            description = safe_str(item.get('description', ''))
            
            # Extraer imagen de preview
            image_url = safe_str(item.get('preview1', ''))
            if not image_url and item.get('preview2'):
                image_url = safe_str(item.get('preview2', ''))
            
            # Extraer enlace de descarga
            download_url = safe_str(item.get('downloadlink1', ''))
            if not download_url and item.get('downloadlink2'):
                download_url = safe_str(item.get('downloadlink2', ''))
            
            # Crear URL OCS para instalación
            ocs_url = ""
            if download_url:
                # Determinar tipo de tema basado en la categoría
                theme_type = "themes"  # Por defecto
                if category == "132":  # Icon Themes
                    theme_type = "icons"
                elif category == "108":  # Cursor Themes
                    theme_type = "cursors"
                elif category == "123":  # GNOME Shell Themes
                    theme_type = "gnome_shell_extensions"
                
                ocs_url = ocs_handler.create_ocs_url(download_url, theme_type)
            
            # Extraer estadísticas
            downloads = int(item.get('downloads', 0))
            rating = float(item.get('score', 0))
            
            # Crear ID único
            theme_id = str(item.get('id', f"{name}_{author}".replace(' ', '_').lower()))
            
            return ThemeItem(
                id=theme_id,
                name=name,
                author=author,
                description=description,
                image_url=image_url,
                download_url=download_url,
                category=category,
                downloads=downloads,
                rating=rating,
                tags=item.get('tags', []) if isinstance(item.get('tags', []), list) else [],
                version=safe_str(item.get('version', '')),
                last_updated=safe_str(item.get('changedate', '')),
                ocs_url=ocs_url
            )
            
        except Exception as e:
            print(f"[STORE] Error parseando item de API: {e}")
            return None
    
    def get_latest_themes(self, category: str = "all", page: int = 1) -> List[ThemeItem]:
        """Obtener temas más recientes usando la API"""
        cache_key = f"latest_{category}_{page}"
        
        # Verificar cache
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_timeout:
                return cached_data
        
        # Parámetros para la API
        params = {
            'cat': self.category_mapping.get(category, ''),
            'ord': 'latest',
            'page': page,
            'limit': 20
        }
        
        # Realizar petición
        data = self._make_api_request('search', params)
        
        if not data or 'data' not in data:
            print("[STORE] No se obtuvieron datos de la API, usando datos de respaldo")
            # Usar datos de respaldo
            filtered_themes = []
            for theme in self._fallback_themes:
                if category == "all" or theme.category == category:
                    filtered_themes.append(theme)
            return filtered_themes
        
        # Parsear resultados
        themes = []
        for item in data['data']:
            theme = self._parse_api_item(item, category)
            if theme:
                themes.append(theme)
        
        # Guardar en cache
        self._cache[cache_key] = (themes, time.time())
        
        print(f"[STORE] Encontrados {len(themes)} temas usando API OCS")
        return themes
    
    def get_popular_themes(self, category: str = "all") -> List[ThemeItem]:
        """Obtener temas populares usando la API"""
        # Parámetros para la API
        params = {
            'cat': self.category_mapping.get(category, ''),
            'ord': 'rating',
            'page': 1,
            'limit': 20
        }
        
        # Realizar petición
        data = self._make_api_request('search', params)
        
        if not data or 'data' not in data:
            print("[STORE] No se obtuvieron datos de la API, usando datos de respaldo")
            # Usar datos de respaldo
            filtered_themes = []
            for theme in self._fallback_themes:
                if category == "all" or theme.category == category:
                    filtered_themes.append(theme)
            # Ordenar por rating
            filtered_themes.sort(key=lambda x: x.rating, reverse=True)
            return filtered_themes
        
        # Parsear resultados
        themes = []
        for item in data['data']:
            theme = self._parse_api_item(item, category)
            if theme:
                themes.append(theme)
        
        return themes
    
    def search_themes(self, query: str, category: str = "all", page: int = 1) -> List[ThemeItem]:
        """Buscar temas usando la API"""
        # Parámetros para la API
        params = {
            'cat': self.category_mapping.get(category, ''),
            'search': query,
            'ord': 'latest',
            'page': page,
            'limit': 20
        }
        
        # Realizar petición
        data = self._make_api_request('search', params)
        
        if not data or 'data' not in data:
            print("[STORE] No se obtuvieron datos de la API, usando datos de respaldo")
            # Usar datos de respaldo con filtrado por búsqueda
            filtered_themes = []
            query_lower = query.lower()
            for theme in self._fallback_themes:
                if category == "all" or theme.category == category:
                    if (query_lower in theme.name.lower() or 
                        query_lower in theme.description.lower() or
                        any(query_lower in tag.lower() for tag in theme.tags or [])):
                        filtered_themes.append(theme)
            return filtered_themes
        
        # Parsear resultados
        themes = []
        for item in data['data']:
            theme = self._parse_api_item(item, category)
            if theme:
                themes.append(theme)
        
        return themes
    
    def check_connection(self) -> bool:
        """Verificar conexión a la API"""
        try:
            data = self._make_api_request('search', {'limit': 1})
            return data is not None and 'data' in data
        except:
            return False
    
    def get_site_status(self) -> dict:
        """Obtener estado del sitio"""
        is_connected = self.check_connection()
        return {
            'connected': is_connected,
            'status': 'online' if is_connected else 'offline',
            'message': 'Conectado a GNOME-Look.org' if is_connected else 'No se puede conectar a GNOME-Look.org'
        }

class StoreWindow(Adw.ApplicationWindow):
    """Ventana de la tienda de temas usando OCS"""
    
    def __init__(self, app: Adw.Application, parent_window=None):
        super().__init__(application=app, title="Tienda de Temas GNOME-Look")
        self.set_default_size(900, 700)
        self.set_size_request(700, 500)
        self.parent_window = parent_window
        self.app = app
        # Crear overlay de toast
        self.toast_overlay = Adw.ToastOverlay()
        # Construir UI principal
        self._build_ui()
        # Poner el contenido dentro del overlay
        self.toast_overlay.set_child(self.get_content())
        self.set_content(self.toast_overlay)
        
        # Inicializar store
        self.store = GNOMELookStore()
        
        # Estado de la aplicación
        self.current_category = "all"
        self.is_loading = False
        self.themes = []
        
        # Verificar conexión inicial
        self._check_connection_status()
        
        # Cargar temas iniciales
        GLib.timeout_add(1000, self._load_initial_themes)
    
    def _build_ui(self):
        """Construir la interfaz de usuario"""
        # Panel principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header bar
        header_bar = self._create_header_bar()
        main_box.append(header_bar)
        
        # Contenido principal
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        main_box.append(content_box)
        
        # Barra de estado
        self.status_bar = self._create_status_bar()
        content_box.append(self.status_bar)
        
        # Controles de categoría
        category_box = self._create_category_controls()
        content_box.append(category_box)
        
        # Lista de temas
        self.themes_list = self._create_themes_list()
        content_box.append(self.themes_list)
        
        # Spinner de carga
        self.loading_spinner = Gtk.Spinner()
        self.loading_spinner.set_halign(Gtk.Align.CENTER)
        self.loading_spinner.set_visible(False)
        content_box.append(self.loading_spinner)
    
    def _create_header_bar(self):
        """Crear header bar"""
        header_bar = Adw.HeaderBar()
        header_bar.set_css_classes(["flat"])
        
        # Título
        title = Adw.WindowTitle()
        title.set_title("Tienda de Temas")
        title.set_subtitle("GNOME-Look.org")
        header_bar.set_title_widget(title)
        
        # Botones del header
        # Botón de recargar
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text("Recargar temas")
        refresh_button.connect("clicked", self._on_refresh_clicked)
        header_bar.pack_end(refresh_button)
        
        # Botón de abrir en navegador
        browser_button = Gtk.Button()
        browser_button.set_icon_name("web-browser-symbolic")
        browser_button.set_tooltip_text("Abrir GNOME-Look.org")
        browser_button.connect("clicked", self._abrir_gnome_look)
        header_bar.pack_end(browser_button)
        
        return header_bar
    
    def _create_status_bar(self):
        """Crear barra de estado"""
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_box.set_css_classes(["status-bar"])
        
        # Icono de estado
        self.status_icon = Gtk.Image()
        self.status_icon.set_from_icon_name("network-wireless-symbolic")
        status_box.append(self.status_icon)
        
        # Mensaje de estado
        self.status_label = Gtk.Label()
        self.status_label.set_text("Conectando a GNOME-Look.org...")
        status_box.append(self.status_label)
        
        # Botón de reconectar
        self.reconnect_button = Gtk.Button()
        self.reconnect_button.set_label("Reconectar")
        self.reconnect_button.set_visible(False)
        self.reconnect_button.connect("clicked", self._on_reconnect_clicked)
        status_box.append(self.reconnect_button)
        
        status_box.set_hexpand(True)
        return status_box
    
    def _create_category_controls(self):
        """Crear controles de categoría"""
        category_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        # Etiqueta
        label = Gtk.Label()
        label.set_text("Categoría:")
        category_box.append(label)
        
        # Botones de categoría
        categories = [
            ("all", "Todas", "applications-graphics-symbolic"),
            ("gtk", "GTK", "applications-graphics-symbolic"),
            ("icons", "Iconos", "applications-graphics-symbolic"),
            ("cursor", "Cursors", "input-mouse-symbolic"),
            ("shell", "Shell", "applications-system-symbolic")
        ]
        
        for cat_id, cat_name, icon_name in categories:
            button = Gtk.Button()
            button.set_label(cat_name)
            button.set_icon_name(icon_name)
            button.set_css_classes(["flat"])
            button.connect("clicked", self._on_category_selected, cat_id)
            category_box.append(button)
        
        category_box.set_hexpand(True)
        return category_box
    
    def _create_themes_list(self):
        """Crear lista de temas"""
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        # List box
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.set_css_classes(["themes-list"])
        
        scrolled.set_child(self.list_box)
        return scrolled
    
    def _check_connection_status(self):
        """Verificar estado de conexión"""
        def check_thread():
            status = self.store.get_site_status()
            GLib.idle_add(self._update_connection_status, status)
        
        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()
    
    def _update_connection_status(self, status: dict):
        """Actualizar estado de conexión en la UI"""
        if status['connected']:
            self.status_icon.set_icon_name("network-wireless-symbolic")
            self.status_label.set_text(status['message'])
            self.reconnect_button.set_visible(False)
        else:
            self.status_icon.set_from_icon_name("network-wireless-offline-symbolic")
            self.status_label.set_text(status['message'])
            self.reconnect_button.set_visible(True)
    
    def _on_reconnect_clicked(self, *_):
        """Reconectar a GNOME-Look.org"""
        self._check_connection_status()
        self._load_initial_themes()
    
    def _on_refresh_clicked(self, *_):
        """Recargar temas"""
        self._load_themes()
    
    def _abrir_gnome_look(self, *_):
        """Abrir GNOME-Look.org en el navegador"""
        webbrowser.open("https://www.gnome-look.org")
    
    def _on_category_selected(self, button, category):
        """Cambiar categoría seleccionada"""
        self.current_category = category
        self._load_themes()
    
    def _load_initial_themes(self):
        """Cargar temas iniciales"""
        self._load_themes()
        return False  # No repetir
    
    def _load_themes(self):
        """Cargar temas de la categoría actual"""
        if self.is_loading:
            return
        
        self.is_loading = True
        self.loading_spinner.set_visible(True)
        self.loading_spinner.start()
        
        def load_thread():
            try:
                themes = self.store.get_latest_themes(self.current_category)
                GLib.idle_add(self._update_themes_list, themes)
            except Exception as e:
                print(f"Error cargando temas: {e}")
                GLib.idle_add(self._update_themes_list, [])
            finally:
                GLib.idle_add(self._finish_loading)
        
        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()
    
    def _update_themes_list(self, themes: List[ThemeItem]):
        """Actualizar lista de temas"""
        # Limpiar lista actual
        while self.list_box.get_first_child():
            self.list_box.remove(self.list_box.get_first_child())
        
        if not themes:
            # Mostrar mensaje de no hay temas
            no_themes_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            no_themes_box.set_halign(Gtk.Align.CENTER)
            no_themes_box.set_valign(Gtk.Align.CENTER)
            no_themes_box.set_margin_top(48)
            no_themes_box.set_margin_bottom(48)
            
            icon = Gtk.Image()
            icon.set_from_icon_name("applications-graphics-symbolic")
            icon.set_pixel_size(64)
            no_themes_box.append(icon)
            
            label = Gtk.Label()
            label.set_text("No se encontraron temas")
            label.set_css_classes(["dim-label"])
            no_themes_box.append(label)
            
            row = Gtk.ListBoxRow()
            row.set_child(no_themes_box)
            self.list_box.append(row)
        else:
            # Agregar temas
            for theme in themes:
                row = self._create_theme_row(theme)
                self.list_box.append(row)
    
    def _finish_loading(self):
        """Finalizar carga"""
        self.is_loading = False
        self.loading_spinner.stop()
        self.loading_spinner.set_visible(False)
    
    def _create_theme_row(self, theme: ThemeItem) -> Gtk.ListBoxRow:
        """Crear fila de tema"""
        row = Gtk.ListBoxRow()
        
        # Contenedor principal
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(16)
        box.set_margin_end(16)
        
        # Imagen del tema
        image_box = Gtk.Box()
        image_box.set_size_request(80, 80)
        
        if theme.image_url:
            # Cargar imagen de forma asíncrona
            self._load_theme_image(image_box, theme.image_url)
        else:
            # Imagen por defecto
            default_image = Gtk.Image()
            default_image.set_from_icon_name("applications-graphics-symbolic")
            default_image.set_pixel_size(48)
            default_image.set_css_classes(["dim-label"])
            image_box.append(default_image)
        
        box.append(image_box)
        
        # Información del tema
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)
        
        # Nombre del tema
        name_label = Gtk.Label()
        name_label.set_text(theme.name)
        name_label.set_css_classes(["heading"])
        name_label.set_halign(Gtk.Align.START)
        info_box.append(name_label)
        
        # Autor
        author_label = Gtk.Label()
        author_label.set_text(f"por {theme.author}")
        author_label.set_css_classes(["dim-label"])
        author_label.set_halign(Gtk.Align.START)
        info_box.append(author_label)
        
        # Descripción
        if theme.description:
            desc_label = Gtk.Label()
            desc_label.set_text(theme.description[:100] + "..." if len(theme.description) > 100 else theme.description)
            desc_label.set_css_classes(["dim-label"])
            desc_label.set_halign(Gtk.Align.START)
            desc_label.set_wrap(True)
            info_box.append(desc_label)
        
        # Estadísticas
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        stats_box.set_margin_top(8)
        
        if theme.downloads > 0:
            downloads_label = Gtk.Label()
            downloads_label.set_text(f"📥 {theme.downloads} descargas")
            downloads_label.set_css_classes(["dim-label"])
            stats_box.append(downloads_label)
        
        if theme.rating > 0:
            rating_label = Gtk.Label()
            rating_label.set_text(f"⭐ {theme.rating:.1f}")
            rating_label.set_css_classes(["dim-label"])
            stats_box.append(rating_label)
        
        info_box.append(stats_box)
        box.append(info_box)
        
        # Botón de instalación
        if theme.ocs_url:
            install_button = Gtk.Button()
            install_button.set_label("Instalar")
            install_button.set_icon_name("system-software-install-symbolic")
            install_button.set_css_classes(["suggested-action"])
            install_button.connect("clicked", self._on_install_theme, theme)
            box.append(install_button)
        
        row.set_child(box)
        return row
    
    def _load_theme_image(self, image_box: Gtk.Box, image_url: str):
        """Cargar imagen del tema de forma asíncrona"""
        def load_image():
            try:
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                
                # Crear imagen desde bytes usando GdkPixbuf
                loader = GdkPixbuf.PixbufLoader.new()
                loader.write(response.content)
                loader.close()
                pixbuf = loader.get_pixbuf()
                
                # Crear imagen GTK
                image = Gtk.Image()
                image.set_from_pixbuf(pixbuf)
                
                GLib.idle_add(lambda: self._set_theme_image(image_box, image))
                
            except Exception as e:
                print(f"Error cargando imagen: {e}")
                GLib.idle_add(lambda: self._set_default_image(image_box))
        
        thread = threading.Thread(target=load_image, daemon=True)
        thread.start()
    
    def _set_theme_image(self, image_box: Gtk.Box, image: Gtk.Image):
        """Establecer imagen del tema"""
        # Limpiar contenedor
        while image_box.get_first_child():
            image_box.remove(image_box.get_first_child())
        
        image_box.append(image)
    
    def _set_default_image(self, image_box: Gtk.Box):
        """Establecer imagen por defecto"""
        # Limpiar contenedor
        while image_box.get_first_child():
            image_box.remove(image_box.get_first_child())
        
        default_image = Gtk.Image()
        default_image.set_from_icon_name("applications-graphics-symbolic")
        default_image.set_pixel_size(48)
        default_image.set_css_classes(["dim-label"])
        image_box.append(default_image)
    
    def _on_install_theme(self, button, theme: ThemeItem):
        """Instalar tema usando OCS"""
        if not theme.ocs_url:
            self._show_toast("No se puede instalar este tema", False)
            return
        
        # Mostrar diálogo de confirmación
        dialog = Gtk.Dialog()
        dialog.set_title("Instalar Tema")
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        
        content_area = dialog.get_content_area()
        content_area.set_spacing(12)
        content_area.set_margin_top(24)
        content_area.set_margin_bottom(24)
        content_area.set_margin_start(24)
        content_area.set_margin_end(24)
        
        # Información del tema
        info_label = Gtk.Label()
        info_label.set_text(f"¿Instalar '{theme.name}' por {theme.author}?")
        info_label.set_css_classes(["heading"])
        content_area.append(info_label)
        
        desc_label = Gtk.Label()
        desc_label.set_text("El tema se instalará usando el protocolo OCS nativo de GNOME.")
        desc_label.set_css_classes(["dim-label"])
        desc_label.set_wrap(True)
        content_area.append(desc_label)
        
        # Botones
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Instalar", Gtk.ResponseType.OK)
        
        dialog.connect("response", self._on_install_dialog_response, theme)
        dialog.present()
    
    def _on_install_dialog_response(self, dialog, response, theme: ThemeItem):
        """Respuesta del diálogo de instalación"""
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK:
            self._execute_ocs_installation(theme)
    
    def _execute_ocs_installation(self, theme: ThemeItem):
        """Ejecutar instalación usando OCS"""
        # Mostrar spinner de instalación
        self._show_install_spinner(f"Instalando {theme.name}...")
        
        def install_thread():
            try:
                def progress_callback(message, msg_type):
                    GLib.idle_add(self._update_install_progress, message, msg_type)
                
                success, result = ocs_handler.install_theme(theme.ocs_url, progress_callback)
                
                GLib.idle_add(self._show_install_result, success, result, theme.name)
                
            except Exception as e:
                GLib.idle_add(self._show_install_result, False, str(e), theme.name)
        
        thread = threading.Thread(target=install_thread, daemon=True)
        thread.start()
    
    def _show_install_spinner(self, message: str):
        """Mostrar spinner de instalación"""
        # Crear overlay de instalación
        self.install_overlay = Gtk.Overlay()
        self.install_overlay.set_child(self.get_content())
        
        # Box de instalación
        install_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        install_box.set_halign(Gtk.Align.CENTER)
        install_box.set_valign(Gtk.Align.CENTER)
        install_box.set_css_classes(["install-overlay"])
        
        # Spinner
        spinner = Gtk.Spinner()
        spinner.start()
        install_box.append(spinner)
        
        # Mensaje
        label = Gtk.Label()
        label.set_text(message)
        install_box.append(label)
        
        self.install_overlay.add_overlay(install_box)
        self.set_content(self.install_overlay)
    
    def _update_install_progress(self, message: str, msg_type: str):
        """Actualizar progreso de instalación"""
        # Actualizar mensaje en el overlay
        pass  # Implementar si es necesario
    
    def _show_install_result(self, success: bool, result: str, theme_name: str):
        """Mostrar resultado de instalación"""
        # Restaurar contenido original
        if hasattr(self, 'install_overlay'):
            original_content = self.install_overlay.get_child()
            self.set_content(original_content)
            delattr(self, 'install_overlay')
        
        # Mostrar toast
        if success:
            self._show_toast(f"✅ {theme_name} instalado correctamente", True)
        else:
            self._show_toast(f"❌ Error instalando {theme_name}: {result}", False)
    
    def _show_toast(self, message: str, is_success: bool):
        """Mostrar toast de notificación"""
        toast = Adw.Toast()
        toast.set_title(message)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)

# Ejemplo de uso para testing
if __name__ == "__main__":
    store = GNOMELookStore()
    
    print("=== ESTADO DEL SITIO ===")
    status = store.get_site_status()
    print(f"Estado: {'🟢 Online' if status['connected'] else '🔴 Offline'}")
    print(f"Mensaje: {status['message']}")
    
    print("\n=== TEMAS RECIENTES ===")
    themes = store.get_latest_themes()
    for theme in themes[:5]:
        print(f"📦 {theme.name} por {theme.author}")
        print(f"   ⭐ {theme.rating} | 📥 {theme.downloads}")
        print(f"   📝 {theme.description[:50]}...")
        print()