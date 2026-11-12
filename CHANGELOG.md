# Changelog

## 1.0.0 - 2026-11-12

- 首个正式版本，发行包名为 `oxy-py-sdk`，Python 导入包名为 `oxy`。
- 支持 Python 3.15 及以上版本，提供类型标记 `py.typed`。
- 提供日志、集合、日期时间、UUID、路径及 MD5/SHA256 等基础工具。
- 提供 `codec` 可选依赖，支持 DES、RSA 加解密及签名。
- 提供 `data` 可选依赖，支持 DataFrame 拆分及 Excel 文件缓存，包含 pandas、openpyxl。
- 提供 `http` 可选依赖，支持异步 HTTP 请求、请求装饰器及响应处理。
- 提供 `setting` 可选依赖，支持 YAML 配置读写；搭配 `codec` 支持配置文件加解密。
- 支持组合安装可选依赖，或通过 `oxy-py-sdk[all]` 安装全部功能依赖。
- 使用 GitHub Release 触发构建，通过 Trusted Publishing 发布到 PyPI。
- 补充安装示例、发布说明、项目元数据及 MIT 许可证声明。
