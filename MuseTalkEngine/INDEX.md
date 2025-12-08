# MuseTalk 实时推理系统 - 文件索引

## 📂 项目结构

```
MuseTalkEngine/
├── 🎯 核心文件
│   ├── preprocess_assets.py           # 离线预处理：提取人脸坐标
│   ├── main_realtime.py               # 实时推理服务：FastAPI + FP16
│   └── requirements_realtime.txt      # Python 依赖清单
│
├── 🔧 工具脚本
│   ├── start_realtime_service.sh      # 一键启动脚本 (可执行)
│   └── test_realtime_system.py        # 自动化测试脚本
│
├── 📝 配置文件
│   └── .env.example                   # 环境变量配置模板
│
├── 📚 文档
│   ├── README_REALTIME.md             # 详细使用文档 (主文档)
│   ├── QUICKSTART.md                  # 快速开始指南
│   ├── IMPLEMENTATION_SUMMARY.md       # 实现总结与技术架构
│   └── INDEX.md                       # 本文件：文件索引
│
├── 📂 数据目录 (需创建)
│   ├── data/
│   │   ├── video/                     # 存放原始视频
│   │   │   └── idle.mp4               # 默认视频
│   │   └── preprocessed/              # 存放预处理结果
│   │       ├── idle_bbox.pkl          # 人脸边界框 (Pickle)
│   │       └── idle_bbox.json         # 人脸边界框 (JSON)
│   └── temp/                          # 临时文件
│
└── 🗂️ 原有文件 (项目自带)
    ├── core/                          # 核心模块
    ├── offline/                       # 离线推理
    ├── streaming/                     # 流式处理
    └── main.py                        # 原有主入口
```

---

## 📋 文件清单

### 核心实现 (2个)

| 文件名 | 行数 | 说明 | 优先级 |
|--------|------|------|--------|
| `preprocess_assets.py` | ~350 | 视频预处理脚本 | ⭐⭐⭐ 必读 |
| `main_realtime.py` | ~600 | 实时推理服务 | ⭐⭐⭐ 必读 |

### 配置文件 (2个)

| 文件名 | 行数 | 说明 | 优先级 |
|--------|------|------|--------|
| `requirements_realtime.txt` | ~50 | Python 依赖 | ⭐⭐⭐ |
| `.env.example` | ~90 | 环境变量模板 | ⭐⭐ |

### 工具脚本 (2个)

| 文件名 | 行数 | 说明 | 优先级 |
|--------|------|------|--------|
| `start_realtime_service.sh` | ~120 | 启动脚本 | ⭐⭐⭐ 推荐 |
| `test_realtime_system.py` | ~200 | 测试脚本 | ⭐⭐ |

### 文档 (4个)

| 文件名 | 行数 | 说明 | 优先级 |
|--------|------|------|--------|
| `README_REALTIME.md` | ~600 | 完整文档 | ⭐⭐⭐ 主文档 |
| `QUICKSTART.md` | ~250 | 快速指南 | ⭐⭐⭐ 入门必读 |
| `IMPLEMENTATION_SUMMARY.md` | ~550 | 技术总结 | ⭐⭐ 架构了解 |
| `INDEX.md` | ~150 | 本文件 | ⭐ 索引 |

---

## 🚀 快速开始（3步）

### 第1步：预处理视频
```bash
python preprocess_assets.py --video ./data/video/idle.mp4
```

### 第2步：启动服务
```bash
./start_realtime_service.sh
```

### 第3步：测试接口
```bash
curl http://localhost:8000/
```

---

## 📖 阅读顺序

### 新手推荐
1. **QUICKSTART.md** - 快速了解系统
2. **start_realtime_service.sh** - 一键启动
3. **README_REALTIME.md** - 深入学习

### 开发者推荐
1. **IMPLEMENTATION_SUMMARY.md** - 技术架构
2. **preprocess_assets.py** - 预处理实现
3. **main_realtime.py** - 推理服务实现
4. **README_REALTIME.md** - API 文档

### 运维推荐
1. **.env.example** - 配置模板
2. **start_realtime_service.sh** - 启动流程
3. **test_realtime_system.py** - 测试验证
4. **README_REALTIME.md** - 故障排查

---

## 🎯 文件功能速查

### 我想...

#### 启动服务
→ **start_realtime_service.sh**

#### 预处理新视频
→ **preprocess_assets.py**

#### 了解 API 接口
→ **README_REALTIME.md** (API 路由章节)

#### 调整配置
→ **.env.example**

#### 集成到 .NET
→ **README_REALTIME.md** (C# 集成示例)

#### 查看性能指标
→ **IMPLEMENTATION_SUMMARY.md** (性能基准章节)

#### 测试系统
→ **test_realtime_system.py**

#### 故障排查
→ **README_REALTIME.md** (常见问题章节)

---

## 📊 代码统计

### 总览
- **Python 文件**: 4 个
- **Shell 脚本**: 1 个
- **配置文件**: 2 个
- **文档文件**: 4 个
- **总代码量**: ~1800 行
- **总文档量**: ~1600 行

### 代码分布
```
preprocess_assets.py       350 行  (20%)
main_realtime.py           600 行  (33%)
test_realtime_system.py    200 行  (11%)
start_realtime_service.sh  120 行  (7%)
其他配置                    130 行  (7%)
文档                       1600 行 (88%)
```

---

## 🔗 依赖关系

```
.env.example
    ↓
start_realtime_service.sh
    ├─→ preprocess_assets.py
    │       ↓
    │   idle_bbox.pkl
    │       ↓
    └─→ main_realtime.py
            ↓
        FastAPI 服务
            ↓
        HTTP API
```

---

## 🏷️ 标签系统

### 优先级
- ⭐⭐⭐ 必读/必用
- ⭐⭐ 推荐阅读
- ⭐ 可选参考

### 文件类型
- 🎯 核心实现
- 🔧 工具脚本
- 📝 配置文件
- 📚 文档
- 📂 目录

### 阶段标识
- 🔨 开发阶段
- 🧪 测试阶段
- 🚀 部署阶段
- 📊 监控阶段

---

## 🔍 文件搜索

### 按关键词

| 关键词 | 相关文件 |
|--------|----------|
| 预处理 | preprocess_assets.py, README_REALTIME.md |
| 推理 | main_realtime.py, IMPLEMENTATION_SUMMARY.md |
| 配置 | .env.example, README_REALTIME.md |
| 启动 | start_realtime_service.sh, QUICKSTART.md |
| 测试 | test_realtime_system.py, README_REALTIME.md |
| API | main_realtime.py, README_REALTIME.md |
| 优化 | main_realtime.py, IMPLEMENTATION_SUMMARY.md |
| 集成 | README_REALTIME.md, QUICKSTART.md |

### 按功能模块

| 模块 | 相关文件 |
|------|----------|
| 人脸检测 | preprocess_assets.py |
| 模型加载 | main_realtime.py |
| 音频处理 | main_realtime.py |
| 推理管线 | main_realtime.py |
| 视频流 | main_realtime.py |
| 资产管理 | main_realtime.py |

---

## 📦 打包清单

### 最小部署包
```
必选文件：
✅ preprocess_assets.py
✅ main_realtime.py
✅ requirements_realtime.txt
✅ start_realtime_service.sh
✅ README_REALTIME.md
```

### 完整部署包
```
核心：
✅ preprocess_assets.py
✅ main_realtime.py
✅ requirements_realtime.txt

工具：
✅ start_realtime_service.sh
✅ test_realtime_system.py

配置：
✅ .env.example

文档：
✅ README_REALTIME.md
✅ QUICKSTART.md
✅ IMPLEMENTATION_SUMMARY.md
✅ INDEX.md
```

---

## 🆘 帮助中心

### 问题 1: 找不到文件
→ 检查本文件索引，确认文件名和路径

### 问题 2: 不知道从哪开始
→ 阅读 **QUICKSTART.md**

### 问题 3: 代码看不懂
→ 先读 **IMPLEMENTATION_SUMMARY.md**，再看代码

### 问题 4: 服务启动失败
→ 查看 **start_realtime_service.sh** 日志输出

### 问题 5: API 调用失败
→ 参考 **README_REALTIME.md** API 章节

---

## 📞 技术支持

### 文档相关
- 主文档：README_REALTIME.md
- 快速开始：QUICKSTART.md
- 架构说明：IMPLEMENTATION_SUMMARY.md

### 代码相关
- 预处理：preprocess_assets.py (行内注释)
- 推理服务：main_realtime.py (行内注释)

### 配置相关
- 环境变量：.env.example (详细说明)

---

## 🎓 学习路径

### 入门级（0-1天）
1. QUICKSTART.md
2. start_realtime_service.sh
3. 运行测试

### 进阶级（1-3天）
1. README_REALTIME.md
2. preprocess_assets.py (阅读代码)
3. main_realtime.py (阅读代码)
4. 调整配置和参数

### 专家级（3-7天）
1. IMPLEMENTATION_SUMMARY.md (深入理解)
2. 修改和优化代码
3. 集成到生产系统
4. 性能调优

---

## 📅 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2025-12-08 | 初始版本，完整功能 |

---

## ✅ 检查清单

### 部署前
- [ ] 阅读 QUICKSTART.md
- [ ] 复制 .env.example 为 .env
- [ ] 安装依赖 (requirements_realtime.txt)
- [ ] 准备视频文件
- [ ] 运行预处理

### 部署时
- [ ] 执行 start_realtime_service.sh
- [ ] 验证服务启动
- [ ] 测试健康检查接口
- [ ] 运行测试脚本

### 部署后
- [ ] 监控日志
- [ ] 测试 API 接口
- [ ] 验证性能指标
- [ ] 配置自动重启

---

**文件总数**: 11 个  
**代码总量**: ~1800 行  
**文档总量**: ~1600 行  
**总计**: ~3400 行

---

**最后更新**: 2025-12-08  
**维护者**: 数字人后端团队  
**硬件**: 2x NVIDIA RTX 4090D (24GB VRAM)

---

**快速链接**:
- [快速开始](./QUICKSTART.md)
- [完整文档](./README_REALTIME.md)
- [技术架构](./IMPLEMENTATION_SUMMARY.md)
- [配置模板](./.env.example)

---

**祝使用愉快！🚀**
