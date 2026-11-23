"""비교 시험: 우리 프로그램 결과를 표로 (benchmark/우리_결과.md, 그림 benchmark/out/).

    python benchmark/run_ours.py

조건: 지하 1개 층, 직각 주차, 기본 법규(일반 2.5×5.0, 확장 2.6×5.2, 차로 6.0m, 기둥 700×500).
'대수만'(동선 가중치 0)과 '보통'(1) 두 가지, 그리고 다른 도구에 맞춘 비교용 설정(정형 8.1m 격자·기둥 600·일반형만).
"""
import dataclasses
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from make_sites import SITES  # noqa: E402
from parking_ai import export  # noqa: E402
from parking_ai.engine import search  # noqa: E402
from parking_ai.rules import Rules  # noqa: E402

CONFS = {
    "대수만": dict(circ_weight=0),
    "보통(동선 포함)": dict(circ_weight=1),
    # PRKNG_sqr 와 비슷한 조건: 8.1m 정사각 격자, 기둥 600, 확장형 비율 없이
    "8.1m 격자·기둥600·확장형 없음": dict(circ_weight=0, fixed_span=8.1, column_w=0.6, column_d=0.6, ext_ratio=0.0),
}

if __name__ == "__main__":
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    rows = []
    for name, (site, cores, ramps, note) in SITES.items():
        for cname, kw in CONFS.items():
            r = Rules(effort="normal", floors=1, park_angles=(90,), ramp_mode="drawn" if ramps else "none", **kw)
            t = time.time()
            res = search(site, cores, ramps=ramps, rules=r, log=lambda m: None)
            dt = time.time() - t
            st = res[0]["stats"]
            png = f"{name}_{list(CONFS).index(cname)}.png"
            export.plan_png(res[0], os.path.join(out, png), 0)
            rows.append((name, cname, st["total_legal"], st["area_per_stall"], st["circulation"]["avg_drive"],
                         st["circulation"]["dead_ends"], round(dt), png))
            print(rows[-1], flush=True)
    L = ["# 우리 프로그램 결과 (비교 시험용)", "",
         "지하 1개 층 · 직각 주차 · `python benchmark/run_ours.py` 로 다시 만들 수 있음", "",
         "| 대지 | 설정 | 법정 대수 | 대당 면적(㎡) | 평균 주행(m) | 막다른 차로 | 시간(초) | 그림 |", "|---|---|---|---|---|---|---|---|"]
    for n, c, tot, aps, avg, de, dt, png in rows:
        L.append(f"| {n} | {c} | **{tot}** | {aps} | {avg} | {de} | {dt} | [보기](out/{png}) |")
    open(os.path.join(HERE, "우리_결과.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("저장:", os.path.join(HERE, "우리_결과.md"))
