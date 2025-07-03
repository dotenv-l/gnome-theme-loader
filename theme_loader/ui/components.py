"""
UI Components module for GNOME Theme Loader
Contains reusable UI components
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk, Adw, Gdk, Gio, GLib  # type: ignore
from gi.repository import GdkPixbuf  # type: ignore
from pathlib import Path

class ModernToast(Gtk.Box):
    """Toast personalizado para notificaciones modernas"""
    def __init__(self, message, is_success=True):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.set_css_classes(["toast", "success" if is_success else "error"])
        
        # Icono
        icon = Gtk.Image()
        icon.set_from_icon_name("emblem-ok-symbolic" if is_success else "dialog-error-symbolic")
        self.append(icon)
        
        # Mensaje
        label = Gtk.Label(label=message)
        label.set_hexpand(True)
        self.append(label)

class ThemeCard(Gtk.Box):
    """Tarjeta moderna para mostrar temas"""
    def __init__(self, name, theme_type, path, apply_callback, preview_callback=None, delete_callback=None, is_applied=False, description=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.theme_type = theme_type
        self.name = name
        self.path = path
        self.apply_callback = apply_callback
        self.preview_callback = preview_callback
        self.delete_callback = delete_callback
        self.set_css_classes(["card", "theme-card"])
        if is_applied:
            self.add_css_class("theme-applied")
        
        # Header de la tarjeta
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.set_margin_top(16)
        header.set_margin_bottom(12)
        header.set_margin_start(16)
        header.set_margin_end(16)
        
        # Miniatura si existe
        thumb = Gtk.Image()
        thumb_path = None
        if path:
            for fname in ["screenshot.png", "preview.png", "screenshot.jpg", "preview.jpg"]:
                candidate = Path(path) / fname
                if candidate.exists():
                    thumb_path = str(candidate)
                    break
        if thumb_path:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(thumb_path, 64, 64, True)
            thumb.set_from_pixbuf(pixbuf)
        else:
            icon_name = {
                "gtk": "applications-graphics-symbolic",
                "shell": "desktop-symbolic",
                "icons": "folder-pictures-symbolic",
                "cursor": "input-mouse-symbolic",
                "grub": "computer-symbolic"
            }.get(theme_type, "package-x-generic-symbolic")
            thumb.set_from_icon_name(icon_name)
            thumb.set_css_classes(["theme-icon"])
        header.append(thumb)
        
        # Información del tema
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        name_label = Gtk.Label(label=name)
        name_label.set_css_classes(["heading", "theme-name"])
        name_label.set_xalign(0)
        name_label.set_ellipsize(3)
        info_box.append(name_label)
        
        # Tipo de tema con estilo badge
        type_label = Gtk.Label(label=theme_type.upper())
        type_label.set_css_classes(["caption", "theme-type-badge"])
        type_label.set_xalign(0)
        info_box.append(type_label)
        
        # Descripción corta
        if description:
            desc_label = Gtk.Label(label=description[:80] + ("..." if len(description) > 80 else ""))
            desc_label.set_css_classes(["caption", "dim-label"])
            desc_label.set_xalign(0)
            desc_label.set_wrap(True)
            info_box.append(desc_label)
        info_box.set_hexpand(True)
        header.append(info_box)
        
        # Botones de acción
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Botón de vista previa (si hay callback)
        if preview_callback:
            preview_btn = Gtk.Button()
            preview_btn.set_icon_name("view-preview-symbolic")
            preview_btn.set_css_classes(["flat", "circular"])
            preview_btn.set_tooltip_text("Vista previa")
            preview_btn.connect("clicked", self._on_preview_clicked)
            actions_box.append(preview_btn)
        
        # Botón de aplicar con hover effect
        self.apply_btn = Gtk.Button(label="Aplicar")
        self.apply_btn.set_css_classes(["suggested-action", "pill"])
        self.apply_btn.connect("clicked", self._on_apply_clicked)
        actions_box.append(self.apply_btn)
        
        # Botón de eliminar
        if delete_callback:
            delete_btn = Gtk.Button()
            delete_btn.set_icon_name("user-trash-symbolic")
            delete_btn.set_css_classes(["flat", "circular", "error"])
            delete_btn.set_tooltip_text("Eliminar tema")
            delete_btn.connect("clicked", self._on_delete_clicked)
            actions_box.append(delete_btn)
        
        # Etiqueta de aplicado
        if is_applied:
            applied_label = Gtk.Label(label="Aplicado")
            applied_label.set_css_classes(["caption", "theme-applied-label"])
            actions_box.append(applied_label)
        
        header.append(actions_box)
        self.append(header)
        
        # Ruta con estilo sutil
        if path:
            path_label = Gtk.Label(label=str(path))
            path_label.set_css_classes(["caption", "dim-label", "theme-path"])
            path_label.set_xalign(0)
            path_label.set_ellipsize(1)
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
    
    def _on_preview_clicked(self, button):
        """Manejar click en vista previa"""
        if self.preview_callback:
            self.preview_callback(self.theme_type, self.name, str(self.path))
    
    def _on_delete_clicked(self, button):
        if self.delete_callback:
            self.delete_callback(self.theme_type, self.name, self.path, self)
    
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
    def __init__(self, on_file_dropped, enhanced=False):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.on_file_dropped = on_file_dropped
        self.enhanced = enhanced
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

        # Funcionalidad mejorada
        if enhanced:
            self._add_enhanced_features()

        self.set_size_request(300, 200)

        # Configurar drag and drop
        self._setup_dnd()
    
    def _add_enhanced_features(self):
        """Agregar características mejoradas"""
        # Botón para buscar online
        online_btn = Gtk.Button(label="Buscar Temas Online")
        online_btn.set_css_classes(["pill", "flat"])
        online_btn.set_icon_name("web-browser-symbolic")
        online_btn.connect("clicked", self._on_online_search)
        self.append(online_btn)
    
    def _on_online_search(self, button):
        """Abrir navegador para buscar temas"""
        import webbrowser
        webbrowser.open("https://www.gnome-look.org/")
    
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
            transient_for=self.get_root(),
            action=Gtk.FileChooserAction.OPEN
        )
        
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Abrir", Gtk.ResponseType.OK)
        
        self._add_file_filters(dialog)
        
        def on_response(dlg, response):
            if response == Gtk.ResponseType.OK:
                file_path = Path(dlg.get_file().get_path())
                self.on_file_dropped(file_path)
            dialog.destroy()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _add_file_filters(self, dialog):
        """Agregar filtros de archivos"""
        # Filtro para archivos comprimidos
        compressed_filter = Gtk.FileFilter()
        compressed_filter.set_name("Archivos de tema")
        compressed_filter.add_pattern("*.zip")
        compressed_filter.add_pattern("*.tar.gz")
        compressed_filter.add_pattern("*.tar.xz")
        compressed_filter.add_pattern("*.tar.bz2")
        compressed_filter.add_pattern("*.tar")
        dialog.add_filter(compressed_filter)
        
        # Filtro para todos los archivos
        all_filter = Gtk.FileFilter()
        all_filter.set_name("Todos los archivos")
        all_filter.add_pattern("*")
        dialog.add_filter(all_filter)

class ActivityLog(Gtk.Box):
    """Widget para mostrar logs de actividad"""
    def __init__(self, compact=False, max_items=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.compact = compact
        self.max_items = max_items
        self.messages = []
        self.set_css_classes(["activity-log"])
        
        # Header con botón de limpiar
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.set_margin_start(12)
        header.set_margin_end(12)
        header.set_margin_top(8)
        header.set_margin_bottom(8)
        
        title = Gtk.Label(label="Actividad" if not compact else "Actividad Reciente")
        title.set_css_classes(["heading"])
        title.set_xalign(0)
        title.set_hexpand(True)
        header.append(title)
        
        clear_btn = Gtk.Button(label="Limpiar")
        clear_btn.set_css_classes(["flat"])
        clear_btn.connect("clicked", self.clear)
        header.append(clear_btn)
        
        self.append(header)
        
        # Scrolled window para los mensajes
        scrolled = Gtk.ScrolledWindow()
        if compact:
            scrolled.set_min_content_height(150)
            scrolled.set_max_content_height(200)
        else:
            scrolled.set_min_content_height(200)
            scrolled.set_max_content_height(400)
        scrolled.set_vexpand(True)
        
        # Box para los mensajes
        self.messages_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.messages_box.set_margin_start(12)
        self.messages_box.set_margin_end(12)
        self.messages_box.set_margin_bottom(12)
        
        scrolled.set_child(self.messages_box)
        self.append(scrolled)
    
    def add_message(self, message, message_type="info"):
        """Agregar un mensaje al log"""
        # Agregar a la lista de mensajes
        self.messages.append({"message": message, "type": message_type})
        
        # Limitar número de mensajes si se especifica
        if self.max_items and len(self.messages) > self.max_items:
            self.messages = self.messages[-self.max_items:]
        
        # Actualizar display
        self._update_display()
        
        # Auto-scroll al final
        GLib.timeout_add(100, self._scroll_to_bottom)
    
    def _update_display(self):
        """Actualizar la visualización de mensajes"""
        # Limpiar display actual
        while self.messages_box.get_first_child():
            self.messages_box.remove(self.messages_box.get_first_child())
        
        # Mostrar mensajes (limitados si es compacto)
        display_messages = self.messages
        if self.compact and self.max_items:
            display_messages = self.messages[-self.max_items:]
        
        for msg_data in display_messages:
            label = Gtk.Label(label=msg_data["message"])
            label.set_css_classes(["log-message", f"log-{msg_data['type']}"])
            label.set_xalign(0)
            label.set_wrap(True)
            label.set_selectable(True)
            
            self.messages_box.append(label)
    
    def _scroll_to_bottom(self):
        """Hacer scroll automático al final"""
        scrolled = self.get_last_child()
        if scrolled and hasattr(scrolled, 'get_vadjustment'):
            adj = scrolled.get_vadjustment()
            adj.set_value(adj.get_upper())
        return False
    
    def clear(self, button=None):
        """Limpiar todos los mensajes"""
        self.messages.clear()
        self._update_display()

class ThemePreview(Gtk.Box):
    """Widget para vista previa de temas"""
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_css_classes(["theme-preview"])
        self.set_size_request(200, 150)
        
        # Placeholder inicial
        self._show_placeholder()
    
    def _show_placeholder(self):
        """Mostrar placeholder cuando no hay tema seleccionado"""
        # Limpiar contenido actual
        while self.get_first_child():
            self.remove(self.get_first_child())
        
        # Icono placeholder
        icon = Gtk.Image()
        icon.set_from_icon_name("image-missing-symbolic")
        icon.set_pixel_size(48)
        icon.set_css_classes(["dim-label"])
        self.append(icon)
        
        # Texto placeholder
        label = Gtk.Label(label="Selecciona un tema para ver la vista previa")
        label.set_css_classes(["body", "dim-label"])
        label.set_wrap(True)
        label.set_justify(Gtk.Justification.CENTER)
        self.append(label)
    
    def show_preview(self, theme_type: str, theme_name: str, theme_path: str):
        """Mostrar vista previa de un tema"""
        # Limpiar contenido actual
        while self.get_first_child():
            self.remove(self.get_first_child())
        
        # Título del tema
        title = Gtk.Label(label=theme_name)
        title.set_css_classes(["heading"])
        title.set_xalign(0)
        self.append(title)
        
        # Tipo de tema
        type_label = Gtk.Label(label=f"Tipo: {theme_type.upper()}")
        type_label.set_css_classes(["caption", "dim-label"])
        type_label.set_xalign(0)
        self.append(type_label)
        
        # Ruta
        path_label = Gtk.Label(label=f"Ubicación: {theme_path}")
        path_label.set_css_classes(["caption", "dim-label"])
        path_label.set_xalign(0)
        path_label.set_ellipsize(1)  # PANGO_ELLIPSIZE_START
        self.append(path_label)
        
        # Información adicional según el tipo
        if theme_type == "gtk":
            self._show_gtk_preview(theme_path)
        elif theme_type == "icons":
            self._show_icon_preview(theme_path)
        elif theme_type == "cursor":
            self._show_cursor_preview(theme_path)
        else:
            self._show_generic_preview(theme_type, theme_path)
    
    def _show_gtk_preview(self, theme_path: str):
        """Mostrar vista previa de tema GTK"""
        # Aquí podrías mostrar una captura de pantalla o información del tema
        info_label = Gtk.Label(label="Tema GTK detectado")
        info_label.set_css_classes(["body"])
        self.append(info_label)
    
    def _show_icon_preview(self, theme_path: str):
        """Mostrar vista previa de tema de iconos"""
        # Mostrar algunos iconos de ejemplo
        info_label = Gtk.Label(label="Paquete de iconos")
        info_label.set_css_classes(["body"])
        self.append(info_label)
    
    def _show_cursor_preview(self, theme_path: str):
        """Mostrar vista previa de tema de cursor"""
        info_label = Gtk.Label(label="Tema de cursor")
        info_label.set_css_classes(["body"])
        self.append(info_label)
    
    def _show_generic_preview(self, theme_type: str, theme_path: str):
        """Mostrar vista previa genérica"""
        info_label = Gtk.Label(label=f"Tema {theme_type}")
        info_label.set_css_classes(["body"])
        self.append(info_label) 