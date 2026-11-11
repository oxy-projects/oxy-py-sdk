from enum import Enum

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding


class SignPadding(Enum):
    """
    签名加密标准
    """
    PSS = padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    )
    PKCS1 = padding.PKCS1v15()
