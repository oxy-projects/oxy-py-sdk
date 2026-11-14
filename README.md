# oxy-py-sdk

Python 通用工具库，提供 HTTP 请求、配置管理、加解密、日志和数据处理工具。
发行包名为 `oxy-py-sdk`，Python 导入包名为 `oxy`。支持 Python 3.15 及以上版本。

## 按需安装

基础包包含日志、集合、通用语言工具及 MD5/SHA256，无第三方运行时依赖。
未安装 colorama 时日志使用无颜色输出；安装 `[all]` 会同时安装 colorama，启用彩色日志。
其他功能按需安装：

```bash
pip install oxy-py-sdk
pip install "oxy-py-sdk[codec]"        # DES、RSA、签名等加解密
pip install "oxy-py-sdk[data]"         # DataFrame、Excel 读写及缓存
pip install "oxy-py-sdk[http]"         # HTTP 请求
pip install "oxy-py-sdk[setting]"      # YAML 配置读写
pip install "oxy-py-sdk[http,setting]" # 自由组合
pip install "oxy-py-sdk[setting,codec]" # 配置文件加解密
pip install "oxy-py-sdk[all]"          # 全部功能依赖，含彩色日志
```

| 分组 | 依赖 | 模块 |
| --- | --- | --- |
| codec | pycryptodome、cryptography | `oxy.utils.codec` |
| data | pandas、openpyxl | `oxy.utils.data`、`oxy.utils.data.cache` |
| http | httpx（含 HTTP/2）、pydantic | `oxy.utils.http` |
| setting | pyyaml | `oxy.utils.setting` |

`setting` 的字典读取和转换不需要 YAML 依赖；配置文件加解密需要同时安装 `setting` 和 `codec`。
MD5/SHA256 使用标准库，无需安装 `codec`。DES 和 MD5 主要用于兼容现有协议。

## 使用示例

基础工具：

```python
from oxy.utils.lang import gen_uuid_str
from oxy.utils.lang.collection import distinct

print(gen_uuid_str())
print(distinct([1, 1, 2]))  # [1, 2]
```

安装 `oxy-py-sdk[http]` 后：

```python
import asyncio
from oxy.utils.http import api

@api.get("https://httpbin.org/get")
async def fetch():
    return {"q": "python"}

result = asyncio.run(fetch())
```

HTTP 日志通过装饰器的 `log` 参数控制，需由应用配置日志处理器并启用 DEBUG 级别：

```python
from oxy.utils.http import HttpLogs

@api.get("https://httpbin.org/get", log=HttpLogs.ALL)
async def fetch_with_logs():
    return {"q": "python"}
```

`HttpLogs.DEFAULT`（默认值）仅记录请求，`HttpLogs.ALL` 同时记录请求和成功响应，
`HttpLogs.NONE` 关闭这两类日志。HTTP 状态错误仍记录 ERROR 日志。

安装 `oxy-py-sdk[setting]` 后：

```python
from pathlib import Path
from oxy.utils.setting import dump_yaml, load_yaml

dump_yaml({"project": {"name": "demo"}}, Path("settings.yaml"))
settings = load_yaml(Path("settings.yaml"))
```

## 开发与验证

```bash
uv sync --locked --all-extras
uv run --locked --all-extras python -m pytest -q
uv build
uvx twine check --strict dist/*
```

测试不需要真实外部服务，HTTP 请求使用模拟传输。

只安装指定功能：

```bash
uv sync --locked --extra http --extra setting
```

修改依赖后运行 `uv lock` 并提交 `pyproject.toml` 与 `uv.lock`。

## 发布

完整配置及操作步骤见 [发布说明](https://github.com/oxy-projects/oxy-py-sdk/main/RELEASING.md)，版本记录见 [CHANGELOG](https://github.com/oxy-projects/oxy-py-sdk/blob/main/CHANGELOG.md)。
发布 GitHub Release 后自动构建并发布到 PyPI。
版本来源为 `pyproject.toml`，Release 标签必须是 `v` 加版本号，例如 `v1.0.0`。

## 许可证

[MIT](https://github.com/oxy-projects/oxy-py-sdk/blob/main/LICENSE)，Copyright (c) 2026 wangjz。
