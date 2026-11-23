"""비교 시험용 대지 DXF 만들기 (합성 대지 — 개인 도면 아님).

    python benchmark/make_sites.py

다른 도구에서도 읽히도록 레이어 이름은 영문(SITE·CORE·RAMP), 단위는 mm 입니다.
"""
import os

import ezdxf
from shapely.geometry import Polygon, box

HERE = os.path.dirname(os.path.abspath(__file__))

# 이름: (대지, 코어, 경사로, 설명)
SITES = {
    "B0_rect": (box(0, 0, 60, 40), [], [], "직사각형 60×40m, 코어·경사로 없음 — 모든 도구가 다룰 수 있는 가장 단순한 경우"),
    "B1_sample": (Polygon([(0, 0), (70, 0), (76, 30), (68, 50), (0, 50)]), [box(20, 20, 28, 30), box(48, 8, 55, 16)],
                  [box(0, 27, 6.4, 50)], "꺾인 대지 약 3,600㎡, 코어 2, 직선 경사로 1 (프로그램 예시 도면과 같음)"),
    "B2_big": (Polygon([(0, 0), (120, 0), (130, 40), (115, 80), (0, 80)]),
               [box(30, 30, 40, 42), box(80, 50, 90, 60), box(95, 10, 103, 18)], [box(0, 50, 6.4, 80)],
               "큰 대지 약 9,800㎡, 코어 3, 경사로 1"),
}


def write(path, site, cores, ramps):
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4  # mm
    for n, c in (("SITE", 7), ("CORE", 8), ("RAMP", 5)):
        doc.layers.add(n, color=c)
    msp = doc.modelspace()
    k = 1000.0
    for g, layer in [(site, "SITE")] + [(c, "CORE") for c in cores] + [(r, "RAMP") for r in ramps]:
        msp.add_lwpolyline([(x * k, y * k) for x, y in list(g.exterior.coords)[:-1]], close=True, dxfattribs={"layer": layer})
    doc.saveas(path)


if __name__ == "__main__":
    for name, (site, cores, ramps, note) in SITES.items():
        p = os.path.join(HERE, f"{name}.dxf")
        write(p, site, cores, ramps)
        print(p, f"{site.area:,.0f}㎡", note)
