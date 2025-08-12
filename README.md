# HSR Assistant Driver

MCP server that exposes Honkai: Star Rail game automation functionality to LLMs by integrating Auto Simulated Universe and March7thAssistant scripts.

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

## acknowledgements

This project integrates functionality from the following Honkai: Star Rail automation scripts:

- [Auto_Simulated_Universe](https://github.com/CHNZYX/Auto_Simulated_Universe.git) - Game automation scripts for Honkai: Star Rail
- [March7thAssistant](https://github.com/moesnow/March7thAssistant.git) - Game automation scripts for Honkai: Star Rail
