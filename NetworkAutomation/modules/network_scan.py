import socket
import subprocess
import platform
import ipaddress
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from app_runtime import hidden_subprocess_kwargs


# ==========================================================
# PING HOST
# ==========================================================

def ping_host(ip, timeout=1000, stop_event=None):
    """
    Ping một IP.

    timeout:
        milliseconds

    stop_event:
        Nếu được set trước khi ping thì bỏ qua.
    """

    if stop_event is not None and stop_event.is_set():
        return None

    system = platform.system().lower()

    if system == "windows":

        command = [
            "ping",
            "-n",
            "1",
            "-w",
            str(timeout),
            ip
        ]

    else:

        timeout_seconds = max(
            1,
            int(timeout / 1000)
        )

        command = [
            "ping",
            "-c",
            "1",
            "-W",
            str(timeout_seconds),
            ip
        ]

    try:

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            **hidden_subprocess_kwargs()
        )

        return result.returncode == 0

    except Exception as error:

        print(
            f"Ping error {ip}: {error}"
        )

        return False


# ==========================================================
# GET HOSTNAME
# ==========================================================

def get_hostname(ip):
    """
    Lấy hostname từ IP.
    """

    try:

        hostname = socket.gethostbyaddr(ip)[0]

        return hostname

    except Exception:

        return ""


# ==========================================================
# GET MAC
# ==========================================================

def get_mac_from_arp(ip):
    """
    Lấy MAC từ bảng ARP của Windows.
    """

    try:

        result = subprocess.run(
            ["arp", "-a", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="cp850",
            errors="ignore",
            **hidden_subprocess_kwargs()
        )

        output = result.stdout

        mac_pattern = (
            r"([0-9A-Fa-f]{2}"
            r"(?:-[0-9A-Fa-f]{2}){5})"
        )

        match = re.search(
            mac_pattern,
            output
        )

        if match:

            return match.group(1).upper()

        return ""

    except Exception as error:

        print(
            f"ARP error {ip}: {error}"
        )

        return ""


# ==========================================================
# SCAN HOST
# ==========================================================

def scan_host(
    ip,
    timeout=1000,
    stop_event=None,
    callback=None
):
    """
    Scan một host.

    callback event:

        {
            "event": "started",
            "ip": ip
        }

    Khi hoàn thành:

        {
            "event": "completed",
            "result": result
        }
    """

    if stop_event is not None and stop_event.is_set():

        return None

    # ------------------------------------------------------
    # START TIME
    # ------------------------------------------------------

    start_time = time.perf_counter()

    # ------------------------------------------------------
    # CALLBACK: HOST STARTED
    # ------------------------------------------------------

    if callback is not None:

        try:

            callback(
                {
                    "event": "started",
                    "ip": ip
                }
            )

        except Exception:
            pass

    print(
        f"Scanning: {ip}"
    )

    # ------------------------------------------------------
    # PING
    # ------------------------------------------------------

    online = ping_host(
        ip,
        timeout,
        stop_event
    )

    if online is None:

        return None

    # ------------------------------------------------------
    # ONLINE
    # ------------------------------------------------------

    if online:

        hostname = get_hostname(
            ip
        )

        mac = get_mac_from_arp(
            ip
        )

        status = "Online"

    # ------------------------------------------------------
    # OFFLINE
    # ------------------------------------------------------

    else:

        hostname = ""

        mac = ""

        status = "Offline"

    # ------------------------------------------------------
    # DURATION
    # ------------------------------------------------------

    duration = (
        time.perf_counter()
        - start_time
    )

    duration = round(
        duration,
        2
    )

    # ------------------------------------------------------
    # RESULT
    # ------------------------------------------------------

    result = {

        "time": datetime.now().strftime(
            "%H:%M:%S"
        ),

        "ip": ip,

        "hostname": hostname,

        "mac": mac,

        "status": status,

        "duration": duration
    }

    # ------------------------------------------------------
    # CALLBACK: COMPLETED
    # ------------------------------------------------------

    if callback is not None:

        try:

            callback(
                {
                    "event": "completed",
                    "result": result
                }
            )

        except Exception:
            pass

    return result


# ==========================================================
# SCAN NETWORK
# ==========================================================

def scan_network(
    network,
    max_workers=50,
    timeout=1000,
    stop_event=None,
    callback=None
):
    """
    Scan toàn bộ network.

    callback được gọi realtime:

        started
        completed

    Ví dụ:

        scan_network(
            "192.168.1.0/24",
            callback=my_callback
        )

    """

    print(
        f"Starting network scan: {network}"
    )

    # ------------------------------------------------------
    # VALIDATE NETWORK
    # ------------------------------------------------------

    try:

        net = ipaddress.ip_network(
            network,
            strict=False
        )

    except ValueError as error:

        raise ValueError(
            f"Network không hợp lệ: {network}"
        ) from error

    # ------------------------------------------------------
    # GET HOSTS
    # ------------------------------------------------------

    hosts = [
        str(ip)
        for ip in net.hosts()
    ]

    total_hosts = len(hosts)

    print(
        f"Total hosts: {total_hosts}"
    )

    # ------------------------------------------------------
    # CALLBACK TOTAL
    # ------------------------------------------------------

    if callback is not None:

        try:

            callback(
                {
                    "event": "total",
                    "total": total_hosts
                }
            )

        except Exception:
            pass

    results = []

    if not hosts:

        return results

    # ------------------------------------------------------
    # STOP EVENT
    # ------------------------------------------------------

    if stop_event is None:

        stop_event = threading.Event()

    # ------------------------------------------------------
    # EXECUTOR
    # ------------------------------------------------------

    executor = ThreadPoolExecutor(
        max_workers=max_workers
    )

    futures = {}

    try:

        # --------------------------------------------------
        # SUBMIT TASKS
        # --------------------------------------------------

        for ip in hosts:

            if stop_event.is_set():

                break

            future = executor.submit(
                scan_host,
                ip,
                timeout,
                stop_event,
                callback
            )

            futures[future] = ip

        # --------------------------------------------------
        # GET RESULTS REALTIME
        # --------------------------------------------------

        for future in as_completed(
            futures
        ):

            ip = futures[future]

            try:

                result = future.result()

                if result is not None:

                    results.append(
                        result
                    )

                    print(
                        f"{ip} -> "
                        f"{result['status']} "
                        f"({result['duration']}s)"
                    )

            except Exception as error:

                print(
                    f"Scan error {ip}: {error}"
                )

            # --------------------------------------------------
            # STOP
            # --------------------------------------------------

            if stop_event.is_set():

                for pending_future in futures:

                    if not pending_future.done():

                        pending_future.cancel()

                break

    finally:

        # --------------------------------------------------
        # CANCEL PENDING
        # --------------------------------------------------

        for future in futures:

            if not future.done():

                future.cancel()

        # --------------------------------------------------
        # SHUTDOWN
        # --------------------------------------------------

        executor.shutdown(
            wait=False,
            cancel_futures=True
        )

    # ------------------------------------------------------
    # SORT RESULTS
    # ------------------------------------------------------

    results.sort(
        key=lambda x:
        ipaddress.ip_address(
            x["ip"]
        )
    )

    # ------------------------------------------------------
    # FINISHED
    # ------------------------------------------------------

    if stop_event.is_set():

        print(
            "Network scan stopped."
        )

    else:

        print(
            "Network scan completed."
        )

    return results


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print(
        "=" * 60
    )

    print(
        "NETWORK SCAN TEST"
    )

    print(
        "=" * 60
    )

    network = input(
        "Nhập network, ví dụ "
        "192.168.1.0/24: "
    ).strip()

    stop_event = threading.Event()

    def test_callback(event):

        if event["event"] == "started":

            print(
                f"[START] "
                f"{event['ip']}"
            )

        elif event["event"] == "completed":

            result = event["result"]

            print(
                f"[DONE] "
                f"{result['ip']} -> "
                f"{result['status']} "
                f"{result['duration']}s"
            )

    try:

        results = scan_network(
            network,
            max_workers=50,
            timeout=1000,
            stop_event=stop_event,
            callback=test_callback
        )

        print()

        print(
            "=" * 60
        )

        print(
            "RESULT"
        )

        print(
            "=" * 60
        )

        for device in results:

            print(
                f"{device['time']:8} | "
                f"{device['ip']:15} | "
                f"{device['hostname']:25} | "
                f"{device['mac']:17} | "
                f"{device['status']:8} | "
                f"{device['duration']}s"
            )

        print()

        print(
            f"Total: "
            f"{len(results)} devices"
        )

    except Exception as error:

        print(
            f"ERROR: {error}"
        )