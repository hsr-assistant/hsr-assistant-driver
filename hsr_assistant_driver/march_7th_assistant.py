from typing import Any
from pathlib import Path

import yaml


MARCH_7TH_ASSISTANT_DIR = Path(__file__).parent.parent / "March7thAssistant"
AUTO_SIMULATED_UNIVERSE_DIR = Path(__file__).parent.parent / "Auto_Simulated_Universe"


def prepare_config_yaml(updates: dict) -> None:
    # Write this minimal config.yaml. Other configs will be defaults.
    config_file_path = MARCH_7TH_ASSISTANT_DIR / "config.yaml"
    with open(config_file_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(
            updates, file, default_flow_style=False, allow_unicode=True, sort_keys=False
        )


def prepare_to_run(run_config: dict) -> tuple[list[str], dict[str, Any]]:
    task: str = run_config["task"]
    if task == "material":
        category: str = run_config["material_config"]["category"]
        id: str = run_config["material_config"]["id"]
        config_updates = {
            "instance_type": category,
            "instance_names": {category: id},
        }
        prepare_config_yaml(config_updates)

        args = ["power"]
    elif task == "universe":
        universe_type = run_config["universe_config"]["type"]
        difficulty = run_config["universe_config"].get("difficulty", 0)

        python_exe_path = (
            AUTO_SIMULATED_UNIVERSE_DIR / ".venv" / "Scripts" / "python.exe"
        )
        universe_category = "divergent" if universe_type == "差分宇宙" else "universe"

        config_updates = {
            "python_exe_path": str(python_exe_path),
            "universe_operation_mode": "source",
            "universe_category": universe_category,
            "universe_bonus_enable": True,
            "universe_count": 1,
            "universe_path": str(AUTO_SIMULATED_UNIVERSE_DIR),
            "universe_requirements": True,
            "universe_difficulty": difficulty,
        }
        prepare_config_yaml(config_updates)

        args = ["universe"]
    elif task == "claim_reward":
        args = ["claim_reward_daily_training"]
    else:
        raise NotImplementedError

    python = MARCH_7TH_ASSISTANT_DIR / ".venv" / "Scripts" / "python.exe"

    args = [str(python), str(MARCH_7TH_ASSISTANT_DIR / "main.py"), *args]
    kwargs = {"cwd": str(MARCH_7TH_ASSISTANT_DIR)}

    return args, kwargs
