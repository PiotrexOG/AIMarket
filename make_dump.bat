@echo off

docker exec -t postgres pg_dump ^
  -U postgres ^
  -d stock_sim ^
  --clean ^
  --if-exists ^
  --create ^
  > dump1.sql

echo Backup zapisany do dump.sql

pause