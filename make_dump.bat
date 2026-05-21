@echo off
echo [INFO] Pobieram dump z kontenera Docker...

:: 'postgres' to nazwa kontenera z Twojego pliku docker-compose.yml
docker exec -e PGPASSWORD=postgres postgres pg_dump -U postgres -d stock_sim -F p -b -v > dump2.sql

if %ERRORLEVEL% NEQ 0 (
    echo [BŁĄD] Nie udało się pobrać dumpa. Upewnij się, że kontener Docker działa!
    pause
    exit /b
)

echo [SUKCES] Gotowe! Plik dump2.sql został zapisany.
pause