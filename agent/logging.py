import json
import time

from datetime import datetime
from pathlib import Path

# Prepare log ID and directory
run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
logs_dir = Path(__file__).with_name("logs")
logs_dir.mkdir(exist_ok=True)
log_path = logs_dir / f"{run_id}.jsonl"


def log_event(event: str, model: str, started_at: float | int,tool: str,args: dict) -> None:
    """
    Write a log record to the log file of the current run

    :param event: Type of event ("user_task", "tool_call", "tool_result", "final")
    :param model: The model being used for the tool call
    :param started_at: Timestamp from when the event started
    :param tool: Name of the tool or function being called
    :param args: Arguments passed to the tool or function
    """

    record = {
        "ts": datetime.now().astimezone().isoformat(),
        "run_id": run_id,
        "event": event,
        "tool": tool,
        "args": args,
        "ok": True,
        "model": model,
        "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
    }

    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_error(started_at: float | int, model: str, tool: str,args: dict, error: Exception) -> None:
    """
    Write a log record to the log file of the current run

    :param model: The model being used for the tool call
    :param started_at: Timestamp from when the event started
    :param tool: Name of the tool or function being called
    :param args: Arguments passed to the tool or function
    :param error: Error message
    """

    record = {
        "ts": datetime.now().astimezone().isoformat(),
        "run_id": run_id,
        "event": "error",
        "tool": tool,
        "args": args,
        "ok": False,
        "model": model,
        "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
        "error": str(error),
    }

    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")