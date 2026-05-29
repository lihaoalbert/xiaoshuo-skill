# Agent 架构文档

## 系统设计

本项目的 Agent 系统是一个**多模型协同的短剧创作审查流水线**。8 个专用 Agent 各自负责一个审查维度，使用不同的大模型（根据任务对深度理解 vs 模式识别的需求分配），通过隔离的 git worktree 并行执行。

### 设计原则

1. **单一职责**：每个 Agent 只审一个维度。不在一个 Agent 里塞五个维度——拆分后可以并行、可以独立迭代、可以用最适合该维度的模型。
2. **模型匹配**：深度理解型任务用 Opus（角色弧线、跨集连贯性、平台法律条款解读），模式识别型用 Haiku/Sonnet（字数、比例、笑话密度）。
3. **隔离执行**：所有 Agent 跑在 git worktree 中，互不干扰。可并行启动，无竞态问题。
4. **结构化输出**：所有 Agent 统一输出 JSON，`verdict` 字段为 `pass|pass_with_warnings|fail`（平台合规用四级），可被程序化消费。
5. **先亮优点，再找问题**：每个 Agent 被要求先找出值得保留的元素，再标记问题。确保反馈是建设性而非破坏性的。

---

## Agent 详细规格

### 1. character-checker（角色一致性审查）

| 属性 | 值 |
|------|-----|
| 文件 | `.claude/agents/character-checker.md` |
| 模型 | `opus` |
| 输入 | `characters.md` + 剧本 + `continuity-log.md` |
| 输出 | `verdict` + `issues[]` + `line_counts{}` + `summary` |

**审查维度：**
- 每句台词是否符合角色词汇量/句式习惯/口头禅
- 角色行为是否超出当前角色弧线阶段
- 秦朗台词量：3-8句正常，超12句标记
- 固定配角是否有超300字完全无台词/动作

**典型问题标记：** 口头禅缺席、角色行为与弧线阶段不符、台词分配失衡

---

### 2. comedy-checker（笑点审查）

| 属性 | 值 |
|------|-----|
| 文件 | `.claude/agents/comedy-checker.md` |
| 模型 | `sonnet` |
| 输入 | 剧本 + `continuity-log.md` |
| 输出 | `verdict` + `stats{joke_count, density, type_distribution}` + `issues[]` + `callback_opportunities[]` |

**审查维度：**
- 笑点密度：每500字至少1-2个有效笑点
- 新鲜度：同一梗不连续两集使用
- 笑点依赖角色性格（好梗）还是纯粹段子（坏梗）
- 是否依赖网络梗/流行语（应避免）
- 喜剧真空区：连续300字无喜剧元素

**典型问题标记：** 梗重复使用、段子驱动而非角色驱动、网络流行语依赖

---

### 3. structure-checker（结构审查）

| 属性 | 值 |
|------|-----|
| 文件 | `.claude/agents/structure-checker.md` |
| 模型 | `haiku` |
| 输入 | 剧本 |
| 输出 | `verdict` + `stats{total_chars, reversal_count, scene_count}` + `issues[]` |

**审查维度：**
- 冷开场钩子位置：≤150字
- 反转数量：≥1，位置30-50%/60-80%
- 结尾情绪落点必须向上
- 场景数：1-2个主场景
- 连续对白不超过3轮无中断
- 总字数：1500-2800

**典型问题标记：** 字数严重不达标、反转位置偏移、结尾跌入负面情绪

---

### 4. continuity-checker（连贯性追踪）

| 属性 | 值 |
|------|-----|
| 文件 | `.claude/agents/continuity-checker.md` |
| 模型 | `opus` |
| 输入 | `continuity-log.md` + 剧本 + `characters.md` |
| 输出 | `verdict` + `issues[]` + `foreshadowing_status[]` + `new_tracking_items[]` |

**审查维度：**
- 时间线：和上集间隔合理
- 角色知识状态：与continuity-log一致
- 伏笔：前集已埋的是否推进
- 伤病/道具：状态延续正确
- 关系状态：不出现"重置"

**典型问题标记：** 知识状态跳跃、伏笔遗忘、道具消失/出现不连贯

---

### 5. reader-avatar（读者视角审查）

| 属性 | 值 |
|------|-----|
| 文件 | `.claude/agents/reader-avatar.md` |
| 模型 | `sonnet` |
| 输入 | 剧本 |
| 输出 | `verdict` + `emotional_journey[]` + `moments_that_landed[]` + `would_share_with_friend` + `summary` |

**读者身份（按项目切换）：**

| 项目 | 读者 | 核心特质 |
|------|------|---------|
| 骑手女王 | 28岁都市女性 | 通勤刷剧，笑点高，讨厌鸡汤，点过很多外卖 |
| 后妈 | 35岁重组家庭成员 | 对"后妈"标签敏感，需要角色真实而非可爱 |
| 山海食单 | 22-30岁年轻人 | 喜欢千与千寻/虫师，不信鬼神但相信食物的记忆 |
| 丧尸区 | 30-50岁普通人 | 住过小区，不喜欢丧尸片但这个不一样 |

**审查方式：** 不要分析结构/弧线/伏笔。记录真实感受。笑了吗？在哪句？感动了吗？在哪段？走神了吗？在哪里？

---

### 6. platform-checker（平台合规审查）

| 属性 | 值 |
|------|-----|
| 文件 | `.claude/agents/platform-checker.md` |
| 模型 | `opus` |
| 输入 | 审核规范 + 剧本/概念 + characters + outline |
| 输出 | `verdict(四级)` + `subject_tier` + `absolute_prohibitions[]` + `hidden_redlines[]` + `modification_checklist[]` |

**审查依据：** `resources/txt/最新平台审核规范(1)(1).txt`（抖音漫剧 2026.5 标准）

**四级 verdict：** `pass` → `pass_with_risks` → `high_risk` → `fail`

**审查层级：**
1. 绝对禁止题材（触碰即下架）
2. 隐性红线（不公开但零容忍）
3. 六大零容忍红线
4. 差异化审核尺度（S/A/B/C级）
5. 通用合规要求

---

### 7. hook-checker（开场钩子审查）

| 属性 | 值 |
|------|-----|
| 文件 | `.claude/agents/hook-checker.md` |
| 模型 | `opus` |
| 输入 | 剧本/概念 + characters + outline |
| 输出 | `verdict` + `first_3_seconds{hook_type, hook_strength}` + `first_30_seconds{...}` + `algorithm_risk{}` + `rewrite_suggestions[]` |

**双层审查结构：**
- **前3秒层**：六种钩子类型（好奇缺口/情绪触发/模式中断/悬念提问/反常并置/即时紧张），1-5强度评分，"划走测试"
- **前30秒层**：调性交付、世界观效率、角色记忆点、利益点建立、信息密度、节奏曲线

**七种失败模式：** 空洞空镜、解说堆砌、虚假承诺、慢热过长、通用开场、信息过载、调性错位

**测量基准：** `[场景]` 行不计入等效时长，从第一个动作描述/对白开始计数

---

### 8. writers-room（作家室）

| 属性 | 值 |
|------|-----|
| 文件 | `.claude/agents/writers-room.md` |
| 模型 | `opus` |
| 使用方式 | 三个 Agent 并行 Pitch |

**三个方向：**
- Agent A: 更荒谬（错位梗、反差、出乎意料的道具）
- Agent B: 更走心（脆弱时刻、安静瞬间、不说出口的情绪）
- Agent C: 配角破局（关键配角在关键时刻说关键的话）

**选择标准：** 最不可预测但最合理 / 最能揭示角色新的一面 / 能推进剧情

---

## 数据 Schema

### review-schema.json

统一的审查输出 schema，定义 `verdict` 枚举、`issue` 对象结构、`severity` 级别。

### continuity-schema.json

连贯性追踪的数据结构，定义伏笔、知识状态、道具、关系变化的追踪格式。

---

## Agent 开发规范

### 添加新 Agent

1. 在 `.claude/agents/` 下创建 `<agent-name>.md`
2. YAML frontmatter 指定 `model`（opus/sonnet/haiku）
3. 定义审查维度、工作流程、输出格式（JSON）
4. 在 `CLAUDE.md` 和 `README.md` 中更新 Agent 矩阵
5. 至少用一个实际项目测试

### Agent 文件格式

```markdown
---
model: opus
---

# Agent 名称

你是XXX的审查员。[角色描述]

## 工作流程
1. 读取...
2. 比对...
3. 输出...

## 审查维度
- 维度1
- 维度2

## 输出格式
必须输出以下 JSON（用 ```json 代码块包裹）：
{...}
```

### 模型选择指南

| 任务特征 | 推荐模型 |
|---------|---------|
| 需要深度理解角色弧线/法律文本/跨集关联 | `opus` |
| 需要平衡分析质量与速度（情绪体验、笑话识别） | `sonnet` |
| 纯机械检查（数字数、算比例、检查格式） | `haiku` |
| 创意生成（多方向 Pitch） | `opus` |

### 并行执行

Agent 之间无依赖关系时可全并行：
```
// ✅ 正确：同一集的不同审查维度
character(Ep1) ‖ comedy(Ep1) ‖ structure(Ep1) ‖ continuity(Ep1) ‖ reader(Ep1)

// ✅ 正确：不同集的同一维度
character(Ep1) ‖ character(Ep2) ‖ character(Ep3)

// ❌ 不需要并行但无害：有依赖关系的审查
// （所有审查只读，不存在写依赖）
```
