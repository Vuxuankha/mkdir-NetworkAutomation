"""Run active unit tests and regression using disposable data."""
import os
import importlib
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    missing = []
    for name in ('pandas', 'openpyxl', 'paramiko', 'cryptography', 'pysnmp', 'tkinter'):
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(name)
    if missing:
        print('FAIL: missing runtime dependencies: '+', '.join(missing), file=sys.stderr)
        print('Install requirements.txt before running release checks.', file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix='na-release-check-') as temporary:
        environment = dict(os.environ, NETWORK_AUTOMATION_DATA_DIR=temporary)
        for command in ([sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py','-v'],
                        [sys.executable,'regression_test.py']):
            result = subprocess.run(command, cwd=ROOT, env=environment)
            if result.returncode:
                return result.returncode
    print('PASS: release checks; disposable data removed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
