# 创作工作室

> 喜剧的内核是悲剧，但悲剧说出来要让人笑。笑完之后，心里有光。

基于 **Claude Code Agent 架构** 的短剧创作系统。多 Agent 协同审查，覆盖创作质量、读者体验、平台合规全链路。

---

## 架构设计

```
                          ┌──────────────────────┐
                          │    Showrunner (你)    │
                          │   创意决策 · 文案修改  │
                          └──────────┬───────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
     ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
     │  Phase 审查层    │   │  单集审查层 (×5)  │   │  专项审查层 (×2) │
     │                 │   │                 │   │                 │
     │ hook-checker    │   │ character       │   │ platform        │
     │ (概念/开场)     │   │ comedy          │   │ (平台合规)       │
     │                 │   │ structure       │   │                 │
     │                 │   │ continuity      │   │                 │
     │                 │   │ reader-avatar   │   │                 │
     └─────────────────┘   └─────────────────┘   └─────────────────┘
```

### Agent 矩阵

| Agent | 文件 | 模型 | 职责 |
|-------|------|------|------|
| **character-checker** | `.claude/agents/character-checker.md` | `opus` | 角色一致性：每句台词/行动是否符合角色圣经 |
| **comedy-checker** | `.claude/agents/comedy-checker.md` | `sonnet` | 笑点审查：密度、新鲜度、类型分布、喜剧真空区 |
| **structure-checker** | `.claude/agents/structure-checker.md` | `haiku` | 结构审查：字数、反转位置、情绪弧线、场景数 |
| **continuity-checker** | `.claude/agents/continuity-checker.md` | `opus` | 连贯性追踪：跨集矛盾、伏笔推进、知识状态 |
| **reader-avatar** | `.claude/agents/reader-avatar.md` | `sonnet` | 读者视角：目标受众的真实感受、共鸣点、分享意愿 |
| **platform-checker** | `.claude/agents/platform-checker.md` | `opus` | 平台合规：六大红线、隐性红线、差异化审核尺度 |
| **hook-checker** | `.claude/agents/hook-checker.md` | `opus` | 开场钩子：前3秒/前30秒留存、类型误读、算法风险 |
| **writers-room** | `.claude/agents/writers-room.md` | `opus` | 作家室：并行 Pitch 三个方向（荒诞/走心/配角破局） |

### 模型分工原则

```
深度理解（角色、连贯、合规、钩子）→ opus
平衡分析（笑点、读者）           → sonnet
机械检查（字数、比例、位置）     → haiku
```

---

## 在编项目

| 项目 | 类型 | 格式 | 状态 |
|------|------|------|------|
| 《骑手女王》 | 都市无厘头喜剧 | 短剧 24 集 | 第一幕完成（8/24），第二幕完成（16/24） |
| 《骑手女王 v2》 | 都市轻喜剧 | 短剧 24 集 | Phase 1 概念阶段 |
| 《后妈》 | 黑色幽默 / 家庭剧情 | 短剧 20 集 | 第一幕完成（8/20） |
| 《山海食单》 | 奇幻美食 / 公路冒险 | 短剧 24 集 | 第一幕完成（8/24） |
| 《丧尸区业主委员会》 | 末世喜剧 / 群像 | 短剧 24 集 | 第一幕完成（8/24） |

---

## 工作流程

### 新项目开发（五阶段）

```
Phase 1: 概念提案
  │ 输出：concept.md
  │ 审查：reader-avatar + platform-checker + hook-checker
  │ 通过标准：三个 agent 全 pass
  ▼
Phase 2: 角色圣经
  │ 输出：characters.md
  │ 审查：character-checker + platform-checker
  │ 通过标准：两个 agent 全 pass
  ▼
Phase 3: 分集大纲
  │ 输出：outline.md
  │ 审查：structure-checker + continuity-checker + platform-checker
  │ 通过标准：三个 agent 全 pass
  ▼
Phase 4: 第 1 集剧本
  │ 输出：episodes/01-xxx.md
  │ 审查：全部 7 个 agent
  │ 通过标准：无 FAIL，WARN ≤ 2
  ▼
Phase 5: 逐集写作
    每集：写 → 全审查 → 修改 → 审查通过 → 下一集
    每 8 集：单元回顾 + continuity-log 更新
```

### 单集审查（五维 × 专项）

```
编剧完成第 N 集
  │
  ├─ character-checker ──── 角色一致性 ──── pass/warn/fail
  ├─ comedy-checker ─────── 笑点审查 ────── pass/warn/fail
  ├─ structure-checker ──── 结构审查 ────── pass/warn/fail
  ├─ continuity-checker ─── 连贯性追踪 ──── pass/warn/fail
  ├─ reader-avatar ──────── 读者视角 ────── pass/warn/fail
  ├─ hook-checker ───────── 开场钩子 ────── pass/warn/fail
  └─ platform-checker ───── 平台合规 ────── pass/risk/high_risk/fail
                │
                ▼
        Showrunner 综合判定
        (修改 → 复审查 → 通过 → 下一集)
```

---

## 安装和使用

### 前置条件

- [Claude Code](https://claude.ai/code) CLI 或 IDE 扩展
- Git

### 初始化

```bash
# 克隆仓库
git clone <repo-url> xiaoshuo
cd xiaoshuo

# 确认 Agent 定义就绪
ls .claude/agents/
# 应该看到 8 个 agent 文件 + 2 个 schema 文件

# 确认 Claude Code 能识别项目配置
cat CLAUDE.md
```

### 使用 Agent

所有 Agent 通过 `Agent` 工具调用，使用 `isolation: "worktree"` 隔离执行：

**单 Agent 调用**
```
Agent({
  description: "Character check Ep1",
  subagent_type: "claude",
  isolation: "worktree",
  prompt: "读取 projects/骑手女王/characters.md 和 episodes/01-xxx.md，执行角色一致性审查..."
})
```

**并行审查（5-7 个 Agent 同时运行）**
```
// 每集全维度审查，所有 Agent 并行启动
Agent(character-checker, Ep N)
Agent(comedy-checker, Ep N)
Agent(structure-checker, Ep N)
Agent(continuity-checker, Ep N)
Agent(reader-avatar, Ep N)
Agent(platform-checker, Ep N)  // 整季审查时可合并
Agent(hook-checker, Ep N)      // Ep1 重点审查
```

**审查结果处理**
```
每个 Agent 返回 JSON（```json 代码块）
  → Showrunner 汇总所有审查结果
  → 标记 FAIL/WARN 项
  → 编剧根据 modification_checklist 修改
  → 复审查通过
  → 更新 continuity-log.md
```

### 平台合规审查

```bash
# 全项目合规审查（需先准备审核规范文件）
# 审核规范路径: resources/txt/最新平台审核规范(1)(1).txt
Agent(platform-checker, 项目名)
```

### 作家室（卡住时的创意突破）

```
让三个 Agent 并行 Pitch：
  Agent A: 更荒谬的方向（错位梗、反差、出乎意料的道具）
  Agent B: 更走心的方向（脆弱时刻、安静瞬间、不说出口的情绪）
  Agent C: 配角破局（关键配角在关键时刻说关键的话）
```

---

## 项目结构

```
.
├── CLAUDE.md                          # 项目配置（Agent 自动加载）
├── README.md                          # 本文件
├── AGENTS.md                          # Agent 架构详细文档
├── .claude/
│   ├── settings.json                  # 项目级配置
│   ├── agents/                        # Agent 定义文件
│   │   ├── character-checker.md
│   │   ├── comedy-checker.md
│   │   ├── structure-checker.md
│   │   ├── continuity-checker.md
│   │   ├── reader-avatar.md
│   │   ├── platform-checker.md
│   │   ├── hook-checker.md
│   │   ├── writers-room.md
│   │   ├── continuity-schema.json     # 连贯性数据 schema
│   │   └── review-schema.json         # 审查输出 schema
│   └── worktrees/                     # Agent 隔离工作区
├── projects/
│   ├── 骑手女王/
│   │   ├── characters.md
│   │   ├── outline.md
│   │   ├── notes.md
│   │   ├── continuity-log.md
│   │   └── episodes/
│   ├── 骑手女王v2/                    # 新架构重写版
│   │   ├── concept.md
│   │   ├── characters.md              # (Phase 2)
│   │   ├── outline.md                 # (Phase 3)
│   │   └── episodes/                  # (Phase 4+)
│   ├── 后妈/
│   ├── 山海食单/
│   └── 丧尸区业主委员会/
└── resources/
    └── txt/
        └── 最新平台审核规范(1)(1).txt  # 抖音 2026.5 审核标准
```

---

## 审查维度速查

| 维度 | 关键指标 | FAIL 条件 |
|------|---------|----------|
| 🎭 角色 | 台词/行动符合设定，弧线阶段正确 | 角色行为崩坏、口头禅连续 3 集缺席 |
| 😂 笑点 | 密度≥1/500字，性格驱动，无重复梗 | 连续 3 集同梗、网络流行语依赖 |
| 📐 结构 | 1500-2800字，冷开场≤150字，反转≥1 | 字数<1000、无反转、结尾情绪负面 |
| 🔗 连贯 | 时间线、知识状态、伏笔推进 | 前后矛盾、伏笔遗忘≥3集 |
| 👤 读者 | 情绪旅程、共鸣点、分享意愿 | 读者"出戏"、"感觉被操控" |
| 🪝 钩子 | 前3秒钩子强度≥3，无类型误读 | 强度≤2、触发≥2种误读风险 |
| 🛡️ 合规 | 六大红线、隐性红线、题材分级 | 触发绝对禁止项、隐性红线 |

---

## 通用剧本格式

```
第 X 集：[集标题]

[场景：地点 - 时间]
[动作描述，用方括号包裹，简洁有力]
角色名：对白内容
角色名：(内心 OS)
---
[场景切换]
```

- 每集 1500-2800 字
- 每集 1-2 个主场景
- 冷开场 150 字内出钩子
- 每集结尾留 hook 连接下一集

---

## 创作原则

- **人物 > 情节**：角色驱动的故事，读者笑/哭是因为认识这个角色
- **细节即代入感**：真实的行业细节让荒诞有根
- **不教育、不鸡汤**：让读者自己感受到力量
- **女性视角**：女性互助和羁绊是核心主线，爱情线是副线
- **中国质感**：故事发生在中国真实的街道、小区、写字楼里
- **合规优先**：概念阶段即考虑平台审核，而非完稿后补救
