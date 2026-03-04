@echo off
REM --- Window 1: GizmoSQL Server ---
start "GizmoSQL Server" cmd /k "gizmosql_server.exe -B duckdb --database-filename "C:\projects\blogpost\gizmosql-matrix\persons.duckdb" --username scott --password tiger"

REM Give the server a moment to initialize before connecting
timeout /t 3 /nobreak >nul

REM --- Window 2: GizmoSQL Client ---
start "GizmoSQL Client" cmd /k "gizmosql_client --username scott --host localhost --port 31337"

REM --- Window 3: Update Persons Agent ---
start "Update Persons Agent" cmd /k "call C:\projects\blogpost\gizmosql-matrix\.venv\Scripts\activate.bat && set GIZMOSQL_USERNAME=scott && set GIZMOSQL_PASSWORD=tiger && python "C:\projects\blogpost\gizmosql-matrix\update-persons-agent.py""
