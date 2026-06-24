# Cómo contribuir a VYN

¡Gracias por tu interés! Esta guía resume el flujo de trabajo.

## Entorno de desarrollo

```bash
git clone https://github.com/Chriss-devv/Vyn.git
cd Vyn
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp config_template.json config.json   # tu config real (ignorada por git)
```

## Antes de abrir un Pull Request

1. **Compila**: `python -m compileall core modules ui *.py`
2. **Lint**: `ruff check .`
3. **Tests**: `pytest -q`
4. No incluyas secretos: `config.json`, `.env` y `*.db` están en `.gitignore`.

## Estilo

- Python 3.11+, 4 espacios, líneas ≤ 100 col (ver `ruff.toml` y `.editorconfig`).
- Commits descriptivos, en imperativo.

## Reportar bugs

Usa la plantilla de *issue* e incluye SO, versión de Python y pasos para reproducir.
