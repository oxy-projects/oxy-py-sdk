import base64
import os
import re
from pathlib import Path
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding, types

from oxy.utils.codec.crypto_model import SignPadding
from oxy.utils.lang import logger

log = logger.of(__name__)


def load_user_keys(base_dir: Path = Path.home().joinpath('.ssh'), force_first: bool = False) \
        -> tuple[types.PrivateKeyTypes, types.PublicKeyTypes]:
    """
    加载用户秘钥：以.pem结尾，包含public和private名称的文件
    :param base_dir: 秘钥存放目录，默认为用户目录.ssh下，即：~/.ssh/.
    :param force_first: 强制选择第一个秘钥
    :return: (私钥，公钥)
    """
    key_pairs = [(pub_key_file.replace('public', 'private'), pub_key_file) for pub_key_file in os.listdir(base_dir)
                 if re.search(r'public\S+\.pem$', pub_key_file)
                 and base_dir.joinpath(pub_key_file.replace('public', 'private')).is_file()]
    if not key_pairs:
        log.error(f'用户目录下<{base_dir.absolute()}>未找到秘钥文件！')
        raise FileNotFoundError(f'用户目录下<{base_dir.absolute()}>未找到秘钥文件！')

    pri_key_file, pub_key_file = key_pairs[0]
    if len(key_pairs) > 1 and not force_first:
        log.warning(f'用户目录下找到多个秘钥文件：')
        for i, key_pair in enumerate(key_pairs):
            log.warning(f'{i + 1}. {key_pair[0]} and {key_pair[1]}')
        while True:
            try:
                select_idx = int(input(f'请选择要使用的秘钥文件[输入1至{len(key_pairs)}]：'))
                if 1 <= select_idx <= len(key_pairs):
                    pri_key_file, pub_key_file = key_pairs[select_idx - 1]
                    break
            except ValueError:
                log.error(f'请正确输入序号！')
    log.warning(f'选择使用的秘钥文件：\n  - {pri_key_file} \n  - {pub_key_file}')
    return load_private_key(base_dir.joinpath(pri_key_file)), load_public_key(base_dir.joinpath(pub_key_file))


def load_user_public_key(base_dir: Path = Path.home().joinpath('.ssh'), force_first: bool = False) \
        -> Optional[types.PublicKeyTypes]:
    """
    加载用户公钥：以.pem结尾，包含public名称的文件
    :param base_dir: 秘钥存放目录，默认为用户目录.ssh下，即：~/.ssh/.
    :param force_first: 强制选择第一个秘钥
    """
    keys = [pub_key_file for pub_key_file in os.listdir(base_dir) if re.search(r'public\S+\.pem$', pub_key_file)]
    if not keys:
        log.error(f'用户目录下<{base_dir.absolute()}>未找到公钥文件！')
        raise FileNotFoundError(f'用户目录下<{base_dir.absolute()}>未找到公钥文件！')

    pub_key_file = keys[0]
    if len(keys) > 1 and not force_first:
        log.warning(f'用户目录下找到多个公钥文件：')
        for i, key in enumerate(keys):
            log.warning(f'{i + 1}. {key}')
        while True:
            try:
                select_idx = int(input(f'请选择要使用的公钥文件[输入1至{len(keys)}]：'))
                if 1 <= select_idx <= len(keys):
                    pub_key_file = keys[select_idx - 1]
                    break
            except ValueError:
                log.error(f'请正确输入序号！')
    log.warning(f'选择使用的公钥文件：\n  - {pub_key_file}')
    return load_public_key(base_dir.joinpath(pub_key_file))


def load_user_private_key(base_dir: Path = Path.home().joinpath('.ssh'), force_first: bool = False) \
        -> Optional[types.PrivateKeyTypes]:
    """
    加载用户私钥：以.pem结尾，包含private名称的文件
    :param base_dir: 秘钥存放目录，默认为用户目录.ssh下，即：~/.ssh/.
    :param force_first: 强制选择第一个秘钥
    """
    keys = [pri_key_file for pri_key_file in os.listdir(base_dir) if re.search(r'private\S+\.pem$', pri_key_file)]
    if not keys:
        log.error(f'用户目录下<{base_dir.absolute()}>未找到私钥文件！')
        raise FileNotFoundError(f'用户目录下<{base_dir.absolute()}>未找到私钥文件！')

    pri_key_file = keys[0]
    if len(keys) > 1 and not force_first:
        log.warning(f'用户目录下找到多个私钥文件：')
        for i, key in enumerate(keys):
            log.warning(f'{i + 1}. {key}')
        while True:
            try:
                select_idx = int(input(f'请选择要使用的私钥文件[输入1至{len(keys)}]：'))
                if 1 <= select_idx <= len(keys):
                    pri_key_file = keys[select_idx - 1]
                    break
            except ValueError:
                log.error(f'请正确输入序号！')
    log.warning(f'选择使用的私钥文件：\n  - {pri_key_file}')
    return load_private_key(base_dir.joinpath(pri_key_file))


def generate_rsa_keys(serialize: bool = False) -> tuple[types.PrivateKeyTypes | str, types.PublicKeyTypes | str]:
    """
    生成一个RSA密钥对
    :param serialize: 如果为True，则返回秘钥序列化的字符串
    :return: (私钥, 公钥)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    if not serialize:
        return private_key, public_key
    # 私钥序列化
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    # 公钥序列化
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return str(private_pem, 'utf-8'), str(public_pem, 'utf-8')


def load_public_key(public_key_pem: Path | bytes | types.PublicKeyTypes) -> types.PublicKeyTypes:
    """
    加载公钥
    :param public_key_pem: 支持秘钥文件路径、秘钥字节流、秘钥对象
    """
    if isinstance(public_key_pem, Path):
        with open(public_key_pem, 'rb') as file:
            file_bytes = file.read()
        # 递归处理
        return load_public_key(file_bytes)
    elif isinstance(public_key_pem, bytes):
        return serialization.load_pem_public_key(public_key_pem, default_backend())
    elif isinstance(public_key_pem, types.PublicKeyTypes):
        return public_key_pem
    else:
        raise TypeError('公钥入参格式异常，请检查')


def load_private_key(private_key_pem: Path | bytes | types.PrivateKeyTypes) -> types.PrivateKeyTypes:
    """
    加载私钥
    :param private_key_pem: 支持秘钥文件路径、秘钥字节流、秘钥对象
    """
    if isinstance(private_key_pem, Path):
        with open(private_key_pem, 'rb') as file:
            file_bytes = file.read()
        # 递归处理
        return load_private_key(file_bytes)
    elif isinstance(private_key_pem, bytes):
        return serialization.load_pem_private_key(private_key_pem, password=None, backend=default_backend())
    elif isinstance(private_key_pem, types.PrivateKeyTypes):
        return private_key_pem
    else:
        raise TypeError('私钥入参格式异常，请检查')


def encrypt_message(public_key_pem: Path | bytes | types.PublicKeyTypes, message: str | bytes) \
        -> tuple[types.PublicKeyTypes, str]:
    """
    公钥加密
    :param public_key_pem: 支持秘钥文件路径、秘钥字节流、秘钥对象
    """
    if isinstance(message, str):
        message = message.encode('utf-8')
    # 加载公钥
    public_key = load_public_key(public_key_pem)
    # 加密
    chunk_size = 128
    if len(message) > chunk_size:
        # 超长分段加密
        enc_messages = [encrypt_message(public_key, message[i:i+chunk_size])[1] for i in range(0, len(message), chunk_size)]
        return public_key, '__'.join(enc_messages)
    enc_message = public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return public_key, base64.b64encode(enc_message).decode('utf-8')


def decrypt_message(private_key_pem: Path | bytes | types.PrivateKeyTypes, encrypted_message: str | bytes) \
        -> tuple[types.PrivateKeyTypes, str]:
    """
    私钥解密
    :param private_key_pem: 支持秘钥文件路径、秘钥字节流、秘钥对象
    :param encrypted_message: 加密信息
    """
    # 加载私钥
    private_key = load_private_key(private_key_pem)
    if isinstance(encrypted_message, bytes):
        encrypted_message = encrypted_message.decode('ascii')
    # 分段边界可能位于 UTF-8 字符内部，合并全部明文字节后再解码。
    decrypted_parts = [
        private_key.decrypt(
            base64.b64decode(part),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        for part in encrypted_message.split('__')
    ]
    return private_key, b''.join(decrypted_parts).decode('utf-8')


def sign_message(private_key_pem: Path | bytes | types.PrivateKeyTypes, message: str | bytes,
                 *, padding: SignPadding = SignPadding.PSS, digest_sign: bool = False) \
        -> tuple[types.PrivateKeyTypes, str]:
    """
    私钥加签
    :param private_key_pem: 支持秘钥文件路径、秘钥字节流、秘钥对象
    :param padding：签名加密标准
    :param digest_sign: 是否对message先进行哈希得到摘要信息，然后再对摘要信息加签
    """
    if isinstance(message, str):
        message = message.encode('utf-8')
    if digest_sign:
        # 消息摘要
        digest_hasher = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest_hasher.update(message)
        message = digest_hasher.finalize()
    # 加载私钥
    private_key = load_private_key(private_key_pem)
    # 使用私钥签名
    # types.rsa.RSAPrivateKey.sign()
    sign_message = private_key.sign(
        data=message,
        padding=padding.value,
        algorithm=hashes.SHA256()
    )
    return private_key, base64.b64encode(sign_message).decode('utf-8')


def verify_message(public_key_pem: Path | bytes | types.PublicKeyTypes, message: str | bytes, sign: str | bytes,
                   *, padding: SignPadding = SignPadding.PSS, digest_sign: bool = False) \
        -> tuple[types.PublicKeyTypes, bool]:
    """
    :param public_key_pem: 支持秘钥文件路径、秘钥字节流、秘钥对象
    :param sign: 需要验证的签名
    :param padding：签名加密标准
    :param digest_sign: 是否对message先进行哈希得到摘要信息，然后再对摘要信息加签
    """
    if isinstance(message, str):
        message = message.encode('utf-8')
    # 可视签名解码
    sign = base64.b64decode(sign)
    if digest_sign:
        # 消息摘要
        digest_hasher = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest_hasher.update(message)
        message = digest_hasher.finalize()
    # 加载公钥
    public_key = load_public_key(public_key_pem)
    # 使用公钥验签
    try:
        # types.rsa.RSAPublicKey.verify()
        public_key.verify(
            sign,
            message,
            padding.value,
            hashes.SHA256()
        )
        verified = True
    except InvalidSignature:
        verified = False
    return public_key, verified
