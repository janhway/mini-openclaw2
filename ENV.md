# CODEX_CON束规范（Python 项目 · 强制执行版）

> 本文件定义 Codex 在本仓库中 **必须遵守的运行与工程约束**
> 所有规则均为强制，除非明确标记为可选

---

# 1. 环境与运行约束

## 1.1 Python 环境管理

### 强制要求

* 必须使用工具

```
uv
```

* 严禁使用

```
conda
virtualenv
venv (原生命令)
poetry
pipenv
```

* Python 版本

```
3.12
```

* 所有虚拟环境与依赖必须由 `uv` 管理

---

## 1.2 虚拟环境创建与激活

### 创建（首次）

```
uv venv --python 3.12
```

默认生成：

```
.venv/
```

---

### 激活

#### macOS / Linux

```
source .venv/bin/activate
```

#### Windows PowerShell

```
.venv\Scripts\Activate.ps1
```

#### Windows cmd

```
.venv\Scripts\activate.bat
```

---

## 1.3 依赖管理

### 必须存在文件

```
requirements.in
requirements.lock
```

---

### 安装方式（唯一允许）

```
uv pip install -r requirements.lock
```

---

### 严禁行为

```
pip install xxx
pip install -r requirements.in
跳过 lock 文件安装
```

---

# 2. 网络代理约束

## 2.1 代理设置方式

### macOS / Linux

```
export http_proxy=http://127.0.0.1:7897
export https_proxy=http://127.0.0.1:7897
```

> 该命令由用户提供
> Codex 不负责实现

---

### Windows PowerShell

```
$Env:http_proxy="http://127.0.0.1:7897"
$Env:https_proxy="http://127.0.0.1:7897"
```

---

### Windows cmd

```
set http_proxy=http://127.0.0.1:7897
set https_proxy=http://127.0.0.1:7897
```

---

## 2.2 强制规则

以下操作 **必须在代理设置后执行**

```
uv venv
uv pip install
```

---

## 2.3 禁止行为

* 在代码中写死代理
* 自定义代理配置文件
* 修改代理端口

必须只使用环境变量：

```
http_proxy
https_proxy
```

---

# 3. 临时文件目录规范

## 3.1 目录位置（强制）

所有临时文件必须位于

```
./tmp/
```

---

## 3.2 程序行为

### 启动时

```
若 ./tmp 不存在 → 自动创建
```

### 退出时

```
不清理
```

（用于调试与排障）

---

## 3.3 严禁行为

使用系统临时目录

```
/tmp
/var/tmp
%TEMP%
tempfile.gettempdir()
```

---

# 4. 日志与输出规则

## 4.1 标准输出

```
stdout 只允许业务输出
```

---

## 4.2 日志

必须使用

```
logging 模块
```

禁止：

```
print 调试日志
stderr 混写业务信息
```

---

# 5. Codex 红线（违反即视为失败）

以下行为完全禁止：

* 使用 conda / virtualenv / poetry
* 不使用 uv 管理依赖
* 代码中写死代理地址
* 使用系统临时目录
* stdout 混入日志
* 直接 pip 安装依赖
* 绕过 lock 文件

---

# 6. Codex 执行优先级

当出现冲突时，按以下顺序执行：

1️⃣ 本文件
2️⃣ 仓库 README
3️⃣ 用户指令
4️⃣ Codex 默认行为

---

# 7. Codex 执行目标

生成的代码必须满足：

* 可在全新机器一键运行
* 可复现依赖
* 无环境漂移
* 无隐式网络假设
* 临时文件可追踪
* 日志行为可控

---
