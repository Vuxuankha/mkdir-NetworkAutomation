import socket
import subprocess
import platform
import ipaddress
import re
import time
import threading
import math
import queue
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
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
            math.ceil(timeout / 1000)
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
            timeout=max(1, timeout / 1000) + 2,
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

_dns_slots = threading.BoundedSemaphore(16)


def get_hostname(ip, timeout=1.0, stop_event=None):
    """Bound caller wait and resolver concurrency, even if OS DNS hangs."""
    if stop_event is not None and stop_event.is_set():
        return ''
    if not _dns_slots.acquire(blocking=False):
        return ''
    result = queue.Queue(maxsize=1)
    def resolve():
        try:
            try:
                name = socket.gethostbyaddr(ip)[0]
            except Exception:
                name = ''
            result.put_nowait(name)
        finally:
            _dns_slots.release()
    thread = threading.Thread(target=resolve, daemon=True)
    try:
        thread.start()
    except Exception:
        _dns_slots.release()
        raise
    deadline = time.monotonic() + timeout
    while stop_event is None or not stop_event.is_set():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return ''
        try:
            return result.get(timeout=min(.05, remaining))
        except queue.Empty:
            pass
    return ''


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
            timeout=3,
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
    callback=None,
    resolve_hostnames=True,
    dns_timeout=1.0
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

        hostname = get_hostname(ip, dns_timeout, stop_event) if resolve_hostnames else ""

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

    if stop_event is not None and stop_event.is_set():
        return None

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
    callback=None,
    resolve_hostnames=True,
    dns_timeout=1.0
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

    if not isinstance(max_workers, int) or not 1 <= max_workers <= 256:
        raise ValueError('Số luồng phải từ 1 đến 256.')
    if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Timeout phải là số dương hữu hạn (ms).')
    if not isinstance(dns_timeout, (int, float)) or not math.isfinite(dns_timeout) or dns_timeout <= 0:
        raise ValueError('DNS timeout phải là số dương hữu hạn (giây).')
    total_hosts = net.num_addresses
    if net.version == 4 and net.prefixlen < 31:
        total_hosts -= 2
    elif net.version == 6 and net.prefixlen < 127:
        total_hosts -= 1
    if callback is not None:
        try:
            callback({'event': 'total', 'total': total_hosts})
        except Exception:
            pass
    stop_event = stop_event if stop_event is not None else threading.Event()
    results = []
    if stop_event.is_set():
        return results
    hosts = iter(net.hosts())
    executor = ThreadPoolExecutor(max_workers=max_workers)
    futures = {}
    exhausted = False
    try:
        while not stop_event.is_set():
            # Keep only a small window of tasks; never materialize the subnet.
            while not exhausted and len(futures) < max_workers * 2 and not stop_event.is_set():
                ip = next(hosts, None)
                if ip is None:
                    exhausted = True
                    break
                future = executor.submit(scan_host, str(ip), timeout, stop_event, callback, resolve_hostnames, dns_timeout)
                futures[future] = str(ip)
            if not futures:
                break
            done, _ = wait(futures, timeout=.1, return_when=FIRST_COMPLETED)
            for future in done:
                ip = futures.pop(future)
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as error:
                    print(f'Scan error {ip}: {error}')
    finally:
        for future in futures:
            future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)

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