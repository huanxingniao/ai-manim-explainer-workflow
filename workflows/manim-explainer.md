---
description: 从主题关键词到完整 Manim 科普视频的全自动化工作流（含 Audio-Driven Animation 音画对齐）
---

# Manim 科普视频自动化工作流 v2

**项目路径**：`当前工作区根目录`
**参考实现**：`attention_v4.py`（当前最新技术范本）

---

## 前置资产（直接复用，不要重建）

以下类定义来自 `attention_v4.py`，直接复制：
- `WordToken(VGroup)` — 圆角词牌，支持高亮/暗化
- `FormulaHUD(VGroup)` — 右上角公式悬挂 HUD
- `AlienBody(VGroup)` — 可换装吉祥物，支持 outfit：`"detective"` / `"judge"` / `"student"` / `"backpack_student"`

**吉祥物使用规范（必须遵守）：**
1. `mascot.set_outfit_style("xxx")` — 换装（在 1.0 尺寸下）
2. `mascot.scale(0.25)` — 缩放
3. `mascot.move_to(...)` — 定位
4. 每个场景实例化**独立吉祥物对象**，不得跨场景复用

**场景清理规范：**
- 每个场景结尾 `self.play(FadeOut(VGroup(all_mobs)))` 必须包含当前场景所有对象，含 title
- 不得用 `ReplacementTransform(title, Text(...))` 切换标题

---

## 声画设计核心原则

### 解说词三层结构

| 层级 | 位置 | 表达方式 | 标记 |
|------|------|---------|------|
| **🪝 钩子句** | 每幕第1句 | 设问、直觉类比、悬念 — **允许比喻** | 🪝 |
| **⚙️ 机制句** | 每幕主体 | 精确描述操作步骤 — 禁止比喻 | ⚙️ |
| **🔗 过渡句** | 每幕最后1句 | 承上启下 — **允许修辞** | 🔗 |

两个视角审查冲突时：🪝/🔗 → 视角B（叙事）优先；⚙️ → 视角A（技术）优先

### 高密度文案原则
- 每条解说词字数 ≥ 30 字，解释机制不仅描述画面
- 画面不留空白期：以 TTS 实测时长驱动画面等待而非猜测
- 贯穿例句一以贯之，覆盖公式的全部步骤

---

## Phase 1：场景大纲

获取用户信息后生成六段式大纲：
- 主题关键词 / 目标受众 / 视频时长 / 贯穿例句

```
Scene 0: 开门见山，定场公式
Scene 1: 痛点 — 没有该机制会发生什么？
Scene 2: 核心步骤 A
Scene 3: 核心步骤 B
Scene 3.5（可选）: 底层机理补充
Scene 4: 核心步骤 C
Scene 5: 三步复盘 + 悬念
```

**⛔ 停顿**：以 Markdown 表格展示，等用户确认后进入 Phase 1.5。

---

## Phase 1.5：声画蒙太奇脚本（EDL）

生成两份表格：

**声画对照表**（每场景）：

| 时间 | 画面内容 | 解说词 | 层级 |
|------|---------|--------|------|
| MM:SS | 动画事件 | 精确解说词 | 🪝/⚙️/🔗 |

**EDL 剪辑决定表**（全片）：

| # | TC IN | TC OUT | 时长 | 幕 | 画面事件 | 音频关键 | 同步 |
|---|-------|--------|------|-----|---------|---------|------|

**⛔ 停顿**：用户确认 EDL 后进入 Phase 2。

---

## Phase 2：代码生成（Audio-Driven Architecture）

**核心架构**：不使用硬编码 `self.wait(N)`, 改用 `wait_beat()` 驱动。

### 必须实现的基础设施

```python
# 1. 读取 timing.json（由 Phase 3 生成后反哺）
with open("timing.json") as f:
    TIMING = json.load(f)

# 2. wait_beat 自监督时间控制
def wait_beat(self, beat_idx, beat_start_time):
    info = TIMING[str(beat_idx)]
    elapsed = self.time - beat_start_time
    remaining = info["duration"] + info["padding"] - elapsed
    self.wait(max(0.1, remaining))

# 3. play_at 词级触发（Level 2）
def play_at(self, target_ms, beat_start_time, *animations):
    elapsed_ms = (self.time - beat_start_time) * 1000
    gap = (target_ms - elapsed_ms) / 1000
    if gap > 0:
        self.wait(gap)
    self.play(*animations)
```

### 场景方法签名规范

```python
def scene0(self) -> FormulaHUD:   # 返回 hud 对象
def scene1(self, hud): ...
def sceneN(self, hud): ...

def construct(self):
    hud = self.scene0()
    self.scene1(hud)
    ...
```

### 色彩系统

```python
C_Q   = "#E05C5C"   # Query 红
C_K   = "#5C8AE0"   # Key   蓝
C_V   = "#5CBF6E"   # Value 绿
C_HI  = "#FFD166"   # 高亮  橙黄
C_DIM = "#3A3A3A"   # 暗化  深灰
```

// turbo
生成文件后立即验证语法：
```bash
cd 当前工作区根目录 && source venv/bin/activate && python -c "import py_compile; py_compile.compile('{filename}.py', doraise=True)" && echo "SYNTAX OK"
```

---

## Phase 3：TTS 生成 + timing.json（音频驱动核心）

**原则：先出声音，再渲染画面。让音频决定画面等待时长。**

### 步骤 3-A：生成 TTS 音频

新建 `/tmp/gen_tts_{topic}.py`，格式如下：

```python
TEXTS = [
    "",       # 0 占位
    "beat 1 解说词...",   # 高密度，≥30字
    "beat 2 解说词...",
    ...
]
VOICE = "zh-CN-XiaoxiaoNeural"
```

// turbo
```bash
cd 当前工作区根目录 && source venv/bin/activate && python /tmp/gen_tts_{topic}.py
```

### 步骤 3-B：生成 timing.json

TTS 完成后，用 `ffprobe` 测量每段音频真实时长，自动计算节拍 padding：
- 钩子句 / 幕结尾 / 转折点：padding = 1.4s
- 普通机制句：padding = 0.8s

### 步骤 3-C：生成 events.json（Level 2 词级对齐）

```bash
cd 当前工作区根目录 && source venv/bin/activate && pip install openai-whisper  # 首次需要
python /tmp/gen_events_whisper.py
```

`gen_events_whisper.py` 模板参考：`/tmp/gen_events_whisper.py`（当前项目里已有完整实现）

**TRIGGER_MAP 格式**：
```python
TRIGGER_MAP = {
    beat_id: {
        "动画标识": ["触发词1", "触发词2"],  # 任一匹配即触发
    }
}
```

输出 `events.json`，格式为 `{beat_id → {anim_id → ms_offset}}`。

---

## Phase 4：渲染 + 合并

### 步骤 4-A：渲染视频

// turbo
```bash
cd 当前工作区根目录 && source venv/bin/activate && manimgl {filename}.py {ClassName} -w 2>&1
```

渲染失败常见原因及修复：
- `NameError: DARK_BLUE` → 改为 `BLUE_E`
- `TypeError: scale()` → 检查 `about_edge` 参数格式
- WARNING `Unsupported element type: Image` → 忽略，不影响输出

### 步骤 4-B：合成配音轨

```bash
ffmpeg -y -i videos/{ClassName}.mp4 \
       -i videos/{topic}_voiceover.wav \
       -c:v copy -c:a aac \
       -map 0:v:0 -map 1:a:0 -shortest \
       videos/{ClassName}_with_Audio.mp4
```

### 步骤 4-C：验证

渲染成功后报告：
- 视频总时长（用 `ffprobe -v error -show_entries format=duration`）
- 是否与 EDL 预期时长匹配（允许 ±30s）

---

## Phase 5：Level 2 音画对齐注入

**目标**：把 `events.json` 里的词级时间戳注入 Manim 渲染代码，用 `play_at()` 替换关键幕里的盲触发动画。

### 关键幕替换原则

对于每个在 `events.json` 里有触发事件的 beat：

```python
# 替换前（盲触发）
self.play(Indicate(k_nodes[5]))
self.play(Indicate(k_nodes[2]))

# 替换后（词级精准触发）
bgn = self.time
# ... 先播放 beat 的基础动画 ...
self.play_at(events["17"]["indicate_apple_self"], bgn, Indicate(k_nodes[5]))
self.play_at(events["17"]["indicate_phone"],      bgn, Indicate(k_nodes[2], color=ORANGE))
self.play_at(events["17"]["indicate_eat"],        bgn, Indicate(k_nodes[6], color=C_V))
self.wait_beat(17, bgn)
```

### 重渲染 + 重合并

// turbo
```bash
cd 当前工作区根目录 && source venv/bin/activate && manimgl {filename}.py {ClassName} -w 2>&1
```

---

## 质量检查清单（每次渲染后执行）

- [ ] 所有场景末尾 `FadeOut` 包含了全部 mobs（含 title）
- [ ] `timing.json` 存在且覆盖所有 beat_id
- [ ] `events.json` 存在（Level 2 已启用）
- [ ] `wait_beat()` 实现中有 `max(0.1, remaining)` 保护
- [ ] `play_at()` 实现中有 `if gap > 0` 保护
- [ ] 渲染退出码为 0（无 Python 报错）
- [ ] 最终视频时长与 TTS 总时长相差 ≤ 30s
- [ ] 解说词信息密度：每条 ≥ 30 字，在解释机制，不仅描述画面

---

## 新对话开场 Prompt 模板

### A. 接续当前《Attention v4》最后一公里（Level 2 注入）

```
/manim-explainer

请直接执行 Phase 5（Level 2 音画对齐注入），不需要重新生成剧本或代码。

## 当前项目状态
- 主 Manim 文件：`当前工作区根目录/attention_v4.py`
- 句级节拍时长：`当前工作区根目录/timing.json`
- 词级触发事件：`当前工作区根目录/events.json`（Whisper 已对齐，28个触发点）
- 当前配音轨：`videos/attention_v4_voiceover.wav`
- 当前成品：`videos/AttentionAnimationV4_with_Audio.mp4`（声音稀疏，待修复）

## 要做的事（按顺序）
1. 读 `attention_v4.py`，找到 beat 17/18/19/20/22/24/25/26/28/30 的实现
2. 在这些 beat 里，把关键动效从"无时序触发"改为 `play_at(events[beat_id][anim_id], beat_start, *animations)`
3. `play_at` 实现：elapsed_ms = (self.time - beat_start)*1000; gap=(target_ms-elapsed_ms)/1000; if gap>0: self.wait(gap); self.play(*animations)
4. 重新渲染：`manimgl attention_v4.py AttentionAnimationV4 -w`
5. 重新合并音频：`ffmpeg -y -i videos/AttentionAnimationV4.mp4 -i videos/attention_v4_voiceover.wav -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest videos/AttentionAnimationV4_L2.mp4`

直接开始，不需要询问。
```

### B. 开启全新主题视频

```
/manim-explainer

主题：{主题关键词}
受众：{目标受众}
时长：{目标分钟数}分钟

请从 Phase 1 开始，生成场景大纲，等我确认后继续。
```
