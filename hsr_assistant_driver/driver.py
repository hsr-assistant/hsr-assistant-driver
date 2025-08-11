import asyncio
import codecs
import logging
import jsonschema
import os
import psutil
import sys
import traceback
from typing import Literal

from hsr_assistant_driver.march_7th_assistant import (
    prepare_to_run as prepare_march_7th_assistant,
)


RUN_CONFIG_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "task": {"type": "string", "enum": ["material", "universe", "claim_reward"]},
        "material_config": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": [
                        "饰品提取",
                        "拟造花萼（金）",
                        "拟造花萼（赤）",
                        "凝滞虚影",
                        "侵蚀隧洞",
                        "历战余响",
                    ],
                },
                "id": {"type": "string"},
            },
            "required": ["category", "id"],
            "allOf": [
                {
                    "if": {"properties": {"category": {"const": "饰品提取"}}},
                    "then": {
                        "properties": {
                            "id": {
                                "enum": [
                                    "月下朱殷",
                                    "纷争不休",
                                    "蠹役饥肠",
                                    "永恒笑剧",
                                    "伴你入眠",
                                    "天剑如雨",
                                    "孽果盘生",
                                    "百年冻土",
                                    "温柔话语",
                                    "浴火钢心",
                                    "坚城不倒",
                                ]
                            }
                        }
                    },
                },
                {
                    "if": {"properties": {"category": {"const": "拟造花萼（金）"}}},
                    "then": {
                        "properties": {
                            "id": {"enum": ["回忆之蕾", "以太之蕾", "珍藏之蕾"]}
                        }
                    },
                },
                {
                    "if": {"properties": {"category": {"const": "拟造花萼（赤）"}}},
                    "then": {
                        "properties": {
                            "id": {
                                "enum": [
                                    "鳞渊境",
                                    "收容舱段",
                                    "克劳克影视乐园",
                                    "支援舱段",
                                    "苏乐达™热砂海选会场",
                                    "城郊雪原",
                                    "绥园",
                                    "边缘通路",
                                    "匹诺康尼大剧院",
                                    "铆钉镇",
                                    "「白日梦」酒店-梦镜",
                                    "机械聚落",
                                    "丹鼎司",
                                    "大矿区",
                                    "「纷争荒墟」悬锋城",
                                ]
                            }
                        }
                    },
                },
                {
                    "if": {"properties": {"category": {"const": "凝滞虚影"}}},
                    "then": {
                        "properties": {
                            "id": {
                                "enum": [
                                    "空海之形",
                                    "巽风之形",
                                    "鸣雷之形",
                                    "炎华之形",
                                    "锋芒之形",
                                    "霜晶之形",
                                    "幻光之形",
                                    "冰棱之形",
                                    "震厄之形",
                                    "偃偶之形",
                                    "孽兽之形",
                                    "天人之形",
                                    "幽府之形",
                                    "燔灼之形",
                                    "冰酿之形",
                                    "焦炙之形",
                                    "嗔怒之形",
                                    "职司之形",
                                    "机狼之形",
                                    "今宵之形",
                                    "弦音之形",
                                    "凛月之形",
                                    "役轮之形",
                                    "溟簇之形",
                                    "烬日之形",
                                ]
                            }
                        }
                    },
                },
                {
                    "if": {"properties": {"category": {"const": "侵蚀隧洞"}}},
                    "then": {
                        "properties": {
                            "id": {
                                "enum": [
                                    "霜风之径",
                                    "迅拳之径",
                                    "漂泊之径",
                                    "睿治之径",
                                    "圣颂之径",
                                    "野焰之径",
                                    "药使之径",
                                    "幽冥之径",
                                    "梦潜之径",
                                    "勇骑之径",
                                    "迷识之径",
                                    "弦歌之径",
                                    "雳涌之径",
                                ]
                            }
                        }
                    },
                },
                {
                    "if": {"properties": {"category": {"const": "历战余响"}}},
                    "then": {
                        "properties": {
                            "id": {
                                "enum": [
                                    "晨昏的回眸",
                                    "心兽的战场",
                                    "尘梦的赞礼",
                                    "蛀星的旧靥",
                                    "不死的神实",
                                    "寒潮的落幕",
                                    "毁灭的开端",
                                ]
                            }
                        }
                    },
                },
            ],
        },
        "universe_config": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["模拟宇宙", "差分宇宙"]},
                "difficulty": {"type": "integer", "minimum": 0, "maximum": 5},
            },
            "required": ["type"],
        },
        "claim_reward_config": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["每日实训"]},
            },
            "required": ["type"],
        },
    },
    "required": ["task"],
    "allOf": [
        {
            "if": {"properties": {"task": {"const": "material"}}},
            "then": {"required": ["material_config"]},
        },
        {
            "if": {"properties": {"task": {"const": "universe"}}},
            "then": {"required": ["universe_config"]},
        },
        {
            "if": {"properties": {"task": {"const": "claim_reward"}}},
            "then": {"required": ["claim_reward_config"]},
        },
    ],
}


class AssistantDriver:
    def __init__(self):
        self.timeout_no_output = 900
        self.timeout = 120

        self.assistant_task: asyncio.Task | None = None
        self._assistant_task_lock = asyncio.Lock()

        self.logs: list[str] = []
        self.partial_line: str = ""

    def _format_logs(self, head: str) -> str:
        log_content = self.logs + [self.partial_line.strip()]
        if len(log_content) > 100:
            log_content = (
                log_content[:50] + ["... lines trimmed ..."] + log_content[-50:]
            )
        return "\n".join([head, *log_content])

    async def run(self, run_config: dict) -> str:
        logging.info("Received run request with config:\n%s", run_config)
        async with self._assistant_task_lock:
            if self.assistant_task is not None:
                return "Error: An assistant process is already running. Use 'wait' or 'stop'."
            self.assistant_task = asyncio.create_task(
                self._execute_monitor_process(run_config)
            )
            task = self.assistant_task

        try:
            return await asyncio.wait_for(asyncio.shield(task), timeout=self.timeout)
        except asyncio.TimeoutError:
            return self._format_logs(
                "Assistant running in background.\nCurrent logs:\n"
            )
        except asyncio.CancelledError:
            return "Assistant has been unexpectedly stopped."
        except Exception as e:
            return f"An unexpected error occurred: {e}\n{traceback.format_exc()}"

    async def wait(self) -> str:
        logging.info("Received wait request.")
        async with self._assistant_task_lock:
            if self.assistant_task is None:
                return self._format_logs(
                    "No running assistant to wait for.\nPrevious logs:\n"
                )
            task = self.assistant_task

        try:
            return await asyncio.wait_for(asyncio.shield(task), timeout=self.timeout)
        except asyncio.TimeoutError:
            return self._format_logs("Assistant is still running.\nCurrent logs:\n")
        except asyncio.CancelledError:
            return "Assistant has been unexpectedly stopped."
        except Exception as e:
            return f"An unexpected error occurred: {e}\n{traceback.format_exc()}"

    async def stop(self) -> str:
        logging.info("Received stop request.")
        async with self._assistant_task_lock:
            if self.assistant_task is None:
                return self._format_logs(
                    "No running assistant to stop.\nPrevious logs:\n"
                )

            try:
                self.assistant_task.cancel()
                try:
                    return await self.assistant_task
                except asyncio.CancelledError:
                    pass
                self.assistant_task = None
                return "Process has been stopped."
            except Exception as e:
                return f"An unexpected error occurred: {e}\n{traceback.format_exc()}"

    async def _execute_monitor_process(self, run_config: dict) -> str:
        try:
            jsonschema.validate(run_config, RUN_CONFIG_JSON_SCHEMA)
        except jsonschema.ValidationError as e:
            async with self._assistant_task_lock:
                self.assistant_task = None
            return "Invalid run config:\n" + str(e)

        args, kwargs = prepare_march_7th_assistant(run_config)

        logging.info("Starting assistant with:\nArgs: %s\nKwArgs: %s", args, kwargs)
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.PIPE,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                **kwargs,
            )
        except Exception:
            msg = f"Failed to start assistant process, traceback:\n{e}"
            logging.error(msg)
            async with self._assistant_task_lock:
                self.assistant_task = None
            return msg
        logging.info("Assistant process %s", process)

        output_queue: asyncio.Queue[str] = asyncio.Queue()
        reader_task = asyncio.create_task(
            self._read_char_stream(process.stdout, output_queue)
        )
        monitoring_task = asyncio.create_task(
            self._monitor_process(process, output_queue)
        )

        self.logs = []
        self.partial_line = ""
        was_cancelled = False
        try:
            monitoring_result = await monitoring_task
            logging.info("Monitoring task finished with result:\n%s", monitoring_result)
            return monitoring_result
        except asyncio.CancelledError:
            was_cancelled = True
            raise
        finally:
            if process.returncode is None:
                await self._terminate_process_tree(process)
            else:
                logging.info(
                    "Process already exited with code %s. (%s)",
                    process.returncode,
                    process,
                )

            logging.info("Cancelling reader and monitoring tasks.")
            reader_task.cancel()
            monitoring_task.cancel()
            await asyncio.gather(reader_task, monitoring_task, return_exceptions=True)
            logging.info("Reader and monitoring tasks cancelled.")

            if not was_cancelled:
                async with self._assistant_task_lock:
                    self.assistant_task = None

    async def _monitor_process(
        self, process: asyncio.subprocess.Process, output_queue: asyncio.Queue[str]
    ) -> str:
        quit_reasons: list[str] = []

        while True:  # We do not care about the process terminates or not. We just drain the output.
            try:
                char = await asyncio.wait_for(
                    output_queue.get(), self.timeout_no_output
                )
            except asyncio.TimeoutError:
                logging.info(
                    "No output for %s seconds. Stopping monitoring. (%s)",
                    self.timeout_no_output,
                    process,
                )
                quit_reasons.append(
                    f"[Timeout] No output for {self.timeout_no_output} seconds."
                )
                break

            if not char:  # EOF
                logging.info("EOF reached. Stopping monitoring. (%s)", process)
                break

            self.partial_line += char
            if char == "\n":
                line = self.partial_line.strip()
                self.logs.append(line)
                self.partial_line = ""

                # We want the full "ERROR" line so we detect it here.
                # "ERROR"s in simul.py is retrying, not real error.
                if "ERROR" in line and "simul.py:" not in line:
                    logging.info(
                        "Error log detected. Stopping monitoring. (%s)", process
                    )
                    quit_reasons.append("[Error] Error log detected.")
                    break  # Stop monitoring.

            if self.partial_line.endswith("按回车键关闭窗口. . ."):
                process.stdin.write(b"\n")
                await process.stdin.drain()
                self.logs.append(self.partial_line.strip())
                self.partial_line = ""

        try:
            return_code = await asyncio.wait_for(process.wait(), timeout=1.0)
            quit_reasons.append(f"[Exit] Assistant exited with code {return_code}.")
        except asyncio.TimeoutError:
            pass

        self.logs.append(self.partial_line.strip())
        self.partial_line = ""
        self.logs.extend(["**Quit reason(s):**", *quit_reasons])

        return self._format_logs("Logs:\n")

    async def _read_char_stream(
        self, stream: asyncio.StreamReader, queue: asyncio.Queue
    ) -> None:
        decoder = codecs.getincrementaldecoder("utf-8")()
        try:
            while byte_chunk := await stream.read(1):
                try:
                    if char := decoder.decode(byte_chunk):
                        await queue.put(char)
                        print(char, end="", file=sys.stderr, flush=True)
                except UnicodeDecodeError:
                    print(f"\nIncomplete byte sequence: {byte_chunk!r}")
        finally:
            await queue.put("")

    async def _terminate_process_tree(
        self, process: asyncio.subprocess.Process
    ) -> None:
        logging.info("Terminating process tree for %s", process)
        try:
            ps_process = psutil.Process(process.pid)
            children = ps_process.children(recursive=True)
            logging.info("Children of %s: %s", process, children)

            process.terminate()
            logging.info("Terminating process %s", process)

            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
                logging.info(
                    "Process terminated gracefully in 5 seconds. (%s)", process
                )
            except asyncio.TimeoutError:
                logging.info(
                    "Process did not terminate gracefully, killing it. (%s)", process
                )
                try:
                    ps_process.kill()
                except psutil.NoSuchProcess:
                    logging.warning("Process %s no longer exists.", process)

                logging.info("Waiting for process to terminate ... (%s)", process)
                await process.wait()

                for child in children:
                    logging.info("Killing child process %s. (%s)", child, process)
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass
                logging.info("Process and its subprocesses terminated. (%s)", process)
        except Exception as e:
            logging.error("Error terminating process tree %s: %s", process, e)


_driver_instance = AssistantDriver()


HSR_ASSISTANT_ARGS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["run", "wait", "stop"]},
        "run_config": RUN_CONFIG_JSON_SCHEMA,
    },
    "required": ["action"],
    "if": {"properties": {"action": {"const": "run"}}},
    "then": {"required": ["run_config"]},
}


async def call_hsr_assistant(
    action: Literal["run", "wait", "stop"], run_config: dict | None
) -> str:
    global _driver_instance
    if action == "run":
        assert run_config is not None
        return await _driver_instance.run(run_config)
    elif action == "wait":
        return await _driver_instance.wait()
    elif action == "stop":
        return await _driver_instance.stop()
    return "NotImplemented action: " + action
