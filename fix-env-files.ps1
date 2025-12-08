# Скрипт для проверки и создания .env файлов для Docker

Write-Host "Проверка env файлов..." -ForegroundColor Cyan

# Проверяем backend
$backendEnv = "backend\env.backend"
$backendEnvDot = "backend\.env.backend"

if (Test-Path $backendEnv) {
    Write-Host "Найден: $backendEnv" -ForegroundColor Green
    if (-not (Test-Path $backendEnvDot)) {
        Copy-Item $backendEnv $backendEnvDot
        Write-Host "Создан: $backendEnvDot" -ForegroundColor Yellow
    } else {
        Write-Host "Уже существует: $backendEnvDot" -ForegroundColor Gray
    }
} else {
    Write-Host "Не найден: $backendEnv" -ForegroundColor Red
}

# Проверяем frontend
$frontendEnv = "frontend\env.development"
$frontendEnvDot = "frontend\.env.development"

if (Test-Path $frontendEnv) {
    Write-Host "Найден: $frontendEnv" -ForegroundColor Green
    if (-not (Test-Path $frontendEnvDot)) {
        Copy-Item $frontendEnv $frontendEnvDot
        Write-Host "Создан: $frontendEnvDot" -ForegroundColor Yellow
    } else {
        Write-Host "Уже существует: $frontendEnvDot" -ForegroundColor Gray
    }
} else {
    Write-Host "Не найден: $frontendEnv" -ForegroundColor Red
}

# Проверяем docker папку
Write-Host "`nПроверка docker папки..." -ForegroundColor Cyan
if (Test-Path "docker\.env.backend") {
    Write-Host "Найден: docker\.env.backend" -ForegroundColor Green
    if (-not (Test-Path $backendEnvDot)) {
        Copy-Item "docker\.env.backend" $backendEnvDot
        Write-Host "Скопирован в: $backendEnvDot" -ForegroundColor Yellow
    }
}

if (Test-Path "docker\.env.development") {
    Write-Host "Найден: docker\.env.development" -ForegroundColor Green
    if (-not (Test-Path $frontendEnvDot)) {
        Copy-Item "docker\.env.development" $frontendEnvDot
        Write-Host "Скопирован в: $frontendEnvDot" -ForegroundColor Yellow
    }
}

Write-Host "`nГотово! Проверьте файлы:" -ForegroundColor Cyan
Get-ChildItem -Path backend,frontend -Filter ".env*" -Force | Select-Object FullName

