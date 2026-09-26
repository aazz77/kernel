#!/usr/bin/env python3
"""gen-slim-fragment.py — 从 Debian 官方 amd64 config 生成 slim-desktop.fragment

用法(在仓库 kernel-config/ 目录或仓库根执行):
    python3 kernel-config/gen-slim-fragment.py [base_config] [patterns] [output]

默认:
    base     = kernel-config/config-7.1.8+deb13-amd64
    patterns = kernel-config/slim-patterns.txt
    output   = kernel-config/slim-desktop.fragment

规则:
  - 只对 base config 中实际 =y/=m 的符号生成 "# CONFIG_X is not set"
  - OVERRIDES 中的符号无条件写入(覆盖值或禁用), 不依赖 base 是否出现
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# 固定覆盖: (符号, 值) — 值为 None 表示禁用
OVERRIDES = [
    # 调试信息全关: 构建时间最大收益, 代价是失去 BTF(bpftrace 可用性下降)
    ("CONFIG_DEBUG_INFO_NONE", "y"),
    ("CONFIG_DEBUG_INFO", None),
    ("CONFIG_DEBUG_INFO_BTF", None),
    ("CONFIG_DEBUG_INFO_BTF_MODULES", None),
    ("CONFIG_GDB_SCRIPTS", None),
    # vanilla 树没有 Debian 发行版证书文件, 必须清空否则构建失败
    ("CONFIG_SYSTEM_TRUSTED_KEYS", '""'),
    ("CONFIG_SYSTEM_REVOCATION_KEYS", '""'),
    # 防止 git 状态附加 "+" 到 uname -r
    ("CONFIG_LOCALVERSION_AUTO", None),
]


def load_base(path):
    """返回 base config 中启用的符号 {symbol: value}"""
    enabled = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("CONFIG_") and "=" in line:
                k, v = line.split("=", 1)
                enabled[k] = v
    return enabled


def load_patterns(path):
    """patterns 允许省略 CONFIG_ 前缀, 统一补全。
    两类行:
      - 禁用行: 纯符号名, 可带 * 前缀通配 -> "# CONFIG_X is not set"
      - 设值行: 含 '=', 如 CONFIG_X=y / CONFIG_X=n (=n 归一化为 not set)
    返回 (disable_pats, set_lines)"""
    disable_pats, set_lines = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            if "=" in line:
                sym, _, val = line.partition("=")
                sym = sym.strip()
                if not sym.startswith("CONFIG_"):
                    sym = "CONFIG_" + sym
                if val.strip().lower() == "n":
                    set_lines.append((sym, None))
                else:
                    set_lines.append((sym, val.strip()))
            else:
                disable_pats.append("CONFIG_" + line if not line.startswith("CONFIG_") else line)
    return disable_pats, set_lines


def main():
    args = sys.argv[1:]
    base_file = args[0] if len(args) > 0 else os.path.join(HERE, "config-7.1.8+deb13-amd64")
    pat_file = args[1] if len(args) > 1 else os.path.join(HERE, "slim-patterns.txt")
    out_file = args[2] if len(args) > 2 else os.path.join(HERE, "slim-desktop.fragment")

    enabled = load_base(base_file)
    pats, set_lines = load_patterns(pat_file)

    matched = {}  # symbol -> pattern that disabled it
    for sym in enabled:
        for p in pats:
            if p.endswith("*"):
                if sym.startswith(p[:-1]):
                    matched[sym] = p
                    break
            elif sym == p:
                matched[sym] = p
                break

    by_pattern = {}
    for sym, p in sorted(matched.items()):
        by_pattern.setdefault(p, []).append(sym)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("# slim-desktop.fragment — x64 Debian 13 桌面精简\n")
        f.write("# 由 gen-slim-fragment.py 自动生成, 精简项定义见 slim-patterns.txt\n")
        f.write("# base: %s (启用符号 %d, 禁用 %d)\n" % (os.path.basename(base_file), len(enabled), len(matched)))
        f.write("\n# ---- 固定覆盖 ----\n")
        for k, v in OVERRIDES:
            f.write("%s=%s\n" % (k, v) if v else "# %s is not set\n" % k)
        if set_lines:
            f.write("\n# ---- 显式设置(来自 slim-patterns.txt 设值行) ----\n")
            for k, v in set_lines:
                f.write("%s=%s\n" % (k, v) if v else "# %s is not set\n" % k)
        for p, syms in by_pattern.items():
            f.write("\n# ---- [%s] (%d) ----\n" % (p, len(syms)))
            for s in syms:
                f.write("# %s is not set\n" % s)

    print("base symbols: %d, disabled: %d -> %s" % (len(enabled), len(matched), out_file))


if __name__ == "__main__":
    main()
