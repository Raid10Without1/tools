# PMR-171 Rigctl Bridge

> 将 PMR-171 电台的私有控制协议转换为标准 Hamlib `rigctl` 协议，支持在 JTDX、WSJT-X、Fldigi 等数字模式软件中使用。

---

## 🔧 特性 Features

- ✅ 支持 PMR-171 的串口协议（通过 USB CDC 串口）
- ✅ 提供 Windows `.exe` 可执行文件（无需安装 Python）
- ✅ 支持常用 rigctl 命令：设置频率、模式、PTT 控制
- ✅ 自动识别并选择串口
- ✅ 可与 Hamlib 客户端直接通信（如 JTDX）

---

## 📦 下载 Download

请在 [Releases](https://github.com/Raid10Without1/tools/releases/tag/hamlib) 页面下载最新版本的 `pmr171_rigctl_bridge.exe`。

---

## 🖥️ 使用方法

### 1. 准备

- 将 PMR-171 与电脑连接（USB）
- 确保 Windows 已识别设备（在设备管理器中应看到一个 **COM口**）

### 2. 运行桥接程序

- 双击运行 `pmr171_rigctl_bridge.exe`
- 终端将列出可用串口，输入编号以选择连接的设备

### 3. 配置 JTDX / WSJT-X / Fldigi

| 选项项     | 配置值                   |
|------------|--------------------------|
| Rig        | Hamlib NET rigctl        |
| Address    | 127.0.0.1                |
| Port       | 4532                     |
| PTT        | CAT                      |
| Mode       | None                     |
| Split      | Fake It / None           |

### 4. 配置音频设备

在 `Settings -> Audio` 中选择 PMR-171 的声卡设备。

---

## 📋 支持命令

目前支持以下 Hamlib `rigctl` 命令：

- `F<freq>`：设置频率（如 `F14074000`）
- `f`：返回伪造频率
- `M <mode> <width>`：设置模式（如 `M USB 2400`）
- `T1` / `T0`：PTT 开关
- `t`：返回当前 PTT 状态

---

## ⚠️ 注意事项

- 当前为 **Pre-release** 版本，仅实现基础功能；
- 频率读回、状态查询等命令尚未实现；
- 使用前请确保 PMR-171 设置为 `USB` 控制模式，非 `SDR` 模式；
- 模式切换与发射功率请使用电台本体操作或后续版本扩展。

---

## 📫 联系/反馈

如有问题、建议或功能请求，请通过 [Issues](https://github.com/你的用户名/你的仓库/issues) 提交。

---

## 📜 License
本项目遵循 [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.html) 许可证。你可以自由使用、修改和分发本代码，但所有衍生作品必须保持 GPLv3 兼容性，并提供源代码。


