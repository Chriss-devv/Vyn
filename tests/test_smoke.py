"""Smoke tests: garantizan que el codigo compila y la config base es valida.

No importan dependencias pesadas (ollama, paramiko, spacy): solo validan
sintaxis y la integridad de los archivos de configuracion.
"""
import json
import pathlib
import py_compile

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_all_python_compiles():
    fallos = []
    for py in ROOT.rglob("*.py"):
        if any(p in py.parts for p in (".venv", "build", "dist", "__pycache__")):
            continue
        try:
            py_compile.compile(str(py), doraise=True)
        except py_compile.PyCompileError as exc:  # pragma: no cover
            fallos.append(f"{py}: {exc}")
    assert not fallos, "Archivos que no compilan:\n" + "\n".join(fallos)


def test_config_template_es_json_valido():
    cfg = ROOT / "config_template.json"
    assert cfg.exists(), "Falta config_template.json"
    data = json.loads(cfg.read_text())
    assert "models" in data, "config_template.json debe definir 'models'"
