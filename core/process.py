import os
import sys
import threading
import queue
import time
import hashlib

# from winpty import PtyProcess

from database import update_file_status_by_filename


# ==========================================
# FOLDERS
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

LOG_FOLDER = os.path.join(
    BASE_DIR,
    "logs"
)


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    LOG_FOLDER,
    exist_ok=True
)


# ==========================================
# RUNNING PROCESSES
# ==========================================

# Keyed by absolute file path to isolate identical filenames from different users
RUNNING_PROCESSES = {}


# ==========================================
# OUTPUT QUEUES
# ==========================================

PROCESS_OUTPUTS = {}


# ==========================================
# INPUT QUEUES
# ==========================================

PROCESS_INPUTS = {}


# ==========================================
# LOCK
# ==========================================

PROCESS_LOCK = threading.Lock()


# ==========================================
# LOG PATH
# ==========================================

def _safe_log_name_from_path(filepath):
    # Create a short unique name using basename + sha256 of full path
    base = os.path.basename(filepath)
    h = hashlib.sha256(filepath.encode('utf-8')).hexdigest()[:8]
    name = f"{base}.{h}.log"
    return name


def get_log_path_for_path(filepath):
    filename = _safe_log_name_from_path(filepath)
    return os.path.join(LOG_FOLDER, filename)


# ==========================================
# RESOLVE FILE PATH
# ==========================================

def resolve_file_path(filename):
    if not filename:
        return None

    direct_path = os.path.abspath(
        os.path.join(
            UPLOAD_FOLDER,
            filename
        )
    )

    if os.path.exists(direct_path):
        return direct_path

    for root, _, files in os.walk(UPLOAD_FOLDER):
        if filename in files:
            return os.path.abspath(os.path.join(root, filename))

    return None


# ==========================================
# START PROCESS
# ==========================================

def start_process(filename, file_path=None, proxy=None):
    """
    filename: original filename (for logging);
    file_path: absolute path to the uploaded file (preferred)
    proxy: optional proxy string
    """
    with PROCESS_LOCK:
        # determine actual path
        filepath = file_path or resolve_file_path(filename)

        if filepath is None or not os.path.exists(filepath):
            return (False, "❌ File not found.")

        file_key = os.path.abspath(filepath)

        if file_key in RUNNING_PROCESSES:
            process = RUNNING_PROCESSES[file_key]["process"]
            try:
                if process.isalive():
                    return (False, "⚠️ This file is already running.")
            except Exception:
                pass

            cleanup_process(file_key)

        logpath = get_log_path_for_path(filepath)

        try:
            with open(logpath, "a", encoding="utf-8") as log:
                log.write("\n\n"
                          "========================================\n"
                          f"STARTING FILE: {filename}\n"
                          "========================================\n")

            # Temporarily set proxy env for this spawn if provided
            old_env = os.environ.copy()
            try:
                if proxy:
                    os.environ["HTTP_PROXY"] = proxy
                    os.environ["HTTPS_PROXY"] = proxy

                process = PtyProcess.spawn([
                    sys.executable,
                    "-u",
                    filepath
                ], cwd=os.path.dirname(filepath))
            finally:
                os.environ.clear()
                os.environ.update(old_env)

            PROCESS_OUTPUTS[file_key] = queue.Queue()
            PROCESS_INPUTS[file_key] = queue.Queue()

            RUNNING_PROCESSES[file_key] = {
                "process": process,
                "logpath": logpath,
                "last_output": "",
                "waiting_for_input": False,
                "filepath": filepath,
                "filename": filename,
                "proxy": proxy
            }

            output_thread = threading.Thread(
                target=read_process_output,
                args=(file_key, process, logpath),
                daemon=True
            )
            output_thread.start()

            input_thread = threading.Thread(
                target=write_process_input,
                args=(file_key, process),
                daemon=True
            )
            input_thread.start()

            update_file_status_by_filename(filename, "running")
            return (True, "✅ Process started successfully.")

        except Exception as e:
            return (False, f"❌ Error starting process:\n{e}")


# ==========================================
# READ PROCESS OUTPUT
# ==========================================

def read_process_output(file_key, process, logpath):
    try:
        while process.isalive():
            try:
                output = process.read(4096)
                if not output:
                    time.sleep(0.05)
                    continue

                with open(logpath, "a", encoding="utf-8", errors="replace") as log:
                    log.write(output)
                    log.flush()

                if file_key in PROCESS_OUTPUTS:
                    PROCESS_OUTPUTS[file_key].put(output)

                if file_key in RUNNING_PROCESSES:
                    RUNNING_PROCESSES[file_key]["last_output"] = output

            except Exception:
                break

    finally:
        if file_key in RUNNING_PROCESSES:
            RUNNING_PROCESSES[file_key]["waiting_for_input"] = False
        # mark status stopped by filename stored in record
        try:
            fn = RUNNING_PROCESSES[file_key].get("filename")
            update_file_status_by_filename(fn, "stopped")
        except Exception:
            pass


# ==========================================
# WRITE PROCESS INPUT
# ==========================================

def write_process_input(file_key, process):
    while True:
        try:
            if not process.isalive():
                break
        except Exception:
            break

        try:
            value = PROCESS_INPUTS[file_key].get(timeout=0.5)
        except queue.Empty:
            continue

        if value is None:
            break

        try:
            process.write(value + "\r")
        except Exception:
            break


# ==========================================
# SEND INPUT
# ==========================================

def send_input(identifier, value):
    """
    identifier: either absolute file path or filename (will attempt resolve)
    """
    # resolve to file_key
    file_key = None
    if identifier is None:
        return (False, "❌ Process is not running.")

    if os.path.isabs(str(identifier)) and os.path.exists(identifier):
        file_key = os.path.abspath(identifier)
    else:
        # try to resolve by filename
        path = resolve_file_path(identifier)
        if path:
            file_key = os.path.abspath(path)

    if file_key is None or file_key not in RUNNING_PROCESSES:
        return (False, "❌ Process is not running.")

    process = RUNNING_PROCESSES[file_key]["process"]
    try:
        if not process.isalive():
            cleanup_process(file_key)
            return (False, "❌ Process has already stopped.")
    except Exception:
        return (False, "❌ Could not check process status.")

    try:
        PROCESS_INPUTS[file_key].put(str(value))
        RUNNING_PROCESSES[file_key]["waiting_for_input"] = False
        return (True, "✅ Input sent.")
    except Exception as e:
        return (False, f"❌ Failed to send input:\n{e}")


# ==========================================
# GET OUTPUT
# ==========================================

def get_output(identifier):
    # resolve file_key
    file_key = None
    if os.path.isabs(str(identifier)) and os.path.exists(identifier):
        file_key = os.path.abspath(identifier)
    else:
        path = resolve_file_path(identifier)
        if path:
            file_key = os.path.abspath(path)

    if file_key is None or file_key not in PROCESS_OUTPUTS:
        return ""

    result = []
    try:
        while True:
            result.append(PROCESS_OUTPUTS[file_key].get_nowait())
    except queue.Empty:
        pass

    return "".join(result)


# ==========================================
# STOP PROCESS
# ==========================================

def stop_process(identifier):
    # resolve file_key
    file_key = None
    if os.path.isabs(str(identifier)) and os.path.exists(identifier):
        file_key = os.path.abspath(identifier)
    else:
        path = resolve_file_path(identifier)
        if path:
            file_key = os.path.abspath(path)

    if file_key is None or file_key not in RUNNING_PROCESSES:
        return (False, "⚠️ Process is not running.")

    process = RUNNING_PROCESSES[file_key]["process"]
    try:
        if process.isalive():
            process.terminate()
        cleanup_process(file_key)
        return (True, "⏹️ Process stopped successfully.")
    except Exception as e:
        return (False, f"❌ Error stopping process:\n{e}")


# ==========================================
# RESTART PROCESS
# ==========================================

def restart_process(identifier, proxy=None):
    # identifier can be path or filename
    # stop if running
    file_key = None
    if os.path.isabs(str(identifier)) and os.path.exists(identifier):
        file_path = os.path.abspath(identifier)
    else:
        file_path = resolve_file_path(identifier)

    if file_path and os.path.exists(file_path):
        # stop if exists
        fk = os.path.abspath(file_path)
        if fk in RUNNING_PROCESSES:
            stop_process(fk)
            time.sleep(0.5)
        return start_process(os.path.basename(file_path), file_path=file_path, proxy=proxy)

    return (False, "❌ File not found.")


# ==========================================
# CHECK RUNNING
# ==========================================

def is_running(identifier):
    file_key = None
    if os.path.isabs(str(identifier)) and os.path.exists(identifier):
        file_key = os.path.abspath(identifier)
    else:
        path = resolve_file_path(identifier)
        if path:
            file_key = os.path.abspath(path)

    if file_key is None or file_key not in RUNNING_PROCESSES:
        return False

    process = RUNNING_PROCESSES[file_key]["process"]
    try:
        if process.isalive():
            return True
    except Exception:
        pass

    cleanup_process(file_key)
    return False


# ==========================================
# GET PROCESS STATUS
# ==========================================

def get_process_status(identifier):
    if is_running(identifier):
        return "running"
    return "stopped"


# ==========================================
# WAITING FOR INPUT
# ==========================================

def is_waiting_for_input(identifier):
    file_key = None
    if os.path.isabs(str(identifier)) and os.path.exists(identifier):
        file_key = os.path.abspath(identifier)
    else:
        path = resolve_file_path(identifier)
        if path:
            file_key = os.path.abspath(path)

    if file_key is None or file_key not in RUNNING_PROCESSES:
        return False

    return RUNNING_PROCESSES[file_key].get("waiting_for_input", False)


# ==========================================
# GET LAST OUTPUT
# ==========================================

def get_last_output(identifier):
    file_key = None
    if os.path.isabs(str(identifier)) and os.path.exists(identifier):
        file_key = os.path.abspath(identifier)
    else:
        path = resolve_file_path(identifier)
        if path:
            file_key = os.path.abspath(path)

    if file_key is None or file_key not in RUNNING_PROCESSES:
        return ""

    return RUNNING_PROCESSES[file_key].get("last_output", "")


# ==========================================
# CLEANUP PROCESS
# ==========================================

def cleanup_process(file_key):
    try:
        if file_key in RUNNING_PROCESSES:
            try:
                process = RUNNING_PROCESSES[file_key]["process"]
                try:
                    if process.isalive():
                        process.terminate()
                except Exception:
                    pass
            except Exception:
                pass
            finally:
                try:
                    fn = RUNNING_PROCESSES[file_key].get("filename")
                    update_file_status_by_filename(fn, "stopped")
                except Exception:
                    pass
    except Exception:
        pass

    PROCESS_INPUTS.pop(file_key, None)
    PROCESS_OUTPUTS.pop(file_key, None)
    RUNNING_PROCESSES.pop(file_key, None)


# ==========================================
# GET LOGS
# ==========================================

def get_logs(identifier, max_chars=3500):
    # identifier can be file path or filename
    if os.path.isabs(str(identifier)) and os.path.exists(identifier):
        logpath = get_log_path_for_path(identifier)
    else:
        # try resolve path
        path = resolve_file_path(identifier)
        if path:
            logpath = get_log_path_for_path(path)
        else:
            # fallback to filename-based log
            logpath = os.path.join(LOG_FOLDER, f"{identifier}.log")

    if not os.path.exists(logpath):
        return ("📄 No logs available yet.")

    try:
        with open(logpath, "r", encoding="utf-8", errors="replace") as log:
            content = log.read()

        if not content.strip():
            return ("📄 Log file is empty.")

        if len(content) > max_chars:
            content = content[-max_chars:]
            content = ("… Showing latest logs …\n\n" + content)

        return content
    except Exception as e:
        return ("❌ Could not read logs:\n" + str(e))


# ==========================================
# CLEAR LOGS
# ==========================================

def clear_logs(identifier):
    if os.path.isabs(str(identifier)) and os.path.exists(identifier):
        logpath = get_log_path_for_path(identifier)
    else:
        path = resolve_file_path(identifier)
        if path:
            logpath = get_log_path_for_path(path)
        else:
            logpath = os.path.join(LOG_FOLDER, f"{identifier}.log")

    try:
        with open(logpath, "w", encoding="utf-8"):
            pass
        return True
    except Exception:
        return False


# ==========================================
# DELETE PROCESS / FILE
# ==========================================

def delete_process(identifier):
    # stop if running and delete uploaded file and log
    # identifier can be file path or filename
    if os.path.isabs(str(identifier)) and os.path.exists(identifier):
        filepath = os.path.abspath(identifier)
    else:
        filepath = resolve_file_path(identifier)

    if filepath is None:
        return (False, "❌ File not found.")

    file_key = os.path.abspath(filepath)

    if file_key in RUNNING_PROCESSES:
        stop_process(file_key)

    deleted_file = False
    deleted_log = False

    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            deleted_file = True
    except Exception as e:
        return (False, f"❌ Could not delete file:\n{e}")

    try:
        logpath = get_log_path_for_path(filepath)
        if os.path.exists(logpath):
            os.remove(logpath)
            deleted_log = True
    except Exception:
        pass

    if deleted_file:
        return (True, "🗑️ File deleted successfully.")
    return (False, "❌ File not found.")


# ==========================================
# FILE EXISTS
# ==========================================

def file_exists(filename_or_path):
    if os.path.isabs(str(filename_or_path)) and os.path.exists(filename_or_path):
        return True
    filepath = os.path.join(UPLOAD_FOLDER, filename_or_path)
    return os.path.exists(filepath)
