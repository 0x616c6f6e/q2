# APP 分辨率与资源适配

APP manifest 增加可选字符串数组（最多 16 项，不重复）：

```json
"supported_resolutions": ["368x448", "448x368", "410x502", "502x410"]
```

格式为 **宽x高**，小写 ASCII `x`，像素值 64–1024，无空格、单位和前导零。数组提供适配声明，不自动缩放 UI，也不阻止其他分辨率启动；APP 应为未知尺寸提供自适应布局。省略字段的旧 APP 继续兼容；填写时不能为空。当前出厂 APP 声明这四种目标尺寸，但声明本身不代表每页均已完成视觉验收。

## Lua 获取设备尺寸

需要申请 `display.ui` 能力：

```lua
local q = require("q2")
local resolution, err = q.ui.resolution()  -- 例如 "502x410"
if not resolution then return end         -- 调用失败时处理错误
local w, h = assert(q.ui.width()), assert(q.ui.height())

-- 整屏尺寸选择 UI 配置；控件仍须放在实际 APP 可用区域内。
local profiles = {
    ["502x410"] = {margin = 24, icon_size = 144},
    ["410x502"] = {margin = 20, icon_size = 144},
    ["448x368"] = {margin = 20, icon_size = 128},
    ["368x448"] = {margin = 16, icon_size = 128},
}
local profile = profiles[resolution] or {margin = 12, icon_size = math.min(128, w - 24, h - 24)}
```

`q.ui.resolution()` 返回配置方向下的**完整逻辑屏幕**，不受状态栏、屏保、滚动或当前系统 UI 层影响。没有参数；错误沿用 `nil, {code, number}` 约定。`q.ui.width()/height()` 保持现有内容区语义，不能用扣除状态栏的高度拼出资源目录名。收到 `ui.resize` 后重新取得内容区大小并布局。API 不改变屏幕方向或分辨率。

## 图标目录和选择规则

以 Music APP 为例：

```text
assets/
  icon.png                 # 通用回退图标；manifest.icon 仍指向这里
  368x448/icon.png
  448x368/icon.png
  410x502/icon.png
  502x410/icon.png
```

x86 启动 APP 时优先读 `assets/<整屏分辨率>/<文件名>.png`，不存在才读根目录同名 PNG。Lua 始终使用 `q.ui.image(x, y, "assets/icon.png", size)`，不用拼目录。Homepage 的 catalog 图标同样遵循此规则。匹配目录内独有的 PNG 也可用平铺逻辑名读取；其余尺寸目录不会加载，不占用运行时图片配额。文件存在但损坏、超限或为重解析点时报告错误，不悄悄回退掩盖问题。

各目录现在从原始 SVG 生成实际尺寸 PNG：368×448、448×368 使用 128×128 图标；410×502、502×410 使用 144×144 图标。Homepage 使用同一份配置以原生尺寸显示；状态栏开关不会再改变这四组图标大小，极小内容区仍有边界限制。无专用图标的 APP 使用默认画稿。根目录保留原 PNG 供其他屏幕回退。

尺寸配置位于 `app/artwork/icon-profiles.json`，在 app 目录执行 `npm install && npm run icons` 可同时重新生成图标和 Homepage 的 Lua 尺寸表。生成工具需要 Node.js 和 sharp 0.35.5；普通编译/打包直接使用仓库中的 PNG，不要求 Node。

资源包包含全部尺寸版本，现有每包 32 个文件/1 MiB、单个资源 256 KiB 及运行时 PNG 最大 512×512 的限制保持不变。分辨率目录不增加 Lua 文件系统权限。

## 平台边界

Kernel 新增 `q2_lvgl_resolution(display, &width, &height)`，在 boot 前即可调用；它只返回注册的像素后端尺寸。平台负责选取资源字节，再通过原有 `q2_lvgl_register_png` 绑定到 APP UUID 和稳定逻辑名。

ESP32-S3 接入的是同一份 Kernel，具备新的 Lua API；目前其启动程序仍是内嵌 `display_demo.lua`，尚无出厂 APP 包/目录资源加载流程。本次实现自动目录选择的宿主为 x86，不能将其视为 ESP32 文件系统加载器已完成。

manifest 格式和 Lua API 版本仍为 2，旧 manifest 可继续解析；`q2_manifest_t` 增加字段，C 消费者必须与 Kernel 同步重新编译。
