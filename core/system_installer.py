#!/usr/bin/env python3
"""
VYN v1.2 - System Installer Module
Auto-detects OS (Linux/Windows), installs Ollama, and recommends models based on system specs.
"""

import subprocess
import shutil
import platform
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List

class SystemInstaller:
    """
    Handles automatic system detection and Ollama installation.
    Designed for zero-friction first-run experience.
    Supports both Linux and Windows.
    """
    
    # Model recommendations based on RAM
    MODEL_RECOMMENDATIONS = {
        'low': {  # < 4GB RAM
            'models': ['gemma3:1b', 'qwen3:1b'],
            'primary': 'gemma3:1b',
            'description': 'Modelos ligeros para sistemas con poca RAM'
        },
        'medium': {  # 4-8GB RAM
            'models': ['gemma3:4b', 'qwen3:4b'],
            'primary': 'gemma3:4b',
            'description': 'Modelos balanceados, buen rendimiento'
        },
        'high': {  # 8-16GB RAM
            'models': ['gemma3:4b', 'qwen3:8b', 'llama3.1:8b'],
            'primary': 'qwen3:8b',
            'description': 'Modelos avanzados para código y razonamiento'
        },
        'ultra': {  # > 16GB RAM
            'models': ['qwen3:14b', 'llama3.1:8b', 'mistral:7b'],
            'primary': 'qwen3:14b',
            'description': 'Modelos premium, máxima calidad'
        }
    }
    
    # Distro detection patterns (Linux only)
    DISTRO_PATTERNS = {
        'arch': ['arch', 'manjaro', 'endeavouros', 'garuda'],
        'debian': ['debian', 'ubuntu', 'mint', 'pop', 'elementary', 'zorin', 'kali'],
        'fedora': ['fedora', 'centos', 'rhel', 'rocky', 'alma'],
        'opensuse': ['opensuse', 'suse'],
        'void': ['void'],
        'alpine': ['alpine'],
        'gentoo': ['gentoo']
    }
    
    def __init__(self, console=None):
        self.console = console
        self.is_windows = platform.system() == 'Windows'
        self.is_linux = platform.system() == 'Linux'
        self.is_macos = platform.system() == 'Darwin'
        self.distro_info = self.detect_distro()
        self.ram_gb = self.get_ram_gb()
    
    def log(self, message: str, style: str = ""):
        """Print message, using rich console if available."""
        if self.console:
            self.console.print(f"[{style}]{message}[/{style}]" if style else message)
        else:
            print(message)
    
    def detect_distro(self) -> Dict[str, str]:
        """
        Detects the operating system and distribution.
        
        Returns:
            Dict with 'name', 'family', 'version', 'pretty_name'
        """
        info = {
            'name': 'unknown',
            'family': 'unknown',
            'version': '',
            'pretty_name': 'Unknown OS'
        }
        
        # Windows detection
        if self.is_windows:
            info['name'] = 'windows'
            info['family'] = 'windows'
            info['version'] = platform.version()
            info['pretty_name'] = f"Windows {platform.release()}"
            return info
        
        # macOS detection
        if self.is_macos:
            info['name'] = 'macos'
            info['family'] = 'macos'
            info['version'] = platform.mac_ver()[0]
            info['pretty_name'] = f"macOS {platform.mac_ver()[0]}"
            return info
        
        # Linux detection - Try /etc/os-release first (standard on modern distros)
        os_release = Path('/etc/os-release')
        if os_release.exists():
            try:
                with open(os_release) as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            value = value.strip('"\'')
                            if key == 'ID':
                                info['name'] = value.lower()
                            elif key == 'VERSION_ID':
                                info['version'] = value
                            elif key == 'PRETTY_NAME':
                                info['pretty_name'] = value
                            elif key == 'ID_LIKE':
                                # Fallback family detection
                                info['id_like'] = value.lower()
            except Exception:
                pass
        
        # Determine distro family
        name_lower = info['name'].lower()
        id_like = info.get('id_like', '').lower()
        
        for family, patterns in self.DISTRO_PATTERNS.items():
            if any(p in name_lower for p in patterns) or any(p in id_like for p in patterns):
                info['family'] = family
                break
        
        if info['family'] == 'unknown' and self.is_linux:
            info['family'] = 'linux'
            info['pretty_name'] = info.get('pretty_name', 'Linux')
        
        return info
    
    def get_ram_gb(self) -> float:
        """Get total system RAM in GB."""
        try:
            import psutil
            return psutil.virtual_memory().total / (1024**3)
        except ImportError:
            pass
        
        # Linux fallback: read from /proc/meminfo
        if self.is_linux:
            try:
                with open('/proc/meminfo') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            kb = int(line.split()[1])
                            return kb / (1024**2)
            except Exception:
                pass
        
        # Windows fallback
        if self.is_windows:
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                c_ulong = ctypes.c_ulong
                class MEMORYSTATUS(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', c_ulong),
                        ('dwMemoryLoad', c_ulong),
                        ('dwTotalPhys', c_ulong),
                        ('dwAvailPhys', c_ulong),
                        ('dwTotalPageFile', c_ulong),
                        ('dwAvailPageFile', c_ulong),
                        ('dwTotalVirtual', c_ulong),
                        ('dwAvailVirtual', c_ulong)
                    ]
                memStatus = MEMORYSTATUS()
                memStatus.dwLength = ctypes.sizeof(MEMORYSTATUS)
                kernel32.GlobalMemoryStatus(ctypes.byref(memStatus))
                return memStatus.dwTotalPhys / (1024**3)
            except Exception:
                pass
        
        return 8.0  # Default assumption
    
    def get_ram_tier(self) -> str:
        """Categorize RAM into tiers for model recommendations."""
        if self.ram_gb < 4:
            return 'low'
        elif self.ram_gb < 8:
            return 'medium'
        elif self.ram_gb < 16:
            return 'high'
        else:
            return 'ultra'
    
    def get_recommended_models(self) -> Dict:
        """Get model recommendations based on system RAM."""
        tier = self.get_ram_tier()
        return self.MODEL_RECOMMENDATIONS[tier]
    
    def is_ollama_installed(self) -> bool:
        """Check if Ollama is installed and accessible."""
        if self.is_windows:
            # On Windows, check common installation paths
            ollama_path = shutil.which('ollama')
            if ollama_path:
                return True
            # Check default Windows installation path
            user_path = Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe"
            program_files = Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / "Ollama" / "ollama.exe"
            return user_path.exists() or program_files.exists()
        else:
            return shutil.which('ollama') is not None
    
    def get_ollama_install_command(self) -> Tuple[str, str]:
        """
        Get the appropriate Ollama installation command/instructions for this OS.
        
        Returns:
            Tuple of (command, description)
        """
        if self.is_windows:
            return (
                "https://ollama.com/download/windows",
                "Descarga e instala desde el sitio oficial"
            )
        elif self.is_macos:
            return (
                "curl -fsSL https://ollama.com/install.sh | sh",
                "Instalación via curl (o descarga desde ollama.com)"
            )
        else:
            # Linux - Universal curl method
            return (
                "curl -fsSL https://ollama.com/install.sh | sh", 
                "Instalación universal via curl"
            )
    
    def install_ollama(self, interactive: bool = True) -> bool:
        """
        Install Ollama on the system.
        
        Args:
            interactive: If True, show progress and ask for confirmation
            
        Returns:
            True if installed successfully (or ready to be installed on Windows)
        """
        if self.is_ollama_installed():
            self.log("✓ Ollama ya está instalado", "green")
            return True
        
        command, description = self.get_ollama_install_command()
        
        # Windows: Show download instructions instead of trying to run shell commands
        if self.is_windows:
            self.log("\n[bold yellow]⚠ Ollama no está instalado[/bold yellow]")
            self.log("\n[cyan]Para instalar Ollama en Windows:[/cyan]")
            self.log(f"  1. Abre tu navegador")
            self.log(f"  2. Ve a: [bold]{command}[/bold]")
            self.log(f"  3. Descarga e instala el .exe")
            self.log(f"  4. Reinicia VYN después de instalar")
            self.log("")
            
            # Try to open the URL in default browser
            try:
                import webbrowser
                self.log("[dim]Abriendo navegador...[/dim]")
                webbrowser.open(command)
            except Exception:
                pass
            
            self.log("\n[yellow]Presiona Enter después de instalar Ollama...[/yellow]")
            try:
                input()
            except:
                pass
            
            # Check again after user says they installed
            if self.is_ollama_installed():
                self.log("✓ Ollama detectado!", "green")
                return True
            else:
                self.log("[yellow]Ollama no detectado. Asegúrate de instalarlo y reinicia VYN.[/yellow]")
                return False
        
        # Linux/macOS: Run installation command
        self.log(f"\n[bold cyan]Instalando Ollama...[/bold cyan]")
        self.log(f"[dim]Método: {description}[/dim]")
        self.log(f"[dim]Comando: {command}[/dim]\n")
        
        try:
            # Use shell=True for pipe commands
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Stream output
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.log(f"  {line}", "dim")
            
            process.wait()
            
            if process.returncode == 0:
                # Verify installation
                if self.is_ollama_installed():
                    self.log("\n✓ Ollama instalado correctamente", "green")
                    
                    # Start Ollama service
                    self._start_ollama_service()
                    return True
                else:
                    self.log("\n⚠ Instalación completó pero Ollama no está en PATH", "yellow")
                    return False
            else:
                self.log(f"\n✗ Error en instalación (código: {process.returncode})", "red")
                return False
                
        except Exception as e:
            self.log(f"\n✗ Error: {e}", "red")
            return False
    
    def _start_ollama_service(self):
        """Start the Ollama service/daemon."""
        # On Windows, Ollama runs as a tray app - no need to start service
        if self.is_windows:
            return
        
        try:
            # Try systemd first (Linux)
            subprocess.run(['systemctl', 'start', 'ollama'], 
                          capture_output=True, timeout=10)
        except Exception:
            try:
                # Fallback: start ollama serve in background
                subprocess.Popen(['ollama', 'serve'], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL,
                               start_new_session=True)
                import time
                time.sleep(2)  # Give it time to start
            except Exception:
                pass
    
    def pull_model(self, model_name: str, show_progress: bool = True) -> bool:
        """
        Download/pull an Ollama model.
        
        Args:
            model_name: Name of the model to pull
            show_progress: If True, show download progress
            
        Returns:
            True if pulled successfully
        """
        self.log(f"\n[cyan]Descargando {model_name}...[/cyan]")
        
        try:
            process = subprocess.Popen(
                ['ollama', 'pull', model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            for line in process.stdout:
                line = line.strip()
                if line and show_progress:
                    # Show progress updates
                    if '%' in line or 'pulling' in line.lower():
                        print(f"\r  {line}", end='', flush=True)
                    else:
                        self.log(f"  {line}", "dim")
            
            print()  # New line after progress
            process.wait()
            
            if process.returncode == 0:
                self.log(f"✓ {model_name} instalado", "green")
                return True
            else:
                self.log(f"✗ Error descargando {model_name}", "red")
                return False
                
        except Exception as e:
            self.log(f"✗ Error: {e}", "red")
            return False
    
    def get_system_summary(self) -> str:
        """Get a formatted summary of system detection."""
        tier = self.get_ram_tier()
        tier_emoji = {'low': '🔋', 'medium': '⚡', 'high': '🚀', 'ultra': '💎'}
        
        return f"""
╔══════════════════════════════════════════════════════════╗
║  Sistema detectado                                        ║
╠══════════════════════════════════════════════════════════╣
║  OS: {self.distro_info['pretty_name']:<50}║
║  Familia: {self.distro_info['family']:<45}║
║  RAM: {self.ram_gb:.1f}GB {tier_emoji.get(tier, '')} ({tier}){' '*(39-len(f'{self.ram_gb:.1f}GB ({tier})'))}║
║  Ollama: {'✓ Instalado' if self.is_ollama_installed() else '✗ No instalado':<45}║
╚══════════════════════════════════════════════════════════╝
"""


def run_first_time_setup(console=None) -> Tuple[bool, Dict]:
    """
    Run the complete first-time setup flow.
    
    Returns:
        Tuple of (success, config_dict)
    """
    installer = SystemInstaller(console)
    config = {}
    
    # Step 1: Show system detection
    if console:
        console.print(installer.get_system_summary())
    else:
        print(installer.get_system_summary())
    
    # Step 2: Install Ollama if needed
    if not installer.is_ollama_installed():
        if console:
            from rich.prompt import Confirm
            do_install = Confirm.ask(
                "Ollama no está instalado. ¿Instalarlo automáticamente?",
                default=True
            )
        else:
            response = input("Ollama no está instalado. ¿Instalarlo? (s/n): ")
            do_install = response.lower() in ['s', 'si', 'y', 'yes', '']
        
        if do_install:
            if not installer.install_ollama():
                return False, {}
        else:
            print("⚠ VYN requiere Ollama para funcionar.")
            print("Instala manualmente: curl -fsSL https://ollama.com/install.sh | sh")
            return False, {}
    
    # Step 3: Recommend and pull models
    recommendations = installer.get_recommended_models()
    
    if console:
        console.print(f"\n[bold cyan]Modelos recomendados para tu sistema ({installer.ram_gb:.0f}GB RAM):[/bold cyan]")
        console.print(f"[dim]{recommendations['description']}[/dim]\n")
        
        for i, model in enumerate(recommendations['models'], 1):
            marker = " [cyan](recomendado)[/cyan]" if model == recommendations['primary'] else ""
            console.print(f"  {i}. {model}{marker}")
        
        console.print(f"\n  0. Saltar (configurar después)")
        console.print(f"  c. Modelo personalizado\n")
        
        from rich.prompt import Prompt
        choice = Prompt.ask("Selección (números separados por coma)", default="1")
    else:
        print(f"\nModelos recomendados para {installer.ram_gb:.0f}GB RAM:")
        for i, model in enumerate(recommendations['models'], 1):
            print(f"  {i}. {model}")
        choice = input("Selección (1,2,...): ")
    
    # Parse selection and pull models
    models_to_install = []
    
    if choice.lower() == 'c':
        custom = input("Nombre del modelo (ej: llama3.1:8b): ").strip()
        if custom:
            models_to_install = [custom]
    elif choice != '0':
        for c in choice.split(','):
            c = c.strip()
            if c.isdigit():
                idx = int(c) - 1
                if 0 <= idx < len(recommendations['models']):
                    models_to_install.append(recommendations['models'][idx])
    
    installed_models = []
    for model in models_to_install:
        if installer.pull_model(model):
            installed_models.append(model)
    
    # Build config
    primary_model = installed_models[0] if installed_models else recommendations['primary']
    
    config['models'] = {
        'coding': installed_models[1] if len(installed_models) > 1 else primary_model,
        'research': primary_model,
        'vision': primary_model,
        'sysadmin': primary_model
    }
    
    config['_installer_info'] = {
        'distro': installer.distro_info,
        'ram_gb': installer.ram_gb,
        'ram_tier': installer.get_ram_tier()
    }
    
    return True, config
