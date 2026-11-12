# 发布说明

## 版本规则

版本只在 `pyproject.toml` 的 `[project].version` 中维护。
采用 `MAJOR.MINOR.PATCH`：不兼容变更增加 MAJOR，新增兼容功能增加 MINOR，修复增加 PATCH。
预发布使用 PEP 440 格式，例如 `1.1.0rc1`，对应标签 `v1.1.0rc1`。
修改版本后执行 `uv lock`，同时更新 CHANGELOG。

每次上传都必须使用目标索引尚未使用的版本；已发布文件不能覆盖。

## 本地检查

在干净工作区执行：

```bash
uv sync --locked --all-extras
uv run --locked --all-extras pytest -q
uv build --out-dir dist
uvx twine check --strict dist/*
```

`dist` 应仅保留本次版本的一份 wheel 和源码包；新一轮构建前清理旧产物。
`uv build` 先构建源码包，再从源码包构建 wheel。

## 正式发布

1. 确认本地检查通过、版本和 CHANGELOG 已更新，且目标 PyPI 版本未占用。
2. 为待发布提交创建并推送版本标签，例如 `v1.0.0`。
3. 在 GitHub 创建并发布使用该标签的 Release，填写变更说明。
   仅推送标签不会发布到 PyPI。
4. 工作流检查标签与项目版本一致，然后构建 wheel、源码包并上传到 PyPI。
5. 如设置了 environment 审批，审核该次发布；确认 PyPI 文件和 README 正常。
6. 在全新环境执行 `pip install "oxy-py-sdk[all]==1.0.0"`，验证正式索引安装。

不要用删除/重建标签来覆盖已发布版本。发布失败时先检查目标索引是否已收到部分文件；
工作流不会静默跳过已存在文件。必要时发布新的修订版本。
