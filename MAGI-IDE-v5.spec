# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['magi\\main.py'],
    pathex=[],
    binaries=[],
    # `magi/data` lleva el catálogo de proveedores. Sin esta línea el .exe
    # arrancaría con el respaldo de las constantes —funciona, pero se pierde
    # justo lo que se buscaba: poder arreglar un proveedor sin recompilar.
    datas=[('assets', 'assets'), ('magi-gui/dist', 'magi-gui/dist'),
           ('magi/data', 'magi/data')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Pila de ML que MAGI NO usa y que entraba de polizón en el binario.
    #
    # La cadena, trazada instrumentando __import__:
    #   g4f/tools/files.py -> g4f.integration.markitdown -> markitdown
    #   -> magika -> onnxruntime  (y de ahí torch, transformers, tensorflow)
    #
    # Es la integración opcional de g4f para convertir documentos. Ninguna
    # línea de `magi/` importa torch, transformers, tensorflow, onnxruntime ni
    # PyQt5; lo único que se usa de esta zona es sklearn, en
    # magi/modules/skills/loader.py, y ese se queda.
    #
    # Excluirlos arregla ADEMÁS un cuelgue reproducible de la compilación.
    # Volcado de pila del proceso bloqueado (py-spy):
    #     _load_dll_libraries (torch/__init__.py:265)
    #     import_library (PyInstaller/building/build_main.py:227)
    #     run_next_command (PyInstaller/isolated/_child.py:63)
    # PyInstaller importa cada paquete recolectado en un proceso aislado para
    # resolver sus DLLs; al llegar a torch se quedaba parado indefinidamente en
    # el paso "Looking for dynamic libraries". Tres compilaciones seguidas se
    # colgaron ahí.
    #
    # Y encaja con §I.3: torch y onnxruntime son motores de inferencia LOCAL,
    # justo lo que el proyecto declara no usar. Verificado antes de excluirlos:
    # con estos módulos bloqueados en sys.meta_path, magi.main importa, los 11
    # proveedores se registran, el enjambre reparte gpt/gemini/command con
    # diversidad completa y la inferencia responde.
    #
    # SEGUNDO GRUPO: lo que se cuela desde el Python de quien compila.
    #
    # Auditado midiendo el bundle de una compilación local (Analysis-00.toc
    # contra el tamaño real de cada fichero). Los que más pesaban NO eran
    # dependencias del proyecto: eran extras opcionales de g4f que estaban
    # instalados en el Python global de la máquina de desarrollo.
    #
    #     29,2 MB  speech_recognition  (modelo de lenguaje de pocketsphinx)
    #     10,0 MB  yt_dlp
    #      8,1 MB  pandas
    #      7,2 MB  pypdfium2
    #      7,2 MB  sqlalchemy
    #      6,2 MB  openai
    #      4,2 MB  matplotlib
    #
    # Ninguno aparece en requirements.lock y ninguna línea de `magi/` los
    # importa: 55 MB de binario que dependían de qué tuviera instalado quien
    # le diera a compilar. El .exe del release ya salía sin ellos —se compila
    # desde el lock, en un runner limpio—, así que excluirlos NO cambia lo que
    # se publica: hace que una compilación local produzca el MISMO binario que
    # el release. Un binario que depende del entorno de quien lo genera no se
    # puede depurar contra el que descarga la gente.
    #
    # La regla, escrita para no tener que redescubrirla: si no está en
    # requirements.lock y magi/ no lo importa, no viaja dentro.
    # `tests/test_bundle_coherente.py` comprueba que esta lista y el código no
    # se contradigan.
    excludes=[
        'torch', 'torchvision', 'torchaudio',
        'tensorflow', 'transformers', 'onnxruntime',
        'markitdown', 'magika',
        'PyQt5', 'PySide2', 'PySide6',
        'speech_recognition', 'pocketsphinx',
        'yt_dlp', 'pandas', 'pypdfium2', 'pypdfium2_raw',
        'sqlalchemy', 'openai', 'matplotlib',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MAGI-IDE-v5',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icon.ico'],
)
