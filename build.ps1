Write-Host "Compilando MAGI System IDE Portable..."
pip install pyinstaller pywebview
pyinstaller --clean --onefile --noconsole --name "MAGI-IDE" --add-data "magi-gui/dist;magi-gui/dist" magi/main.py
Write-Host "Proceso Completado. MAGI-IDE.exe deberia estar en la carpeta 'dist'."
