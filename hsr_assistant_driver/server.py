import logging
import os
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, model_validator
from starlette.responses import JSONResponse

from hsr_assistant_driver.driver import (
    HSR_ASSISTANT_ARGS_JSON_SCHEMA,
    call_hsr_assistant,
)


app = FastAPI()


@app.get("/definition")
async def definition_endpoint():
    definition = {
        "name": "hsr_assistant",
        "description": "",
        "input_schema": HSR_ASSISTANT_ARGS_JSON_SCHEMA,
    }
    return JSONResponse({"data": definition})


class ActionArgument(BaseModel):
    action: Literal["run", "wait", "stop"]
    run_config: dict | None = None

    @model_validator(mode="after")
    def check_run_config_if_action_run(self):
        if self.action == "run" and self.run_config is None:
            raise ValueError("run_config is required when action is 'run'")
        return self


@app.post("/action")
async def run_endpoint(args: ActionArgument):
    try:
        result = await call_hsr_assistant(args.action, args.run_config)
        return JSONResponse({"data": result})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


def main():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL"),
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=10003)


if __name__ == "__main__":
    main()
