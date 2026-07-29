import os
import sys
import threading
import queue
import time

from winpty import PtyProcess

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

def get_log_path(filename):

    return os.path.join(
        LOG_FOLDER,
        filename + ".log"
    )


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
            return os.path.abspath(
                os.path.join(
                    root,
                    filename
                )
            )

    return None


# ==========================================
# START PROCESS
# ==========================================

def start_process(filename, file_path=None):

    with PROCESS_LOCK:

        if filename in RUNNING_PROCESSES:

            process = RUNNING_PROCESSES[
                filename
            ]["process"]

            try:

                if process.isalive():

                    return (
                        False,
                        "⚠️ This file is already running."
                    )

            except Exception:

                pass


            cleanup_process(
                filename
            )


    filepath = file_path or resolve_file_path(filename)


    if filepath is None or not os.path.exists(filepath):

        return (
            False,
            "❌ File not found."
        )


    logpath = get_log_path(
        filename
    )


    try:

        with open(

            logpath,

            "a",

            encoding="utf-8"

        ) as log:

            log.write(

                "\n\n"
                "========================================\n"
                f"STARTING FILE: {filename}\n"
                "========================================\n"

            )


        process = PtyProcess.spawn(

            [

                sys.executable,

                "-u",

                filepath

            ],

            cwd=os.path.dirname(

                filepath

            )

        )


        PROCESS_OUTPUTS[
            filename
        ] = queue.Queue()


        PROCESS_INPUTS[
            filename
        ] = queue.Queue()


        RUNNING_PROCESSES[
            filename
        ] = {

            "process": process,

            "logpath": logpath,

            "last_output": "",

            "waiting_for_input": False

        }


        output_thread = threading.Thread(

            target=read_process_output,

            args=(

                filename,

                process,

                logpath

            ),

            daemon=True

        )


        output_thread.start()


        input_thread = threading.Thread(

            target=write_process_input,

            args=(

                filename,

                process

            ),

            daemon=True

        )


        input_thread.start()

        update_file_status_by_filename(
            filename,
            "running"
        )

        return (

            True,

            "✅ Process started successfully."

        )


    except Exception as e:

        return (

            False,

            f"❌ Error starting process:\n{e}"

        )


# ==========================================
# READ PROCESS OUTPUT
# ==========================================

def read_process_output(

    filename,

    process,

    logpath

):

    try:

        while process.isalive():

            try:

                output = process.read(

                    4096

                )


                if not output:

                    time.sleep(

                        0.05

                    )

                    continue


                with open(

                    logpath,

                    "a",

                    encoding="utf-8",

                    errors="replace"

                ) as log:

                    log.write(

                        output

                    )

                    log.flush()


                if filename in PROCESS_OUTPUTS:

                    PROCESS_OUTPUTS[
                        filename
                    ].put(

                        output

                    )


                if filename in RUNNING_PROCESSES:

                    RUNNING_PROCESSES[
                        filename
                    ][

                        "last_output"

                    ] = output


            except Exception:

                break


    finally:

        if filename in RUNNING_PROCESSES:

            RUNNING_PROCESSES[
                filename
            ][

                "waiting_for_input"

            ] = False

        update_file_status_by_filename(
            filename,
            "stopped"
        )


# ==========================================
# WRITE PROCESS INPUT
# ==========================================

def write_process_input(

    filename,

    process

):

    while True:

        try:

            if not process.isalive():

                break

        except Exception:

            break


        try:

            value = PROCESS_INPUTS[

                filename

            ].get(

                timeout=0.5

            )


        except queue.Empty:

            continue


        if value is None:

            break


        try:

            process.write(

                value + "\r"

            )


        except Exception:

            break


# ==========================================
# SEND INPUT
# ==========================================

def send_input(

    filename,

    value

):

    if filename not in RUNNING_PROCESSES:

        return (

            False,

            "❌ Process is not running."

        )


    process = RUNNING_PROCESSES[

        filename

    ]["process"]


    try:

        if not process.isalive():

            cleanup_process(

                filename

            )

            return (

                False,

                "❌ Process has already stopped."

            )


    except Exception:

        return (

            False,

            "❌ Could not check process status."

        )


    try:

        PROCESS_INPUTS[

            filename

        ].put(

            str(value)

        )


        RUNNING_PROCESSES[

            filename

        ][

            "waiting_for_input"

        ] = False


        return (

            True,

            "✅ Input sent."

        )


    except Exception as e:

        return (

            False,

            f"❌ Failed to send input:\n{e}"

        )


# ==========================================
# GET OUTPUT
# ==========================================

def get_output(

    filename

):

    if filename not in PROCESS_OUTPUTS:

        return ""


    result = []


    try:

        while True:

            result.append(

                PROCESS_OUTPUTS[

                    filename

                ].get_nowait()

            )


    except queue.Empty:

        pass


    return "".join(

        result

    )


# ==========================================
# STOP PROCESS
# ==========================================

def stop_process(

    filename

):

    if filename not in RUNNING_PROCESSES:

        return (

            False,

            "⚠️ Process is not running."

        )


    process = RUNNING_PROCESSES[

        filename

    ]["process"]


    try:

        if process.isalive():

            process.terminate()


        cleanup_process(

            filename

        )


        return (

            True,

            "⏹️ Process stopped successfully."

        )


    except Exception as e:

        return (

            False,

            f"❌ Error stopping process:\n{e}"

        )


# ==========================================
# RESTART PROCESS
# ==========================================

def restart_process(

    filename

):

    if filename in RUNNING_PROCESSES:

        stop_process(

            filename

        )


        time.sleep(

            0.5

        )


    return start_process(

        filename

    )


# ==========================================
# CHECK RUNNING
# ==========================================

def is_running(

    filename

):

    if filename not in RUNNING_PROCESSES:

        return False


    process = RUNNING_PROCESSES[

        filename

    ]["process"]


    try:

        if process.isalive():

            return True

    except Exception:

        pass


    cleanup_process(

        filename

    )


    return False


# ==========================================
# GET PROCESS STATUS
# ==========================================

def get_process_status(

    filename

):

    """

    Returns:

    running
    stopped
    crashed

    """


    if filename not in RUNNING_PROCESSES:

        return "stopped"


    process = RUNNING_PROCESSES[

        filename

    ]["process"]


    try:

        if process.isalive():

            return "running"

    except Exception:

        pass


    cleanup_process(

        filename

    )


    return "stopped"


# ==========================================
# WAITING FOR INPUT
# ==========================================

def is_waiting_for_input(

    filename

):

    if filename not in RUNNING_PROCESSES:

        return False


    return RUNNING_PROCESSES[

        filename

    ].get(

        "waiting_for_input",

        False

    )


# ==========================================
# GET LAST OUTPUT
# ==========================================

def get_last_output(

    filename

):

    if filename not in RUNNING_PROCESSES:

        return ""


    return RUNNING_PROCESSES[

        filename

    ].get(

        "last_output",

        ""

    )


# ==========================================
# CLEANUP PROCESS
# ==========================================

def cleanup_process(

    filename

):

    if filename in RUNNING_PROCESSES:

        try:

            process = RUNNING_PROCESSES[

                filename

            ]["process"]


            try:

                if process.isalive():

                    process.terminate()

            except Exception:

                pass

        except Exception:

            pass

        finally:

            update_file_status_by_filename(
                filename,
                "stopped"
            )

    PROCESS_INPUTS.pop(

        filename,

        None

    )


    PROCESS_OUTPUTS.pop(

        filename,

        None

    )


# ==========================================
# GET LOGS
# ==========================================

def get_logs(

    filename,

    max_chars=3500

):

    logpath = get_log_path(

        filename

    )


    if not os.path.exists(

        logpath

    ):

        return (

            "📄 No logs available yet."

        )


    try:

        with open(

            logpath,

            "r",

            encoding="utf-8",

            errors="replace"

        ) as log:

            content = log.read()


        if not content.strip():

            return (

                "📄 Log file is empty."

            )


        if len(content) > max_chars:

            content = content[

                -max_chars:

            ]


            content = (

                "… Showing latest logs …\n\n"

                + content

            )


        return content


    except Exception as e:

        return (

            "❌ Could not read logs:\n"

            + str(e)

        )


# ==========================================
# CLEAR LOGS
# ==========================================

def clear_logs(

    filename

):

    logpath = get_log_path(

        filename

    )


    try:

        with open(

            logpath,

            "w",

            encoding="utf-8"

        ):

            pass


        return True


    except Exception:

        return False


# ==========================================
# DELETE PROCESS / FILE
# ==========================================

def delete_process(

    filename

):

    """

    Stops the process if running

    and deletes the uploaded file.

    The log file is also removed.

    """


    if filename in RUNNING_PROCESSES:

        stop_process(

            filename

        )


    filepath = os.path.join(

        UPLOAD_FOLDER,

        filename

    )


    logpath = get_log_path(

        filename

    )


    deleted_file = False

    deleted_log = False


    try:

        if os.path.exists(

            filepath

        ):

            os.remove(

                filepath

            )

            deleted_file = True


    except Exception as e:

        return (

            False,

            f"❌ Could not delete file:\n{e}"

        )


    try:

        if os.path.exists(

            logpath

        ):

            os.remove(

                logpath

            )

            deleted_log = True


    except Exception:

        pass


    if deleted_file:

        return (

            True,

            "🗑️ File deleted successfully."

        )


    return (

        False,

        "❌ File not found."

    )


# ==========================================
# FILE EXISTS
# ==========================================

def file_exists(

    filename

):

    filepath = os.path.join(

        UPLOAD_FOLDER,

        filename

    )


    return os.path.exists(

        filepath

    )