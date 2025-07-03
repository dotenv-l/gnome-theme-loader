<<<<<<< HEAD
# gnome-theme-loader
v.0.1
=======
# GNOME Theme Loader

> ⚠️ **ADVERTENCIA: Proyecto en desarrollo activo.**
> 
> Esta aplicación está en fase ALFA. Puede contener errores graves, afectar la sesión de usuario o requerir reinicio. **No la uses en entornos de producción ni en sistemas críticos.**

Una aplicación moderna para gestionar temas de GNOME con integración nativa del protocolo OCS (Open Collaboration Services).(sin funcionar)

## 🎯 Características principales

- **Instalación nativa de temas** usando el protocolo OCS
- **Interfaz moderna** con libadwaita
- **Gestión completa** de temas GTK, iconos, cursores, extensiones y GRUB
- **Tienda integrada** con temas populares
- **Asignación manual de iconos** a cualquier aplicación instalada
- **Vista previa y búsqueda eficiente de iconos**
- **Sin web scraping** - usa protocolos nativos de GNOME
- **Seguridad**: la asignación de iconos solo afecta el usuario actual y nunca modifica archivos del sistema

## 🚀 Instalación

### Dependencias

```bash
# Instalar dependencias del sistema
sudo apt install python3-gi python3-gi-cairo gir1.2-adw-1 python3-pip

# Instalar dependencias de Python
pip3 install -r requirements.txt
```

### Ejecutar

```bash
python3 main.py
```

## ⚠️ Advertencia de desarrollo

- Esta aplicación está en **desarrollo activo**. Puede colgar la sesión, mostrar errores inesperados o requerir reinicio de GNOME.
- **No uses en sistemas críticos.**
- Si encuentras un bug que afecta la sesión, elimina los overrides en `~/.local/share/applications/` relacionados o reinicia la sesión.

## 🔥 Novedades recientes

### Asignación manual de iconos
- Modal moderno para asignar cualquier icono a cualquier aplicación instalada.
- Búsqueda eficiente de aplicaciones e iconos.
- Vista previa de icono y nombre de tema en la misma línea.
- La asignación es **segura**: solo se crea un override local, nunca se modifica el archivo original del sistema.

### Mejoras visuales y de UX
- Sidebar y layout adaptativos.
- Sombras, bordes redondeados y transiciones suaves.
- Footer de actividades recientes y barra lateral de previsualización.

### Seguridad y robustez
- Corrección de bugs críticos que podían afectar la sesión.
- Validación estricta al modificar archivos `.desktop`.
- No se cambian permisos ni se sobrescriben archivos del sistema.

## 📁 Estructura del Proyecto

```
gnome-theme-loader/
├── main.py                 # Punto de entrada principal
├── theme_loader/          # Módulo principal
│   ├── app.py            # Aplicación principal
│   ├── core/             # Lógica de negocio
│   │   ├── theme_store.py    # Tienda de temas con OCS
│   │   ├── theme_manager.py  # Gestión de temas
│   │   └── theme_applier.py  # Aplicación de temas
│   ├── ui/               # Interfaz de usuario
│   │   ├── window.py         # Ventana principal
│   │   ├── store_window.py   # Ventana de tienda
│   │   └── components.py     # Componentes UI
│   └── utils/            # Utilidades
│       ├── ocs_handler.py    # Manejador OCS
│       └── gsettings.py      # Configuración GNOME
├── ocs-url/              # Implementación del protocolo OCS
└── requirements.txt      # Dependencias
```

## 🛠️ Desarrollo y pruebas

### Pruebas

```bash
# Probar integración OCS
python3 test_ocs_integration.py

# Probar manejador OCS
python3 test_ocs.py

# Demostración de OCS
python3 demo_ocs_integration.py
```

### Arquitectura

- **Sin web scraping**: La aplicación no usa BeautifulSoup ni parsing de HTML
- **Protocolo OCS nativo**: Usa el protocolo estándar de GNOME-Look.org
- **Interfaz moderna**: Basada en libadwaita para una experiencia GNOME nativa
- **Modular**: Código organizado en módulos reutilizables

## 🎨 Tipos de Temas Soportados

- **Temas GTK**: Temas para aplicaciones GTK3/GTK4
- **Iconos**: Packs de iconos para el sistema
- **Cursores**: Temas de cursor personalizados
- **Extensiones GNOME Shell**: Extensiones para GNOME Shell
- **Temas GRUB**: Temas para el gestor de arranque

## 📝 Licencia

Este proyecto está bajo la licencia GPL v3.

## 🤝 Contribuir

1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Si encuentras problemas o tienes sugerencias, por favor abre un issue en el repositorio.
>>>>>>> 4d0753b (Versión inicial: GNOME Theme Loader (ALFA, en desarrollo))
