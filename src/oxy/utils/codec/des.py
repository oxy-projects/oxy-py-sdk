import codecs

from Crypto.Cipher import DES
from Crypto.Cipher._mode_cbc import CbcMode
from Crypto.Cipher._mode_cfb import CfbMode
from Crypto.Cipher._mode_ctr import CtrMode
from Crypto.Cipher._mode_eax import EaxMode
from Crypto.Cipher._mode_ecb import EcbMode
from Crypto.Cipher._mode_ofb import OfbMode
from Crypto.Cipher._mode_openpgp import OpenPgpMode
from Crypto.Util.Padding import pad, unpad


def encrypt(message: str | bytes, *, key: str | bytes, iv: str | bytes = None, mode: int = None) -> str:
    """
    DES加密
    :param message: 加密数据
    :param key: 加密key
    :param iv: 加密iv
    :param mode: 模式
    :return:
    """
    if message is None:
        raise Exception('请输入需要加密的报文')
    if isinstance(message, str):
        message = message.encode('utf-8')
    # 创建DES对象
    des = _instance(key=key, iv=iv, mode=mode)
    # 填充
    padded_message = pad(message, DES.block_size)
    # 加密
    return codecs.encode(des.encrypt(padded_message), 'hex').decode('utf-8')


def decrypt(encrypted_message: str | bytes, *, key: str | bytes, iv: str | bytes = None, mode: int = None) -> str:
    """
    DES解密
    :param encrypted_message: 待解密数据
    :param key: 加密key
    :param iv: 加密iv
    :param mode: 模式
    :return:
    """
    if encrypted_message is None:
        raise Exception('请输入需要解密的报文')
    if isinstance(encrypted_message, str):
        encrypted_message = encrypted_message.encode('utf-8')
    # 创建DES对象
    des = _instance(key=key, iv=iv, mode=mode)
    # 解密
    padded_message = des.decrypt(codecs.decode(encrypted_message, 'hex'))
    # 去掉填充
    message = unpad(padded_message, DES.block_size)
    return message.decode('utf-8')


def _instance(*, key: str | bytes, iv: str | bytes = None, mode: int = None) \
        -> EcbMode | CbcMode | CfbMode | OfbMode | CtrMode | OpenPgpMode | EaxMode:
    if key is None:
        raise Exception('请输入加密秘钥')
    if isinstance(key, str):
        key = bytes(key.encode('utf-8'))[:8]
    if isinstance(iv, str):
        iv = iv.encode('utf-8')
        # 创建DES对象
    return DES.new(key=key, iv=iv, mode=DES.MODE_CBC if mode is None else mode)
