Write-Host "Compilando MAGI System IDE Portable..."
pip install pyinstaller pywebview
pyinstaller --clean --onefile --noconsole --name "MAGI-IDE-v5" --add-data "magi-gui/dist;magi-gui/dist" magi/main.py
Write-Host "Copiando ejecutable a la carpeta release..."
New-Item -ItemType Directory -Force -Path "release"
Copy-Item "dist\MAGI-IDE-v5.exe" -Destination "release\MAGI-IDE-v5.exe" -Force
Write-Host "Proceso Completado. MAGI-IDE-v5.exe está listo en la carpeta 'release' para descargarse."
