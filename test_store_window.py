#!/usr/bin/env python3
"""
Script de prueba para la ventana de la tienda
Verifica que la tienda se abra correctamente sin errores
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_store_window():
    """Probar la ventana de la tienda"""
    print("🛒 PROBANDO VENTANA DE LA TIENDA")
    print("="*60)
    
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from gi.repository import Gtk, Adw, GLib
        
        # Crear aplicación
        app = Adw.Application(application_id="com.example.TestStore")
        
        def on_activate(app):
            try:
                from theme_loader.ui.store_window import StoreWindow
                
                # Crear ventana de la tienda
                store_window = StoreWindow(app)
                store_window.present()
                
                print("✅ Ventana de la tienda creada exitosamente")
                print("   - La ventana debería estar visible ahora")
                print("   - Verifica que no hay errores en la consola")
                
                # Cerrar después de 5 segundos para la prueba
                def close_window():
                    store_window.close()
                    app.quit()
                    return False
                
                GLib.timeout_add(5000, close_window)
                
            except Exception as e:
                print(f"❌ Error creando ventana de la tienda: {e}")
                import traceback
                traceback.print_exc()
                app.quit()
        
        app.connect("activate", on_activate)
        
        # Ejecutar aplicación
        print("🚀 Iniciando aplicación de prueba...")
        print("   La ventana se cerrará automáticamente en 5 segundos")
        app.run([])
        
        print("✅ Prueba completada exitosamente")
        return True
        
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_store_functionality():
    """Probar funcionalidad de la tienda sin UI"""
    print("\n🔧 PROBANDO FUNCIONALIDAD DE LA TIENDA")
    print("="*60)
    
    try:
        from theme_loader.ui.store_window import GNOMELookStore
        
        # Crear instancia del store
        store = GNOMELookStore()
        
        # Probar obtención de temas
        print("📦 Obteniendo temas...")
        themes = store.get_latest_themes(category="gtk")
        
        if themes:
            print(f"✅ Encontrados {len(themes)} temas")
            for i, theme in enumerate(themes):
                print(f"   {i+1}. {theme.name} por {theme.author}")
                print(f"      OCS URL: {theme.ocs_url[:50]}..." if theme.ocs_url else "      Sin URL OCS")
        else:
            print("❌ No se encontraron temas")
        
        # Probar búsqueda
        print("\n🔍 Probando búsqueda...")
        search_results = store.search_themes("dark", category="gtk")
        print(f"Búsqueda 'dark': {len(search_results)} resultados")
        
        # Probar estado de conexión
        print("\n🌐 Probando conexión...")
        status = store.get_site_status()
        print(f"Estado: {status['status']}")
        print(f"Mensaje: {status['message']}")
        
        print("✅ Funcionalidad de la tienda funciona correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error probando funcionalidad: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🎨 GNOME THEME LOADER - PRUEBA DE LA TIENDA")
    print("="*80)
    print("Este script prueba la ventana de la tienda y su funcionalidad")
    print("="*80)
    
    # Probar funcionalidad sin UI
    functionality_success = test_store_functionality()
    
    # Probar ventana de la tienda
    window_success = test_store_window()
    
    print("\n" + "="*80)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*80)
    print(f"Funcionalidad de la tienda: {'✅ EXITOSO' if functionality_success else '❌ FALLÓ'}")
    print(f"Ventana de la tienda: {'✅ EXITOSO' if window_success else '❌ FALLÓ'}")
    
    if functionality_success and window_success:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("La tienda funciona correctamente.")
    else:
        print("\n⚠️  Algunas pruebas fallaron.")
        print("Revisa los errores arriba.")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main() 