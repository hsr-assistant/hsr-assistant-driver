## setup

Ensure 'git' and 'uv' installed on your Windows system.

```powershell
uv sync
$Env:LOG_LEVEL = "INFO"  # Optional, defaults to WARNING.
uv run -m setup.prepare_subproj
```

## usage

### http server

```powershell
$Env:LOG_LEVEL = "INFO"  # Optional, defaults to WARNING.
uv run -m hsr_assistant_driver.server
```

### mcp server

```powershell
$Env:LOG_LEVEL = "INFO"  # Optional, defaults to WARNING.
uv --directory . run -m hsr_assistant_driver.mcp_server
```
