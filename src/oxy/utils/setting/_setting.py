from functools import wraps
from pathlib import Path
from typing import Callable, Any, Optional

import yaml
from cryptography.hazmat.primitives.asymmetric import types

from oxy.utils.codec import crypto
from oxy.utils.lang import IllegalArgumentException, logger

log = logger.of(__name__)
DEFAULT_CONFIG_FILE_NAME = 'settings.yaml'
DEFAULT_ENCRYPT_FILE_EXT = '.crypto'
_SENSITIVE_KEY_MARKERS = (
    'token', 'secret', 'password', 'passwd', 'credential', 'private', 'web-token',
)


def _redact_for_log(prop_name: str, value: Any) -> Any:
    lowered = prop_name.lower()
    if any(marker in lowered for marker in _SENSITIVE_KEY_MARKERS):
        return '***'
    return value


def config(*, config_dir: str | Path, file_name: str = None):
    """
    项目加载配置
    :param config_dir: 配置文件目录
    :param file_name: 配置文件名称，默认为：settings.yaml
    """
    def decorator(func):
        _settings: Optional[dict] = None

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal config_dir
            nonlocal file_name
            nonlocal _settings

            if _settings:
                return _settings
            if not isinstance(config_dir, Path):
                config_dir = Path(config_dir)
            if not file_name:
                file_name = DEFAULT_CONFIG_FILE_NAME
            _settings = load_yaml(config_dir.joinpath(file_name))
            return _settings
        return wrapper
    return decorator


class DefaultSetting:
    """
    默认配置获取类
    """
    @staticmethod
    def get():
        return {}


def read(prop_name: str, *,
         parser: Callable[[Any], Any] = None,
         settings: dict | Callable[[], dict] = None) -> Callable[[Any], Any]:
    """
    注解形式注入配置值，如果没找到对应配置则按照方法执行结果返回
    :param prop_name: 配置键，英文句号“.”分隔
    :param parser: 配置转换器
    :param settings: 默认读取的配置，如果没有则按照方法返回值获取
    """
    def decorator(func):
        # 增加缓存
        cache = dict()

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal settings
            nonlocal func
            nonlocal cache
            # 没有配置key，则按照方法默认返回
            if not prop_name:
                raise IllegalArgumentException(f'方法<{func.__name__}>请输入需要读取的配置键')
            # 命中配置缓存，则直接返回
            if prop_name in cache:
                return cache[prop_name]
            # 解析配置
            settings = settings or DefaultSetting().get
            settings = settings if isinstance(settings, dict) else settings()
            keys = prop_name.split('.')
            value = settings
            for key in keys:
                value = value.get(key, None)
                if value is None:
                    break
            # 无配置，则按照方法默认返回
            if value is None:
                fun_val = func(*args, **kwargs)
                if fun_val is None or fun_val == '':
                    raise IllegalArgumentException(
                        f'方法<{func.__name__}>未查询到<{prop_name}>的配置值，请完善配置或在方法指定默认值'
                    )
                return fun_val
            # 配置存在，如果有转换器则进行转换
            value = value if not parser else parser(value)
            # 设置缓存并返回
            cache[prop_name] = value
            log.debug('项目配置加载成功，%s：%s', prop_name, _redact_for_log(prop_name, value))
            return value
        return wrapper
    return decorator


def load_yaml(yaml_file: Path) -> dict:
    """
    加载yaml文件配置
    :param yaml_file: yaml文件路径
    """
    if not yaml_file.exists() or not yaml_file.is_file():
        log.error("请正确输入需要加载的yaml文件：%s", yaml_file)
        return {}
    with open(yaml_file, 'r') as f:
        return yaml.safe_load(f)


def dump_yaml(settings: dict, yaml_file: Path):
    """
    配置保存到yaml文件中
    """
    if not yaml_file.exists():
        yaml_file.touch()
    with open(yaml_file, 'w') as f:
        return yaml.safe_dump(settings, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def encrypt_yaml(yaml_file: Path,
                 encrypt_keys: list = None,
                 public_key: types.PublicKeyTypes = None,
                 encrypt_file_ext: str = DEFAULT_ENCRYPT_FILE_EXT) -> Path:
    """
    对指定的yaml文件加密，并返回文件的位置
    :param yaml_file: 待加密yaml文件路径，默认为项目根目录下的settings.yaml文件
    :param encrypt_keys: 需要加密的key，如果不传则全部加密
    :param public_key: 公钥，默认加载用户.ssh目录下的秘钥
    :param encrypt_file_ext: 加密文件的扩展名
    """
    public_key = crypto.load_user_public_key() if public_key is None else public_key
    settings_enc = replace_settings(load_yaml(yaml_file),
                                    lambda val: crypto.encrypt_message(public_key, str(val))[1],
                                    lambda key: encrypt_keys is None or key in encrypt_keys)
    yaml_file_enc = yaml_file.with_suffix(yaml_file.suffix + encrypt_file_ext)
    dump_yaml(settings_enc, yaml_file_enc)
    return yaml_file_enc


def decrypt_yaml(yaml_file: Path,
                 decrypt_keys: list = None,
                 private_key: types.PrivateKeyTypes = None,
                 decrypt_file_ext: str = None) -> Path:
    """
    对指定的yaml文件解密，并返回文件的位置
    :param yaml_file: 待解密yaml文件路径，
    :param decrypt_keys: 需要加密的key，如果不传则全部加密
    :param private_key: 私钥，默认加载用户.ssh目录下的秘钥
    :param decrypt_file_ext: 解密文件的扩展名，默认为去掉.crypto后的扩展名
    """
    private_key = crypto.load_user_private_key() if private_key is None else private_key
    settings_enc = replace_settings(load_yaml(yaml_file),
                                    lambda val: crypto.decrypt_message(private_key, str(val))[1],
                                    lambda key: decrypt_keys is None or key in decrypt_keys)
    yaml_file_enc = yaml_file.parent.joinpath(yaml_file.stem)
    if decrypt_file_ext:
        yaml_file_enc = yaml_file_enc.with_suffix(decrypt_file_ext)
    if yaml_file_enc == yaml_file:
        raise FileExistsError('请输入与解密配置文件不一样的扩展名')
    dump_yaml(settings_enc, yaml_file_enc)
    return yaml_file_enc


def replace_settings(settings: dict, converter: Callable[[Any], Any], key_filter: Callable[[Any], bool]) -> dict:
    return convert_setting(settings, converter, key_filter)


def convert_setting(setting: Any, converter: Callable[[Any], Any], key_filter: Callable[[Any], bool] = None) -> Any:
    """
    转换配置的值
    :param setting: 配置项
    :param converter: 值转换器
    :param key_filter: 键过滤器，即对哪些键进行转换
    """
    key_filter = (lambda x: True) if key_filter is None else key_filter
    if isinstance(setting, dict):
        return {
            k: convert_setting(v, converter, key_filter) if isinstance(v, dict) or key_filter(k) else v
            for k, v in setting.items()
        }
    elif isinstance(setting, list) or isinstance(setting, set):
        return [convert_setting(v, converter, key_filter) for v in setting]
    else:
        try:
            return converter(setting)
        except Exception as ex:
            log.exception('配置转换异常，setting=%s, err=%s', setting, str(ex))
            raise
