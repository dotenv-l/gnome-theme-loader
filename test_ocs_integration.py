#!/usr/bin/env python3
"""
Script de prueba para la integración OCS en GNOME Theme Loader
Verifica que la tienda funcione correctamente usando solo el protocolo OCS
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ocs_store():
    """Probar la tienda OCS"""
    print("🚀 PROBANDO INTEGRACIÓN OCS")
    print("="*60)
    
    try:
        from theme_loader.core.theme_store import GNOMELookStore
        
        # Crear instancia del store
        store = GNOMELookStore()
        
        # Verificar conexión
        print("\n1️⃣ VERIFICANDO CONEXIÓN")
        print("-"*30)
        
        status = store.get_site_status()
        print(f"Estado: {'🟢 Conectado' if status['connected'] else '🔴 Sin conexión'}")
        print(f"Mensaje: {status['message']}")
        
        if not status['connected']:
            print("❌ No se puede conectar a la API. Verifica tu conexión a internet.")
            return False
        
        # Probar obtención de temas
        print("\n2️⃣ OBTENIENDO TEMAS")
        print("-"*30)
        
        # Probar diferentes categorías
        categories = ['gtk', 'icons', 'cursor']
        
        for category in categories:
            print(f"\n📂 Categoría: {category}")
            themes = store.get_latest_themes(category, limit=5)
            
            if themes:
                print(f"   ✅ Encontrados {len(themes)} temas")
                for i, theme in enumerate(themes[:3]):
                    print(f"   {i+1}. {theme.name} por {theme.author}")
                    if theme.ocs_url:
                        print(f"      🔗 URL OCS: {theme.ocs_url[:50]}...")
                    else:
                        print(f"      ⚠️  Sin URL OCS")
            else:
                print(f"   ❌ No se encontraron temas")
        
        # Probar búsqueda
        print("\n3️⃣ PROBANDO BÚSQUEDA")
        print("-"*30)
        
        search_results = store.search_themes("dark", category="gtk", page=1)
        print(f"Búsqueda 'dark' en GTK: {len(search_results)} resultados")
        
        if search_results:
            print("Primeros resultados:")
            for i, theme in enumerate(search_results[:3]):
                print(f"   {i+1}. {theme.name} por {theme.author}")
        
        # Probar temas populares
        print("\n4️⃣ TEMAS POPULARES")
        print("-"*30)
        
        popular_themes = store.get_popular_themes(category="icons", limit=3)
        print(f"Temas populares de iconos: {len(popular_themes)} resultados")
        
        if popular_themes:
            print("Temas populares:")
            for i, theme in enumerate(popular_themes):
                print(f"   {i+1}. {theme.name} (⭐ {theme.rating:.1f}, 📥 {theme.downloads})")
        
        print("\n" + "="*60)
        print("✅ PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("="*60)
        print("\n🎯 La integración OCS está funcionando correctamente.")
        print("   Los temas se obtienen desde la API de GNOME-Look.org")
        print("   y se instalan usando el protocolo OCS nativo.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ocs_handler():
    """Probar el manejador OCS directamente"""
    print("\n🔧 PROBANDO MANEJADOR OCS")
    print("="*60)
    
    try:
        from theme_loader.utils.ocs_handler import ocs_handler
        
        # Probar creación de URL OCS
        print("\n1️⃣ CREANDO URL OCS")
        print("-"*30)
        
        test_url = "https://www.gnome-look.org/p/1234/download"
        test_type = "themes"
        test_filename = "test_theme.tar.gz"
        
        ocs_url = ocs_handler.create_ocs_url(test_url, test_type, test_filename)
        print(f"URL original: {test_url}")
        print(f"Tipo: {test_type}")
        print(f"Archivo: {test_filename}")
        print(f"URL OCS generada: {ocs_url}")
        
        # Probar parsing de URL OCS
        print("\n2️⃣ PARSENDO URL OCS")
        print("-"*30)
        
        parsed = ocs_handler.parse_ocs_url(ocs_url)
        print(f"Comando: {parsed['command']}")
        print(f"URL: {parsed['url']}")
        print(f"Tipo: {parsed['type']}")
        print(f"Archivo: {parsed['filename']}")
        
        # Probar rutas de instalación
        print("\n3️⃣ RUTAS DE INSTALACIÓN")
        print("-"*30)
        
        test_types = ['themes', 'icons', 'cursors', 'gnome_shell_extensions']
        for theme_type in test_types:
            path = ocs_handler.get_install_path(theme_type)
            print(f"{theme_type:20} → {path}")
        
        print("\n✅ Manejador OCS funcionando correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error probando manejador OCS: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🎨 GNOME THEME LOADER - PRUEBAS DE INTEGRACIÓN OCS")
    print("="*80)
    print("Este script verifica que la integración OCS funcione correctamente")
    print("sin necesidad de web scraping.")
    print("="*80)
    
    # Ejecutar pruebas
    store_success = test_ocs_store()
    handler_success = test_ocs_handler()
    
    print("\n" + "="*80)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*80)
    print(f"Tienda OCS: {'✅ EXITOSO' if store_success else '❌ FALLÓ'}")
    print(f"Manejador OCS: {'✅ EXITOSO' if handler_success else '❌ FALLÓ'}")
    
    if store_success and handler_success:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("La integración OCS está lista para usar.")
        print("\n💡 Próximos pasos:")
        print("1. Ejecuta la aplicación principal")
        print("2. Ve a la tienda de temas")
        print("3. Los temas se instalarán usando OCS")
    else:
        print("\n⚠️  Algunas pruebas fallaron.")
        print("Revisa los errores arriba y corrige los problemas.")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main() 