import codecs
from enum import Enum


class Charset(str, Enum):
    ASCII = "ascii"
    LATIN_1 = "iso8859-1"
    UTF_8 = "utf-8"
    UTF_16 = "utf-16"
    UTF_16_BE = "utf-16-be"
    UTF_16_LE = "utf-16-le"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            try:
                canonical = codecs.lookup(value).name
            except LookupError:
                return None

            for member in cls:
                if member.value == canonical:
                    return member

        return None
