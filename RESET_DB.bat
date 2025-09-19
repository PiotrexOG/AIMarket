@echo off
echo Usuwanie wszystkich kontenerow i wolumenow z docker-compose...
docker-compose down -v

echo Sprawdzanie czy wolumen zostal usuniety...
docker volume ls | findstr "postgres"
pause