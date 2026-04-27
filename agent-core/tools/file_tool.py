"""
文件读写工具
职责：在安全目录内读写文件，防止路径穿越攻击
安全目录由环境变量 FILE_BASE_DIR 控制，默认 /app/data/files
"""

import os
import aiofiles
from pathlib import Path

# 文件操作的安全根目录
FILE_BASE_DIR = Path(os.getenv("FILE_BASE_DIR", "/app/data/files"))


def _safe_path(filename: str) -> Path:
    """
    构建安全文件路径，防止路径穿越（如 ../../etc/passwd）
    :param filename: 用户传入的文件名
    :return: 安全的绝对路径
    :raises ValueError: 如果路径试图逃出安全目录
    """
    # 只取文件名部分，去掉任何目录前缀
    safe_name = Path(filename).name
    full_path  = FILE_BASE_DIR / safe_name

    # 二次确认路径在安全目录内
    if not str(full_path).startswith(str(FILE_BASE_DIR)):
        raise ValueError(f"非法路径：{filename}")

    return full_path


async def read_file(path: str) -> str:
    """
    读取文件内容
    :param path: 文件名（只取文件名部分，忽略目录）
    :return: 文件内容字符串
    """
    try:
        file_path = _safe_path(path)

        if not file_path.exists():
            return f"文件不存在：{file_path.name}"

        # 限制读取大小，防止读取超大文件
        if file_path.stat().st_size > 1024 * 1024:  # 1MB 限制
            return f"文件过大（超过1MB），拒绝读取：{file_path.name}"

        async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
            content = await f.read()

        return f"文件 [{file_path.name}] 内容：\n{content}"

    except ValueError as e:
        return f"路径错误：{str(e)}"
    except UnicodeDecodeError:
        return f"文件编码错误，请确保文件为 UTF-8 格式：{path}"
    except Exception as e:
        return f"读取文件失败：{str(e)}"


async def write_file(path: str, content: str = "") -> str:
    """
    写入文件内容
    :param path: 文件名
    :param content: 写入内容
    :return: 操作结果字符串
    """
    try:
        # 确保安全目录存在
        FILE_BASE_DIR.mkdir(parents=True, exist_ok=True)

        file_path = _safe_path(path)

        async with aiofiles.open(file_path, mode="w", encoding="utf-8") as f:
            await f.write(content)

        return f"文件写入成功：{file_path.name}（{len(content)} 字符）"

    except ValueError as e:
        return f"路径错误：{str(e)}"
    except Exception as e:
        return f"写入文件失败：{str(e)}"