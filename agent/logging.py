import json
import time

from datetime import datetime
from pathlib import Path

# Prepare log ID and directory
run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
logs_dir = Path(__file__).with_name("logs")
logs_dir.mkdir(exist_ok=True)
log_path = logs_dir / f"{run_id}.jsonl"


def log_event(event: str, model: str, started_at: float | int,tool: str,args: dict, condition: str) -> None:
    """
    Calls write_log to log an event to the log file of the current run
    :param event: Type of event ("user_task", "tool_call", "tool_result", "final")
    :param model: The model being used for the tool call
    :param started_at: Timestamp from when the event started
    :param tool: Name of the tool or function being called
    :param condition: The condition under which the tool is being called ("preview" or "direct")
    :param args: Arguments passed to the tool or function
    """
    write_log(event, tool, args, True, model, started_at, condition)


def log_error(started_at: float | int, model: str, tool: str,args: dict, error: Exception, condition: str) -> None:
    """
    Call write_log to log an error event to the log file of the current ru
    :param model: The model being used for the tool call
    :param started_at: Timestamp from when the event started
    :param tool: Name of the tool or function being called
    :param args: Arguments passed to the tool or function
    :param error: Error message
    :param condition: The condition under which the tool is being called ("preview" or "direct")
    """
    write_log("error", tool, args, False, model, started_at, str(error), condition)

def write_log(event: str, tool: str, args: dict, ok: bool, model: str, started_at: float | int, condition: str, error: str = None) -> None:
    """
    Writes a log entry to the log file of the current run
    :param event: Type of occurred event (user_task, tool_call, tool_result, error, final)
    :param tool: Which tool or function was called; for user_task and final events, this is "agent"
    :param args: Arguments passed to the tool or function; for user_task and final events, this is the prompt
    :param ok: Whether the tool call was successful or not
    :param model: The model being used for the tool call
    :param started_at: When the event started, used to calculate its run duration
    :param error: Error message if the tool call failed
    """
    record = {
        "ts": datetime.now().astimezone().isoformat(),
        "run_id": run_id,
        "event": event,
        "tool": tool,
        "args": args,
        "ok": ok,
        "model": model,
        "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
        "error": error,
        "condition": condition,
    }

    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")