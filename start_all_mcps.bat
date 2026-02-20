@echo off
echo Starting all MCP servers...

REM Start Email MCP Server (port 8001)
echo Starting Email MCP Server on port 8001...
start "Email MCP Server" cmd /c "cd /d %~dp0 && python -m uvicorn mcp_server.main:app --host 0.0.0.0 --port 8001 --log-level info"

timeout /t 5 /nobreak >nul

REM Start Odoo MCP Server (port 8002)
echo Starting Odoo MCP Server on port 8002...
start "Odoo MCP Server" cmd /c "cd /d %~dp0 && python -m uvicorn odoo_mcp_server:app --host 0.0.0.0 --port 8002 --log-level info"

timeout /t 5 /nobreak >nul

REM Start Social MCP Server (port 8003)
echo Starting Social MCP Server on port 8003...
start "Social MCP Server" cmd /c "cd /d %~dp0 && python -m uvicorn social_mcp_server:app --host 0.0.0.0 --port 8003 --log-level info"

echo.
echo All MCP servers started!
echo.
echo Email MCP Server: http://localhost:8001/docs
echo Odoo MCP Server: http://localhost:8002/docs
echo Social MCP Server: http://localhost:8003/docs
echo.
echo Press any key to exit...
pause >nul