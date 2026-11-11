# oxy-sdk

Python 通用工具库，提供 HTTP 请求、配置管理、加解密、日志和数据处理工具。
发行包名为 `oxy-sdk`，Python 导入包名为 `oxy`。需要 Python 3.15 或更高版本。

## 开发环境

在项目根目录使用 uv 安装项目及开发依赖：

```bash
uv sync --locked
uv run python -c "import oxy; print(oxy.__file__)"
```

## 可选依赖

数据处理模块 `oxy.utils.data._split` 和 `oxy.utils.data.cache` 需要 `excel` extra 中的 pandas。
企微机器人 SDK 通过 `wecom` extra 安装：

```bash
uv sync --locked --extra excel
uv sync --locked --extra wecom
# 安装全部可选依赖
uv sync --locked --all-extras
```

其他项目通过 `oxy-sdk[excel]` 或 `oxy-sdk[wecom]` 声明相应依赖。

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
