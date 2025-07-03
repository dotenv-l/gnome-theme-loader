import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk, Adw, Gdk, Gio, GLib
from pathlib import Path
import tempfile
import zipfile
import tarfile
import os

# Importar módulos locales
from .installer import install_archive
from .gsettings import set_gtk_theme, set_shell_theme, set_icon_theme, set_cursor_theme
from .grub import list_grub_themes, install_grub_theme, apply_grub_theme

# Directorios de temas
THEME_DIR = Path.home() / ".themes"
ICON_DIR = Path.home() / ".icons"
LOCAL_ICON_DIR = Path.home() / ".local/share/icons"
SYSTEM_THEME_DIR = Path("/usr/share/themes")
SYSTEM_ICON_DIR = Path("/usr/share/icons")

class ModernToast(Gtk.Widget):
    """Toast personalizado para notificaciones modernas"""
    def __init__(self, message, is_success=True):
        super().__init__()
        self.set_css_classes(["toast", "success" if is_success else "error"])
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Icono
        icon = Gtk.Image()
        icon.set_from_icon_name("emblem-ok-symbolic" if is_success else "dialog-error-symbolic")
        box.append(icon)
        
        # Mensaje
        label = Gtk.Label(label=message)
        label.set_hexpand(True)
        box.append(label)
        
        self.set_child(box)

class ThemeCard(Gtk.Box):
    """Tarjeta moderna para mostrar temas"""
    def __init__(self, name, theme_type, path, apply_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.theme_type = theme_type
        self.name = name
        self.path = path
        self.apply_callback = apply_callback
        self.set_css_classes(["card", "theme-card"])
        # Header de la tarjeta
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.set_margin_top(16)
        header.set_margin_bottom(12)
        header.set_margin_start(16)
        header.set_margin_end(16)
        # Icono del tipo de tema
        icon = Gtk.Image()
        icon_name = {
            "gtk": "applications-graphics-symbolic",
            "shell": "desktop-symbolic",
            "icons": "folder-pictures-symbolic",
            "cursor": "input-mouse-symbolic",
            "grub": "computer-symbolic"
        }.get(theme_type, "package-x-generic-symbolic")
        icon.set_from_icon_name(icon_name)
        icon.set_css_classes(["theme-icon"])
        header.append(icon)
        # Información del tema
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        name_label = Gtk.Label(label=name)
        name_label.set_css_classes(["heading", "theme-name"])
        name_label.set_xalign(0)
        name_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        info_box.append(name_label)
        # Tipo de tema con estilo badge
        type_label = Gtk.Label(label=theme_type.upper())
        type_label.set_css_classes(["caption", "theme-type-badge"])
        type_label.set_xalign(0)
        info_box.append(type_label)
        info_box.set_hexpand(True)
        header.append(info_box)
        # Botón de aplicar con hover effect
        self.apply_btn = Gtk.Button(label="Aplicar")
        self.apply_btn.set_css_classes(["suggested-action", "pill"])
        self.apply_btn.connect("clicked", self._on_apply_clicked)
        header.append(self.apply_btn)
        self.append(header)
        # Ruta con estilo sutil
        if path:
            path_label = Gtk.Label(label=str(path))
            path_label.set_css_classes(["caption", "dim-label", "theme-path"])
            path_label.set_xalign(0)
            path_label.set_ellipsize(1)  # PANGO_ELLIPSIZE_START
            path_label.set_margin_start(16)
            path_label.set_margin_end(16)
            path_label.set_margin_bottom(16)
            self.append(path_label)
        # Estado de loading
        self.spinner = Gtk.Spinner()
        self.spinner.set_css_classes(["theme-spinner"])
        self.spinner.set_visible(False)
        self.append(self.spinner)
        # Agregar efectos hover
        self._setup_hover_effects()
    
    def _setup_hover_effects(self):
        """Configurar efectos hover modernos"""
        hover_controller = Gtk.EventControllerMotion()
        hover_controller.connect("enter", self._on_hover_enter)
        hover_controller.connect("leave", self._on_hover_leave)
        self.add_controller(hover_controller)
    
    def _on_hover_enter(self, controller, x, y):
        self.add_css_class("theme-card-hover")
    
    def _on_hover_leave(self, controller):
        self.remove_css_class("theme-card-hover")
    
    def _on_apply_clicked(self, button):
        """Manejar click en aplicar con feedback visual"""
        self.set_loading(True)
        GLib.timeout_add(100, lambda: self.apply_callback(self.theme_type, self.name, self))
    
    def set_loading(self, loading):
        """Mostrar/ocultar estado de carga"""
        if loading:
            self.apply_btn.set_visible(False)
            self.spinner.set_visible(True)
            self.spinner.start()
        else:
            self.apply_btn.set_visible(True)
            self.spinner.stop()
            self.spinner.set_visible(False)

class DropZone(Gtk.Box):
    """Zona de arrastrar y soltar moderna"""
    def __init__(self, on_file_dropped):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.on_file_dropped = on_file_dropped
        self.set_css_classes(["drop-zone"])
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)

        # Icono grande
        icon = Gtk.Image()
        icon.set_from_icon_name("folder-download-symbolic")
        icon.set_css_classes(["drop-zone-icon"])
        icon.set_pixel_size(64)
        self.append(icon)

        # Texto principal
        title = Gtk.Label(label="Arrastra tu archivo de tema aquí")
        title.set_css_classes(["title-2", "drop-zone-title"])
        self.append(title)

        # Subtexto
        subtitle = Gtk.Label(label="Soporta archivos .zip, .tar.gz, .tar.xz y más")
        subtitle.set_css_classes(["body", "dim-label"])
        self.append(subtitle)

        # Botón alternativo
        button = Gtk.Button(label="O selecciona un archivo")
        button.set_css_classes(["pill", "opaque"])
        button.connect("clicked", self._on_file_button)
        self.append(button)

        self.set_size_request(300, 200)

        # Configurar drag and drop
        self._setup_dnd()
    
    def _setup_dnd(self):
        """Configurar drag and drop con efectos visuales"""
        target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        target.connect("drop", self._on_drop)
        target.connect("enter", self._on_drag_enter)
        target.connect("leave", self._on_drag_leave)
        self.add_controller(target)
    
    def _on_drag_enter(self, target, x, y):
        self.add_css_class("drop-zone-active")
        return Gdk.DragAction.COPY
    
    def _on_drag_leave(self, target):
        self.remove_css_class("drop-zone-active")
    
    def _on_drop(self, target, gfile, x, y):
        self.remove_css_class("drop-zone-active")
        file_path = Path(gfile.get_path())
        self.on_file_dropped(file_path)
        return True
    
    def _on_file_button(self, button):
        """Abrir selector de archivos"""
        dialog = Gtk.FileChooserDialog(
            title="Selecciona un archivo de tema",
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Abrir", Gtk.ResponseType.ACCEPT)
        dialog.set_modal(True)
        
        # Filtros modernos
        self._add_file_filters(dialog)
        
        def on_response(dlg, response):
            if response == Gtk.ResponseType.ACCEPT:
                file_path = Path(dlg.get_file().get_path())
                self.on_file_dropped(file_path)
            dlg.destroy()
        
        dialog.connect("response", on_response)
        dialog.show()
    
    def _add_file_filters(self, dialog):
        """Agregar filtros de archivo"""
        # Filtro para temas
        filter_theme = Gtk.FileFilter()
        filter_theme.set_name("Archivos de tema")
        for ext in ["*.zip", "*.tar.xz", "*.tar.gz", "*.tar", "*.tgz"]:
            filter_theme.add_pattern(ext)
        dialog.add_filter(filter_theme)
        
        # Filtro para todos
        filter_all = Gtk.FileFilter()
        filter_all.set_name("Todos los archivos")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)

class ActivityLog(Gtk.Box):
    """Log de actividad moderno con scroll automático"""
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.messages = []
        # ScrolledWindow con estilo moderno
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_css_classes(["activity-log"])
        self.scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled.set_min_content_height(150)
        # ListBox para mensajes
        self.listbox = Gtk.ListBox()
        self.listbox.set_css_classes(["boxed-list"])
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.scrolled.set_child(self.listbox)
        self.append(self.scrolled)
    
    def add_message(self, message, message_type="info"):
        """Agregar mensaje con estilo y timestamp"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.set_margin_top(8)
        row.set_margin_bottom(8)
        row.set_margin_start(12)
        row.set_margin_end(12)
        
        # Icono según tipo
        icon = Gtk.Image()
        icon_name = {
            "success": "emblem-ok-symbolic",
            "error": "dialog-error-symbolic",
            "warning": "dialog-warning-symbolic",
            "info": "dialog-information-symbolic"
        }.get(message_type, "dialog-information-symbolic")
        icon.set_from_icon_name(icon_name)
        icon.set_css_classes([f"log-icon-{message_type}"])
        row.append(icon)
        
        # Contenido del mensaje
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        
        # Mensaje principal
        msg_label = Gtk.Label(label=message)
        msg_label.set_css_classes(["body"])
        msg_label.set_xalign(0)
        msg_label.set_wrap(True)
        content_box.append(msg_label)
        
        # Timestamp
        time_label = Gtk.Label(label=timestamp)
        time_label.set_css_classes(["caption", "dim-label"])
        time_label.set_xalign(0)
        content_box.append(time_label)
        
        content_box.set_hexpand(True)
        row.append(content_box)
        
        self.listbox.append(row)
        
        # Auto-scroll al final
        GLib.idle_add(self._scroll_to_bottom)
        
        # Guardar mensaje
        self.messages.append((timestamp, message, message_type))
    
    def _scroll_to_bottom(self):
        """Scroll automático al final"""
        adj = self.scrolled.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
    
    def clear(self):
        """Limpiar log"""
        child = self.listbox.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.listbox.remove(child)
            child = next_child
        self.messages.clear()

class Window(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="Theme Loader",
                         default_width=1000, default_height=700)
        
        self.history = []
        self.current_themes = {}  # Cache de temas actuales
        
        # Configurar CSS personalizado
        self._setup_custom_css()
        
        # Construir UI
        self.set_content(self._build_ui())
        
        # Cargar temas inicialmente
        self._refresh_all_themes()

    def _setup_custom_css(self):
        """Configurar estilos CSS personalizados para una UI moderna"""
        css = """
        .theme-card {
            margin: 6px;
            border-radius: 12px;
            background: alpha(@theme_bg_color, 0.5);
            border: 1px solid alpha(@borders, 0.5);
            transition: all 200ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }
        
        .theme-card-hover {
            background: alpha(@theme_bg_color, 0.8);
            border-color: @accent_bg_color;
            transform: translateY(-2px);
            box-shadow: 0 4px 16px alpha(@accent_bg_color, 0.2);
        }
        
        .theme-name {
            font-weight: 600;
        }
        
        .theme-type-badge {
            background: alpha(@accent_bg_color, 0.15);
            color: @accent_fg_color;
            border-radius: 6px;
            padding: 2px 8px;
            font-size: 0.8em;
            font-weight: 500;
        }
        
        .theme-path {
            font-family: monospace;
            font-size: 0.85em;
        }
        
        .drop-zone {
            border: 2px dashed alpha(@borders, 0.3);
            border-radius: 16px;
            padding: 32px;
            margin: 16px;
            transition: all 200ms ease;
        }
        
        .drop-zone-active {
            border-color: @accent_bg_color;
            background: alpha(@accent_bg_color, 0.1);
            transform: scale(1.02);
        }
        
        .drop-zone-icon {
            opacity: 0.6;
        }
        
        .drop-zone-title {
            font-weight: 600;
        }
        
        .activity-log {
            background: alpha(@theme_bg_color, 0.3);
            border-radius: 12px;
        }
        
        .log-icon-success { color: @success_color; }
        .log-icon-error { color: @error_color; }
        .log-icon-warning { color: @warning_color; }
        .log-icon-info { color: @accent_bg_color; }
        
        .theme-section {
            margin: 8px 0;
        }
        
        .section-header {
            font-weight: 600;
            padding: 16px;
            background: alpha(@theme_bg_color, 0.3);
            border-radius: 8px;
            margin-bottom: 8px;
        }
        
        .floating-action {
            border-radius: 50px;
            min-width: 48px;
            min-height: 48px;
            box-shadow: 0 2px 8px alpha(@shade_color, 0.2);
        }
        """
        
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self) -> Gtk.Widget:
        """Construir interfaz moderna"""
        # Layout principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header bar moderno
        header = self._build_modern_headerbar()
        main_box.append(header)
        
        # Contenido principal con Leaflet para responsive design
        self.leaflet = Adw.Leaflet()
        self.leaflet.set_can_navigate_back(True)
        self.leaflet.set_can_navigate_forward(True)
        
        # Panel lateral
        sidebar = self._build_sidebar()
        self.leaflet.append(sidebar)
        
        # Panel principal
        main_panel = self._build_main_panel()
        self.leaflet.append(main_panel)
        
        main_box.append(self.leaflet)
        
        return main_box

    def _build_modern_headerbar(self):
        """Header bar con diseño moderno"""
        header = Adw.HeaderBar()
        header.set_css_classes(["flat"])
        
        # Título con estilo
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title = Gtk.Label(label="Theme Loader")
        title.set_css_classes(["title-1"])
        subtitle = Gtk.Label(label="Gestiona tus temas de GNOME")
        subtitle.set_css_classes(["caption", "dim-label"])
        title_box.append(title)
        title_box.append(subtitle)
        header.set_title_widget(title_box)
        
        # Botones de acción
        refresh_btn = Gtk.Button()
        refresh_btn.set_icon_name("view-refresh-symbolic")
        refresh_btn.set_css_classes(["flat", "circular"])
        refresh_btn.set_tooltip_text("Actualizar temas")
        refresh_btn.connect("clicked", lambda _: self._refresh_all_themes())
        header.pack_end(refresh_btn)
        
        # Menú principal
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_css_classes(["flat", "circular"])
        
        # Crear menú
        menu = Gio.Menu()
        menu.append("Acerca de", "app.about")
        menu.append("Salir", "app.quit")
        menu_button.set_menu_model(menu)
        
        header.pack_end(menu_button)
        
        return header

    def _build_sidebar(self):
        """Panel lateral moderno"""
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        sidebar_box.set_size_request(320, -1)
        sidebar_box.set_margin_top(16)
        sidebar_box.set_margin_bottom(16)
        sidebar_box.set_margin_start(16)
        sidebar_box.set_margin_end(8)
        
        # Drop zone
        self.drop_zone = DropZone(self._process_file)
        sidebar_box.append(self.drop_zone)
        
        # Separador
        separator = Gtk.Separator()
        separator.set_margin_top(8)
        separator.set_margin_bottom(8)
        sidebar_box.append(separator)
        
        # Log de actividad
        log_label = Gtk.Label(label="Actividad Reciente")
        log_label.set_css_classes(["heading"])
        log_label.set_xalign(0)
        sidebar_box.append(log_label)
        
        self.activity_log = ActivityLog()
        sidebar_box.append(self.activity_log)
        
        # Botón limpiar log
        clear_btn = Gtk.Button(label="Limpiar Registro")
        clear_btn.set_css_classes(["flat"])
        clear_btn.connect("clicked", lambda _: self.activity_log.clear())
        sidebar_box.append(clear_btn)
        
        return sidebar_box

    def _build_main_panel(self):
        """Panel principal con tabs modernos"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(8)
        main_box.set_margin_end(16)
        
        # Tab view moderno
        self.tab_view = Adw.TabView()
        self.tab_view.set_vexpand(True)
        
        # Crear tabs para cada tipo de tema
        self.theme_pages = {}
        theme_types = [
            ("gtk", "Aplicaciones", "applications-graphics-symbolic"),
            ("shell", "Escritorio", "desktop-symbolic"),
            ("icons", "Iconos", "folder-pictures-symbolic"),
            ("cursor", "Cursores", "input-mouse-symbolic"),
            ("grub", "GRUB", "computer-symbolic")
        ]
        
        for theme_type, label, icon_name in theme_types:
            page_content = self._create_theme_page(theme_type)
            page = self.tab_view.append(page_content)
            page.set_title(label)
            page.set_icon(Gio.ThemedIcon.new(icon_name))
            self.theme_pages[theme_type] = page_content
        
        main_box.append(self.tab_view)
        
        return main_box

    def _create_theme_page(self, theme_type):
        """Crear página para un tipo de tema específico"""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # FlowBox para layout responsive de tarjetas
        flowbox = Gtk.FlowBox()
        flowbox.set_css_classes(["theme-section"])
        flowbox.set_valign(Gtk.Align.START)
        flowbox.set_max_children_per_line(3)
        flowbox.set_min_children_per_line(1)
        flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        flowbox.set_margin_top(16)
        flowbox.set_margin_bottom(16)
        flowbox.set_margin_start(16)
        flowbox.set_margin_end(16)
        
        scrolled.set_child(flowbox)
        return scrolled

    def _process_file(self, file_path: Path):
        """Procesar archivo con feedback visual mejorado"""
        if not file_path.exists():
            self.activity_log.add_message(f"El archivo no existe: {file_path.name}", "error")
            return
        
        self.activity_log.add_message(f"Procesando archivo: {file_path.name}", "info")
        
        try:
            # Detectar tipo con feedback
            theme_type = self._detect_theme_type(file_path)
            
            if theme_type == "grub":
                self.activity_log.add_message("Tema GRUB detectado", "info")
                self._install_grub_dialog(file_path)
            elif theme_type == "unknown":
                self.activity_log.add_message("Tipo de tema desconocido, intentando instalación genérica", "warning")
                install_archive(file_path, lambda msg: self.activity_log.add_message(msg, "info"))
                self._refresh_all_themes()
            else:
                self.activity_log.add_message("Tema regular detectado, instalando...", "info")
                install_archive(file_path, lambda msg: self.activity_log.add_message(msg, "info"))
                self._refresh_all_themes()
                self.activity_log.add_message("¡Tema instalado correctamente!", "success")
                
        except Exception as e:
            self.activity_log.add_message(f"Error procesando archivo: {str(e)}", "error")

    def _detect_theme_type(self, file_path: Path):
        """Detectar tipo de tema (manteniendo lógica original)"""
        try:
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td)
                
                # Extraer archivo
                if file_path.suffix.lower() == '.zip':
                    with zipfile.ZipFile(file_path) as zf:
                        zf.extractall(tmp)
                elif file_path.suffix.lower() in ['.tar', '.gz', '.xz'] or \
                     any(file_path.name.lower().endswith(ext) for ext in ['.tar.gz', '.tar.xz', '.tgz']):
                    with tarfile.open(file_path) as tf:
                        tf.extractall(tmp)
                else:
                    return "unknown"
                
                # Analizar contenido
                has_grub = False
                has_theme = False
                
                for root, dirs, files in os.walk(tmp):
                    if "theme.txt" in files:
                        has_grub = True
                    if any(d in dirs for d in ["gtk-3.0", "gtk-4.0", "gtk-2.0", "gnome-shell"]) or \
                       "index.theme" in files or "cursors" in dirs:
                        has_theme = True
                
                return "grub" if has_grub else ("theme" if has_theme else "unknown")
                    
        except Exception:
            return "unknown"

    def _refresh_all_themes(self):
        """Actualizar todas las páginas de temas"""
        self.activity_log.add_message("Actualizando lista de temas...", "info")
        
        # Crear directorios si no existen
        THEME_DIR.mkdir(exist_ok=True)
        ICON_DIR.mkdir(exist_ok=True)
        
        # Refrescar cada tipo de tema
        theme_configs = {
            "gtk": (
                [THEME_DIR, SYSTEM_THEME_DIR],
                self._is_valid_gtk_theme
            ),
            "shell": (
                [THEME_DIR, SYSTEM_THEME_DIR],
                self._is_valid_shell_theme
            ),
            "icons": (
                [ICON_DIR, LOCAL_ICON_DIR, SYSTEM_ICON_DIR],
                self._is_valid_icon_theme
            ),
            "cursor": (
                [ICON_DIR, LOCAL_ICON_DIR, SYSTEM_ICON_DIR],
                self._is_valid_cursor_theme
            )
        }
        
        for theme_type, (directories, validator) in theme_configs.items():
            themes = self._scan_themes(directories, validator)
            self._populate_theme_page(theme_type, themes)
        
        # GRUB themes
        try:
            grub_themes = list_grub_themes()
            grub_dict = {theme: None for theme in grub_themes}
            self._populate_theme_page("grub", grub_dict)
        except Exception as e:
            self.activity_log.add_message(f"Error listando temas GRUB: {str(e)}", "warning")
        
        self.activity_log.add_message("Temas actualizados correctamente", "success")

    def _populate_theme_page(self, theme_type, themes_dict):
        """Poblar página con tarjetas de temas y separador visual"""
        scrolled = self.theme_pages[theme_type]
        viewport = scrolled.get_child()
        flowbox = viewport.get_child()
        # Limpiar contenido existente
        child = flowbox.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            flowbox.remove(child)
            child = next_child
        # Agregar separador visual
        section_label = Gtk.Label(label=theme_type.upper())
        section_label.set_css_classes(["section-header"])
        section_label.set_xalign(0)
        flowbox.append(section_label)
        # Agregar tarjetas de temas
        for name, path in sorted(themes_dict.items()):
            card = ThemeCard(name, theme_type, path, self._apply_theme_with_feedback)
            flowbox.append(card)

    def _apply_theme_with_feedback(self, theme_type, name, card_widget):
        """Aplicar tema con feedback visual"""
        try:
            success = False
            
            if theme_type == "gtk":
                success = set_gtk_theme(name)
                msg = f"Tema GTK '{name}' aplicado correctamente" if success else f"Error aplicando tema GTK '{name}'"
            elif theme_type == "shell":
                success = set_shell_theme(name)
                msg = f"Tema Shell '{name}' aplicado correctamente" if success else f"Error aplicando tema Shell '{name}'"
            elif theme_type == "icons":
                success = set_icon_theme(name)
                msg = f"Tema de iconos '{name}' aplicado correctamente" if success else f"Error aplicando iconos '{name}'"
            elif theme_type == "cursor":
                success = set_cursor_theme(name)
                msg = f"Tema de cursor '{name}' aplicado correctamente" if success else f"Error aplicando cursor '{name}'"
            elif theme_type == "grub":
                self._apply_grub_theme_dialog(name)
                card_widget.set_loading(False)
                return
            else:
                msg = f"Tipo de tema desconocido: {theme_type}"
                success = False
            
            # Mostrar feedback
            self.activity_log.add_message(msg, "success" if success else "error")
            
            # Mostrar toast notification
            self._show_toast(msg, success)
            
        except Exception as e:
            error_msg = f"Error aplicando tema '{name}': {str(e)}"
            self.activity_log.add_message(error_msg, "error")
            self._show_toast(error_msg, False)
        
        finally:
            # Quitar estado de loading
            GLib.timeout_add(500, lambda: card_widget.set_loading(False))

    def _show_toast(self, message, is_success):
        """Mostrar notificación toast moderna"""
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)  # 3 segundos
        
        # Aquí podrías agregar el toast a un ToastOverlay si lo tienes configurado
        # Por ahora solo agregamos al log de actividad
        pass

    def _apply_grub_theme_dialog(self, theme_name):
        """Diálogo moderno para aplicar tema GRUB"""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Aplicar Tema GRUB",
            body=f"¿Deseas aplicar el tema GRUB '{theme_name}'?\n\nEsto requiere permisos de administrador y modificará la configuración de arranque del sistema."
        )
        
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("apply", "Aplicar Tema")
        dialog.set_response_appearance("apply", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        
        def on_response(dlg, response):
            if response == "apply":
                try:
                    self.activity_log.add_message(f"Aplicando tema GRUB: {theme_name}...", "info")
                    success, msg = apply_grub_theme(theme_name)
                    
                    if success:
                        self.activity_log.add_message(f"Tema GRUB '{theme_name}' aplicado correctamente", "success")
                        self._show_toast(f"Tema GRUB aplicado: {theme_name}", True)
                    else:
                        self.activity_log.add_message(f"Error aplicando tema GRUB: {msg}", "error")
                        self._show_toast(f"Error aplicando tema GRUB: {msg}", False)
                        
                except Exception as e:
                    error_msg = f"Error aplicando tema GRUB: {str(e)}"
                    self.activity_log.add_message(error_msg, "error")
                    self._show_toast(error_msg, False)
            
            dlg.close()
        
        dialog.connect("response", on_response)
        dialog.present()

    def _install_grub_dialog(self, archive_path):
        """Diálogo moderno para instalar tema GRUB"""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Instalar Tema GRUB",
            body="Este archivo contiene un tema GRUB. La instalación requiere permisos de administrador."
        )
        
        # Crear contenido personalizado del diálogo
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        # Campo para nombre del tema
        name_group = Adw.PreferencesGroup()
        name_group.set_title("Configuración del Tema")
        
        name_row = Adw.EntryRow()
        name_row.set_title("Nombre del tema")
        name_row.set_text(archive_path.stem)
        name_group.add(name_row)
        
        content_box.append(name_group)
        dialog.set_extra_child(content_box)
        
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("install", "Instalar Tema")
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("install")
        dialog.set_close_response("cancel")
        
        def on_response(dlg, response):
            if response == "install":
                theme_name = name_row.get_text().strip()
                if theme_name:
                    try:
                        self.activity_log.add_message(f"Instalando tema GRUB: {theme_name}...", "info")
                        success, msg = install_grub_theme(archive_path, theme_name)
                        
                        if success:
                            self.activity_log.add_message(f"Tema GRUB '{theme_name}' instalado correctamente", "success")
                            self._show_toast(f"Tema GRUB instalado: {theme_name}", True)
                            self._refresh_all_themes()
                        else:
                            self.activity_log.add_message(f"Error instalando tema GRUB: {msg}", "error")
                            self._show_toast(f"Error instalando tema GRUB: {msg}", False)
                            
                    except Exception as e:
                        error_msg = f"Error instalando tema GRUB: {str(e)}"
                        self.activity_log.add_message(error_msg, "error")
                        self._show_toast(error_msg, False)
                else:
                    self.activity_log.add_message("Debes especificar un nombre para el tema", "warning")
            
            dlg.close()
        
        dialog.connect("response", on_response)
        dialog.present()

    def _scan_themes(self, directories, validator_func):
        """Escanear temas en múltiples directorios con validación (lógica original)"""
        themes = {}
        
        for directory in directories:
            if not directory.exists():
                continue
                
            try:
                for item in directory.iterdir():
                    if item.is_dir() and validator_func(item):
                        themes[item.name] = item
            except PermissionError:
                continue
                
        return themes

    def _is_valid_gtk_theme(self, theme_path: Path):
        """Validar si es un tema GTK válido (lógica original)"""
        return (
            (theme_path / "gtk-4.0").exists() or
            (theme_path / "gtk-3.0").exists() or
            (theme_path / "gtk-2.0").exists() or
            any((theme_path / subdir / "gtk-4.0").exists() for subdir in ["gtk", "Gtk"] if (theme_path / subdir).exists()) or
            any((theme_path / subdir / "gtk-3.0").exists() for subdir in ["gtk", "Gtk"] if (theme_path / subdir).exists())
        )

    def _is_valid_shell_theme(self, theme_path: Path):
        """Validar si es un tema Shell válido (lógica original)"""
        return (
            (theme_path / "gnome-shell").exists() or
            any((theme_path / subdir / "gnome-shell").exists() for subdir in ["shell", "Shell"] if (theme_path / subdir).exists())
        )

    def _is_valid_icon_theme(self, icon_path: Path):
        """Validar si es un tema de iconos válido (lógica original)"""
        return (icon_path / "index.theme").exists()

    def _is_valid_cursor_theme(self, cursor_path: Path):
        """Validar si es un tema de cursor válido (lógica original)"""
        return (
            (cursor_path / "cursors").exists() or
            (cursor_path / "cursor.theme").exists()
        )


class Application(Adw.Application):
    """Aplicación principal modernizada"""
    
    def __init__(self):
        super().__init__(application_id="com.themeloader.modern")
        self.connect("activate", self.on_activate)
        
        # Configurar acciones
        self._setup_actions()
    
    def _setup_actions(self):
        """Configurar acciones de la aplicación"""
        # Acción "Acerca de"
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about_action)
        self.add_action(about_action)
        
        # Acción "Salir"
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<primary>q"])
    
    def on_activate(self, app):
        """Activar aplicación"""
        self.window = Window(self)
        self.window.present()
    
    def on_about_action(self, action, param):
        """Mostrar diálogo "Acerca de" moderno"""
        about = Adw.AboutWindow(
            transient_for=self.window,
            application_name="GNOME Theme Loader",
            application_icon="applications-graphics-symbolic",
            developer_name="Tu Nombre",
            version="2.0.0",
            copyright="© 2024 Tu Nombre",
            comments="Gestor moderno de temas para GNOME con interfaz intuitiva y funciones avanzadas.",
            website="https://github.com/tu-usuario/theme-loader",
            issue_url="https://github.com/tu-usuario/theme-loader/issues",
            license_type=Gtk.License.GPL_3_0
        )
        
        # Información adicional
        about.add_credit_section(
            "Desarrolladores",
            ["Tu Nombre https://github.com/tu-usuario"]
        )
        
        about.add_credit_section(
            "Diseño",
            ["Basado en GNOME HIG", "Libadwaita Design Patterns"]
        )
        
        about.present()


def main():
    """Función principal para ejecutar la aplicación"""
    app = Application()
    return app.run(None)