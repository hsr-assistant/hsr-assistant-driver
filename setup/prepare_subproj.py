import logging
import os
from pathlib import Path
import subprocess
import sys


def run_command(command, cwd=None):
    logging.info(f"Executing: {' '.join(command)}")
    try:
        if VERBOSE:
            kwargs = {"stdout": sys.stdout, "stderr": sys.stderr}
        else:
            kwargs = {"capture_output": True}
        subprocess.run(
            command, check=True, text=True, encoding="utf-8", cwd=cwd, **kwargs
        )
        return True
    except subprocess.CalledProcessError as e:
        logging.error(
            f"Command failed with exit code {e.returncode}: {' '.join(command)}"
        )
        if not VERBOSE:
            logging.error(f"STDOUT:\n{e.stdout}")
            logging.error(f"STDERR:\n{e.stderr}")
        return False
    except FileNotFoundError:
        logging.error(
            f"Command not found. Make sure '{command[0]}' is installed and in your PATH."
        )
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return False


def prepare_common(
    patch_file: Path, project_dir: Path, project_url: str, project_commit: str
):
    if project_dir.exists():
        logging.warning(
            f"Project directory '{project_dir}' already exists. Skipping prepare."
            " If previous setup failed, delete the directory and try again."
        )
        return True

    logging.info(f"Cloning {project_url} into {project_dir}")
    if not run_command(["git", "clone", project_url, str(project_dir)]):
        logging.error("Failed to clone the repository.")
        return False

    logging.info(f"Checking out commit {project_commit} in {project_dir}")
    if not run_command(["git", "checkout", project_commit], cwd=project_dir):
        logging.error(f"Failed to checkout commit {project_commit}.")
        return False

    logging.info(f"Applying patch {patch_file} to {project_dir}")
    if not run_command(["git", "apply", "-p1", str(patch_file)], cwd=project_dir):
        logging.error("Failed to apply the patch.")
        return False

    logging.info(f"Running uv sync in {project_dir}")
    if not run_command(["uv", "sync"], cwd=project_dir):
        logging.error("Failed to run uv sync.")
        return False


def prepare_march_7th_assistant():
    """Clones, patches, and sets up the March7thAssistant project."""
    logging.info("Starting setup for March7thAssistant.")

    patch_file = Path(__file__).parent / "march-7th-assistant.patch"
    project_dir = Path(__file__).parent.parent / "March7thAssistant"
    project_url = "https://github.com/moesnow/March7thAssistant.git"
    project_commit = "cb278086562b77f5687e1233020e3b9178d7b957"

    prepare_common(patch_file, project_dir, project_url, project_commit)

    logging.info(f"Running python import_ocr.py in {project_dir}")
    python = project_dir / ".venv" / "Scripts" / "python.exe"
    if not run_command([str(python), "import_ocr.py"], cwd=project_dir):
        logging.error("Failed to run import_ocr.py.")
        return False

    logging.info("March7thAssistant setup complete.")
    return True


def prepare_auto_simulated_universe():
    """Clones, patches, and sets up the Auto_Simulated_Universe project."""
    logging.info("Starting setup for Auto_Simulated_Universe.")

    patch_file = Path(__file__).parent / "auto-simulated-universe.patch"
    project_dir = Path(__file__).parent.parent / "Auto_Simulated_Universe"
    project_url = "https://github.com/CHNZYX/Auto_Simulated_Universe.git"
    project_commit = "bf091321db2dd8c7063d66d88eaf8e2d4f1db066"

    prepare_common(patch_file, project_dir, project_url, project_commit)

    logging.info("Auto_Simulated_Universe setup complete.")
    return True


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL"),
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    VERBOSE = logging.getLogger().level in [logging.DEBUG, logging.INFO]

    if not prepare_march_7th_assistant():
        logging.error("March7thAssistant setup failed. Aborting.")
        sys.exit(1)

    if not prepare_auto_simulated_universe():
        logging.error("auto_simulated_universe setup failed. Aborting.")
        sys.exit(1)

    logging.info("All projects set up successfully.")
