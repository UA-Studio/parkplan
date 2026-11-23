@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 지하주차장 배치
rem 다른 프로그램(QGIS, Anaconda 등)이 깔아 둔 파이썬 설정이 방해하지 않게 비운다
set PYTHONHOME=
set PYTHONPATH=
set PYTHONSTARTUP=
set PYTHONNOUSERSITE=1
set PYTHONUTF8=1
if not exist "%~dp0python\python.exe" (
  echo 압축이 다 풀리지 않았습니다. zip 파일을 오른쪽 클릭 - "모두 압축 풀기" 한 뒤 풀린 폴더에서 실행하세요.
  pause
  exit /b 1
)
echo 브라우저에 화면이 열립니다. 이 검은 창을 닫으면 프로그램이 꺼집니다.
"%~dp0python\python.exe" -s -m parking_ai %*
pause
