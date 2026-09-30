import subprocess
import platform
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


# ==========================================================
# PING ONE HOST
# ==========================================================

def ping_host(ip, timeout=1000):

    ip = ip.strip()

    if not ip:

        return {
            "time": datetime.now().strftime("%H:%M:%S"),
            "ip": ip,
            "status": "Error",
            "response": None
        }

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

    start_time = time.perf_counter()

    try:

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        elapsed = (
            time.perf_counter() - start_time
        ) * 1000

        # ==================================================
        # ONLINE
        # ==================================================

        if result.returncode == 0:

            output = result.stdout

            # Windows:
            # time=1ms
            # time<1ms
            # time=10ms

            match = re.search(
                r"time[=<]\s*(\d+(?:\.\d+)?)\s*ms",
                output,
                re.IGNORECASE
            )

            if match:

                response_time = float(
                    match.group(1)
                )

                if response_time.is_integer():

                    response_time = int(
                        response_time
                    )

            else:

                response_time = round(
                    elapsed,
                    2
                )

            return {
                "time": datetime.now().strftime(
                    "%H:%M:%S"
                ),
                "ip": ip,
                "status": "Online",
                "response": response_time
            }

        # ==================================================
        # OFFLINE
        # ==================================================

        return {
            "time": datetime.now().strftime(
                "%H:%M:%S"
            ),
            "ip": ip,
            "status": "Offline",
            "response": None
        }

    except Exception as error:

        return {
            "time": datetime.now().strftime(
                "%H:%M:%S"
            ),
            "ip": ip,
            "status": "Error",
            "response": None,
            "error": str(error)
        }


# ==========================================================
# PING MULTIPLE HOSTS
# ==========================================================

def ping_multiple(
    ips,
    max_workers=50,
    timeout=1000
):

    results = []

    if not ips:

        return results

    workers = min(
        max_workers,
        len(ips)
    )

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        futures = {
            executor.submit(
                ping_host,
                ip,
                timeout
            ): ip
            for ip in ips
        }

        for future in as_completed(futures):

            ip = futures[future]

            try:

                result = future.result()

                results.append(
                    result
                )

            except Exception as error:

                results.append(
                    {
                        "time": datetime.now().strftime(
                            "%H:%M:%S"
                        ),
                        "ip": ip,
                        "status": "Error",
                        "response": None,
                        "error": str(error)
                    }
                )

    # ======================================================
    # GIỮ NGUYÊN THỨ TỰ IP NGƯỜI DÙNG NHẬP
    # ======================================================

    order = {
        ip: index
        for index, ip in enumerate(ips)
    }

    results.sort(
        key=lambda item: order.get(
            item["ip"],
            999999
        )
    )

    return results


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("PING TEST")
    print("=" * 60)

    ips = [
        "192.168.1.1",
        "192.168.1.10",
        "192.168.1.20"
    ]

    results = ping_multiple(
        ips,
        max_workers=50,
        timeout=1000
    )

    for result in results:

        print(
            f"{result['time']} | "
            f"{result['ip']:15} | "
            f"{result['status']:8} | "
            f"{result['response']}"
        )