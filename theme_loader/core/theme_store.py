"""
Tienda de temas - Búsqueda e instalación desde GNOME-Look usando OCS
"""

import requests
import json
import time
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import threading
from dataclasses import dataclass
from urllib.parse import urljoin

@dataclass
class ThemeItem:
    """Representa un tema de la tienda"""
    id: str
    name: str
    author: str
    description: str
    category: str
    downloads: int
    rating: float
    image_url: str
    download_url: str
    file_size: str
    last_updated: str
    tags: List[str]
    ocs_url: str = ""  # URL OCS para instalación
    
class GNOMELookStore:
    """Cliente para buscar e instalar temas desde GNOME-Look usando OCS"""
    
    def __init__(self):
        # URL base de GNOME-Look
        self.base_url = "https://www.gnome-look.org"
        self.session = requests.Session()
        
        # Headers para las peticiones
        self.session.headers.update({
            'User-Agent': 'GNOME-Theme-Loader/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
        # Configuración
        self.timeout = 15
        self.max_retries = 3
        self.retry_delay = 2
        
        # Mapeo de categorías
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
        
        # Temas de ejemplo para cuando no hay conexión
        self._fallback_themes = self._create_fallback_themes()
        
    def _create_fallback_themes(self) -> List[ThemeItem]:
        """Crear temas de ejemplo para cuando no hay conexión"""
        return [
            ThemeItem(
                id="adwaita_dark",
                name="Adwaita Dark",
                author="GNOME Team",
                description="Tema oscuro oficial de GNOME con diseño moderno y limpio",
                category="gtk",
                downloads=50000,
                rating=4.8,
                image_url="",
                download_url="https://www.gnome-look.org/p/1234/download",
                file_size="2.5 MB",
                last_updated="2024-01-15",
                tags=["dark", "official", "gnome"],
                ocs_url="ocs://install?url=https%3A//www.gnome-look.org/p/1234/download&type=themes&filename=adwaita_dark.tar.gz"
            ),
            ThemeItem(
                id="arc_theme",
                name="Arc Theme",
                author="Arc Community",
                description="Tema moderno y plano con esquinas redondeadas",
                category="gtk",
                downloads=75000,
                rating=4.9,
                image_url="",
                download_url="https://www.gnome-look.org/p/5678/download",
                file_size="3.2 MB",
                last_updated="2024-01-10",
                tags=["modern", "flat", "rounded"],
                ocs_url="ocs://install?url=https%3A//www.gnome-look.org/p/5678/download&type=themes&filename=arc_theme.tar.gz"
            ),
            ThemeItem(
                id="papirus_icons",
                name="Papirus Icons",
                author="Papirus Team",
                description="Pack de iconos coloridos y modernos para Linux",
                category="icons",
                downloads=120000,
                rating=4.7,
                image_url="",
                download_url="https://www.gnome-look.org/p/9012/download",
                file_size="45.8 MB",
                last_updated="2024-01-20",
                tags=["icons", "colorful", "modern"],
                ocs_url="ocs://install?url=https%3A//www.gnome-look.org/p/9012/download&type=icons&filename=papirus_icons.tar.gz"
            ),
            ThemeItem(
                id="breeze_cursors",
                name="Breeze Cursors",
                author="KDE Team",
                description="Cursores elegantes y suaves del proyecto KDE",
                category="cursor",
                downloads=25000,
                rating=4.6,
                image_url="",
                download_url="https://www.gnome-look.org/p/3456/download",
                file_size="1.8 MB",
                last_updated="2024-01-05",
                tags=["cursors", "smooth", "kde"],
                ocs_url="ocs://install?url=https%3A//www.gnome-look.org/p/3456/download&type=cursors&filename=breeze_cursors.tar.gz"
            ),
            ThemeItem(
                id="yaru_theme",
                name="Yaru Theme",
                author="Ubuntu Team",
                description="Tema oficial de Ubuntu con colores vibrantes",
                category="gtk",
                downloads=85000,
                rating=4.5,
                image_url="",
                download_url="https://www.gnome-look.org/p/7890/download",
                file_size="4.1 MB",
                last_updated="2024-01-12",
                tags=["ubuntu", "official", "vibrant"],
                ocs_url="ocs://install?url=https%3A//www.gnome-look.org/p/7890/download&type=themes&filename=yaru_theme.tar.gz"
            )
        ]
        
    def _make_request(self, url: str, params: dict = None) -> Optional[requests.Response]:
        """Realizar petición HTTP con reintentos"""
        for attempt in range(self.max_retries):
            try:
                print(f"[STORE] Intentando conectar: {url} (intento {attempt + 1})")
                
                # Delay aleatorio para evitar rate limiting
                if attempt > 0:
                    delay = self.retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(delay)
                
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response
                
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
        
    def search_themes(self, query: str, category: str = "all", page: int = 1) -> List[ThemeItem]:
        """Buscar temas en GNOME-Look"""
        try:
            # Por ahora, devolver temas de ejemplo
            # En el futuro, esto podría conectarse a una API real
            print(f"[STORE] Búsqueda: '{query}' en categoría '{category}'")
            
            # Filtrar temas de ejemplo por categoría y consulta
            filtered_themes = []
            for theme in self._fallback_themes:
                # Filtrar por categoría
                if category != "all" and theme.category != category:
                    continue
                
                # Filtrar por consulta
                if query.lower() in theme.name.lower() or query.lower() in theme.description.lower():
                    filtered_themes.append(theme)
            
            print(f"[STORE] Encontrados {len(filtered_themes)} temas usando datos locales")
            return filtered_themes
            
        except Exception as e:
            print(f"Error buscando temas: {e}")
            return []
    
    def get_popular_themes(self, category: str = "all", limit: int = 20) -> List[ThemeItem]:
        """Obtener temas populares"""
        try:
            # Filtrar temas de ejemplo por categoría y ordenar por descargas
            filtered_themes = []
            for theme in self._fallback_themes:
                if category == "all" or theme.category == category:
                    filtered_themes.append(theme)
            
            # Ordenar por descargas (descendente)
            filtered_themes.sort(key=lambda x: x.downloads, reverse=True)
            
            return filtered_themes[:limit]
            
        except Exception as e:
            print(f"Error obteniendo temas populares: {e}")
            return []
    
    def get_latest_themes(self, category: str = "all", limit: int = 20) -> List[ThemeItem]:
        """Obtener temas más recientes"""
        try:
            # Filtrar temas de ejemplo por categoría y ordenar por fecha
            filtered_themes = []
            for theme in self._fallback_themes:
                if category == "all" or theme.category == category:
                    filtered_themes.append(theme)
            
            # Ordenar por fecha (descendente)
            filtered_themes.sort(key=lambda x: x.last_updated, reverse=True)
            
            return filtered_themes[:limit]
            
        except Exception as e:
            print(f"Error obteniendo temas recientes: {e}")
            return []
    
    def get_theme_details(self, theme_id: str) -> Optional[ThemeItem]:
        """Obtener detalles completos de un tema"""
        try:
            # Buscar en temas de ejemplo
            for theme in self._fallback_themes:
                if theme.id == theme_id:
                    return theme
            return None
            
        except Exception as e:
            print(f"Error obteniendo detalles del tema: {e}")
            return None
    
    def download_theme(self, theme: ThemeItem, download_path: Path) -> bool:
        """Descargar e instalar un tema usando OCS"""
        try:
            if not theme.ocs_url:
                print(f"[STORE] No hay URL OCS para {theme.name}")
                return False
            
            # Importar ocs_handler aquí para evitar dependencias circulares
            from ..utils.ocs_handler import ocs_handler
            
            # Instalar usando OCS
            success, result = ocs_handler.install_theme(theme.ocs_url)
            
            if success:
                print(f"[STORE] Tema {theme.name} instalado correctamente usando OCS")
                return True
            else:
                print(f"[STORE] Error instalando {theme.name}: {result}")
                return False
                
        except Exception as e:
            print(f"Error descargando tema: {e}")
            return False
    
    def check_connection(self) -> bool:
        """Verificar conexión a GNOME-Look.org"""
        try:
            response = self._make_request(self.base_url)
            return response is not None
        except:
            return False
    
    def get_site_status(self) -> dict:
        """Obtener estado del sitio"""
        is_connected = self.check_connection()
        return {
            'connected': is_connected,
            'status': 'online' if is_connected else 'offline',
            'message': 'Conectado a GNOME-Look.org' if is_connected else 'Usando datos locales - Conecta a internet para temas actualizados'
        } 