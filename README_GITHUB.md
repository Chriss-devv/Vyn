# 🤖 VYN v1.0 - AI Assistant System

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/platform-linux-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/license-Proprietary-red.svg" alt="License">
</p>

**VYN** (Voice Your Needs) - Asistente de IA autónomo con capacidades avanzadas de búsqueda web, ejecución de código, gestión de infraestructura remota y análisis de imágenes.

---

## ✨ Características

- 🔍 **Búsqueda Web Inteligente** con extracción completa de contenido
- 🧪 **Sandbox de Código** con auto-corrección
- 🤖 **Auto-Switching** entre modelos según la tarea
- 🏠 **Gestión de Home Lab** via SSH
- 🖼️ **Vision AI** para análisis de imágenes
- 🧠 **Memoria Persistente** con base de datos SQLite
- ⚙️ **100% Customizable** via setup wizard interactivo

---

## 📥 Instalación

### Prerequisitos

1. **Ollama** debe estar instalado:
```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl start ollama
```

2. **Descargar al menos un modelo**:
```bash
ollama pull llama3.1:8b
```

### Descargar VYN

**Linux x64:**
```bash
wget https://github.com/tu-usuario/vyn/releases/latest/download/vyn-linux-x64-v1.0.0
chmod +x vyn-linux-x64-v1.0.0
./vyn-linux-x64-v1.0.0
```

El setup wizard se ejecutará automáticamente en la primera ejecución.

---

## 💻 Uso Rápido

```bash
> help                  # Ver comandos
> busca noticias        # Búsqueda web
> haz código python     # Generar código
> config                # Ver configuración
> salir                 # Salir
```

---

## 📝 Licencia

**Propietaria** - Todos los derechos reservados

Este es software propietario. El código fuente NO está disponible públicamente.

Para licencias comerciales o código fuente, contacta: license@vyn-ai.com

---

## 🎯 Soporte

- 📧 Email: support@vyn-ai.com
- 🐛 Issues: [GitHub Issues](https://github.com/tu-usuario/vyn/issues)
- 📖 Docs: [Wiki](https://github.com/tu-usuario/vyn/wiki)

---

## 🔒 Seguridad

VYN ejecuta todo localmente. Tus datos nunca salen de tu máquina.

- ✅ Sin telemetría
- ✅ Sin conexiones a servidores externos
- ✅ Código ejecutado en sandbox aislado

---

## ⚡ Características Técnicas

- Basado en Ollama (modelos locales)
- Arquitectura modular
- Sistema de permisos en cascada
- Graceful shutdown con signal handlers
- Anti-alucinación con validación de fuentes

---

**🎉 Desarrollado por Chris - Ingeniero TI**

_Si te gusta VYN, dale una ⭐ al repositorio_
