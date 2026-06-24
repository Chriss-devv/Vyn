#!/usr/bin/env python3

import json
import os
import shutil
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich import box
from rich.table import Table
from i18n import TRANSLATIONS
from core.system_installer import SystemInstaller

console = Console()

class SetupWizard:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "vyn"
        self.config_file = self.config_dir / "config.json"
        self.config = {}
        self.lang = 'es'
    
    def tr(self, key):
        return TRANSLATIONS.get(self.lang, TRANSLATIONS['es']).get(key, key)
    
    def select_language(self):
        console.clear()
        console.print("""
[bold cyan]╔══════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║           VYN v1.0 - AI Assistant System                 ║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════╝[/bold cyan]

[yellow]Select language / Selecciona idioma:[/yellow]

  1. English
  2. Español

""")
        choice = Prompt.ask("Option / Opción", choices=["1", "2"], default="2")
        self.lang = 'en' if choice == "1" else 'es'
        self.config['language'] = self.lang
    
    def welcome(self):
        console.clear()
        console.print(f"""
[bold cyan]╔══════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║           {self.tr('welcome_title'):^44}║[/bold cyan]
[bold cyan]║              {self.tr('first_time_wizard'):^42}║[/bold cyan]
[bold cyan]╚══════════════════════════════════════════════════════════╝[/bold cyan]

[yellow]{self.tr('welcome')}[/yellow]

{self.tr('wizard_intro')}
{self.tr('skip_info')}

[dim]{self.tr('press_enter')}[/dim]
""")
        input()
    
    def get_installed_models(self):
        import subprocess
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return []
            lines = result.stdout.strip().split('\n')
            models = []
            for line in lines[1:]:
                if line.strip():
                    parts = line.split()
                    if parts:
                        models.append(parts[0])
            return models
        except Exception:
            return []
    
    def pull_model(self, model_name):
        import subprocess
        console.print(f"\n[cyan]{self.tr('downloading')} {model_name}...[/cyan]")
        console.print(f"[dim]{self.tr('download_time')}[/dim]\n")
        
        try:
            process = subprocess.Popen(
                ['ollama', 'pull', model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in process.stdout:
                console.print(f"[dim]{line.strip()}[/dim]")
            process.wait()
            
            if process.returncode == 0:
                console.print(f"\n[green]✓[/green] {model_name} {self.tr('installed_ok')}")
                return True
            else:
                console.print(f"\n[red]{self.tr('download_failed')}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return False
    
    def select_model_from_list(self, models, role_name, allow_none=True):
        table = Table(title=self.tr('installed_models'), show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Model" if self.lang == 'en' else "Modelo", style="green")
        
        for idx, model in enumerate(models, 1):
            table.add_row(str(idx), model)
        
        if allow_none:
            table.add_row("0", f"[dim]{self.tr('skip_none')}[/dim]")
        
        console.print(table)
        
        while True:
            try:
                choice = Prompt.ask(f"[cyan]{self.tr('model_for').format(role_name)}[/cyan]")
                choice_num = int(choice)
                
                if choice_num == 0 and allow_none:
                    return None
                elif 1 <= choice_num <= len(models):
                    return models[choice_num - 1]
                else:
                    console.print(f"[red]{self.tr('invalid_number')}[/red]")
            except ValueError:
                console.print(f"[red]{self.tr('enter_number')}[/red]")
    
    def setup_models(self):
        console.print(f"\n[bold cyan]═══ {self.tr('models_title')} ═══[/bold cyan]\n")
        
        console.print(f"[yellow]{self.tr('detecting_models')}[/yellow]")
        models = self.get_installed_models()
        
        if not models:
            console.print(f"\n[red]⚠️  {self.tr('no_models_found')}[/red]")
            console.print(f"[yellow]{self.tr('need_model')}[/yellow]\n")
            
            # Use RAM-based recommendations if installer available
            if hasattr(self, 'installer'):
                recommendations = self.installer.get_recommended_models()
                ram_tier = self.installer.get_ram_tier()
                
                console.print(f"[cyan]Modelos recomendados para {self.installer.ram_gb:.0f}GB RAM ({ram_tier}):[/cyan]")
                console.print(f"[dim]{recommendations['description']}[/dim]\n")
                
                for i, model in enumerate(recommendations['models'], 1):
                    marker = " [cyan](recomendado)[/cyan]" if model == recommendations['primary'] else ""
                    console.print(f"  {i}. {model}{marker}")
                
                console.print(f"\n  0. Saltar (configurar después)")
                console.print(f"  c. Modelo personalizado\n")
                
                choice = Prompt.ask("Selección (números separados por coma)", default="1")
                
                models_to_install = []
                if choice.lower() == 'c':
                    custom = Prompt.ask("Nombre del modelo (ej: llama3.1:8b)")
                    if custom:
                        models_to_install = [custom]
                elif choice != '0':
                    for c in choice.split(','):
                        c = c.strip()
                        if c.isdigit():
                            idx = int(c) - 1
                            if 0 <= idx < len(recommendations['models']):
                                models_to_install.append(recommendations['models'][idx])
                
                installed = []
                for model in models_to_install:
                    if self.installer.pull_model(model):
                        installed.append(model)
                
                if installed:
                    primary = installed[0]
                    self.config['models'] = {
                        'coding': installed[1] if len(installed) > 1 else primary,
                        'research': primary,
                        'vision': primary,
                        'sysadmin': primary
                    }
                    console.print(f"\n[green]✓[/green] Modelos configurados")
                    return
                else:
                    # Use default recommendations
                    primary = recommendations['primary']
                    self.config['models'] = {
                        'coding': primary,
                        'research': primary,
                        'vision': primary,
                        'sysadmin': primary
                    }
                    return
            else:
                # Fallback to original behavior
                console.print(f"[cyan]{self.tr('recommended_models')}[/cyan]")
                console.print("  • gemma3:4b (rápido, 4GB RAM)")
                console.print("  • qwen3:8b (código, 8GB RAM)")
                console.print("  • llama3.1:8b (general, 8GB RAM)")
                console.print("  • llava:7b (visión, 8GB RAM)\n")
                
                do_pull = Confirm.ask(self.tr('download_now'), default=True)
                
                if do_pull:
                    model_to_pull = Prompt.ask(self.tr('which_model'), default="gemma3:4b")
                    success = self.pull_model(model_to_pull)
                    
                    if success:
                        console.print(f"\n[green]✓[/green] {self.tr('using_for_all').format(model_to_pull)}")
                        self.config['models'] = {
                            'coding': model_to_pull,
                            'research': model_to_pull,
                            'vision': model_to_pull,
                            'sysadmin': model_to_pull
                        }
                        return
                    else:
                        self.config['models'] = {
                            'coding': 'gemma3:4b',
                            'research': 'gemma3:4b',
                            'vision': 'gemma3:4b',
                            'sysadmin': 'gemma3:4b'
                        }
                        return
                else:
                    console.print(f"\n[yellow]{self.tr('using_defaults')}[/yellow]")
                    self.config['models'] = {
                        'coding': 'gemma3:4b',
                        'research': 'gemma3:4b',
                        'vision': 'gemma3:4b',
                        'sysadmin': 'gemma3:4b'
                    }
                    return
        
        console.print(f"[green]✓[/green] {self.tr('models_found').format(len(models))}\n")
        
        console.print(f"[yellow]{self.tr('vyn_uses_models')}[/yellow]")
        console.print(f"  • {self.tr('coding_desc')}")
        console.print(f"  • {self.tr('research_desc')}")
        console.print(f"  • {self.tr('vision_desc')}")
        console.print(f"  • {self.tr('sysadmin_desc')}\n")
        
        if len(models) == 1:
            use_single = Confirm.ask(self.tr('only_one_model').format(models[0]), default=True)
            
            if use_single:
                self.config['models'] = {
                    'coding': models[0],
                    'research': models[0],
                    'vision': models[0],
                    'sysadmin': models[0]
                }
                console.print(f"[green]✓[/green] {self.tr('using_for_all').format(models[0])}")
                return
        
        self.config['models'] = {}
        default_model = models[0]
        
        console.print(f"\n[cyan]{self.tr('select_model_for')}[/cyan]")
        console.print(f"[dim]{self.tr('select_0_default')}[/dim]\n")
        
        coding = self.select_model_from_list(models, "CODING")
        self.config['models']['coding'] = coding if coding else default_model
        
        research = self.select_model_from_list(models, "RESEARCH")
        self.config['models']['research'] = research if research else default_model
        
        vision = self.select_model_from_list(models, "VISION")
        self.config['models']['vision'] = vision if vision else default_model
        
        sysadmin = self.select_model_from_list(models, "SYSADMIN")
        self.config['models']['sysadmin'] = sysadmin if sysadmin else default_model
        
        console.print(f"\n[green]✓[/green] {self.tr('models_configured')}")
    
    def setup_homelab(self):
        console.print(f"\n[bold cyan]═══ {self.tr('homelab_title')} ═══[/bold cyan]\n")
        
        console.print(f"[yellow]{self.tr('homelab_desc')}[/yellow]")
        console.print(f"{self.tr('homelab_optional')}\n")
        
        enable_homelab = Confirm.ask(self.tr('have_homelab'), default=False)
        
        if enable_homelab:
            console.print(f"\n[green]{self.tr('great_configure')}[/green]\n")
            
            host = Prompt.ask(self.tr('server_ip'))
            user = Prompt.ask(self.tr('ssh_user'), default="root")
            
            ssh_key_default = str(Path.home() / ".ssh" / "id_ed25519")
            ssh_key = Prompt.ask(self.tr('ssh_key_path'), default=ssh_key_default)
            
            if not Path(ssh_key).exists():
                console.print(f"[red]⚠️  {self.tr('key_not_exist').format(ssh_key)}[/red]")
                create_key = Confirm.ask(self.tr('help_create_key'))
                
                if create_key:
                    console.print(f"\n[yellow]{self.tr('run_this')}[/yellow]")
                    console.print(f"[cyan]ssh-keygen -t ed25519 -f {ssh_key}[/cyan]")
                    console.print(f"\n{self.tr('then_run')}")
                    console.print(f"[cyan]ssh-copy-id -i {ssh_key}.pub {user}@{host}[/cyan]\n")
                    input(f"{self.tr('press_enter_done')}")
            
            self.config['homelab'] = {
                'enabled': True,
                'host': host,
                'user': user,
                'ssh_key': ssh_key,
                'port': 22
            }
            console.print(f"\n[green]✓[/green] {self.tr('homelab_configured').format(f'{user}@{host}')}")
        else:
            self.config['homelab'] = {'enabled': False}
            console.print(f"[dim]{self.tr('homelab_disabled')}[/dim]")
    
    def setup_web_search(self):
        console.print(f"\n[bold cyan]═══ {self.tr('web_search_title')} ═══[/bold cyan]\n")
        console.print(f"[yellow]{self.tr('web_search_desc')}[/yellow]\n")
        
        enable_search = Confirm.ask(self.tr('enable_search'), default=True)
        
        if enable_search:
            max_results = Prompt.ask(self.tr('max_results'), default="5")
            timeout = Prompt.ask(self.tr('timeout_seconds'), default="10")
            
            self.config['web_search'] = {
                'enabled': True,
                'max_results': int(max_results),
                'timeout': int(timeout),
                'extract_full_content': True
            }
            console.print(f"[green]✓[/green] {self.tr('search_enabled')}")
        else:
            self.config['web_search'] = {'enabled': False}
    
    def setup_sandbox(self):
        console.print(f"\n[bold cyan]═══ {self.tr('sandbox_title')} ═══[/bold cyan]\n")
        console.print(f"[yellow]{self.tr('sandbox_desc')}[/yellow]\n")
        
        enable_sandbox = Confirm.ask(self.tr('enable_sandbox'), default=True)
        
        if enable_sandbox:
            sandbox_dir = Prompt.ask(self.tr('sandbox_dir'), default="/tmp/vyn_sandbox")
            max_retries = Prompt.ask(self.tr('max_retries'), default="3")
            timeout = Prompt.ask(self.tr('exec_timeout'), default="30")
            
            self.config['sandbox'] = {
                'enabled': True,
                'directory': sandbox_dir,
                'max_retries': int(max_retries),
                'timeout': int(timeout),
                'auto_correct': True
            }
            Path(sandbox_dir).mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✓[/green] {self.tr('sandbox_configured').format(sandbox_dir)}")
        else:
            self.config['sandbox'] = {'enabled': False}
    
    def setup_memory(self):
        console.print(f"\n[bold cyan]═══ {self.tr('memory_title')} ═══[/bold cyan]\n")
        console.print(f"[yellow]{self.tr('memory_desc')}[/yellow]\n")
        
        db_location = Prompt.ask(self.tr('db_location'), default=str(self.config_dir / "vyn_brain.db"))
        
        self.config['memory'] = {
            'enabled': True,
            'database': db_location,
            'store_conversations': True,
            'learn_patterns': True
        }
        console.print(f"[green]✓[/green] {self.tr('memory_configured')}")
    
    def setup_ui(self):
        console.print(f"\n[bold cyan]═══ {self.tr('ui_title')} ═══[/bold cyan]\n")
        
        theme_options = {"1": "monokai", "2": "dracula", "3": "nord", "4": "gruvbox"}
        
        console.print(f"[yellow]{self.tr('themes_available')}[/yellow]")
        for key, theme in theme_options.items():
            console.print(f"  {key}. {theme}")
        
        theme_choice = Prompt.ask(f"\n{self.tr('choose_theme')}", choices=list(theme_options.keys()), default="1")
        show_telemetry = Confirm.ask(self.tr('show_telemetry'), default=True)
        
        self.config['ui'] = {
            'theme': theme_options[theme_choice],
            'show_telemetry': show_telemetry,
            'auto_clear': False
        }
        console.print(f"[green]✓[/green] {self.tr('theme_set').format(theme_options[theme_choice])}")
    
    def setup_advanced(self):
        console.print(f"\n[bold cyan]═══ {self.tr('advanced_title')} ═══[/bold cyan]\n")
        
        show_advanced = Confirm.ask(self.tr('configure_advanced'), default=False)
        
        if show_advanced:
            enable_cve = Confirm.ask(self.tr('enable_cve'), default=True)
            enable_vision = Confirm.ask(self.tr('enable_vision'), default=True)
            enable_rag = Confirm.ask(self.tr('enable_rag'), default=True)
            
            if enable_rag:
                scan_paths = Prompt.ask(self.tr('dirs_to_scan'), default=str(Path.home() / "projects"))
                scan_paths = [p.strip() for p in scan_paths.split(",")]
            else:
                scan_paths = []
            
            self.config['advanced'] = {
                'cve_scanner': {'enabled': enable_cve},
                'vision': {'enabled': enable_vision},
                'rag': {'enabled': enable_rag, 'scan_paths': scan_paths}
            }
        else:
            self.config['advanced'] = {
                'cve_scanner': {'enabled': True},
                'vision': {'enabled': True},
                'rag': {'enabled': False, 'scan_paths': []}
            }
    
    def save_config(self):
        console.print(f"\n[bold cyan]═══ {self.tr('saving_config')} ═══[/bold cyan]\n")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        console.print(f"[green]✓[/green] {self.tr('config_saved')}")
        console.print(f"  [cyan]{self.config_file}[/cyan]\n")
    
    def summary(self):
        console.print(f"\n[bold cyan]═══ {self.tr('summary_title')} ═══[/bold cyan]\n")
        
        enabled = self.tr('enabled')
        disabled = self.tr('disabled')
        
        summary_text = f"""
{self.tr('models_label')}
  • Coding: {self.config['models']['coding']}
  • Research: {self.config['models']['research']}
  • Vision: {self.config['models']['vision']}
  • SysAdmin: {self.config['models']['sysadmin']}

{self.tr('homelab_label')}
  {'• ' + enabled + ': ' + self.config['homelab'].get('host', '') if self.config['homelab']['enabled'] else '• ' + disabled}

{self.tr('search_label')}
  {'• ' + enabled if self.config['web_search']['enabled'] else '• ' + disabled}

{self.tr('sandbox_label')}
  {'• ' + enabled + ': ' + self.config['sandbox'].get('directory', '') if self.config['sandbox']['enabled'] else '• ' + disabled}

{self.tr('theme_label')}
  • {self.config['ui']['theme']}
"""
        console.print(Panel(summary_text, box=box.ROUNDED))
        
        console.print(f"\n[green]✨ {self.tr('config_complete')}[/green]")
        console.print(f"\n{self.tr('edit_config')}")
        console.print(f"  [cyan]{self.config_file}[/cyan]\n")
        console.print(f"[yellow]{self.tr('to_start')}[/yellow]")
        console.print("  [cyan]./vyn[/cyan] or [cyan]python vyn.py[/cyan]\n")
        input(f"{self.tr('press_enter')}")
    
    def setup_system(self):
        """Step 1: Detect system and install Ollama if needed."""
        console.print(f"\n[bold cyan]═══ {self.tr('system_detection') if 'system_detection' in TRANSLATIONS.get(self.lang, {}) else 'Detección del Sistema'} ═══[/bold cyan]\n")
        
        self.installer = SystemInstaller(console)
        
        # Show system info
        console.print(f"[green]✓[/green] Sistema: {self.installer.distro_info['pretty_name']}")
        console.print(f"[green]✓[/green] RAM: {self.installer.ram_gb:.1f}GB")
        console.print(f"[green]✓[/green] Tier: {self.installer.get_ram_tier()}")
        
        # Store system info in config
        self.config['_system'] = {
            'distro': self.installer.distro_info['name'],
            'distro_family': self.installer.distro_info['family'],
            'ram_gb': round(self.installer.ram_gb, 1),
            'ram_tier': self.installer.get_ram_tier()
        }
        
        # Check Ollama
        if self.installer.is_ollama_installed():
            console.print(f"[green]✓[/green] Ollama: Instalado")
        else:
            console.print(f"\n[yellow]⚠ Ollama no está instalado[/yellow]")
            console.print(f"[dim]VYN requiere Ollama para funcionar.[/dim]\n")
            
            install_ollama = Confirm.ask(
                "¿Instalar Ollama automáticamente?" if self.lang == 'es' else "Install Ollama automatically?",
                default=True
            )
            
            if install_ollama:
                success = self.installer.install_ollama()
                if not success:
                    console.print(f"\n[red]Error instalando Ollama.[/red]")
                    console.print(f"[yellow]Instala manualmente:[/yellow]")
                    console.print(f"  [cyan]curl -fsSL https://ollama.com/install.sh | sh[/cyan]\n")
                    raise Exception("Ollama installation failed")
            else:
                console.print(f"\n[yellow]Instala Ollama manualmente para continuar:[/yellow]")
                console.print(f"  [cyan]curl -fsSL https://ollama.com/install.sh | sh[/cyan]\n")
                raise Exception("Ollama required")
        
        console.print()
    
    def run(self):
        try:
            self.select_language()
            self.welcome()
            self.setup_system()  # NEW: System detection & Ollama install
            self.setup_models()
            self.setup_homelab()
            self.setup_web_search()
            self.setup_sandbox()
            self.setup_memory()
            self.setup_ui()
            self.setup_advanced()
            self.save_config()
            self.summary()
            return True
        except KeyboardInterrupt:
            console.print(f"\n\n[red]{self.tr('setup_cancelled')}[/red]")
            return False
        except Exception as e:
            console.print(f"\n\n[red]Error: {e}[/red]")
            return False

def main():
    wizard = SetupWizard()
    success = wizard.run()
    
    if success:
        console.print(f"[green]{wizard.tr('all_ready')}[/green]")
    else:
        console.print(f"[yellow]{wizard.tr('incomplete')}[/yellow]")

if __name__ == "__main__":
    main()
