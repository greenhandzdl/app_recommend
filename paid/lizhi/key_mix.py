#!/usr/bin/env python3
"""
XML 二进制混淆/反混淆工具 (XOR + Salt + Base64)
用途：将 XML 当作纯二进制混淆成文本，便于上传 GitHub
原理：用密钥 + 随机盐生成无限密钥流，逐字节异或，最后 Base64 编码
注意：这是混淆，不是高强度加密，请自行保管密钥
"""

import os
import sys
import base64
import hashlib
import argparse

SALT_SIZE = 16  # 随机盐长度


def _generate_key_stream(password: str, salt: bytes, length: int) -> bytes:
    """
    用 SHA256 计数器模式生成伪随机密钥流（无限长度）
    速度快，适合任意大小的文件
    """
    key_stream = b""
    counter = 0
    while len(key_stream) < length:
        hasher = hashlib.sha256()
        hasher.update(password.encode("utf-8"))
        hasher.update(salt)
        hasher.update(str(counter).encode())
        key_stream += hasher.digest()
        counter += 1
    return key_stream[:length]


def obfuscate_file(input_path: str, output_path: str, password: str):
    """混淆（加密）：二进制 -> Base64 文本"""
    with open(input_path, "rb") as f:
        plain_data = f.read()

    # 生成随机盐
    salt = os.urandom(SALT_SIZE)

    # 生成密钥流并异或
    key_stream = _generate_key_stream(password, salt, len(plain_data))
    obfuscated_bytes = bytes(a ^ b for a, b in zip(plain_data, key_stream))

    # 组合：盐 + 混淆数据，再转为 Base64 文本
    final_data = salt + obfuscated_bytes
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(base64.b64encode(final_data).decode("ascii"))

    print(f"[✓] 混淆完成，已保存至：{output_path}")
    print(f"    原始大小：{len(plain_data)} 字节，混淆后文本大小：{len(final_data) * 4 // 3} 字符")


def deobfuscate_file(input_path: str, output_path: str, password: str):
    """反混淆（解密）：Base64 文本 -> 二进制原文"""
    with open(input_path, "r", encoding="utf-8") as f:
        b64_data = f.read().strip()

    try:
        raw = base64.b64decode(b64_data)
    except Exception:
        raise ValueError("无效的 Base64 数据，请检查文件是否损坏")

    if len(raw) < SALT_SIZE:
        raise ValueError("数据太短，无法提取盐值")

    # 提取盐和密文
    salt = raw[:SALT_SIZE]
    obfuscated_bytes = raw[SALT_SIZE:]

    # 生成同样的密钥流并异或还原
    key_stream = _generate_key_stream(password, salt, len(obfuscated_bytes))
    plain_data = bytes(a ^ b for a, b in zip(obfuscated_bytes, key_stream))

    with open(output_path, "wb") as f:
        f.write(plain_data)

    print(f"[✓] 反混淆完成，已还原至：{output_path}")
    print(f"    还原大小：{len(plain_data)} 字节")


def main():
    parser = argparse.ArgumentParser(
        description="XML 轻量级混淆工具（基于 XOR + 盐 + Base64）"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 混淆子命令
    enc_parser = subparsers.add_parser("obfuscate", help="混淆 XML 文件")
    enc_parser.add_argument("input", help="输入的 XML 文件路径")
    enc_parser.add_argument("output", help="输出的混淆文本文件路径")
    enc_parser.add_argument("-p", "--password", required=True, help="混淆密钥（自己记住）")

    # 反混淆子命令
    dec_parser = subparsers.add_parser("deobfuscate", help="反混淆还原 XML 文件")
    dec_parser.add_argument("input", help="输入的混淆文本文件路径")
    dec_parser.add_argument("output", help="输出的还原 XML 文件路径")
    dec_parser.add_argument("-p", "--password", required=True, help="混淆时使用的密钥")

    args = parser.parse_args()

    try:
        if args.command == "obfuscate":
            obfuscate_file(args.input, args.output, args.password)
        elif args.command == "deobfuscate":
            deobfuscate_file(args.input, args.output, args.password)
    except Exception as e:
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()