#!/usr/bin/env python3
"""
Script de prueba para el manejador OCS
Demuestra cómo usar el protocolo ocs:// para instalar temas
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from theme_loader.utils.ocs_handler import ocs_handler

def test_ocs_parsing():
    """Probar el parsing de URLs OCS"""
    print("🔍 PROBANDO PARSING DE URLS OCS")
    print("="*50)
    
    # URL de ejemplo
    test_url = "ocs://install?url=https%3A//example.com/theme.tar.gz&type=themes&filename=my_theme.tar.gz"
    
    try:
        params = ocs_handler.parse_ocs_url(test_url)
        print(f"URL original: {test_url}")
        print(f"Comando: {params['command']}")
        print(f"URL de descarga: {params['url']}")
        print(f"Tipo: {params['type']}")
        print(f"Nombre de archivo: {params['filename']}")
        print("✅ Parsing exitoso")
    except Exception as e:
        print(f"❌ Error en parsing: {e}")

def test_ocs_url_creation():
    """Probar la creación de URLs OCS"""
    print("\n🔗 PROBANDO CREACIÓN DE URLS OCS")
    print("="*50)
    
    url = "https://www.gnome-look.org/p/1234/download"
    install_type = "themes"
    filename = "awesome_theme.tar.gz"
    
    ocs_url = ocs_handler.create_ocs_url(url, install_type, filename)
    print(f"URL original: {url}")
    print(f"Tipo: {install_type}")
    print(f"Nombre: {filename}")
    print(f"URL OCS generada: {ocs_url}")
    print("✅ Creación exitosa")

def test_install_paths():
    """Probar las rutas de instalación"""
    print("\n📁 PROBANDO RUTAS DE INSTALACIÓN")
    print("="*50)
    
    test_types = ['themes', 'icons', 'cursors', 'gnome_shell_extensions']
    
    for theme_type in test_types:
        path = ocs_handler.get_install_path(theme_type)
        print(f"{theme_type}: {path}")
    
    print("✅ Rutas obtenidas correctamente")

def test_theme_listing():
    """Probar el listado de temas instalados"""
    print("\n📋 PROBANDO LISTADO DE TEMAS")
    print("="*50)
    
    themes = ocs_handler.list_installed_themes('themes')
    print(f"Temas instalados: {len(themes)}")
    
    for theme in themes[:5]:  # Mostrar solo los primeros 5
        print(f"  - {theme['name']} ({theme['type']})")
    
    if not themes:
        print("  No hay temas instalados")
    
    print("✅ Listado completado")

def test_gnome_look_info():
    """Probar obtención de información desde GNOME-Look"""
    print("\n🌐 PROBANDO OBTENCIÓN DE INFORMACIÓN DE GNOME-LOOK")
    print("="*50)
    
    # URL de ejemplo (puedes cambiarla por una real)
    test_url = "https://www.gnome-look.org/p/1234/"
    
    try:
        info = ocs_handler.get_theme_info_from_gnome_look(test_url)
        print(f"Título: {info['title']}")
        print(f"Descripción: {info['description'][:100]}...")
        print(f"Enlaces de descarga: {len(info['download_links'])}")
        print("✅ Información obtenida")
    except Exception as e:
        print(f"❌ Error obteniendo información: {e}")

def main():
    print("🚀 INICIANDO PRUEBAS DEL MANEJADOR OCS")
    print("="*60)
    
    # Ejecutar todas las pruebas
    test_ocs_parsing()
    test_ocs_url_creation()
    test_install_paths()
    test_theme_listing()
    test_gnome_look_info()
    
    print("\n" + "="*60)
    print("✅ TODAS LAS PRUEBAS COMPLETADAS")
    print("\n💡 Para instalar un tema real, usa:")
    print("   ocs_handler.install_theme('ocs://install?url=...&type=themes')")

if __name__ == "__main__":
    main() 