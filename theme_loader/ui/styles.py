"""
Styles module for GNOME Theme Loader
Handles CSS loading and management
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk
from pathlib import Path

def load_styles():
    """Load CSS styles from the resources file"""
    css_file = Path(__file__).parent.parent / "resources" / "styles.css"
    
    if not css_file.exists():
        print(f"Warning: CSS file not found at {css_file}")
        return
    
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            css_data = f.read()
        
        # Load CSS into the display
        display = Gdk.Display.get_default()
        if display:
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(css_data.encode())
            
            # Apply to the display
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            print("CSS styles loaded successfully")
        else:
            print("Warning: No display available for CSS loading")
            
    except Exception as e:
        print(f"Error loading CSS styles: {e}")

def get_css_provider():
    """Get CSS provider for custom styling"""
    css_file = Path(__file__).parent.parent / "resources" / "styles.css"
    
    if not css_file.exists():
        return None
    
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            css_data = f.read()
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css_data.encode())
        return css_provider
        
    except Exception as e:
        print(f"Error creating CSS provider: {e}")
        return None 