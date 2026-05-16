#!/usr/bin/env python3
"""校验生成的项目结构完整性"""

import sys
from pathlib import Path

REQUIRED_FILES = [
    "conftest.py",
    "config/settings.py",
    "api/base_client.py",
    "utils/validator.py",
    "utils/logger.py",
    ".env.example",
    ".gitignore",
    "requirements.txt",
    "generator.json",
]

REQUIRED_DIRS = [
    "config",
    "api",
    "testcases",
    "scenarios",
    "data",
    "utils",
]


def validate(project_path: str) -> bool:
    root = Path(project_path)
    errors = []

    for d in REQUIRED_DIRS:
        if not (root / d).is_dir():
            errors.append(f"缺目录: {d}")

    for f in REQUIRED_FILES:
        if not (root / f).is_file():
            errors.append(f"缺文件: {f}")

    # 检查 .env.example 有 BASE_URL
    env = root / ".env.example"
    if env.is_file() and "BASE_URL" not in env.read_text():
        errors.append(".env.example 缺少 BASE_URL")

    # 检查 testcases 不为空
    tc = root / "testcases"
    if tc.is_dir() and not any(tc.glob("test_*.py")):
        errors.append("testcases/ 下没有 test_*.py 文件")

    # 检查 generator.json 合法
    import json
    gen = root / "generator.json"
    if gen.is_file():
        try:
            data = json.loads(gen.read_text())
            for key in ("version", "source_type", "generated_endpoints"):
                if key not in data:
                    errors.append(f"generator.json 缺字段: {key}")
        except json.JSONDecodeError as e:
            errors.append(f"generator.json 不是合法 JSON: {e}")

    if errors:
        print("❌ 项目校验失败：")
        for e in errors:
            print(f"  - {e}")
        return False

    print("✅ 项目结构校验通过")
    return True


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    sys.exit(0 if validate(path) else 1)
