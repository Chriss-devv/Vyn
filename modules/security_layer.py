#!/usr/bin/env python3
"""
VYN v1.2 - Security Layer
Enhanced security module for command execution with:
- Command explanation before execution
- Dry-run mode
- Audit logging
- Risk classification
"""

import logging
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)


class SecurityLayer:
    """
    VYN Security Layer
    Provides transparent, secure command execution with audit trail.
    """
    
    # Global dry-run mode flag
    DRY_RUN = False
    
    # Audit log location
    AUDIT_FILE = Path.home() / ".config" / "vyn" / "audit.log"
    
    # Risk levels
    RISK_LOW = "LOW"
    RISK_MEDIUM = "MEDIUM"
    RISK_HIGH = "HIGH"
    RISK_CRITICAL = "CRITICAL"
    
    # Dangerous command patterns with risk levels
    DANGEROUS_PATTERNS = {
        # CRITICAL - Data destruction
        r'rm\s+(-rf|-fr|--recursive)': (RISK_CRITICAL, "Eliminación recursiva de archivos"),
        r'rm\s+-[a-z]*r': (RISK_CRITICAL, "Eliminación recursiva de archivos"),
        r'mkfs\.': (RISK_CRITICAL, "Formateo de disco"),
        r'dd\s+if=': (RISK_CRITICAL, "Escritura directa a disco"),
        r'>\s*/dev/sd[a-z]': (RISK_CRITICAL, "Escritura directa a dispositivo"),
        r':\(\)\s*{\s*:\|:\s*&\s*}': (RISK_CRITICAL, "Fork bomb"),
        r'mv\s+/\s': (RISK_CRITICAL, "Mover directorio raíz"),
        r'rm\s+/': (RISK_CRITICAL, "Eliminar desde raíz"),
        
        # HIGH - System modification
        r'\|\s*(ba)?sh': (RISK_HIGH, "Pipe a shell (posible código remoto)"),
        r'curl.*\|\s*(ba)?sh': (RISK_HIGH, "Descarga y ejecución de script"),
        r'wget.*\|\s*(ba)?sh': (RISK_HIGH, "Descarga y ejecución de script"),
        r'chmod\s+(777|666)': (RISK_HIGH, "Permisos inseguros"),
        r'chown\s+-R.*/': (RISK_HIGH, "Cambio de propietario recursivo"),
        r'>\s*/etc/': (RISK_HIGH, "Escritura a configuración del sistema"),
        r'sudo\s+rm': (RISK_HIGH, "Eliminación con privilegios root"),
        r'systemctl\s+(stop|disable)': (RISK_HIGH, "Detener servicio del sistema"),
        
        # MEDIUM - Potentially harmful
        r'kill\s+-9': (RISK_MEDIUM, "Terminación forzosa de proceso"),
        r'pkill': (RISK_MEDIUM, "Terminación de procesos por nombre"),
        r'iptables': (RISK_MEDIUM, "Modificación de firewall"),
        r'ufw\s+(disable|delete)': (RISK_MEDIUM, "Modificación de firewall"),
        r'apt.*remove': (RISK_MEDIUM, "Desinstalación de paquete"),
        r'pacman\s+-R': (RISK_MEDIUM, "Desinstalación de paquete"),
        r'dnf.*remove': (RISK_MEDIUM, "Desinstalación de paquete"),
        r'docker\s+rm': (RISK_MEDIUM, "Eliminación de contenedor"),
        r'docker\s+rmi': (RISK_MEDIUM, "Eliminación de imagen"),
    }
    
    # Safe command patterns (always allowed without confirmation)
    SAFE_PATTERNS = [
        r'^ls\s', r'^ls$',
        r'^cat\s', r'^head\s', r'^tail\s',
        r'^pwd$', r'^whoami$', r'^hostname$',
        r'^echo\s', r'^printf\s',
        r'^date$', r'^uptime$', r'^free\s',
        r'^df\s', r'^du\s',
        r'^ps\s', r'^top\s', r'^htop$',
        r'^docker\s+ps', r'^docker\s+images', r'^docker\s+logs',
        r'^systemctl\s+status',
        r'^journalctl\s',
        r'^ip\s+addr', r'^ip\s+a$', r'^ifconfig$',
        r'^ping\s',
        r'^which\s', r'^whereis\s', r'^type\s',
        r'^man\s', r'^help\s',
        r'^git\s+(status|log|diff|branch)',
        r'^find\s', r'^grep\s', r'^awk\s', r'^sed\s',
    ]
    
    def __init__(self, console=None, lang: str = 'es'):
        self.console = console
        self.lang = lang
        self._ensure_audit_file()
    
    def _ensure_audit_file(self):
        """Ensure audit log directory and file exist."""
        self.AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not self.AUDIT_FILE.exists():
            self.AUDIT_FILE.touch()
    
    def log(self, message: str, style: str = ""):
        """Print message using rich console if available."""
        if self.console:
            if style:
                self.console.print(f"[{style}]{message}[/{style}]")
            else:
                self.console.print(message)
        else:
            print(message)
    
    def classify_risk(self, command: str) -> Tuple[str, Optional[str]]:
        """
        Classify the risk level of a command.
        
        Args:
            command: Command to classify
            
        Returns:
            Tuple of (risk_level, reason)
        """
        command = command.strip()
        
        # Check if it's a safe command
        for pattern in self.SAFE_PATTERNS:
            if re.match(pattern, command, re.IGNORECASE):
                return (self.RISK_LOW, None)
        
        # Check against dangerous patterns
        for pattern, (risk, reason) in self.DANGEROUS_PATTERNS.items():
            if re.search(pattern, command, re.IGNORECASE):
                return (risk, reason)
        
        # Default to MEDIUM for unknown commands
        return (self.RISK_MEDIUM, None)
    
    def is_safe_command(self, command: str) -> bool:
        """Check if a command is safe to execute without confirmation."""
        risk, _ = self.classify_risk(command)
        return risk == self.RISK_LOW
    
    def explain_command(self, command: str) -> str:
        """
        Generate a human-readable explanation of what a command does.
        
        Args:
            command: Command to explain
            
        Returns:
            Explanation string
        """
        parts = command.strip().split()
        if not parts:
            return "Comando vacío"
        
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        explanations = {
            'rm': self._explain_rm(args),
            'mv': self._explain_mv(args),
            'cp': self._explain_cp(args),
            'chmod': self._explain_chmod(args),
            'chown': self._explain_chown(args),
            'docker': self._explain_docker(args),
            'systemctl': self._explain_systemctl(args),
            'apt': self._explain_apt(args),
            'pacman': self._explain_pacman(args),
            'dnf': self._explain_dnf(args),
            'curl': self._explain_curl(args),
            'wget': self._explain_wget(args),
        }
        
        if cmd in explanations:
            return explanations[cmd]
        
        return f"Ejecutar comando: {cmd}"
    
    def _explain_rm(self, args: List[str]) -> str:
        """Explain rm command."""
        recursive = any(a in ['-r', '-rf', '-fr', '--recursive'] for a in args)
        force = any(a in ['-f', '-rf', '-fr', '--force'] for a in args)
        targets = [a for a in args if not a.startswith('-')]
        
        action = "ELIMINAR RECURSIVAMENTE" if recursive else "Eliminar"
        if force:
            action += " (forzado, sin confirmación)"
        
        return f"{action}: {', '.join(targets) if targets else 'archivos'}"
    
    def _explain_mv(self, args: List[str]) -> str:
        """Explain mv command."""
        non_flags = [a for a in args if not a.startswith('-')]
        if len(non_flags) >= 2:
            return f"Mover '{non_flags[0]}' a '{non_flags[-1]}'"
        return "Mover archivos"
    
    def _explain_cp(self, args: List[str]) -> str:
        """Explain cp command."""
        recursive = any(a in ['-r', '-R', '--recursive'] for a in args)
        non_flags = [a for a in args if not a.startswith('-')]
        if len(non_flags) >= 2:
            action = "Copiar recursivamente" if recursive else "Copiar"
            return f"{action} '{non_flags[0]}' a '{non_flags[-1]}'"
        return "Copiar archivos"
    
    def _explain_chmod(self, args: List[str]) -> str:
        """Explain chmod command."""
        for a in args:
            if a.isdigit() and len(a) == 3:
                return f"Cambiar permisos a {a}"
        return "Cambiar permisos de archivo"
    
    def _explain_chown(self, args: List[str]) -> str:
        """Explain chown command."""
        recursive = any(a in ['-R', '--recursive'] for a in args)
        action = "Cambiar propietario recursivamente" if recursive else "Cambiar propietario"
        return action
    
    def _explain_docker(self, args: List[str]) -> str:
        """Explain docker command."""
        if not args:
            return "Docker"
        subcommand = args[0]
        explanations = {
            'run': 'Crear y ejecutar contenedor',
            'start': 'Iniciar contenedor',
            'stop': 'Detener contenedor',
            'restart': 'Reiniciar contenedor',
            'rm': 'ELIMINAR contenedor',
            'rmi': 'ELIMINAR imagen',
            'pull': 'Descargar imagen',
            'push': 'Subir imagen',
            'build': 'Construir imagen',
            'ps': 'Listar contenedores',
            'images': 'Listar imágenes',
            'logs': 'Ver logs de contenedor',
            'exec': 'Ejecutar comando en contenedor',
        }
        return explanations.get(subcommand, f"Docker {subcommand}")
    
    def _explain_systemctl(self, args: List[str]) -> str:
        """Explain systemctl command."""
        if not args:
            return "Systemctl"
        action = args[0]
        service = args[1] if len(args) > 1 else "servicio"
        explanations = {
            'start': f'Iniciar servicio {service}',
            'stop': f'DETENER servicio {service}',
            'restart': f'Reiniciar servicio {service}',
            'enable': f'Habilitar servicio {service} al inicio',
            'disable': f'Deshabilitar servicio {service}',
            'status': f'Ver estado de {service}',
        }
        return explanations.get(action, f"Systemctl {action}")
    
    def _explain_apt(self, args: List[str]) -> str:
        """Explain apt command."""
        if not args:
            return "APT"
        action = args[0]
        pkgs = [a for a in args[1:] if not a.startswith('-')]
        pkg_str = ', '.join(pkgs) if pkgs else "paquetes"
        explanations = {
            'install': f'Instalar: {pkg_str}',
            'remove': f'ELIMINAR: {pkg_str}',
            'purge': f'ELIMINAR COMPLETAMENTE: {pkg_str}',
            'update': 'Actualizar lista de paquetes',
            'upgrade': 'Actualizar paquetes instalados',
        }
        return explanations.get(action, f"APT {action}")
    
    def _explain_pacman(self, args: List[str]) -> str:
        """Explain pacman command."""
        for a in args:
            if a.startswith('-'):
                if 'S' in a:
                    return "Instalar paquete"
                if 'R' in a:
                    return "ELIMINAR paquete"
                if 'Q' in a:
                    return "Consultar paquetes"
        return "Pacman"
    
    def _explain_dnf(self, args: List[str]) -> str:
        """Explain dnf command."""
        if not args:
            return "DNF"
        action = args[0]
        explanations = {
            'install': 'Instalar paquete',
            'remove': 'ELIMINAR paquete',
            'update': 'Actualizar paquetes',
            'upgrade': 'Actualizar sistema',
        }
        return explanations.get(action, f"DNF {action}")
    
    def _explain_curl(self, args: List[str]) -> str:
        """Explain curl command."""
        url = next((a for a in args if a.startswith('http')), None)
        if url:
            # Check if piped to shell
            return f"Descargar de {url[:50]}..."
        return "Descargar con curl"
    
    def _explain_wget(self, args: List[str]) -> str:
        """Explain wget command."""
        url = next((a for a in args if a.startswith('http')), None)
        if url:
            return f"Descargar de {url[:50]}..."
        return "Descargar con wget"
    
    def audit_log(self, command: str, risk: str, confirmed: bool, 
                  executed: bool, result: Optional[Dict] = None):
        """
        Log command execution to audit file.
        
        Args:
            command: The command that was attempted
            risk: Risk classification
            confirmed: Whether user confirmed execution
            executed: Whether command was actually executed
            result: Optional execution result
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'risk': risk,
            'confirmed': confirmed,
            'executed': executed,
            'dry_run': self.DRY_RUN,
            'success': result.get('success') if result else None,
            'error': result.get('error') if result else None,
        }
        
        try:
            with open(self.AUDIT_FILE, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def get_audit_history(self, limit: int = 50) -> List[Dict]:
        """
        Get recent audit history.
        
        Args:
            limit: Maximum entries to return
            
        Returns:
            List of audit entries (newest first)
        """
        entries = []
        try:
            with open(self.AUDIT_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except FileNotFoundError:
            pass
        
        return list(reversed(entries[-limit:]))
    
    def format_confirmation_prompt(self, command: str) -> str:
        """
        Format a detailed confirmation prompt for a dangerous command.
        
        Args:
            command: Command to execute
            
        Returns:
            Formatted prompt string
        """
        risk, reason = self.classify_risk(command)
        explanation = self.explain_command(command)
        
        risk_emoji = {
            self.RISK_LOW: "✅",
            self.RISK_MEDIUM: "⚠️",
            self.RISK_HIGH: "🔶",
            self.RISK_CRITICAL: "🔴",
        }
        
        lines = [
            f"\n{risk_emoji.get(risk, '❓')} [{risk}] Comando detectado",
            f"",
            f"  Comando:  {command}",
            f"  Acción:   {explanation}",
        ]
        
        if reason:
            lines.append(f"  Riesgo:   {reason}")
        
        if risk == self.RISK_CRITICAL:
            lines.extend([
                f"",
                f"  [ADVERTENCIA] Este comando puede causar pérdida irreversible de datos.",
                f"  Escribe 'CONFIRMO' para ejecutar.",
            ])
        elif risk == self.RISK_HIGH:
            lines.extend([
                f"",
                f"  Este comando modifica el sistema de forma significativa.",
                f"  Escribe 'si' para ejecutar.",
            ])
        
        return "\n".join(lines)
    
    def request_confirmation(self, command: str) -> Tuple[bool, str]:
        """
        Request user confirmation for a command.
        
        Args:
            command: Command to confirm
            
        Returns:
            Tuple of (confirmed, confirmation_type)
        """
        risk, _ = self.classify_risk(command)
        
        if self.DRY_RUN:
            self.log(f"\n[DRY-RUN] El siguiente comando NO se ejecutará:")
            self.log(f"  {command}", "cyan")
            return (False, "dry_run")
        
        if risk == self.RISK_LOW:
            return (True, "auto")
        
        prompt = self.format_confirmation_prompt(command)
        self.log(prompt)
        
        if risk == self.RISK_CRITICAL:
            self.log("\n¿Ejecutar? (escribe CONFIRMO): ", end="")
            response = input().strip()
            confirmed = response == "CONFIRMO"
            return (confirmed, "explicit" if confirmed else "denied")
        else:
            self.log("\n¿Ejecutar? (s/n): ", end="")
            response = input().strip().lower()
            confirmed = response in ['s', 'si', 'y', 'yes']
            return (confirmed, "explicit" if confirmed else "denied")


def create_security_layer(console=None, lang: str = 'es') -> SecurityLayer:
    """Factory function to create SecurityLayer instance."""
    return SecurityLayer(console, lang)
