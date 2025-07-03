#!/usr/bin/env python3
"""
Demostración de la integración OCS en GNOME Theme Loader
Muestra cómo usar el protocolo ocs:// para instalar temas
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from theme_loader.utils.ocs_handler import ocs_handler

def demo_ocs_basics():
    """Demostrar funcionalidades básicas de OCS"""
    print("🚀 DEMOSTRACIÓN DE INTEGRACIÓN OCS")
    print("="*60)
    
    # 1. Crear URL OCS
    print("\n1️⃣ CREANDO URL OCS")
    print("-"*30)
    
    download_url = "https://www.gnome-look.org/p/1234/download"
    theme_type = "themes"
    filename = "awesome_theme.tar.gz"
    
    ocs_url = ocs_handler.create_ocs_url(download_url, theme_type, filename)
    print(f"URL de descarga: {download_url}")
    print(f"Tipo de tema: {theme_type}")
    print(f"Nombre de archivo: {filename}")
    print(f"URL OCS generada: {ocs_url}")
    
    # 2. Parsear URL OCS
    print("\n2️⃣ PARSENDO URL OCS")
    print("-"*30)
    
    parsed = ocs_handler.parse_ocs_url(ocs_url)
    print(f"Comando: {parsed['command']}")
    print(f"URL: {parsed['url']}")
    print(f"Tipo: {parsed['type']}")
    print(f"Archivo: {parsed['filename']}")
    
    # 3. Rutas de instalación
    print("\n3️⃣ RUTAS DE INSTALACIÓN")
    print("-"*30)
    
    types_to_show = ['themes', 'icons', 'cursors', 'gnome_shell_extensions']
    for theme_type in types_to_show:
        path = ocs_handler.get_install_path(theme_type)
        print(f"{theme_type:20} → {path}")

def demo_theme_management():
    """Demostrar gestión de temas"""
    print("\n4️⃣ GESTIÓN DE TEMAS")
    print("-"*30)
    
    # Listar temas instalados
    themes = ocs_handler.list_installed_themes('themes')
    print(f"Temas GTK instalados: {len(themes)}")
    
    if themes:
        print("Primeros 5 temas:")
        for i, theme in enumerate(themes[:5]):
            print(f"  {i+1}. {theme['name']}")
    else:
        print("  No hay temas instalados")
    
    # Listar iconos instalados
    icons = ocs_handler.list_installed_themes('icons')
    print(f"\nIconos instalados: {len(icons)}")
    
    if icons:
        print("Primeros 3 iconos:")
        for i, icon in enumerate(icons[:3]):
            print(f"  {i+1}. {icon['name']}")

def demo_installation_simulation():
    """Simular proceso de instalación"""
    print("\n5️⃣ SIMULACIÓN DE INSTALACIÓN")
    print("-"*30)
    
    # URL de ejemplo (no real)
    test_ocs_url = "ocs://install?url=https%3A//example.com/theme.tar.gz&type=themes&filename=test_theme.tar.gz"
    
    print(f"URL OCS de prueba: {test_ocs_url}")
    print("(Esta es una simulación, no se descargará nada real)")
    
    try:
        # Parsear la URL
        params = ocs_handler.parse_ocs_url(test_ocs_url)
        print(f"✅ URL parseada correctamente")
        print(f"   Comando: {params['command']}")
        print(f"   URL: {params['url']}")
        print(f"   Tipo: {params['type']}")
        
        # Obtener ruta de instalación
        install_path = ocs_handler.get_install_path(params['type'])
        print(f"   Se instalaría en: {install_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def demo_gnome_look_integration():
    """Demostrar integración con GNOME-Look"""
    print("\n6️⃣ INTEGRACIÓN CON GNOME-LOOK")
    print("-"*30)
    
    # URL de ejemplo de GNOME-Look
    gnome_look_url = "https://www.gnome-look.org/p/1234/"
    
    print(f"Obteniendo información de: {gnome_look_url}")
    print("(Esta es una demostración, la URL no es real)")
    
    try:
        info = ocs_handler.get_theme_info_from_gnome_look(gnome_look_url)
        print(f"Título: {info['title']}")
        print(f"Descripción: {info['description'][:100]}...")
        print(f"Enlaces de descarga encontrados: {len(info['download_links'])}")
        
        if info['download_links']:
            print("Primeros enlaces:")
            for i, link in enumerate(info['download_links'][:3]):
                print(f"  {i+1}. {link}")
                
    except Exception as e:
        print(f"❌ Error obteniendo información: {e}")

def show_usage_examples():
    """Mostrar ejemplos de uso"""
    print("\n7️⃣ EJEMPLOS DE USO")
    print("-"*30)
    
    print("📝 Cómo usar OCS en tu código:")
    print()
    
    print("1. Instalar tema desde URL OCS:")
    print("   success, result = ocs_handler.install_theme('ocs://install?url=...&type=themes')")
    print()
    
    print("2. Crear URL OCS:")
    print("   ocs_url = ocs_handler.create_ocs_url('https://...', 'themes', 'theme.tar.gz')")
    print()
    
    print("3. Listar temas instalados:")
    print("   themes = ocs_handler.list_installed_themes('themes')")
    print()
    
    print("4. Obtener información de GNOME-Look:")
    print("   info = ocs_handler.get_theme_info_from_gnome_look('https://www.gnome-look.org/p/...')")
    print()
    
    print("5. Remover tema:")
    print("   success = ocs_handler.remove_theme('theme_name', 'themes')")

def main():
    """Función principal de demostración"""
    print("🎨 GNOME THEME LOADER - INTEGRACIÓN OCS")
    print("="*60)
    print("Este script demuestra la integración del protocolo OCS")
    print("para instalación nativa de temas desde GNOME-Look.org")
    print("="*60)
    
    # Ejecutar todas las demostraciones
    demo_ocs_basics()
    demo_theme_management()
    demo_installation_simulation()
    demo_gnome_look_integration()
    show_usage_examples()
    
    print("\n" + "="*60)
    print("✅ DEMOSTRACIÓN COMPLETADA")
    print("="*60)
    print()
    print("🎯 PRÓXIMOS PASOS:")
    print("1. Ejecuta tu aplicación principal")
    print("2. Ve a la tienda de temas")
    print("3. Los temas ahora se instalarán usando OCS")
    print("4. ¡Disfruta de la instalación nativa de temas!")
    print()
    print("💡 Ventajas de OCS:")
    print("   • Instalación directa en ubicaciones correctas")
    print("   • Protocolo estándar de GNOME-Look.org")
    print("   • Sin necesidad de web scraping complejo")
    print("   • Manejo automático de archivos comprimidos")
    print("   • Compatible con el ecosistema GNOME")

if __name__ == "__main__":
    main() 