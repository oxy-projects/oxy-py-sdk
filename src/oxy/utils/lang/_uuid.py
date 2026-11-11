import uuid


def gen_uuid_str() -> str:
    return str(uuid.uuid4()).replace('-', '')
