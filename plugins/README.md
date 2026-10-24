# ChatGPT 插件分发目录

这里维护两个插件的打包入口，Skill 源码仍只维护在仓库根目录的 `skills/`。
不手工复制通用规范到多个插件，不包含个人邮箱、私人应用绑定或凭证。

| 插件 | 内容 | 应用依赖 |
| --- | --- | --- |
| development-standards（开发规范助手） | develop-software、prompt-authoring-spec、skill-authoring-spec | 无 |
| nexum-development（Nexum 开发助手） | nexum-chatgpt-development | 使用者自己的 Nexum 连接；默认包不绑定应用 |

两者可同时使用，不重复分发通用 Skill。Nexum 场景的软件开发需要实际读取通用插件中的
develop-software 及适用资源；仅连接检查不要求通用开发流程。名称出现不等于资源已加载。
插件不提供额外权限，也不自动创建 Work/Codex 任务。

## 构建

在仓库根目录使用 Python 3.10+（构建器只用标准库）：

```sh
python3 plugins/build.py all
python3 -m unittest discover -s tests -p 'test_plugin_distribution.py' -v
```

输出在被 Git 忽略的 `plugins/dist/`，ZIP 内含根清单与完整的 Skill 资源，保留源许可。
这是可构建源码目录，不要把清单所在子目录单独压缩安装，也不要把整个仓库作为一个插件包。

构建时移除两份可选 UI 默认提示中的 Codex 专属调用文案；Nexum 包增加资源位置与跨插件
依赖说明。三个通用 Skill 的正文不改写。打包版本由各目录的 plugin.json 管理；
源内容变化后发布者需要审核并更新版本。构建不会自动上传、发布 Release 或更新已安装插件。

## 使用与分发

- 通用 ZIP：由接收者使用其宿主支持的插件创建/导入方式安装。GitHub 链接不是保证可用的
  ChatGPT 一键安装入口，个人账户导入和跨账户分发仍需实测。
- Nexum ZIP：接收者自行连接其有权访问的 Nexum 应用。没有应用绑定的模板不自动提供工具。
- 需要私人账户绑定时，可在核实实际 app ID 后运行：

```sh
python3 plugins/build.py nexum-development --nexum-app-id VERIFIED_APP_ID
```

把 VERIFIED_APP_ID 替换为实际 app ID，不能用 plugin ID、Agent ID 或 OAuth client ID。
该参数只写入引用，不创建 OAuth Grant；生成的 `-personal.zip` 不作为通用分发包。
不得把应用凭证写入任何参数或插件文件。

同工作区分享受其分享权限控制。公开插件目录提交是独立流程，本目录没有完成公开审核，
也不承诺 GitHub 内容会自动同步到个人已安装插件。

## 许可与验收

各 Skill 原有许可保持不变。develop-software 当前为 Private Use License；
本目录的存在不授予第三方再分发许可。对外分发前由权利人明确授权范围。

构建器测试检查 3+1 分包、资源闭包、重复构建、应用绑定隔离和错误输入。
这不等于 ChatGPT/Codex 自动选择、真实 Nexum 调用或缺失依赖行为已通过端到端验收。
