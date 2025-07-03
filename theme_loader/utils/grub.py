import os
import subprocess
from pathlib import Path
import tempfile
import tarfile
import zipfile
import re
import shutil

GRUB_THEMES_DIR = Path("/boot/grub/themes")
GRUB_CONFIG = Path("/etc/default/grub")

def list_grub_themes():
    """Listar temas GRUB disponibles"""
    if not GRUB_THEMES_DIR.exists():
        return []
    return [d.name for d in GRUB_THEMES_DIR.iterdir() 
            if d.is_dir() and (d / "theme.txt").exists()]

def run_pkexec(cmd):
    """Helper para ejecutar pkexec con manejo de errores mejorado"""
    env = os.environ.copy()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode == 0:
        return True, result.stdout.strip()
    
    # Manejo de errores mejorado
    error_msg = (result.stderr or "") + ("\n" + result.stdout if result.stdout else "")
    
    if "No polkit authentication agent found" in error_msg or "polkit" in error_msg.lower():
        error_msg += "\n\nNo se detectó un agente de autenticación PolicyKit."
        error_msg += "\nInstala uno como 'policykit-1-gnome' o ejecuta el siguiente comando en terminal:\n"
        error_msg += f"sudo {' '.join(cmd[1:])}"
    else:
        error_msg += f"\n\nSi el problema persiste, ejecuta manualmente en terminal:\n"
        error_msg += f"sudo {' '.join(cmd[1:])}"
    
    return False, error_msg.strip()

def detect_archive_type(archive_path: Path):
    """Detectar tipo de archivo comprimido de forma más robusta"""
    suffixes = archive_path.suffixes
    name_lower = archive_path.name.lower()
    
    # ZIP
    if archive_path.suffix.lower() == ".zip":
        return "zip"
    
    # TAR variants
    if (name_lower.endswith(".tar.gz") or name_lower.endswith(".tgz") or
        name_lower.endswith(".tar.xz") or name_lower.endswith(".tar.bz2") or
        name_lower.endswith(".tar")):
        return "tar"
    
    return None

def find_theme_directory(base_path: Path):
    """Buscar directorio que contenga theme.txt de forma más inteligente"""
    candidates = []
    
    # Buscar recursivamente (máximo 2 niveles)
    for root in [base_path] + list(base_path.iterdir()):
        if not root.is_dir():
            continue
            
        if (root / "theme.txt").exists():
            candidates.append(root)
            
        # Buscar un nivel más profundo
        for subdir in root.iterdir():
            if subdir.is_dir() and (subdir / "theme.txt").exists():
                candidates.append(subdir)
    
    if not candidates:
        return None
    
    # Si hay múltiples candidatos, preferir el que esté en la raíz
    root_candidates = [c for c in candidates if c.parent == base_path]
    return root_candidates[0] if root_candidates else candidates[0]

def get_update_grub_cmd():
    # Buscar update-grub en rutas comunes
    for path in ["/usr/sbin/update-grub", "/sbin/update-grub"]:
        if os.path.exists(path):
            return ["pkexec", path]
    if shutil.which("update-grub"):
        return ["pkexec", shutil.which("update-grub")]
    elif shutil.which("grub-mkconfig"):
        return ["pkexec", "grub-mkconfig", "-o", "/boot/grub/grub.cfg"]
    else:
        return None

def install_grub_theme(archive_path: Path, theme_name: str):
    """Instalar un tema GRUB desde un archivo comprimido"""
    if not archive_path.exists():
        return False, "El archivo no existe"
    
    archive_type = detect_archive_type(archive_path)
    if not archive_type:
        return False, f"Formato no soportado: {archive_path.suffix}"
    
    try:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            
            # Descomprimir según el tipo
            if archive_type == "zip":
                with zipfile.ZipFile(archive_path) as zf:
                    zf.extractall(tmp)
            elif archive_type == "tar":
                with tarfile.open(archive_path) as tf:
                    tf.extractall(tmp)
            
            # Buscar carpeta con theme.txt
            theme_dir = find_theme_directory(tmp)
            if not theme_dir:
                return False, "No se encontró theme.txt en el archivo"
            
            # Verificar que el directorio de destino no exista
            dest = GRUB_THEMES_DIR / theme_name
            if dest.exists():
                return False, f"El tema '{theme_name}' ya existe"
            
            # Crear directorio de temas si no existe
            mkdir_cmd = ["pkexec", "mkdir", "-p", str(GRUB_THEMES_DIR)]
            ok, msg = run_pkexec(mkdir_cmd)
            if not ok:
                return False, f"Error creando directorio de temas: {msg}"
            
            # Copiar tema usando pkexec
            cmd = ["pkexec", "cp", "-r", str(theme_dir), str(dest)]
            return run_pkexec(cmd)
            
    except Exception as e:
        return False, f"Error durante la instalación: {str(e)}"

def apply_grub_theme(theme_name: str):
    """Aplicar un tema GRUB (modifica config y ejecuta update-grub)"""
    try:
        # Verificar que el tema existe
        theme_dir = GRUB_THEMES_DIR / theme_name
        if not theme_dir.exists() or not (theme_dir / "theme.txt").exists():
            return False, f"El tema '{theme_name}' no existe o es inválido"
        
        theme_path = f"/boot/grub/themes/{theme_name}/theme.txt"
        
        # Leer configuración actual con permisos de root
        read_cmd = ["pkexec", "cat", str(GRUB_CONFIG)]
        ok, current_content = run_pkexec(read_cmd)
        if not ok:
            return False, f"Error leyendo configuración GRUB: {current_content}"
        
        # Crear nueva configuración
        lines = current_content.split('\n')
        theme_line = f'GRUB_THEME="{theme_path}"'
        theme_found = False
        
        # Buscar y reemplazar línea existente
        for i, line in enumerate(lines):
            if line.strip().startswith('GRUB_THEME='):
                lines[i] = theme_line
                theme_found = True
                break
        
        # Si no se encontró, agregar al final
        if not theme_found:
            lines.append(theme_line)
        
        new_content = '\n'.join(lines)
        
        # Escribir nueva configuración usando tee (más confiable que sed)
        write_cmd = ["pkexec", "tee", str(GRUB_CONFIG)]
        result = subprocess.run(write_cmd, input=new_content, 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Error desconocido"
            return False, f"Error escribiendo configuración: {error_msg}"
        
        # Ejecutar update-grub o grub-mkconfig
        update_cmd = get_update_grub_cmd()
        if not update_cmd:
            return False, "No se encontró 'update-grub' ni 'grub-mkconfig' en el sistema. Por favor, actualiza GRUB manualmente."
        ok, msg = run_pkexec(update_cmd)
        if not ok:
            return False, f"Error actualizando GRUB: {msg}"
        
        return True, "Tema aplicado correctamente"
        
    except Exception as e:
        return False, f"Error aplicando tema: {str(e)}"

def remove_grub_theme(theme_name: str):
    """Eliminar un tema GRUB instalado"""
    try:
        theme_dir = GRUB_THEMES_DIR / theme_name
        if not theme_dir.exists():
            return False, f"El tema '{theme_name}' no existe"
        
        # Eliminar directorio del tema
        cmd = ["pkexec", "rm", "-rf", str(theme_dir)]
        return run_pkexec(cmd)
        
    except Exception as e:
        return False, f"Error eliminando tema: {str(e)}"

# Función de utilidad para validar nombres de tema
def validate_theme_name(name: str):
    """Validar que el nombre del tema sea seguro"""
    if not name or not isinstance(name, str):
        return False, "Nombre inválido"
    
    # Solo permitir caracteres alfanuméricos, guiones y guiones bajos
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False, "El nombre solo puede contener letras, números, guiones y guiones bajos"
    
    if len(name) > 50:
        return False, "El nombre es demasiado largo (máximo 50 caracteres)"
    
    return True, "Nombre válido"