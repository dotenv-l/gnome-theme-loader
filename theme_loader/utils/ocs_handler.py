"""
Manejador del protocolo OCS (OpenCollaborationServices)
Implementa la funcionalidad de ocs-url para instalar temas desde GNOME-Look.org
"""

import urllib.parse
import subprocess
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple
import requests
import zipfile
import tarfile
import json
import re

class OCSHandler:
    """Manejador del protocolo OCS para instalación de temas"""
    
    def __init__(self):
        # Mapeo de tipos de instalación a directorios
        self.install_types = {
            'themes': '~/.themes',
            'icons': '~/.local/share/icons',
            'cursors': '~/.icons',
            'wallpapers': '~/.local/share/wallpapers',
            'fonts': '~/.fonts',
            'gnome_shell_extensions': '~/.local/share/gnome-shell/extensions',
            'gtk3_themes': '~/.themes',
            'gtk4_themes': '~/.themes',
            'shell_themes': '~/.themes',
            'cursor_themes': '~/.icons',
            'icon_themes': '~/.local/share/icons',
            'grub_themes': '/boot/grub/themes',
            'plymouth_themes': '/usr/share/plymouth/themes'
        }
        
        # Alias para compatibilidad
        self.type_aliases = {
            'gnome_shell_themes': 'themes',
            'cinnamon_themes': 'themes',
            'gtk2_themes': 'themes',
            'gtk3_themes': 'themes',
            'metacity_themes': 'themes',
            'xfwm4_themes': 'themes',
            'openbox_themes': 'themes',
            'kvantum_themes': 'themes',
            'compiz_themes': 'emerald_themes',
            'beryl_themes': 'emerald_themes',
            'plasma4_plasmoids': 'plasma_plasmoids',
            'plasma5_plasmoids': 'plasma_plasmoids',
            'plasma5_look_and_feel': 'plasma_look_and_feel',
            'plasma5_desktopthemes': 'plasma_desktopthemes',
            'plasma_color_schemes': 'color_schemes'
        }
    
    def parse_ocs_url(self, ocs_url: str) -> Dict[str, str]:
        """Parsear una URL OCS y extraer sus componentes"""
        try:
            # Verificar que es una URL OCS válida
            if not ocs_url.startswith(('ocs://', 'ocss://')):
                raise ValueError("URL debe comenzar con ocs:// o ocss://")
            
            # Parsear la URL
            parsed = urllib.parse.urlparse(ocs_url)
            
            # Extraer comando y parámetros
            command = parsed.netloc
            params = urllib.parse.parse_qs(parsed.query)
            
            # Decodificar parámetros
            result = {
                'command': command,
                'url': urllib.parse.unquote(params.get('url', [''])[0]),
                'type': urllib.parse.unquote(params.get('type', ['downloads'])[0]),
                'filename': urllib.parse.unquote(params.get('filename', [''])[0])
            }
            
            return result
            
        except Exception as e:
            raise ValueError(f"Error parseando URL OCS: {e}")
    
    def get_install_path(self, install_type: str) -> Path:
        """Obtener la ruta de instalación para un tipo específico"""
        # Resolver alias
        if install_type in self.type_aliases:
            install_type = self.type_aliases[install_type]
        
        # Obtener ruta base
        if install_type in self.install_types:
            base_path = self.install_types[install_type]
        else:
            base_path = '~/Downloads'  # Por defecto
        
        # Expandir ~ y crear directorio si no existe
        path = Path(base_path).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        
        return path
    
    def download_file(self, url: str, filename: str = None) -> Path:
        """Descargar archivo desde URL"""
        try:
            # Crear directorio temporal
            temp_dir = Path(tempfile.mkdtemp())
            
            # Determinar nombre del archivo
            if not filename:
                filename = url.split('/')[-1]
                if '?' in filename:
                    filename = filename.split('?')[0]
            
            file_path = temp_dir / filename
            
            # Descargar archivo
            print(f"Descargando: {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return file_path
            
        except Exception as e:
            raise Exception(f"Error descargando archivo: {e}")
    
    def extract_archive(self, archive_path: Path, extract_to: Path) -> bool:
        """Extraer archivo comprimido"""
        try:
            print(f"Extrayendo: {archive_path.name}")
            
            if archive_path.suffix in ['.zip']:
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
                    
            elif archive_path.suffix in ['.tar.gz', '.tgz']:
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_to)
                    
            elif archive_path.suffix in ['.tar.xz', '.txz']:
                with tarfile.open(archive_path, 'r:xz') as tar_ref:
                    tar_ref.extractall(extract_to)
                    
            elif archive_path.suffix in ['.tar.bz2', '.tbz2']:
                with tarfile.open(archive_path, 'r:bz2') as tar_ref:
                    tar_ref.extractall(extract_to)
                    
            else:
                # Si no es un archivo comprimido, copiarlo directamente
                shutil.copy2(archive_path, extract_to / archive_path.name)
            
            return True
            
        except Exception as e:
            print(f"Error extrayendo archivo: {e}")
            return False
    
    def install_theme(self, ocs_url: str, callback=None) -> Tuple[bool, str]:
        """Instalar tema usando URL OCS"""
        try:
            # Parsear URL OCS
            params = self.parse_ocs_url(ocs_url)
            
            if callback:
                callback(f"Parseando URL OCS: {params['command']}", "info")
            
            # Obtener ruta de instalación
            install_path = self.get_install_path(params['type'])
            
            if callback:
                callback(f"Instalando en: {install_path}", "info")
            
            # Descargar archivo
            archive_path = self.download_file(params['url'], params['filename'])
            
            if callback:
                callback(f"Archivo descargado: {archive_path.name}", "info")
            
            # Extraer archivo
            success = self.extract_archive(archive_path, install_path)
            
            if success:
                # Limpiar archivo temporal
                archive_path.unlink(missing_ok=True)
                archive_path.parent.rmdir()
                
                if callback:
                    callback(f"Tema instalado exitosamente en {install_path}", "success")
                
                return True, f"Tema instalado en {install_path}"
            else:
                return False, "Error extrayendo archivo"
                
        except Exception as e:
            if callback:
                callback(f"Error: {str(e)}", "error")
            return False, str(e)
    
    def create_ocs_url(self, url: str, install_type: str, filename: str = None) -> str:
        """Crear URL OCS a partir de parámetros"""
        params = {
            'url': urllib.parse.quote(url),
            'type': urllib.parse.quote(install_type)
        }
        
        if filename:
            params['filename'] = urllib.parse.quote(filename)
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"ocs://install?{query_string}"
    
    def get_theme_info_from_gnome_look(self, theme_url: str) -> Dict[str, str]:
        """Obtener información de un tema desde GNOME-Look.org"""
        try:
            response = requests.get(theme_url, timeout=15)
            response.raise_for_status()
            
            # Buscar información básica en el HTML
            html = response.text
            
            # Extraer título
            title_match = re.search(r'<title>(.*?)</title>', html)
            title = title_match.group(1) if title_match else "Tema sin nombre"
            
            # Extraer descripción
            desc_match = re.search(r'<meta name="description" content="(.*?)"', html)
            description = desc_match.group(1) if desc_match else ""
            
            # Buscar enlaces de descarga
            download_links = re.findall(r'href="([^"]*download[^"]*)"', html)
            
            return {
                'title': title,
                'description': description,
                'download_links': download_links,
                'url': theme_url
            }
            
        except Exception as e:
            return {
                'title': "Error obteniendo información",
                'description': str(e),
                'download_links': [],
                'url': theme_url
            }
    
    def list_installed_themes(self, theme_type: str = 'themes') -> list:
        """Listar temas instalados de un tipo específico"""
        install_path = self.get_install_path(theme_type)
        
        if not install_path.exists():
            return []
        
        themes = []
        for item in install_path.iterdir():
            if item.is_dir():
                themes.append({
                    'name': item.name,
                    'path': str(item),
                    'type': theme_type
                })
        
        return themes
    
    def remove_theme(self, theme_name: str, theme_type: str = 'themes') -> bool:
        """Remover un tema instalado"""
        try:
            install_path = self.get_install_path(theme_type)
            theme_path = install_path / theme_name
            
            if theme_path.exists():
                if theme_path.is_dir():
                    shutil.rmtree(theme_path)
                else:
                    theme_path.unlink()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error removiendo tema: {e}")
            return False

# Instancia global
ocs_handler = OCSHandler() 