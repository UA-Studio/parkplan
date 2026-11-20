"""화면 시험: 서버를 켜고 브라우저(Playwright)로 예시 도면 → 배치 찾기 → 결과 탭이 나오는지 확인.

    pip install playwright && python -m playwright install chromium
    pytest tests/test_gui.py -v
"""
import os
import socket
import subprocess
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(os.environ.get("TEST_OUT", os.path.join(ROOT, "test_out")))
os.makedirs(OUT, exist_ok=True)
pw = pytest.importorskip("playwright.sync_api")


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


@pytest.fixture
def server():
    port = _free_port()
    p = subprocess.Popen([sys.executable, "-m", "parking_ai", "--no-browser", "--port", str(port)], cwd=ROOT,
                         env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    url = f"http://127.0.0.1:{port}/"
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", port), 0.5).close()
            break
        except OSError:
            time.sleep(0.5)
    yield url
    p.terminate()


def test_gui_sample_run(server):
    errors = []
    with pw.sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(server)
        page.screenshot(path=os.path.join(OUT, "화면_1_시작.png"))
        page.click("#sample")
        page.wait_for_selector("#go:not([disabled])", timeout=60_000)
        page.click("#go")
        page.wait_for_selector("#alts button", timeout=900_000)
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(OUT, "화면_2_결과.png"))
        tabs = page.locator("#alts button").count()
        b.close()
    assert tabs >= 1
    assert not errors, errors
