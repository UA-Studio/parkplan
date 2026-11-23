"""Windows 무설치 묶음 만들기 (GitHub Actions의 Windows에서 실행).

    python tools/build_windows.py <파이썬 폴더> [--out dist]

<파이썬 폴더>: python.exe, Lib, DLLs 가 들어 있는 64비트 Windows 파이썬 (NuGet 'python' 패키지의 tools 폴더).
결과: dist/parking_layout_windows_v{VERSION}_{DATE}.zip
  지하주차장_윈도우/
    지하주차장 실행.bat   ← 더블클릭
    먼저_읽어주세요.txt
    사용법_전체.md
    예시/예시_대지.dxf
    python/               ← 내장 파이썬 + 라이브러리 + parking_ai
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP = "지하주차장_윈도우"
LIMIT = 250 * 1024 * 1024  # 파일 하나 250MB 넘지 않게


def version():
    s = open(os.path.join(ROOT, "parking_ai", "__init__.py"), encoding="utf-8").read()
    return re.search(r'VERSION\s*=\s*"([^"]+)"', s).group(1), re.search(r'DATE\s*=\s*"([^"]+)"', s).group(1)


def ignore(_d, names):
    return [n for n in names if n in ("__pycache__",) or n.endswith((".pyc", ".pyo"))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("python_dir")
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"))
    a = ap.parse_args()
    ver, date = version()
    stage = os.path.join(a.out, "stage")
    shutil.rmtree(stage, ignore_errors=True)
    top = os.path.join(stage, TOP)
    py = os.path.join(top, "python")
    shutil.copytree(a.python_dir, py, ignore=ignore)
    exe = os.path.join(py, "python.exe")
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["PYTHONNOUSERSITE"] = "1"
    run = lambda *c: subprocess.run([exe, "-s", *c], check=True, env=env)
    run("-m", "ensurepip", "--upgrade")
    run("-m", "pip", "install", "--no-warn-script-location", "--no-cache-dir", "-r", os.path.join(ROOT, "requirements.txt"))
    site = os.path.join(py, "Lib", "site-packages")
    shutil.copytree(os.path.join(ROOT, "parking_ai"), os.path.join(site, "parking_ai"), ignore=ignore)
    # 크기 줄이기: 묶음에서 쓰지 않는 시험·캐시
    for dp, dn, _ in os.walk(py, topdown=False):
        for d in dn:
            if d in ("__pycache__",) or (d in ("tests", "test") and "parking_ai" not in dp):
                shutil.rmtree(os.path.join(dp, d), ignore_errors=True)
    # 정리한 뒤에도 묶음 안 파이썬이 우리 패키지와 라이브러리를 실제로 불러오는지
    run("-c", "import parking_ai, parking_ai.app, parking_ai.engine, shapely, numpy, ezdxf, rhino3dm, matplotlib; print('import ok', parking_ai.VERSION)")

    pk = os.path.join(ROOT, "packaging", "windows")
    shutil.copy(os.path.join(pk, "지하주차장 실행.bat"), top)
    txt = open(os.path.join(pk, "먼저_읽어주세요.txt"), encoding="utf-8", newline="").read()
    open(os.path.join(top, "먼저_읽어주세요.txt"), "w", encoding="utf-8", newline="").write(txt.replace("{VERSION}", ver).replace("{DATE}", date))
    shutil.copy(os.path.join(ROOT, "docs", "사용법_상세.md"), os.path.join(top, "사용법_전체.md"))
    os.makedirs(os.path.join(top, "예시"), exist_ok=True)
    shutil.copy(os.path.join(ROOT, "예시", "예시_대지.dxf"), os.path.join(top, "예시"))

    # zip은 파이썬 zipfile로 (한글 이름 UTF-8 표시 → 윈도우 탐색기에서 제대로 보임)
    zp = os.path.join(a.out, f"parking_layout_windows_v{ver}_{date}.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for dp, dn, fn in os.walk(top):
            dn.sort()
            for f in sorted(fn):
                p = os.path.join(dp, f)
                z.write(p, os.path.relpath(p, stage).replace(os.sep, "/"))
    with zipfile.ZipFile(zp) as z:
        assert z.testzip() is None
        bad = [i.filename for i in z.infolist() if not i.filename.isascii() and not i.flag_bits & 0x800]
        assert not bad, bad
        n = len(z.infolist())
    size = os.path.getsize(zp)
    assert size < LIMIT, f"{size / 1e6:.0f}MB > 250MB"
    print(f"{zp}  {size / 1e6:.1f}MB  파일 {n}개")
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write(f"zip={zp}\nname={os.path.basename(zp)}\nversion={ver}\ndate={date}\n")


if __name__ == "__main__":
    main()
