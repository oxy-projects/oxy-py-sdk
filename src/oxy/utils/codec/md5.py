import hashlib


def encrypt(message: str | bytes):
    if isinstance(message, str):
        message = message.encode('utf-8')
    # 创建一个md5对象
    md5 = hashlib.md5()
    md5.update(message)
    return md5.hexdigest()
