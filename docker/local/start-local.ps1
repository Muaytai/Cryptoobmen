# Проверяем, запущена ли сеть/базы данных
$networkExists = docker network ls | Select-String "cryptoobmen_network"
if (-not $networkExists) {
    Write-Host "Запускаем базы данных и создаем сеть..."
    docker-compose -f docker/postgres/docker-compose.db.yml up -d
    Start-Sleep -Seconds 5
} else {
    Write-Host "Сеть cryptoobmen_network уже существует."
}

# Запускаем локальную среду
Write-Host "Запускаем локальную среду разработки..."
docker-compose -f docker/local/docker-compose.local.yml up -d --build

Write-Host "Локальная среда запущена."
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend: http://localhost:8000" 