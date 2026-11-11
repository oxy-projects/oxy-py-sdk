import hashlib
from pathlib import Path


def encrypt(message: str | bytes):
    if isinstance(message, str):
        message = message.encode('utf-8')
    sha256 = hashlib.sha256()
    sha256.update(message)
    return sha256.hexdigest()


def encrypt_file(file: Path):
    if file is None or not file.exists():
        raise Exception('文件不存在')
    sha256 = hashlib.sha256()
    # 打开文件并读取内容，同时更新哈希对象
    with open(file, 'rb') as file:  # 以二进制读取模式打开文件
        while chunk := file.read(4096):  # 每次读取4096字节，直到文件末尾
            sha256.update(chunk)
    return sha256.hexdigest()
