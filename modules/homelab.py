"""
VYN v1.2 - Home Lab Management
SSH-based remote server management with security controls.
"""

import logging
import subprocess
import shlex
import sys
from typing import Dict, Optional, List
import paramiko
from pathlib import Path

logger = logging.getLogger(__name__)


class HomeLab:
    """
    Manages SSH connections to home lab server with two-tier permission system.
    SAFE commands execute automatically, DANGEROUS commands require confirmation.
    """
    
    # Server configuration (ajusta a tu red en config.json)
    DEFAULT_HOST = "192.168.1.100"
    DEFAULT_USER = "root"
    DEFAULT_KEY = str(Path.home() / ".ssh" / "id_ed25519")
    DEFAULT_TIMEOUT = 30
    
    # Safe commands that can auto-execute
    SAFE_COMMANDS = [
        'df', 'docker ps', 'docker images', 'systemctl status',
        'free', 'tail', 'cat', 'ls', 'pwd', 'whoami', 'uptime',
        'top -bn1', 'htop -n1', 'ps aux', 'netstat', 'ss',
        'journalctl', 'dmesg', 'uname', 'hostname'
    ]
    
    # Dangerous command patterns (require confirmation)
    DANGEROUS_PATTERNS = [
        'rm', 'delete', 'restart', 'reboot', 'shutdown', 'halt',
        'kill', 'pkill', 'systemctl restart', 'systemctl stop',
        'docker restart', 'docker stop', 'docker rm', 'docker kill',
        'nginx -s reload', 'service restart', 'init 6', 'poweroff'
    ]
    
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        user: str = DEFAULT_USER,
        key_path: str = DEFAULT_KEY,
        timeout: int = DEFAULT_TIMEOUT
    ):
        self.host = host
        self.user = user
        self.key_path = key_path
        self.timeout = timeout
        self.ssh_client: Optional[paramiko.SSHClient] = None
        
        logger.info(f"[VYN] HomeLab initialized for {user}@{host}")
    
    def _is_safe_command(self, command: str) -> bool:
        """
        Checks if a command is in the safe list.
        
        Args:
            command: Command to check
            
        Returns:
            True if safe, False if dangerous
        """
        command_lower = command.lower().strip()
        
        # Check if starts with any safe command
        for safe_cmd in self.SAFE_COMMANDS:
            if command_lower.startswith(safe_cmd):
                return True
        
        # Check for dangerous patterns
        for dangerous in self.DANGEROUS_PATTERNS:
            if dangerous in command_lower:
                return False
        
        # If not in safe list and no dangerous patterns, treat as potentially dangerous
        return False
    
    def connect(self) -> bool:
        """
        Establishes SSH connection to home lab server.
        
        Returns:
            True if connected successfully
        """
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.ssh_client.connect(
                hostname=self.host,
                username=self.user,
                key_filename=self.key_path,
                timeout=10
            )
            
            logger.info(f"[VYN] ✅ Connected to {self.user}@{self.host}")
            return True
            
        except Exception as e:
            logger.error(f"[VYN] ❌ SSH connection failed: {e}")
            return False
    
    def disconnect(self):
        """Closes SSH connection"""
        if self.ssh_client:
            self.ssh_client.close()
            logger.info("[VYN] SSH connection closed")
    
    def execute_remote(
        self,
        command: str,
        require_confirmation: bool = True,
        stream_output: bool = True
    ) -> Dict:
        """
        Executes command on remote server with real-time output.
        
        Args:
            command: Command to execute
            require_confirmation: Whether to ask for confirmation (overridden for safe commands)
            stream_output: Whether to stream output in real-time
            
        Returns:
            Dict with success, output, error
        """
        # Determine if command is safe
        is_safe = self._is_safe_command(command)
        
        # Ask for confirmation if dangerous
        if not is_safe and require_confirmation:
            from rich.prompt import Confirm
            from rich.console import Console
            
            console = Console()
            console.print(f"\n[red]⚠️  DANGEROUS COMMAND DETECTED[/red]")
            console.print(f"[yellow]Command:[/yellow] {command}")
            console.print(f"[yellow]Server:[/yellow] {self.user}@{self.host}")
            
            confirmed = Confirm.ask("[red]Execute this command?[/red]", default=False)
            
            if not confirmed:
                logger.info("[VYN] User cancelled dangerous command")
                return {
                    'success': False,
                    'output': '',
                    'error': 'Operation cancelled by user',
                    'cancelled': True
                }
        
        # Sanitize command
        safe_command = shlex.quote(command)
        
        # Connect if not already connected
        if not self.ssh_client or not self.ssh_client.get_transport() or not self.ssh_client.get_transport().is_active():
            if not self.connect():
                return {
                    'success': False,
                    'output': '',
                    'error': 'Failed to establish SSH connection'
                }
        
        print(f"\n{'='*60}")
        print(f"🌐 Ejecutando en {self.user}@{self.host}: {command}")
        print(f"{'='*60}\n")
        
        try:
            # Execute command
            stdin, stdout, stderr = self.ssh_client.exec_command(
                command,
                timeout=self.timeout
            )
            
            output_lines = []
            error_lines = []
            
            if stream_output:
                # Stream output in real-time
                for line in stdout:
                    line = line.rstrip()
                    print(line)
                    sys.stdout.flush()
                    output_lines.append(line)
                
                # Read errors
                for line in stderr:
                    error_lines.append(line.rstrip())
            else:
                # Read all at once
                output_lines = [line.rstrip() for line in stdout.readlines()]
                error_lines = [line.rstrip() for line in stderr.readlines()]
            
            # Get exit status
            exit_status = stdout.channel.recv_exit_status()
            
            output_str = '\n'.join(output_lines)
            error_str = '\n'.join(error_lines) if error_lines else None
            
            print(f"\n{'='*60}")
            if exit_status == 0:
                print("✅ Comando remoto completado")
            else:
                print(f"❌ Comando terminó con código {exit_status}")
            print(f"{'='*60}\n")
            
            # Log this operation
            logger.info(f"[VYN] Remote command executed: {command} (exit: {exit_status})")
            
            return {
                'success': exit_status == 0,
                'output': output_str,
                'error': error_str,
                'exit_status': exit_status
            }
            
        except Exception as e:
            logger.error(f"[VYN] Remote execution failed: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
    
    def audit_log(self, command: str, result: Dict):
        """
        Logs command execution for audit trail.
        
        Args:
            command: Executed command
            result: Execution result
        """
        # This would typically write to a dedicated audit log file
        logger.info(f"[VYN][AUDIT] Command: {command}, Success: {result.get('success')}, Exit: {result.get('exit_status')}")
    
    def quick_diagnostic(self) -> Dict:
        """
        Runs a set of diagnostic commands on the server.
        
        Returns:
            Dict with diagnostic results
        """
        diagnostics = {}
        
        safe_checks = [
            ('disk_usage', 'df -h'),
            ('memory', 'free -h'),
            ('docker_containers', 'docker ps'),
            ('uptime', 'uptime'),
            ('system_load', 'top -bn1 | head -n 5')
        ]
        
        print("\n🔍 Ejecutando diagnóstico del servidor...\n")
        
        for name, cmd in safe_checks:
            result = self.execute_remote(cmd, require_confirmation=False, stream_output=False)
            diagnostics[name] = {
                'success': result['success'],
                'output': result['output'] if result['success'] else result.get('error', 'Failed')
            }
        
        return diagnostics
    
    def execute_command(self, command: str, dangerous_ok: bool = True) -> Dict:
        """Simplified execution - auto-detects safe/dangerous"""
        result = self.execute_remote(command, require_confirmation=dangerous_ok, stream_output=True)
        if result['success']:
            self.audit_log(command, result)
        return result
    
    def close(self):
        """Ensure cleanup"""
        self.disconnect()
