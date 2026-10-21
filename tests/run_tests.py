"""Реальные запуски C++-программы; только стандартная библиотека Python."""
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
COMPILER = Path(r"C:\msys64\ucrt64\bin\g++.exe")
EXE = ROOT / "bin/chess.exe"
NONE = "Угрозы королю нет."
ROOK = "Королю угрожает чёрная ладья."
BISHOP = "Королю угрожает чёрный слон."
BOTH = "Королю угрожают чёрная ладья и чёрный слон."
RANGE = "Ошибка: координаты должны быть от 1 до 8."
OVERLAP = "Ошибка: фигуры должны занимать разные клетки."
FORMAT = "Ошибка: требуется шесть целых координат."

# Порядок координат: король, ладья, слон. Ожидания заданы до запуска.
CASES = [
    ("Нет линий атаки", "4 4 1 2 2 1", NONE),
    ("Ладья по горизонтали", "4 4 1 4 8 7", ROOK),
    ("Ладья по вертикали", "4 4 4 8 1 2", ROOK),
    ("Слон на восходящей диагонали", "4 4 1 2 1 1", BISHOP),
    ("Слон на нисходящей диагонали", "4 4 1 2 7 1", BISHOP),
    ("Обе фигуры атакуют", "4 4 4 1 1 1", BOTH),
    ("Слон перекрывает ладью по горизонтали", "8 4 1 4 5 4", NONE),
    ("Слон перекрывает ладью по вертикали", "3 8 3 1 3 5", NONE),
    ("Ладья перекрывает слона на диагонали", "8 8 4 4 1 1", NONE),
    ("Ладья перекрывает слона на обратной диагонали", "1 8 4 5 8 1", NONE),
    ("Слон за ладьёй не блокирует", "8 4 3 4 1 4", ROOK),
    ("Слон за королём не блокирует", "5 4 1 4 8 4", ROOK),
    ("Ладья за слоном не блокирует", "8 8 1 1 3 3", BISHOP),
    ("Ладья за королём не блокирует", "5 5 8 8 1 1", BISHOP),
    ("Фигура вне линии атаки не блокирует", "8 8 1 8 4 7", ROOK),
    ("Соседние атакующие фигуры", "4 4 4 3 5 5", BOTH),
    ("Границы доски", "1 1 1 8 8 8", BOTH),
    ("Слон другого цвета поля", "1 1 3 5 8 7", NONE),
    ("Координата ноль", "0 1 2 3 4 5", RANGE),
    ("Координата девять", "1 1 2 3 9 5", RANGE),
    ("Отрицательная координата", "1 1 -2 3 4 5", RANGE),
    ("Король и ладья на одной клетке", "4 4 4 4 1 1", OVERLAP),
    ("Король и слон на одной клетке", "4 4 1 2 4 4", OVERLAP),
    ("Ладья и слон на одной клетке", "4 4 1 2 1 2", OVERLAP),
    ("Буквы вместо координаты", "a 1 2 3 4 5", FORMAT),
    ("Дробь в последней координате", "1 1 2 3 4 5.5", FORMAT),
    ("Число с суффиксом", "1 1 2 3 4 5x", FORMAT),
    ("Переполнение целого числа", "99999999999999999999 1 2 3 4 5", FORMAT),
    ("Недостаточно координат", "1 1 2 3", FORMAT),
    ("Пустой ввод", "", FORMAT),
]


def main():
    env = os.environ.copy()
    env["TEMP"] = env["TMP"] = str(ROOT / "work/tmp")
    # Статическая линковка позволяет запускать EXE без изменения PATH.
    command = [str(COMPILER), "-std=c++17", "-Wall", "-Wextra", "-pedantic", "-static",
               "-finput-charset=UTF-8", "-fexec-charset=UTF-8",
               "src/main.cpp", "-o", "bin/chess.exe"]
    version = subprocess.run([str(COMPILER), "--version"], cwd=ROOT,
                             env=env, capture_output=True, text=True, encoding="utf-8")
    build = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
    log = [f"Время: {datetime.now().astimezone().isoformat()}", version.stdout,
           "$ " + subprocess.list2cmdline(command), "stdout:", build.stdout,
           "stderr:", build.stderr, f"Код компиляции: {build.returncode}"]
    (ROOT / "evidence/build.log").write_text("\n".join(log), encoding="utf-8")
    if build.returncode:
        raise SystemExit("Compilation failed; see evidence/build.log")
    records = []
    for number, (name, data, expected) in enumerate(CASES, 1):
        proc = subprocess.run([str(EXE)], input=data + "\n", cwd=ROOT, env=env,
                              capture_output=True, text=True, encoding="utf-8", timeout=5)
        actual = proc.stdout.strip().splitlines()[-1]
        expected_code = 1 if expected.startswith("Ошибка:") else 0
        passed = actual == expected and proc.returncode == expected_code and not proc.stderr
        records.append(dict(id=number, name=name, input=data, expected=expected,
                            actual=actual, expected_exit=expected_code,
                            exit_code=proc.returncode, passed=passed,
                            stdout=proc.stdout, stderr=proc.stderr))
    summary = dict(timestamp=datetime.now().astimezone().isoformat(),
                   compiler=version.stdout.splitlines()[0],
                   source_sha256=hashlib.sha256((ROOT / "src/main.cpp").read_bytes()).hexdigest(),
                   exe_sha256=hashlib.sha256(EXE.read_bytes()).hexdigest(),
                   build_returncode=build.returncode, warnings=build.stderr,
                   total=len(records), passed=sum(r["passed"] for r in records), tests=records)
    (ROOT / "evidence/results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with (ROOT / "evidence/results.csv").open("w", encoding="utf-8-sig", newline="") as f:
        keys = ["id", "name", "input", "expected", "actual", "exit_code", "passed"]
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    lines = []
    for r in records:
        lines += [f"Тест {r['id']}: {r['name']}", f"Ввод: {r['input']!r}",
                  f"Ожидалось: {r['expected']}", "Фактический stdout:", r["stdout"].rstrip(),
                  f"Код выхода: {r['exit_code']}; PASS={r['passed']}", ""]
    (ROOT / "evidence/test_runs.log").write_text("\n".join(lines), encoding="utf-8")
    print(f"BUILD: exit={build.returncode}; warnings={'yes' if build.stderr else 'no'}")
    print(f"TESTS: {summary['passed']}/{summary['total']} PASS")
    if summary["passed"] != summary["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
