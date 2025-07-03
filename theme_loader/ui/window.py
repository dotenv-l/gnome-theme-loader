"""
Main Window module for GNOME Theme Loader - Improved UX Version
Contains the main application window and UI logic with enhanced user experience
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Adw, Gdk, Gio, GLib, GObject, GdkPixbuf  # type: ignore
from pathlib import Path
import subprocess
import os
import configparser
import threading

# Importar módulos locales
from .components import DropZone, ThemeCard, ActivityLog, ModernToast, ThemePreview
from .styles import load_styles
from ..core.theme_manager import ThemeManager
from ..core.theme_scanner import ThemeScanner
from ..core.theme_applier import ThemeApplier
from theme_loader.utils import list_installed_applications, list_all_theme_icons, assign_custom_icon_to_app

class Window(Adw.ApplicationWindow):
    """Ventana principal de la aplicación con UX mejorada"""
    
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="GNOME Theme Loader")
        
        # Configurar ventana
        self.set_default_size(1200, 800)
        self.set_size_request(900, 600)
        
        # Estado de la aplicación
        self.current_theme_type = "gtk"
        self.is_loading = False
        self.applied_themes = {}  # Temas aplicados actualmente
        
        # Inicializar componentes core
        self.theme_manager = ThemeManager()
        self.theme_scanner = ThemeScanner()
        self.theme_applier = ThemeApplier(callback=self._log_message)
        
        # Cargar estilos
        load_styles()
        
        # Construir UI
        self._build_ui()
        
        # Inicializar componentes
        self._create_theme_pages()
        
        # Conectar acciones del menú
        self._connect_menu_actions()
        
        # Cargar datos iniciales
        GLib.timeout_add(500, self._initial_load)
    
    def _connect_menu_actions(self):
        """Conectar acciones del menú principal"""
        app = self.get_application()
        
        # Acción de configuración
        config_action = Gio.SimpleAction.new("configuration", None)
        config_action.connect("activate", lambda action, param: self._show_configuration_dialog())
        app.add_action(config_action)
        
        # Acción de preferencias (placeholder)
        prefs_action = Gio.SimpleAction.new("preferences", None)
        prefs_action.connect("activate", lambda action, param: self._show_toast("⚙️ Preferencias próximamente", True))
        app.add_action(prefs_action)
        
        # Acción de ayuda (placeholder)
        help_action = Gio.SimpleAction.new("help", None)
        help_action.connect("activate", lambda action, param: self._show_toast("❓ Ayuda próximamente", True))
        app.add_action(help_action)
        
        # Acción de acerca de (placeholder)
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", lambda action, param: self._show_toast("ℹ️ GNOME Theme Loader\nVersión 1.0\nDesarrollado por tu equipo", True))
        app.add_action(about_action)
        
        # Reiniciar app
        restart_action = Gio.SimpleAction.new("restart", None)
        restart_action.connect("activate", lambda action, param: self._restart_app())
        app.add_action(restart_action)
        
        # Exportar configuración
        export_action = Gio.SimpleAction.new("export", None)
        export_action.connect("activate", lambda action, param: self._show_toast("🗄️ Exportar configuración próximamente", True))
        app.add_action(export_action)
        
        # Importar configuración
        import_action = Gio.SimpleAction.new("import", None)
        import_action.connect("activate", lambda action, param: self._show_toast("📂 Importar configuración próximamente", True))
        app.add_action(import_action)
        
        # Ver logs avanzados
        logs_action = Gio.SimpleAction.new("logs", None)
        logs_action.connect("activate", lambda action, param: self._show_toast("📝 Logs avanzados próximamente", True))
        app.add_action(logs_action)
    
    def _build_ui(self):
        """Construir la interfaz de usuario con diseño mejorado"""
        # Panel principal vertical
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        # Header bar
        header_bar = self._create_header_bar()
        main_box.append(header_bar)
        # Contenedor central (sidebar, centro, preview)
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        content_box.set_hexpand(True)
        content_box.set_vexpand(True)
        main_box.append(content_box)
        # Sidebar
        left_panel_box = self._build_left_panel()
        left_panel_box.set_hexpand(False)
        content_box.append(left_panel_box)
        # Panel central
        center_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        center_panel.set_hexpand(True)
        center_panel.set_vexpand(True)
        center_panel.set_margin_top(24)
        center_panel.set_margin_bottom(24)
        center_panel.set_margin_start(24)
        center_panel.set_margin_end(24)
        # Botón de instalación manual flotante
        self.manual_install_btn = Gtk.Button(label="+ Instalar manualmente")
        self.manual_install_btn.set_css_classes(["manual-install-btn"])
        self.manual_install_btn.set_halign(Gtk.Align.START)
        self.manual_install_btn.connect("clicked", self._on_install_clicked)
        center_panel.append(self.manual_install_btn)
        # Stack para contenido de temas
        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.content_stack.set_transition_duration(200)
        self.content_stack.set_hexpand(True)
        self.content_stack.set_vexpand(True)
        center_panel.append(self.content_stack)
        # Spinner de carga central
        self.center_spinner = Gtk.Spinner()
        self.center_spinner.set_halign(Gtk.Align.CENTER)
        self.center_spinner.set_valign(Gtk.Align.CENTER)
        self.center_spinner.set_visible(False)
        center_panel.append(self.center_spinner)
        content_box.append(center_panel)
        # Barra lateral derecha colapsable para vista previa
        self.preview_expanded = False
        self.preview_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.preview_panel.set_size_request(48, -1)
        self.preview_panel.set_hexpand(False)
        self.preview_panel.set_vexpand(True)
        self.preview_panel.set_css_classes(["preview-sidebar"])
        # Botón de ojo para expandir/contraer
        self.preview_toggle_btn = Gtk.Button()
        self.preview_toggle_btn.set_icon_name("view-preview-symbolic")
        self.preview_toggle_btn.set_tooltip_text("Mostrar/Ocultar vista previa")
        self.preview_toggle_btn.set_css_classes(["flat", "preview-toggle-btn"])
        self.preview_toggle_btn.connect("clicked", self._on_toggle_preview_sidebar)
        self.preview_panel.append(self.preview_toggle_btn)
        # Contenedor de vista previa (solo visible si expandido)
        self.preview_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.preview_content_box.set_hexpand(True)
        self.preview_content_box.set_vexpand(True)
        self.preview_content_box.set_visible(False)
        self.preview_panel.append(self.preview_content_box)
        content_box.append(self.preview_panel)
        # Footer de actividad reciente
        self.activity_footer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.activity_footer.set_size_request(-1, 150)
        self.activity_footer.set_hexpand(True)
        self.activity_footer.set_vexpand(False)
        self.activity_footer.set_css_classes(["activity-footer"])
        # Título y log
        activity_title = Gtk.Label(label="Actividad Reciente")
        activity_title.set_css_classes(["heading"])
        activity_title.set_halign(Gtk.Align.START)
        self.activity_footer.append(activity_title)
        self.activity_log = ActivityLog(compact=True, max_items=8)
        self.activity_footer.append(self.activity_log)
        main_box.append(self.activity_footer)
        # Overlay para toasts
        self.toast_overlay = Gtk.Overlay()
        self.toast_overlay.set_child(main_box)
        self.set_content(self.toast_overlay)
    
    def _create_header_bar(self):
        """Crear header bar moderna"""
        header_bar = Adw.HeaderBar()
        header_bar.set_css_classes(["flat"])
        # self.set_titlebar(header_bar)  # Eliminado para AdwWindow
        
        # Título dinámico
        self.header_title = Adw.WindowTitle()
        self.header_title.set_title("GNOME Theme Loader")
        self.header_title.set_subtitle("Temas GTK")
        header_bar.set_title_widget(self.header_title)
        
        # Botones del header - lado izquierdo
        self._create_header_left_buttons(header_bar)
        
        # Botones del header - lado derecho
        self._create_header_right_buttons(header_bar)
        return header_bar
    
    def _create_header_left_buttons(self, header_bar):
        """Crear botones del lado izquierdo del header"""
        # Botón de engrane como menú principal
        gear_btn = Gtk.MenuButton()
        gear_btn.set_icon_name("emblem-system-symbolic")
        gear_btn.set_tooltip_text("Menú principal")
        # Menú contextual completo
        menu = Gio.Menu()
        menu.append("Tienda de Temas", "app.store")
        menu.append("Configuración", "app.configuration")
        menu.append("Preferencias", "app.preferences")
        menu.append("Ayuda", "app.help")
        menu.append("Acerca de", "app.about")
        menu.append("Reiniciar App", "app.restart")
        menu.append("Exportar Configuración", "app.export")
        menu.append("Importar Configuración", "app.import")
        menu.append("Ver Logs Avanzados", "app.logs")
        gear_btn.set_menu_model(menu)
        header_bar.pack_start(gear_btn)
        # Indicador de estado/carga
        self.status_spinner = Gtk.Spinner()
        self.status_spinner.set_visible(False)
        header_bar.pack_start(self.status_spinner)
    
    def _create_header_right_buttons(self, header_bar):
        """Crear botones del lado derecho del header"""
        # Búsqueda
        search_button = Gtk.ToggleButton()
        search_button.set_icon_name("system-search-symbolic")
        search_button.set_tooltip_text("Buscar temas")
        search_button.connect("toggled", self._on_search_toggled)
        header_bar.pack_end(search_button)
        
        # Refrescar
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text("Actualizar lista de temas")
        refresh_button.connect("clicked", self._on_refresh_clicked)
        header_bar.pack_end(refresh_button)
        
        # Instalar tema
        install_button = Gtk.Button()
        install_button.set_css_classes(["suggested-action"])
        install_button.set_icon_name("document-open-symbolic")
        install_button.set_tooltip_text("Instalar nuevo tema")
        install_button.connect("clicked", self._on_install_clicked)
        header_bar.pack_end(install_button)
    
    def _build_left_panel(self) -> Gtk.Box:
        """Panel lateral izquierdo colapsable con navegación y acciones"""
        self.sidebar_expanded = True
        self.sidebar_width_expanded = 220
        self.sidebar_width_collapsed = 60
        self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.sidebar_box.set_size_request(self.sidebar_width_expanded, -1)
        self.sidebar_box.set_hexpand(False)
        self.sidebar_box.set_vexpand(True)
        self.sidebar_box.set_css_classes(["sidebar"])
        # Botón expandir/contraer justo encima de categorías
        self.sidebar_toggle_btn = Gtk.Button()
        self.sidebar_toggle_btn.set_icon_name("pan-end-symbolic")
        self.sidebar_toggle_btn.set_css_classes(["flat", "sidebar-toggle-btn"])
        self.sidebar_toggle_btn.set_tooltip_text("Expandir/Contraer barra lateral")
        self.sidebar_toggle_btn.connect("clicked", self._on_toggle_sidebar)
        self.sidebar_box.append(self.sidebar_toggle_btn)
        # Categorías
        self.category_panel = self._build_category_panel()
        self.sidebar_box.append(self.category_panel)
        # Separador
        self.sidebar_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        # Acciones rápidas
        self.quick_actions_panel = self._build_quick_actions()
        self.sidebar_box.append(self.quick_actions_panel)
        return self.sidebar_box

    def _on_toggle_sidebar(self, button):
        self.sidebar_expanded = not self.sidebar_expanded
        width = self.sidebar_width_expanded if self.sidebar_expanded else self.sidebar_width_collapsed
        self.sidebar_box.set_size_request(width, -1)
        # Cambiar iconos/textos en categorías y acciones
        for btn in self.category_buttons.values():
            box = btn.get_child()
            if not box: continue
            children = list(box)
            if len(children) > 1:
                label = children[1]
                label.set_visible(self.sidebar_expanded)
            btn.set_tooltip_text(btn.get_tooltip_text() if self.sidebar_expanded else children[1].get_text())
        for btn in self.quick_action_buttons:
            box = btn.get_child()
            if not box: continue
            children = list(box)
            if len(children) > 1:
                label = children[1]
                label.set_visible(self.sidebar_expanded)
            btn.set_tooltip_text(btn.get_tooltip_text() if self.sidebar_expanded else children[1].get_text())
        # Cambiar icono del botón de toggle
        if self.sidebar_expanded:
            self.sidebar_toggle_btn.set_icon_name("pan-end-symbolic")
        else:
            self.sidebar_toggle_btn.set_icon_name("pan-start-symbolic")

    def _build_category_panel(self) -> Gtk.Box:
        """Panel de categorías solo iconos o iconos+texto según expansión"""
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        panel.set_margin_top(16)
        panel.set_margin_bottom(16)
        panel.set_margin_start(8)
        panel.set_margin_end(8)
        self.category_buttons = {}
        nav_items = [
            ("gtk", "Temas GTK", "applications-graphics-symbolic"),
            ("shell", "GNOME Shell", "desktop-symbolic"),
            ("icons", "Paquetes de Iconos", "folder-pictures-symbolic"),
            ("cursor", "Cursores", "input-mouse-symbolic"),
            ("grub", "GRUB", "computer-symbolic")
        ]
        for theme_type, label, icon_name in nav_items:
            btn = Gtk.Button()
            btn.set_css_classes(["flat", "nav-button"])
            btn.set_tooltip_text(label)
            btn.set_hexpand(True)
            btn.set_halign(Gtk.Align.FILL)
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            icon = Gtk.Image()
            icon.set_from_icon_name(icon_name)
            icon.set_pixel_size(20)
            box.append(icon)
            label_widget = Gtk.Label(label=label)
            label_widget.set_xalign(0)
            label_widget.set_visible(self.sidebar_expanded)
            box.append(label_widget)
            btn.set_child(box)
            btn.connect("clicked", self._on_category_selected, theme_type)
            self.category_buttons[theme_type] = btn
            panel.append(btn)
        return panel

    def _build_quick_actions(self) -> Gtk.Box:
        """Panel de acciones rápidas solo iconos o iconos+texto según expansión"""
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        panel.set_margin_top(16)
        panel.set_margin_bottom(16)
        panel.set_margin_start(8)
        panel.set_margin_end(8)
        self.quick_action_buttons = []
        actions = [
            ("Restablecer Todo", "edit-undo-symbolic", self._on_reset_all_clicked),
            ("Crear Respaldo", "document-save-symbolic", self._on_backup_clicked),
            ("Importar Config", "document-open-symbolic", self._on_import_config_clicked)
        ]
        for label, icon_name, callback in actions:
            btn = Gtk.Button()
            btn.set_css_classes(["flat", "action-button"])
            btn.set_tooltip_text(label)
            btn.set_hexpand(True)
            btn.set_halign(Gtk.Align.FILL)
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            icon = Gtk.Image()
            icon.set_from_icon_name(icon_name)
            icon.set_pixel_size(18)
            box.append(icon)
            label_widget = Gtk.Label(label=label)
            label_widget.set_xalign(0)
            label_widget.set_visible(self.sidebar_expanded)
            box.append(label_widget)
            btn.set_child(box)
            btn.connect("clicked", callback)
            self.quick_action_buttons.append(btn)
            panel.append(btn)
        return panel

    def _create_theme_pages(self):
        """Crear páginas para cada tipo de tema"""
        theme_types = ["gtk", "shell", "icons", "cursor", "grub"]
        
        for theme_type in theme_types:
            page = self._create_theme_page(theme_type)
            self.content_stack.add_named(page, theme_type)
        
        # Mostrar página inicial
        self.content_stack.set_visible_child_name("gtk")
    
    def _create_theme_page(self, theme_type: str) -> Gtk.ScrolledWindow:
        """Crear página individual para tipo de tema"""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        # Solo para la categoría de iconos, agrega el botón de personalización
        if theme_type == "icons":
            customize_btn = Gtk.Button(label="Personalizar icono de aplicación")
            customize_btn.set_css_classes(["suggested-action", "customize-app-icon-btn"])
            customize_btn.set_halign(Gtk.Align.START)
            customize_btn.connect("clicked", self._on_customize_app_icon)
            container.append(customize_btn)
        # Grid de temas compacta
        self.theme_grids = getattr(self, 'theme_grids', {})
        self.theme_grids[theme_type] = Gtk.FlowBox()
        self.theme_grids[theme_type].set_valign(Gtk.Align.START)
        self.theme_grids[theme_type].set_max_children_per_line(4)
        self.theme_grids[theme_type].set_selection_mode(Gtk.SelectionMode.NONE)
        self.theme_grids[theme_type].set_homogeneous(True)
        self.theme_grids[theme_type].set_column_spacing(16)
        self.theme_grids[theme_type].set_row_spacing(16)
        self.theme_grids[theme_type].set_css_classes(["theme-grid"])
        container.append(self.theme_grids[theme_type])
        # Placeholder para cuando no hay temas
        self.empty_states = getattr(self, 'empty_states', {})
        self.empty_states[theme_type] = self._create_empty_state(theme_type)
        container.append(self.empty_states[theme_type])
        scrolled.set_child(container)
        return scrolled
    
    def _create_empty_state(self, theme_type: str) -> Gtk.Box:
        """Crear estado vacío para cuando no hay temas"""
        empty_state = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        empty_state.set_valign(Gtk.Align.CENTER)
        empty_state.set_vexpand(True)
        empty_state.set_visible(False)
        
        # Icono grande
        icon = Gtk.Image()
        icon.set_from_icon_name("folder-symbolic")
        icon.set_pixel_size(64)
        icon.set_css_classes(["dim-label"])
        empty_state.append(icon)
        
        # Texto principal
        title = Gtk.Label(label=f"No hay temas {theme_type.upper()} instalados")
        title.set_css_classes(["title-2"])
        empty_state.append(title)
        
        # Texto secundario
        subtitle = Gtk.Label()
        subtitle.set_text("Arrastra archivos aquí o usa el botón 'Instalar' para agregar temas")
        subtitle.set_css_classes(["body"])
        subtitle.set_wrap(True)
        subtitle.set_justify(Gtk.Justification.CENTER)
        empty_state.append(subtitle)
        
        # Botón de acción
        action_btn = Gtk.Button(label="Buscar Temas Online")
        action_btn.set_css_classes(["pill", "suggested-action"])
        action_btn.connect("clicked", self._on_find_themes_online, theme_type)
        empty_state.append(action_btn)
        
        return empty_state
    
    # Event handlers
    def _on_nav_button_clicked(self, button, theme_type):
        """Manejar navegación entre categorías"""
        # Actualizar botones activos
        for btn in self.nav_buttons.values():
            btn.remove_css_class("suggested-action")
        button.add_css_class("suggested-action")
        
        # Cambiar contenido
        self.current_theme_type = theme_type
        self.content_stack.set_visible_child_name(theme_type)
        
        # Actualizar título
        titles = {
            "gtk": "Temas GTK",
            "shell": "GNOME Shell",
            "icons": "Paquetes de Iconos", 
            "cursor": "Cursores",
            "grub": "Temas GRUB"
        }
        self.header_title.set_subtitle(titles.get(theme_type, "Temas"))
    
    def _on_search_toggled(self, button):
        """Toggle barra de búsqueda"""
        self.search_bar.set_search_mode(button.get_active())
    
    def _on_search_changed(self, entry):
        """Filtrar temas según búsqueda"""
        search_text = entry.get_text().lower()
        # Implementar filtrado de temas
        self._filter_themes(search_text)
    
    def _on_refresh_clicked(self, button):
        """Refrescar temas"""
        if not self.is_loading:
            self._refresh_all_themes()
    
    def _on_install_clicked(self, button):
        """Abrir diálogo de instalación"""
        self._show_install_dialog()
    
    def _on_reset_all_clicked(self, button):
        """Restablecer todos los temas"""
        self._show_reset_confirmation()
    
    def _on_backup_clicked(self, button):
        """Crear respaldo de configuración"""
        self._create_theme_backup()
    
    def _on_import_config_clicked(self, button):
        """Importar configuración"""
        self._show_import_dialog()
    
    def _on_expand_activity_clicked(self, button):
        """Expandir vista de actividad"""
        # Cambiar a página de historial completo
        if not self.content_stack.get_child_by_name("history"):
            history_page = self._create_full_history_page()
            self.content_stack.add_named(history_page, "history")
        self.content_stack.set_visible_child_name("history")
    
    def _on_find_themes_online(self, button, theme_type):
        """Abrir navegador para buscar temas online"""
        urls = {
            "gtk": "https://www.gnome-look.org/browse/cat/135/",
            "shell": "https://www.gnome-look.org/browse/cat/134/",
            "icons": "https://www.gnome-look.org/browse/cat/132/",
            "cursor": "https://www.gnome-look.org/browse/cat/107/",
            "grub": "https://www.gnome-look.org/browse/cat/109/"
        }
        
        if theme_type in urls:
            Gtk.show_uri(self, urls[theme_type], Gdk.CURRENT_TIME)
    
    # Core functionality methods
    def _initial_load(self):
        """Carga inicial de la aplicación"""
        self._set_loading(True)
        self._log_message("Iniciando GNOME Theme Loader...", "info")
        self._refresh_all_themes()
        return False
    
    def _refresh_all_themes(self):
        """Refrescar todos los temas"""
        if self.is_loading:
            return
        
        self._set_loading(True)
        self._log_message("Escaneando temas instalados...", "info")
        
        # Escanear temas
        themes = self.theme_manager.scan_themes()
        
        # Actualizar contadores y páginas
        total_themes = 0
        for theme_type, theme_list in themes.items():
            count = len(theme_list)
            total_themes += count
            
            # Actualizar página
            self._populate_theme_page(theme_type, theme_list)
        
        # Actualizar temas actuales
        self._update_current_themes_display()
        
        self._log_message(f"Escaneo completado: {total_themes} temas encontrados", "success")
        self._set_loading(False)
    
    def _populate_theme_page(self, theme_type: str, themes: list):
        """Poblar página de temas con grid mejorado"""
        if theme_type not in self.theme_grids:
            return
        
        grid = self.theme_grids[theme_type]
        empty_state = self.empty_states[theme_type]
        
        # Limpiar grid
        while grid.get_first_child():
            grid.remove(grid.get_first_child())
        
        if not themes:
            grid.set_visible(False)
            empty_state.set_visible(True)
            return
        
        grid.set_visible(True)
        empty_state.set_visible(False)
        
        # Obtener tema aplicado actual
        applied_name = self.applied_themes.get(theme_type, None)
        
        # Agregar temas como cards mejoradas
        for theme in themes:
            is_applied = (applied_name == theme["name"])
            description = None
            # Intentar leer descripción corta de index.theme si existe
            index_path = os.path.join(theme["path"], "index.theme")
            if os.path.exists(index_path):
                config = configparser.ConfigParser()
                try:
                    config.read(index_path)
                    if config.has_option("Desktop Entry", "Comment"):
                        description = config.get("Desktop Entry", "Comment")
                except Exception:
                    pass
            card = ThemeCard(
                name=theme["name"],
                theme_type=theme_type,
                path=theme["path"],
                apply_callback=self._apply_theme_with_feedback,
                preview_callback=self._preview_theme,
                delete_callback=self._delete_theme,
                is_applied=is_applied,
                description=description
            )
            grid.append(card)
    
    def _apply_theme_with_feedback(self, theme_type: str, name: str, card_widget):
        """Aplicar tema con feedback mejorado"""
        self._log_message(f"Aplicando tema {name}...", "info")
        
        # Aplicar tema
        success = self.theme_applier.apply_theme(theme_type, name, self._log_message)
        
        # Actualizar estado
        if success:
            self.applied_themes[theme_type] = name
            self._show_toast(f"✓ {name} aplicado correctamente", True)
            self._update_current_themes_display()
        else:
            self._show_toast(f"✗ Error al aplicar {name}", False)
        
        # Actualizar estado de la card
        if card_widget:
            card_widget.set_loading(False)
    
    def _preview_theme(self, theme_type: str, name: str, path: str):
        # Mostrar la vista previa en el panel derecho
        self.preview_expanded = True
        self.preview_panel.set_size_request(320, -1)
        self.preview_content_box.set_visible(True)
        # Limpiar contenido anterior
        for child in list(self.preview_content_box):
            self.preview_content_box.remove(child)
        # Icono grande
        icon = Gtk.Image()
        icon.set_from_icon_name("applications-graphics-symbolic")
        icon.set_pixel_size(64)
        self.preview_content_box.append(icon)
        # Nombre
        name_label = Gtk.Label(label=name)
        name_label.set_css_classes(["heading"])
        name_label.set_halign(Gtk.Align.START)
        self.preview_content_box.append(name_label)
        # Tipo
        type_label = Gtk.Label(label=f"Tipo: {theme_type.upper()}")
        type_label.set_css_classes(["caption"])
        type_label.set_halign(Gtk.Align.START)
        self.preview_content_box.append(type_label)
        # Ruta
        path_label = Gtk.Label(label=f"Ruta: {path}")
        path_label.set_css_classes(["caption", "dim-label"])
        path_label.set_halign(Gtk.Align.START)
        self.preview_content_box.append(path_label)
        # ... puedes agregar más detalles aquí ...
    
    def _show_large_preview(self, theme_type, name, path):
        # Implementar modal o ventana para vista previa grande
        pass
    
    def _filter_themes(self, search_text: str):
        """Filtrar temas según texto de búsqueda"""
        if not hasattr(self, 'theme_grids'):
            return
        
        current_grid = self.theme_grids.get(self.current_theme_type)
        if not current_grid:
            return
        
        # Iterar sobre las cards y mostrar/ocultar según búsqueda
        child = current_grid.get_first_child()
        while child:
            if hasattr(child, 'theme_name'):
                theme_name = child.theme_name.lower()
                visible = search_text in theme_name if search_text else True
                child.set_visible(visible)
            child = child.get_next_sibling()
    
    def _update_current_themes_display(self):
        # Ya no se usa category_content_box, así que este método puede quedar vacío o solo actualizar el estado si es necesario
        pass
    
    def _set_loading(self, loading: bool):
        """Mostrar/ocultar spinner de carga central"""
        if loading:
            self.center_spinner.set_visible(True)
            self.center_spinner.start()
        else:
            self.center_spinner.set_visible(False)
            self.center_spinner.stop()
    
    def _process_file(self, file_path: Path):
        """Procesar archivo de tema con feedback mejorado"""
        if not file_path.exists():
            self._log_message(f"Archivo no encontrado: {file_path}", "error")
            self._show_toast(f"✗ Archivo no encontrado", False)
            return
        
        self._log_message(f"Procesando archivo: {file_path.name}", "info") 
        self._show_toast(f"📦 Procesando {file_path.name}...", True)
        
        # Instalar tema con callback de progreso
        installed_theme_name = {"name": None, "type": None}
        def progress_callback(message, msg_type):
            self._log_message(message, msg_type)
            # Detectar nombre y tipo del tema instalado desde el mensaje
            if msg_type == "info" and ("aplicado" in message or "aplicados" in message):
                # Ejemplo: "GTK aplicado: Everforest-Dark"
                parts = message.split(":")
                if len(parts) == 2:
                    tipo, nombre = parts[0].strip(), parts[1].strip()
                    if "GTK" in tipo.upper():
                        installed_theme_name["type"] = "gtk"  # type: ignore
                        installed_theme_name["name"] = nombre
                    elif "SHELL" in tipo.upper():
                        installed_theme_name["type"] = "shell"  # type: ignore
                        installed_theme_name["name"] = nombre
                    elif "ICONOS" in tipo.upper():
                        installed_theme_name["type"] = "icons"  # type: ignore
                        installed_theme_name["name"] = nombre
                    elif "CURSOR" in tipo.upper():
                        installed_theme_name["type"] = "cursor"  # type: ignore
                        installed_theme_name["name"] = nombre
        
        success, message = self.theme_manager.install_theme_archive(
            file_path, 
            callback=progress_callback
        )
        
        if success:
            self._show_toast(f"✓ Tema instalado correctamente", True)
            # Refrescar después de un breve delay
            GLib.timeout_add(1000, self._refresh_all_themes)
            # Aplicar el tema recién instalado si se detectó
            if installed_theme_name["name"] and installed_theme_name["type"]:
                # Buscar la card correspondiente y pasarle un dummy widget
                self._apply_theme_with_feedback(installed_theme_name["type"], installed_theme_name["name"], card_widget=None)
        else:
            self._log_message(f"Error: {message}", "error")
            self._show_toast(f"✗ Error: {message}", False)
    
    def _show_install_dialog(self):
        """Mostrar diálogo de instalación mejorado"""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Instalar Nuevo Tema",
            body="Selecciona un archivo de tema para instalar"
        )
        
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("file", "Seleccionar Archivo")
        dialog.add_response("url", "Desde URL")
        
        dialog.set_response_appearance("file", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dlg, response):
            if response == "file":
                self._show_file_chooser()
            elif response == "url":
                self._show_url_dialog()
            dialog.close()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _show_file_chooser(self):
        """Mostrar selector de archivos mejorado"""
        dialog = Gtk.FileChooserDialog(
            title="Seleccionar Archivo de Tema",
            transient_for=self,
            action=Gtk.FileChooserAction.OPEN
        )
        
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Instalar", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        
        # Filtros mejorados
        theme_filter = Gtk.FileFilter()
        theme_filter.set_name("Archivos de Tema")
        theme_filter.add_pattern("*.zip")
        theme_filter.add_pattern("*.tar.gz")
        theme_filter.add_pattern("*.tar.xz")
        theme_filter.add_pattern("*.tar.bz2")
        theme_filter.add_pattern("*.7z")
        theme_filter.add_pattern("*.rar")
        dialog.add_filter(theme_filter)
        
        compressed_filter = Gtk.FileFilter()
        compressed_filter.set_name("Archivos Comprimidos")
        compressed_filter.add_pattern("*.zip")
        compressed_filter.add_pattern("*.tar.*")
        compressed_filter.add_pattern("*.7z")
        compressed_filter.add_pattern("*.rar")
        dialog.add_filter(compressed_filter)
        
        all_filter = Gtk.FileFilter()
        all_filter.set_name("Todos los Archivos")
        all_filter.add_pattern("*")
        dialog.add_filter(all_filter)
        
        def on_response(dlg, response):
            if response == Gtk.ResponseType.OK:
                file_path = Path(dlg.get_file().get_path())
                self._process_file(file_path)
            dialog.destroy()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _show_url_dialog(self):
        """Mostrar diálogo para instalar desde URL"""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Instalar desde URL",
            body="Introduce la URL del archivo de tema"
        )
        
        # Entry para URL
        url_entry = Gtk.Entry()
        url_entry.set_placeholder_text("https://ejemplo.com/tema.zip")
        url_entry.set_margin_start(12)
        url_entry.set_margin_end(12)
        
        dialog.set_extra_child(url_entry)
        
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("download", "Descargar")
        dialog.set_response_appearance("download", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dlg, response):
            if response == "download":
                url = url_entry.get_text().strip()
                if url:
                    self._download_and_install_theme(url)
            dialog.close()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _download_and_install_theme(self, url: str):
        """Descargar e instalar tema desde URL"""
        self._log_message(f"Descargando tema desde: {url}", "info")
        self._show_toast("⬇️ Descargando tema...", True)
        
        # Implementar descarga en hilo separado
        def download_thread():
            try:
                import urllib.request
                import tempfile
                
                # Crear archivo temporal
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                    urllib.request.urlretrieve(url, tmp_file.name)
                    
                    # Procesar archivo descargado
                    GLib.idle_add(self._process_file, Path(tmp_file.name))
                    
            except Exception as e:
                GLib.idle_add(self._log_message, f"Error al descargar: {str(e)}", "error")
                GLib.idle_add(self._show_toast, "✗ Error en la descarga", False)
        
        import threading
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
    
    def _show_reset_confirmation(self):
        """Mostrar confirmación para restablecer"""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Restablecer Todos los Temas",
            body="¿Estás seguro de que quieres restablecer todos los temas a los valores por defecto del sistema?\n\nEsta acción no se puede deshacer."
        )
        
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("reset", "Restablecer")
        dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)
        
        def on_response(dlg, response):
            if response == "reset":
                self._reset_all_themes()
            dialog.close()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _reset_all_themes(self):
        """Restablecer todos los temas"""
        self._log_message("Restableciendo todos los temas...", "info")
        self._show_toast("🔄 Restableciendo temas...", True)
        
        success = self.theme_applier.reset_to_defaults(self._log_message)
        
        if success:
            self.applied_themes.clear()
            self._update_current_themes_display()
            self._show_toast("✓ Temas restablecidos correctamente", True)
        else:
            self._show_toast("✗ Error al restablecer temas", False)
    
    def _create_theme_backup(self):
        """Crear respaldo de la configuración actual"""
        self._log_message("Creando respaldo de configuración...", "info")
        self._show_toast("💾 Creando respaldo...", True)
        
        # TODO: Implementar lógica de backup
        self._log_message("Función de backup no implementada aún", "warning")
        self._show_toast("⚠️ Función de backup no implementada", False)
    
    def _show_import_dialog(self):
        """Mostrar diálogo para importar configuración"""
        dialog = Gtk.FileChooserDialog(
            title="Importar Configuración de Temas",
            transient_for=self,
            action=Gtk.FileChooserAction.OPEN
        )
        
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Importar", Gtk.ResponseType.OK)
        
        # Filtro para archivos de configuración
        config_filter = Gtk.FileFilter()
        config_filter.set_name("Configuración de Temas")
        config_filter.add_pattern("*.json")
        config_filter.add_pattern("*.conf")
        dialog.add_filter(config_filter)
        
        def on_response(dlg, response):
            if response == Gtk.ResponseType.OK:
                config_path = Path(dlg.get_file().get_path())
                self._import_theme_config(config_path)
            dialog.destroy()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _import_theme_config(self, config_path: Path):
        """Importar configuración de temas"""
        self._log_message(f"Importando configuración desde: {config_path.name}", "info")
        self._show_toast("📥 Importando configuración...", True)
        
        # TODO: Implementar lógica de importación
        self._log_message("Función de importación no implementada aún", "warning")
        self._show_toast("⚠️ Función de importación no implementada", False)
    
    def _create_full_history_page(self) -> Gtk.Box:
        """Crear página completa de historial"""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        page.set_margin_start(20)
        page.set_margin_end(20)
        page.set_margin_top(20)
        page.set_margin_bottom(20)
        
        # Header con acciones
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        title = Gtk.Label(label="Historial Completo de Actividad")
        title.set_css_classes(["title-2"])
        title.set_hexpand(True)
        title.set_xalign(0)
        header.append(title)
        
        # Botón para limpiar historial
        clear_btn = Gtk.Button(label="Limpiar Historial")
        clear_btn.set_css_classes(["destructive-action", "pill"])
        clear_btn.connect("clicked", self._on_clear_history_clicked)
        header.append(clear_btn)
        
        # Botón para exportar log
        export_btn = Gtk.Button(label="Exportar Log")
        export_btn.set_css_classes(["pill"])
        export_btn.connect("clicked", self._on_export_log_clicked)
        header.append(export_btn)
        
        page.append(header)
        
        # Log completo
        full_activity_log = ActivityLog(compact=False, max_items=None)
        page.append(full_activity_log)
        
        return page
    
    def _on_clear_history_clicked(self, button):
        """Limpiar historial de actividad"""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Limpiar Historial",
            body="¿Estás seguro de que quieres eliminar todo el historial de actividad?"
        )
        
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("clear", "Limpiar")
        dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)
        
        def on_response(dlg, response):
            if response == "clear":
                self.activity_log.clear()
                self._show_toast("🗑️ Historial limpiado", True)
            dialog.close()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_export_log_clicked(self, button):
        """Exportar log de actividad"""
        dialog = Gtk.FileChooserDialog(
            title="Exportar Log de Actividad",
            transient_for=self,
            action=Gtk.FileChooserAction.SAVE
        )
        
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Guardar", Gtk.ResponseType.OK)
        dialog.set_current_name("theme_loader_activity.log")
        
        def on_response(dlg, response):
            if response == Gtk.ResponseType.OK:
                log_path = Path(dlg.get_file().get_path())
                self._export_activity_log(log_path)
            dialog.destroy()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _export_activity_log(self, log_path: Path):
        """Exportar log de actividad a archivo"""
        try:
            # TODO: Implementar exportación de log
            log_content = "Log de actividad - GNOME Theme Loader\n" + "="*50 + "\n"
            log_path.write_text(log_content, encoding='utf-8')
            self._show_toast(f"✓ Log exportado a {log_path.name}", True)
        except Exception as e:
            self._log_message(f"Error al exportar log: {str(e)}", "error")
            self._show_toast("✗ Error al exportar log", False)
    
    def _log_message(self, message: str, message_type: str = "info"):
        """Agregar mensaje al log con timestamp"""
        if hasattr(self, 'activity_log'):
            self.activity_log.add_message(message, message_type)
    
    def _show_toast(self, message: str, is_success: bool):
        """Mostrar notificación toast mejorada"""
        toast = ModernToast(message, is_success)
        
        # Agregar al overlay
        self.toast_overlay.add_overlay(toast)
        toast.set_halign(Gtk.Align.CENTER)
        toast.set_valign(Gtk.Align.END)
        toast.set_margin_bottom(30)
        
        # Animación de entrada
        toast.set_opacity(0)
        toast.add_css_class("toast-enter")
        
        def show_animation():
            toast.set_opacity(1)
            return False
        
        GLib.timeout_add(50, show_animation)
        
        # Remover después de 4 segundos
        GLib.timeout_add(4000, lambda: self._remove_toast(toast))
    
    def _remove_toast(self, toast):
        """Remover toast con animación"""
        def fade_out():
            toast.set_opacity(0)
            toast.add_css_class("toast-exit")
            GLib.timeout_add(300, lambda: self.toast_overlay.remove_overlay(toast))
            return False
        
        GLib.idle_add(fade_out)
        return False

    def _show_configuration_dialog(self):
        """Mostrar diálogo de configuración con dependencias"""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Configuración del Sistema",
            body="Verificar dependencias y configuración necesaria para GNOME Theme Loader"
        )
        
        dialog.add_response("close", "Cerrar")
        dialog.add_response("install", "Instalar Dependencias")
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        
        # Crear contenido personalizado
        content_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content_area.set_margin_start(20)
        content_area.set_margin_end(20)
        content_area.set_margin_top(20)
        content_area.set_margin_bottom(20)
        
        # Sección de dependencias
        deps_section = self._create_dependencies_section()
        content_area.append(deps_section)
        
        # Separador
        content_area.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        # Sección de comandos
        cmds_section = self._create_commands_section()
        content_area.append(cmds_section)
        
        dialog.set_extra_child(content_area)
        
        def on_response(dlg, response):
            if response == "install":
                self._install_dependencies()
            dialog.close()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _create_dependencies_section(self) -> Gtk.Box:
        """Crear sección de dependencias"""
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        # Título
        title = Gtk.Label(label="Dependencias Requeridas")
        title.set_css_classes(["heading"])
        title.set_xalign(0)
        section.append(title)
        
        # Lista de dependencias
        dependencies = [
            ("gsettings", "Configuración del sistema GNOME", "gsettings --version"),
            ("pkexec", "Ejecución con privilegios", "pkexec --version"),
            ("update-grub", "Actualización de GRUB", "which update-grub"),
            ("grub-mkconfig", "Configuración de GRUB", "which grub-mkconfig"),
            ("gtk-update-icon-cache", "Caché de iconos GTK", "which gtk-update-icon-cache")
        ]
        
        for dep_name, description, check_cmd in dependencies:
            item = self._create_dependency_item(dep_name, description, check_cmd)
            section.append(item)
        
        return section
    
    def _create_dependency_item(self, name: str, description: str, check_cmd: str) -> Gtk.Box:
        """Crear item de dependencia individual"""
        item = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        # Icono de estado
        icon = Gtk.Image()
        icon.set_from_icon_name("emblem-ok-symbolic")
        icon.set_css_classes(["success"])
        item.append(icon)
        
        # Información
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_hexpand(True)
        
        name_label = Gtk.Label(label=name)
        name_label.set_css_classes(["body"])
        name_label.set_xalign(0)
        info_box.append(name_label)
        
        desc_label = Gtk.Label(label=description)
        desc_label.set_css_classes(["caption", "dim-label"])
        desc_label.set_xalign(0)
        info_box.append(desc_label)
        
        item.append(info_box)
        
        # Botón de verificar
        check_btn = Gtk.Button(label="Verificar")
        check_btn.set_css_classes(["flat"])
        check_btn.connect("clicked", self._check_dependency, name, check_cmd, icon)
        item.append(check_btn)
        
        return item
    
    def _create_commands_section(self) -> Gtk.Box:
        """Crear sección de comandos de instalación"""
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        # Título
        title = Gtk.Label(label="Comandos de Instalación")
        title.set_css_classes(["heading"])
        title.set_xalign(0)
        section.append(title)
        
        # Comandos por distribución
        commands = {
            "Ubuntu/Debian": "sudo apt install grub-common policykit-1",
            "Fedora": "sudo dnf install grub2-tools polkit",
            "Arch Linux": "sudo pacman -S grub polkit",
            "openSUSE": "sudo zypper install grub2 polkit"
        }
        
        for distro, cmd in commands.items():
            cmd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            
            distro_label = Gtk.Label(label=distro)
            distro_label.set_css_classes(["body"])
            distro_label.set_xalign(0)
            cmd_box.append(distro_label)
            
            cmd_label = Gtk.Label(label=cmd)
            cmd_label.set_css_classes(["caption", "monospace"])
            cmd_label.set_xalign(0)
            cmd_label.set_selectable(True)
            cmd_box.append(cmd_label)
            
            section.append(cmd_box)
        
        return section
    
    def _check_dependency(self, button, name: str, check_cmd: str, icon: Gtk.Image):
        """Verificar si una dependencia está instalada"""
        try:
            result = subprocess.run(check_cmd.split(), capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                icon.set_from_icon_name("emblem-ok-symbolic")
                icon.set_css_classes(["success"])
                self._log_message(f"✓ {name} está instalado", "success")
            else:
                icon.set_from_icon_name("dialog-error-symbolic")
                icon.set_css_classes(["error"])
                self._log_message(f"✗ {name} no está instalado", "error")
        except Exception as e:
            icon.set_from_icon_name("dialog-error-symbolic")
            icon.set_css_classes(["error"])
            self._log_message(f"✗ Error verificando {name}: {str(e)}", "error")
    
    def _install_dependencies(self):
        """Instalar dependencias automáticamente"""
        self._log_message("Instalando dependencias...", "info")
        self._show_toast("🔧 Instalando dependencias...", True)
        
        # Detectar distribución
        try:
            with open("/etc/os-release", "r") as f:
                os_info = f.read()
            
            if "ubuntu" in os_info.lower() or "debian" in os_info.lower():
                cmd = ["pkexec", "apt", "install", "-y", "grub-common", "policykit-1"]
            elif "fedora" in os_info.lower():
                cmd = ["pkexec", "dnf", "install", "-y", "grub2-tools", "polkit"]
            elif "arch" in os_info.lower():
                cmd = ["pkexec", "pacman", "-S", "--noconfirm", "grub", "polkit"]
            elif "opensuse" in os_info.lower():
                cmd = ["pkexec", "zypper", "install", "-y", "grub2", "polkit"]
            else:
                self._show_toast("⚠️ Distribución no reconocida", False)
                return
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self._log_message("✓ Dependencias instaladas correctamente", "success")
                self._show_toast("✓ Dependencias instaladas", True)
            else:
                self._log_message(f"✗ Error instalando dependencias: {result.stderr}", "error")
                self._show_toast("✗ Error instalando dependencias", False)
                
        except Exception as e:
            self._log_message(f"✗ Error: {str(e)}", "error")
            self._show_toast("✗ Error detectando distribución", False)
    
    def _show_store_window(self):
        """Mostrar ventana de la tienda de temas"""
        try:
            from .store_window import StoreWindow
            store_window = StoreWindow(self.get_application(), self)
            store_window.present()
        except ImportError as e:
            self._log_message(f"Error importando tienda: {e}", "error")
            self._show_toast("❌ Error abriendo tienda", False)
        except Exception as e:
            self._log_message(f"Error abriendo tienda: {e}", "error")
            self._show_toast("❌ Error abriendo tienda", False)

    def _on_category_selected(self, button, theme_type):
        """Manejar selección de categoría y mostrar lista de temas"""
        # Quitar selección previa
        for btn in self.category_buttons.values():
            btn.remove_css_class("suggested-action")
        button.add_css_class("suggested-action")
        # Mostrar lista de temas de la categoría seleccionada
        self._show_theme_list_for_category(theme_type)

    def _show_theme_list_for_category(self, theme_type):
        # Ya no se usa category_content_box, así que este método puede quedar vacío o solo cambiar la página central
        self.current_theme_type = theme_type
        self.content_stack.set_visible_child_name(theme_type)

    def _create_manual_install_card(self) -> Gtk.Box:
        """Card visual para instalación manual de temas"""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.set_css_classes(["theme-card"])
        card.set_margin_top(8)
        card.set_margin_bottom(8)
        card.set_margin_start(8)
        card.set_margin_end(8)
        card.set_size_request(240, 180)
        card.set_halign(Gtk.Align.FILL)
        card.set_valign(Gtk.Align.FILL)

        # Icono
        icon = Gtk.Image()
        icon.set_from_icon_name("document-open-symbolic")
        icon.set_pixel_size(48)
        icon.set_halign(Gtk.Align.CENTER)
        card.append(icon)

        # Título
        title = Gtk.Label(label="Instalación Manual")
        title.set_css_classes(["heading"])
        title.set_halign(Gtk.Align.CENTER)
        card.append(title)

        # Descripción
        desc = Gtk.Label(label="Sube un archivo de tema o arrástralo aquí para instalarlo.")
        desc.set_wrap(True)
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_halign(Gtk.Align.CENTER)
        card.append(desc)

        # Botón
        btn = Gtk.Button(label="Seleccionar archivo...")
        btn.set_css_classes(["suggested-action"])
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", self._on_open_manual_modal)
        card.append(btn)

        return card

    def _create_store_card(self) -> Gtk.Box:
        """Card visual para acceder a la tienda en línea"""
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.set_css_classes(["theme-card"])
        card.set_margin_top(8)
        card.set_margin_bottom(8)
        card.set_margin_start(8)
        card.set_margin_end(8)
        card.set_size_request(240, 180)
        card.set_halign(Gtk.Align.FILL)
        card.set_valign(Gtk.Align.FILL)

        # Icono
        icon = Gtk.Image()
        icon.set_from_icon_name("applications-internet-symbolic")
        icon.set_pixel_size(48)
        icon.set_halign(Gtk.Align.CENTER)
        card.append(icon)

        # Título
        title = Gtk.Label(label="Tienda en Línea")
        title.set_css_classes(["heading"])
        title.set_halign(Gtk.Align.CENTER)
        card.append(title)

        # Descripción
        desc = Gtk.Label(label="Explora y descarga temas desde GNOME-Look.org fácilmente.")
        desc.set_wrap(True)
        desc.set_justify(Gtk.Justification.CENTER)
        desc.set_halign(Gtk.Align.CENTER)
        card.append(desc)

        # Botón
        btn = Gtk.Button(label="Abrir tienda")
        btn.set_css_classes(["suggested-action"])
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", lambda *_: self._show_store_window())
        card.append(btn)

        return card

    def _on_open_manual_modal(self, button):
        """Mostrar el modal de instalación manual"""
        if hasattr(self, 'manual_modal'):
            self.manual_modal.set_visible(True)

    def _create_manual_install_modal(self) -> Gtk.Dialog:
        """Crear modal para instalación manual de temas (subir/drag&drop) usando Gtk.Dialog"""
        dialog = Gtk.Dialog(title="Instalación Manual de Tema", transient_for=self, modal=True)
        dialog.set_default_size(400, 300)

        # Contenido principal
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_top(24)
        content.set_margin_bottom(24)
        content.set_margin_start(24)
        content.set_margin_end(24)

        # Título
        title = Gtk.Label(label="Sube un archivo de tema o arrástralo aquí")
        title.set_css_classes(["heading"])
        title.set_halign(Gtk.Align.CENTER)
        content.append(title)

        # Área de drop
        drop_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        drop_area.set_css_classes(["drop-zone"])
        drop_area.set_size_request(320, 120)
        drop_area.set_halign(Gtk.Align.CENTER)
        drop_area.set_valign(Gtk.Align.CENTER)
        drop_area.set_margin_top(12)
        drop_area.set_margin_bottom(12)
        drop_area.set_margin_start(12)
        drop_area.set_margin_end(12)
        drop_label = Gtk.Label(label="Arrastra aquí el archivo de tema")
        drop_label.set_halign(Gtk.Align.CENTER)
        drop_area.append(drop_label)
        content.append(drop_area)

        # Botón para seleccionar archivo
        file_btn = Gtk.Button(label="Seleccionar archivo...")
        file_btn.set_css_classes(["suggested-action"])
        file_btn.set_halign(Gtk.Align.CENTER)
        file_btn.connect("clicked", self._on_select_file_for_manual_install)
        content.append(file_btn)

        # Botón de cerrar
        close_btn = Gtk.Button(label="Cerrar")
        close_btn.set_halign(Gtk.Align.CENTER)
        close_btn.connect("clicked", lambda *_: dialog.hide())
        content.append(close_btn)

        # Agregar contenido al área de contenido del diálogo
        box = dialog.get_content_area()
        box.set_spacing(0)
        box.append(content)

        dialog.set_modal(True)
        dialog.set_visible(False)
        return dialog

    def _on_select_file_for_manual_install(self, button):
        """Abrir diálogo de selección de archivo para instalación manual"""
        file_chooser = Gtk.FileChooserNative(
            title="Seleccionar archivo de tema",
            transient_for=self,
            action=Gtk.FileChooserAction.OPEN
        )
        def on_response(native, response):
            if response == Gtk.ResponseType.ACCEPT:
                file_path = native.get_file().get_path()
                print(f"[MANUAL INSTALL] Archivo seleccionado: {file_path}")
                # Aquí puedes llamar a la lógica de instalación manual
                self._process_file(Path(file_path))
            native.destroy()
        file_chooser.connect("response", on_response)
        file_chooser.show()

    def _delete_theme(self, theme_type, name, path, card_widget):
        """Eliminar tema local y refrescar la lista"""
        import shutil
        import os
        try:
            shutil.rmtree(path)
            self._show_toast(f"Tema '{name}' eliminado", True)
            self._refresh_all_themes()
        except Exception as e:
            self._show_toast(f"Error al eliminar '{name}': {e}", False)

    def _restart_app(self):
        import sys, os
        self._show_toast("🔄 Reiniciando aplicación...", True)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _on_toggle_preview_sidebar(self, button):
        self.preview_expanded = not self.preview_expanded
        if self.preview_expanded:
            self.preview_panel.set_size_request(320, -1)
            self.preview_content_box.set_visible(True)
        else:
            self.preview_panel.set_size_request(48, -1)
            self.preview_content_box.set_visible(False)

    def _on_customize_app_icon(self, button):
        dialog = Gtk.Dialog(title="Personalizar icono de aplicación", transient_for=self, modal=True)
        dialog.set_default_size(600, 500)
        content = dialog.get_content_area()
        content.set_spacing(16)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.append(vbox)
        spinner = Gtk.Spinner()
        spinner.set_halign(Gtk.Align.CENTER)
        spinner.set_valign(Gtk.Align.CENTER)
        vbox.append(spinner)
        spinner.start()
        # Limpiar vbox y cargar datos en hilo
        def load_data():
            apps = list_installed_applications()
            icons = list_all_theme_icons()
            GLib.idle_add(lambda: self._populate_customize_icon_modal(dialog, vbox, spinner, apps, icons))
        threading.Thread(target=load_data, daemon=True).start()
        dialog.present()

    def _populate_customize_icon_modal(self, dialog, vbox, spinner, all_apps, all_icons):
        vbox.remove(spinner)
        # Paso 1: Selección de aplicación
        app_label = Gtk.Label(label="1. Selecciona la aplicación:")
        app_label.set_halign(Gtk.Align.START)
        app_label.set_css_classes(["heading"])
        vbox.append(app_label)
        search_label = Gtk.Label(label="Buscar aplicación:")
        search_label.set_halign(Gtk.Align.START)
        vbox.append(search_label)
        search_entry = Gtk.SearchEntry()
        vbox.append(search_entry)
        app_list = Gtk.ListBox()
        app_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        app_rows = []
        # Solo mostrar las primeras 5 apps inicialmente
        for app in all_apps[:5]:
            row = Gtk.ListBoxRow()
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            icon_img = Gtk.Image()
            icon_img.set_from_icon_name(app["icon"])
            icon_img.set_pixel_size(24)
            row_box.append(icon_img)
            label = Gtk.Label(label=app["name"])
            label.set_halign(Gtk.Align.START)
            row_box.append(label)
            row.set_child(row_box)
            row.app_data = app
            app_rows.append(row)
            app_list.append(row)
        app_list.set_vexpand(False)
        vbox.append(app_list)
        def on_search_changed(entry):
            text = entry.get_text().lower()
            # Limpiar lista
            for row in app_rows:
                app_list.remove(row)
            app_rows.clear()
            # Mostrar solo las apps que coincidan (sin límite)
            for app in all_apps:
                if text in app["name"].lower():
                    row = Gtk.ListBoxRow()
                    row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                    icon_img = Gtk.Image()
                    icon_img.set_from_icon_name(app["icon"])
                    icon_img.set_pixel_size(24)
                    row_box.append(icon_img)
                    label = Gtk.Label(label=app["name"])
                    label.set_halign(Gtk.Align.START)
                    row_box.append(label)
                    row.set_child(row_box)
                    row.app_data = app
                    app_rows.append(row)
                    app_list.append(row)
        search_entry.connect("search-changed", on_search_changed)
        selected_app = {"row": None}
        def on_app_selected(listbox, row):
            selected_app["row"] = row
        app_list.connect("row-selected", on_app_selected)
        vbox.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        # Paso 2: Selección de icono (con búsqueda y ComboBox personalizado)
        icon_label = Gtk.Label(label="2. Elige el icono:")
        icon_label.set_halign(Gtk.Align.START)
        icon_label.set_css_classes(["heading"])
        vbox.append(icon_label)
        icon_search = Gtk.SearchEntry()
        vbox.append(icon_search)
        # Preparar lista de iconos [(nombre, tema, ruta)]
        icon_items = []
        for theme, icons in all_icons.items():
            for icon_path in icons:
                icon_name = os.path.splitext(os.path.basename(icon_path))[0]
                icon_items.append((icon_name, theme, icon_path))
        # Modelo filtrable
        filtered_icons = list(icon_items)
        # Usar ListStore para miniatura+nombre+path
        icon_store = Gtk.ListStore(str, str)  # display_text, path
        for name, theme, path in filtered_icons:
            display = f"{name} ({theme})"
            icon_store.append([display, path])
        icon_combo = Gtk.ComboBox.new_with_model(icon_store)
        renderer_pix = Gtk.CellRendererPixbuf()
        renderer_text = Gtk.CellRendererText()
        icon_combo.pack_start(renderer_pix, False)
        icon_combo.pack_start(renderer_text, True)
        icon_combo.add_attribute(renderer_text, "text", 0)
        def set_icon_cell(combo, cell, model, iter):
            path = model.get_value(iter, 1)
            if os.path.exists(path):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(path, 24, 24)
                    cell.set_property("pixbuf", pixbuf)
                except Exception:
                    cell.set_property("pixbuf", None)
            else:
                cell.set_property("pixbuf", None)
        icon_combo.set_cell_data_func(renderer_pix, set_icon_cell)
        vbox.append(icon_combo)
        selected_icon = {"index": None, "data": None}
        def on_icon_changed(combo):
            idx = combo.get_active()
            if idx is not None and idx >= 0:
                model = combo.get_model()
                display = model[idx][0]
                path = model[idx][1]
                # Extraer nombre y tema del display
                if "(" in display and display.endswith(")"):
                    name, theme = display.rsplit(" (", 1)
                    theme = theme[:-1]
                else:
                    name, theme = display, ""
                selected_icon["index"] = idx
                selected_icon["data"] = (name, theme, path)
            else:
                selected_icon["index"] = None
                selected_icon["data"] = None
        icon_combo.connect("changed", on_icon_changed)
        # Búsqueda de iconos
        def on_icon_search(entry):
            text = entry.get_text().lower()
            icon_store.clear()
            for name, theme, path in icon_items:
                if text in name.lower() or text in theme.lower():
                    display = f"{name} ({theme})"
                    icon_store.append([display, path])
        icon_search.connect("search-changed", on_icon_search)
        # Botones para buscar icono personalizado y de otros temas
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        buscar_btn = Gtk.Button(label="Buscar icono personalizado")
        otros_btn = Gtk.Button(label="Tomar de otro tema")
        btn_box.append(buscar_btn)
        btn_box.append(otros_btn)
        vbox.append(btn_box)
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        action_box.set_halign(Gtk.Align.END)
        assign_btn = Gtk.Button(label="Asignar icono")
        assign_btn.set_css_classes(["suggested-action"])
        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", lambda *_: dialog.close())
        action_box.append(assign_btn)
        action_box.append(cancel_btn)
        vbox.append(action_box)
        def on_assign_clicked(btn):
            if not selected_app["row"] or not selected_icon["data"]:
                self._show_toast("Selecciona una aplicación y un icono", False)
                return
            app = selected_app["row"].app_data
            icon_name, theme, path = selected_icon["data"]
            ok, msg = assign_custom_icon_to_app(app["desktop_file"], icon_name)
            self._show_toast(msg, ok)
            if ok:
                dialog.close()