# oxy-sdk

Python 通用工具库，提供 HTTP 请求、配置管理、加解密、日志和数据处理工具。
发行包名为 `oxy-sdk`，Python 导入包名为 `oxy`。需要 Python 3.15 或更高版本。

## 按需安装

基础安装不引入第三方运行时依赖，可使用 `oxy.utils.lang`、集合工具及 MD5/SHA256：

```bash
pip install oxy-sdk
pip install "oxy-sdk[codec]"    # DES、RSA、签名等加解密
pip install "oxy-sdk[data]"     # DataFrame、Excel 读写及缓存
pip install "oxy-sdk[http]"     # HTTP 请求
pip install "oxy-sdk[setting]"  # YAML 配置读写
pip install "oxy-sdk[http,setting]"  # 组合安装
pip install "oxy-sdk[setting,codec]" # 配置文件加解密
pip install "oxy-sdk[all]"      # 全部功能，含 wecom
```

`setting` 的字典读取、转换仅使用标准库；YAML 读写需要 `setting`，
配置文件加解密还需要 `codec`。
`excel` 保留为 `data` 的兼容别名，`wecom` 继续提供企微机器人 SDK。
日志在未安装 colorama 时使用无颜色输出。

## 开发环境

```bash
uv sync --locked --all-extras
uv run --all-extras python -c "import oxy; print(oxy.__file__)"
# 只安装指定功能
uv sync --locked --extra http --extra setting
```

## 测试与构建

```bash
uv run --all-extras pytest
uv build
```

部分测试依赖本地配置或外部服务，运行前请检查 `tests/config.py` 和对应测试文件。

## 项目结构

```text
src/oxy/          # 可发布的 Python 包
tests/           # 测试及资源文件
pyproject.toml   # 项目元数据、依赖和构建配置
uv.lock          # uv 管理的依赖锁文件，提交到版本控制
.python-version  # 开发环境 Python 版本
```

修改依赖后执行 `uv lock`，并提交更新后的 `pyproject.toml` 和 `uv.lock`。
