# Política de Seguridad

## Reporte de vulnerabilidades

Si encuentras una vulnerabilidad, **no abras un issue público**. Escribe en
privado al mantenedor (Chris-devv) vía los canales del perfil de GitHub.
Intentaremos responder en un plazo razonable.

## Manejo de secretos

VYN **no contiene** credenciales en el repositorio:

- La API/keys y la config real viven en `config.json` y `.env`, **ignorados por git**.
- Usa `config_template.json` como base.
- Nunca subas `config.json`, `.env`, `*.db` ni claves SSH.

## Alcance

VYN ejecuta código en un sandbox y administra servidores por SSH. Ejecuta solo
en entornos donde confíes en la configuración y los modelos locales.
