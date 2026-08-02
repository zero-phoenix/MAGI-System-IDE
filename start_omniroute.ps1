$ErrorActionPreference = "Stop"

# Directorio de datos
$MagiData = "$env:LOCALAPPDATA\MagiSystem\route"
if (!(Test-Path $MagiData)) {
    New-Item -ItemType Directory -Force -Path $MagiData | Out-Null
}

cd "D:\PROYECTOS\MAGI System IDE\tools\magi-route"

Write-Host "Construyendo contenedor OmniRoute..."
docker build -t magi-route:latest .

Write-Host "Deteniendo contenedor anterior si existe..."
docker rm -f magi-route-server 2>$null

Write-Host "Iniciando contenedor OmniRoute en puerto 20129..."
docker run -d `
    --name magi-route-server `
    -p 127.0.0.1:20129:20128 `
    -e PORT=20128 `
    -e HOST=0.0.0.0 `
    -e REQUIRE_API_KEY=true `
    -e API_KEY=magi-internal-token `
    -e DATA_DIR="/data" `
    -v "$MagiData`:/data" `
    magi-route:latest

Write-Host "OmniRoute iniciado."
