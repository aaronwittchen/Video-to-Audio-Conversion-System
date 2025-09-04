# run-all.ps1
# Stop if any command fails
$ErrorActionPreference = "Stop"

# Go into python folder and activate venv
Write-Host "=== Activating virtual environment ==="
Set-Location "python"
.\venv\Scripts\Activate.ps1
Set-Location ..

# --- AUTH ---
Write-Host "=== Deploying auth service ==="
Set-Location "python/src/auth"
kubectl apply -f ./manifests
docker build -t auth-service .
Start-Process powershell -ArgumentList "python server.py"
Set-Location ../../..

# --- GATEWAY ---
Write-Host "=== Deploying gateway service ==="
Set-Location "python/src/gateway"
kubectl apply -f ./manifests
docker build -t gateway-service .
Start-Process powershell -ArgumentList "python server.py"
Set-Location ../../..

# --- CONVERTER ---
Write-Host "=== Deploying converter service ==="
Set-Location "python/src/converter"
kubectl apply -f ./manifests
docker build -t converter-service .
Start-Process powershell -ArgumentList "python consumer.py"
Set-Location ../../..
    
Write-Host "=== All services started ==="
