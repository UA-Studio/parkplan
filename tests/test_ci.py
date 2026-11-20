"""자동 시험 (GitHub Actions에서 커밋마다 실행).

    pytest tests/test_ci.py -v

결과 그림·도면은 TEST_OUT 폴더(기본 test_out/)에 남깁니다.
"""
import json
import os
import subprocess
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
OUT = os.path.abspath(os.environ.get("TEST_OUT", os.path.join(ROOT, "test_out")))
os.makedirs(OUT, exist_ok=True)

# 이관 문서 6절의 기준값 (1층, '보통', 동선 가중치 0). 이 값보다 적으면 실패.
BASELINE = {"sample": 111, "user": 82, "big": 331, "auto": 338}


def _record(name, value):
    """결과 표(summary.json)에 한 줄 더하기 — PR 설명·Actions 요약에 씀."""
    p = os.path.join(OUT, "summary.json")
    d = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    d[name] = value
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def test_import_version():
    import parking_ai
    assert parking_ai.VERSION and parking_ai.DATE


def test_cli_example():
    """명령줄로 예시 도면을 넣으면 출력 6종이 생겨야 함."""
    out = os.path.join(OUT, "cli_예시")
    t = time.time()
    p = subprocess.run([sys.executable, "-m", "parking_ai", os.path.join(ROOT, "예시", "예시_대지.dxf"), "--out", out],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=900)
    print(p.stdout[-3000:], p.stderr[-3000:])
    assert p.returncode == 0, p.stderr[-2000:]
    for f in ("B1_평면.png", "배치.dxf", "모델.3dm", "결과_층별대수.csv", "결과_요약.txt", "결과_통계.json"):
        fp = os.path.join(out, f)
        assert os.path.isfile(fp) and os.path.getsize(fp) > 0, f
    import ezdxf
    ezdxf.readfile(os.path.join(out, "배치.dxf"))  # 캐드에서 열리는 DXF인지
    import rhino3dm
    assert rhino3dm.File3dm.Read(os.path.join(out, "모델.3dm")) is not None
    _record("예시 도면 (명령줄)", f"출력 6종 OK · {time.time() - t:.0f}초")


@pytest.mark.parametrize("name", list(BASELINE))
def test_bench_regression(name):
    """대수가 기준값 아래로 떨어지면 실패."""
    from bench import CASES
    from parking_ai.engine import search
    from parking_ai.rules import Rules
    from parking_ai import export
    site, cores, ramps, kw = CASES[name]
    t = time.time()
    res = search(site, cores, ramps=ramps, rules=Rules(effort="normal", circ_weight=0, floors=1, **kw), log=lambda m: None)
    total = res[0]["stats"]["total_legal"]
    export.plan_png(res[0], os.path.join(OUT, f"bench_{name}.png"), 0)
    bad = [c["item"] for c in res[0]["stats"]["checks"] if not c["ok"]]
    _record(f"기준 대지 {name}", f"{total}대 (기준 {BASELINE[name]}) · {time.time() - t:.0f}초"
            + (f" · 미충족 표시: {', '.join(bad)}" if bad else ""))
    assert total >= BASELINE[name], f"{name}: {total}대 < 기준 {BASELINE[name]}대"
