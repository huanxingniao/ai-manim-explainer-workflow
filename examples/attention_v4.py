from manimlib import *
import numpy as np
import json

# 动态加载时长数据
with open("当前工作区根目录/timing.json", "r") as f:
    TIMING = json.load(f)
with open("当前工作区根目录/events.json", "r") as f:
    EVENTS = json.load(f)

SENTENCE = ["小明", "用", "苹果", "手机", "买", "一个", "苹果", "吃"]
C_Q   = "#E05C5C"
C_K   = "#5C8AE0"
C_V   = "#5CBF6E"
C_HI  = "#FFD166"
C_DIM = "#3A3A3A"

class WordToken(VGroup):
    def __init__(self, text, bg_color=GREY_E, text_color=WHITE, font_size=28, **kwargs):
        super().__init__(**kwargs)
        self.label = Text(text, font="PingFang SC", font_size=font_size, color=text_color, weight=BOLD)
        pad_w = self.label.get_width() + 0.5
        pad_h = self.label.get_height() + 0.4
        self.bg = RoundedRectangle(
            corner_radius=0.15, width=pad_w, height=pad_h,
            color=bg_color, fill_opacity=0.85, stroke_width=2
        )
        self.label.move_to(self.bg)
        self.add(self.bg, self.label)

class FormulaHUD(VGroup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.formula = Text(
            "Attention(Q,K,V) = softmax(QK\u1d40/\u221adk)\u00b7V",
            font="Consolas", font_size=20, color=GREY_B
        )
        self.add(self.formula)
        self.to_corner(UR, buff=0.3)

    def pulse(self, color=YELLOW):
        return Indicate(self.formula, color=color, scale_factor=1.05)

class AlienBody(VGroup):
    MAIN_RED  = "#D33F3F"
    DARK_RED  = "#A82B2B"
    EYE_BLACK = "#1A1A1A"
    EYE_GLOW  = "#7FFFD4"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.body        = Circle(radius=2.0).set_fill(self.MAIN_RED, opacity=1.0).set_stroke(self.DARK_RED, width=2)
        self.left_eye    = Circle(radius=0.35).set_fill(self.EYE_BLACK, opacity=1.0).move_to(LEFT*0.7  + UP*0.3)
        self.right_eye   = Circle(radius=0.35).set_fill(self.EYE_BLACK, opacity=1.0).move_to(RIGHT*0.7 + UP*0.3)
        self.left_glow   = Circle(radius=0.15).set_fill(self.EYE_GLOW, opacity=1.0).move_to(self.left_eye.get_center()  + LEFT*0.05 + UP*0.05)
        self.right_glow  = Circle(radius=0.15).set_fill(self.EYE_GLOW, opacity=1.0).move_to(self.right_eye.get_center() + LEFT*0.05 + UP*0.05)
        self.eyes        = VGroup(self.left_eye, self.left_glow, self.right_eye, self.right_glow)
        self.left_antenna  = ArcBetweenPoints(UP*1.8+LEFT*0.8,  UP*2.8+LEFT*1.2,  angle=-PI/4).set_stroke(self.MAIN_RED, width=12)
        self.right_antenna = ArcBetweenPoints(UP*1.8+RIGHT*0.8, UP*2.8+RIGHT*1.2, angle= PI/4).set_stroke(self.MAIN_RED, width=12)
        self.left_arm    = VGroup(Ellipse(width=0.8, height=1.2).set_fill(self.MAIN_RED).rotate( PI/6).move_to(LEFT*2.2  + DOWN*0.2))
        self.right_arm   = VGroup(Ellipse(width=0.8, height=1.2).set_fill(self.MAIN_RED).rotate(-PI/6).move_to(RIGHT*2.2 + DOWN*0.2))
        self.legs        = VGroup(
            Rectangle(width=0.4, height=0.8).set_fill(self.DARK_RED, 1).move_to(DOWN*2+LEFT*0.4),
            Rectangle(width=0.4, height=0.8).set_fill(self.DARK_RED, 1).move_to(DOWN*2+RIGHT*0.4)
        )
        self.outfit = VGroup()
        self.add(self.legs, self.left_antenna, self.right_antenna,
                 self.body, self.eyes, self.left_arm, self.right_arm, self.outfit)

    def right_shoulder_pt(self): return self.body.get_center() + normalize(RIGHT*1.9 + DOWN*0.1) * (self.body.get_width()/2)

    def set_outfit_style(self, style_name):
        self.outfit.clear()
        if style_name == "detective":
            top = self.body.get_top()
            hat_cap = Polygon(
                top+LEFT*2.0, top+LEFT*2.2+UP*1.5, top+UP*2.5,
                top+RIGHT*2.2+UP*1.5, top+RIGHT*2.0, color="#6B3A2A", fill_opacity=1.0
            ).set_stroke(width=0)
            hat_brim = Ellipse(width=5.2, height=1.0, color="#5A2D0C", fill_opacity=1).move_to(top+UP*0.1)
            arm_c = self.right_arm.get_center()
            g_frame  = Circle(radius=0.8, color=GREY_B, stroke_width=8).move_to(arm_c+RIGHT*1.0+UP*1.5)
            g_glass  = Circle(radius=0.75, color=BLUE_A, fill_opacity=0.25).move_to(g_frame)
            g_handle = Line(g_frame.get_bottom()+DOWN*0.2, g_frame.get_bottom()+RIGHT*0.8+DOWN*1.2, color="#4B2C20", stroke_width=8)
            self.outfit.add(hat_brim, hat_cap, VGroup(g_handle, g_frame, g_glass))
        elif style_name == "judge":
            arm_c = self.right_arm.get_center()
            stick = Line(arm_c+UP*0.5, arm_c+UP*2.8, color="#8B5A2B", stroke_width=7)
            board = RoundedRectangle(corner_radius=0.25, width=2.2, height=1.6, color="#C49B66", fill_opacity=1).move_to(stick.get_end()+UP*0.8)
            lbl   = Text("10", font="PingFang SC", font_size=48, color=WHITE).move_to(board)
            self.outfit.add(stick, board, lbl)

# =====================================================
# 主动画类 (Audio-Driven Animation)
# =====================================================
class AttentionAnimationV4(Scene):

    def wait_beat(self, beat_idx, bgn_time):
        """自监督核心时间控制"""
        info = TIMING[str(beat_idx)]
        elapsed = self.time - bgn_time
        target_wait = info["duration"] + info["padding"] - elapsed
        self.wait(max(0.1, target_wait))

    def play_at(self, target_ms, beat_start_time, *animations, **kwargs):
        """词级精准触发：等待至 target_ms 后再 play"""
        elapsed_ms = (self.time - beat_start_time) * 1000
        gap = (target_ms - elapsed_ms) / 1000
        if gap > 0:
            self.wait(gap)
        self.play(*animations, **kwargs)

    def _sentence_row(self, font_size=28, active_idx=None, dim_others=False):
        tokens = []
        for i, w in enumerate(SENTENCE):
            if active_idx is not None and i == active_idx:
                t = WordToken(w, bg_color=C_HI, text_color="#1A1A1A", font_size=font_size)
            elif dim_others and active_idx is not None and i != active_idx:
                t = WordToken(w, bg_color=C_DIM, text_color=GREY_B, font_size=font_size)
            else:
                t = WordToken(w, font_size=font_size)
            tokens.append(t)
        return VGroup(*tokens).arrange(RIGHT, buff=0.22)

    def _title(self, sub, main):
        t1 = Text(sub,  font="PingFang SC", font_size=26, color=GREY_A)
        t2 = Text(main, font="PingFang SC", font_size=36, color=WHITE, weight=BOLD)
        return VGroup(t1, t2).arrange(DOWN, buff=0.1).to_edge(UP, buff=0.35)

    def scene0(self):
        # Beat 1
        bgn = self.time
        hook = Text(
            "同一个'苹果'，一个是手机的品牌，另一个是诱人的水果——", font="PingFang SC", font_size=28, color=C_HI
        ).to_edge(UP, buff=0.5)
        hook2 = Text(
            "大语言模型是怎么在瞬间判断出它在当前句子里的确切含义的呢？", font="PingFang SC", font_size=28, color=WHITE
        ).next_to(hook, DOWN, buff=0.2)
        tokens = [WordToken(w, bg_color=("#E07B2A" if i==2 else ("#4CAF50" if i==6 else GREY_E)), font_size=28) for i, w in enumerate(SENTENCE)]
        row = VGroup(*tokens).arrange(RIGHT, buff=0.22).move_to(ORIGIN)
        self.play(Write(VGroup(hook, hook2), run_time=3.0))
        self.play(LaggedStart(*[FadeIn(t, shift=UP*0.25) for t in tokens], lag_ratio=0.08))
        self.wait_beat(1, bgn)

        # Beat 2 — 公式出现后整体 pulse 高亮，不用浮层字母（避免坐标错位混叠）
        bgn = self.time
        formula_big = Text("Attention(Q,K,V) = softmax(QK\u1d40/\u221adk)\u00b7V", font="Consolas", font_size=36, color=C_HI).move_to(DOWN*1.8)
        self.play(FadeOut(VGroup(hook, hook2)), row.animate.move_to(UP*2.5).scale(0.82), FadeIn(formula_big, shift=UP*1.5), run_time=1.5)
        # 台词提到 Query/Key/Value 时，对整体公式依次做颜色 Indicate（安全无混叠）
        self.play_at(EVENTS["2"]["indicate_Q"], bgn, Indicate(formula_big, color=C_Q, scale_factor=1.04), run_time=0.5)
        self.play_at(EVENTS["2"]["indicate_K"], bgn, Indicate(formula_big, color=C_K, scale_factor=1.04), run_time=0.5)
        self.play_at(EVENTS["2"]["indicate_V"], bgn, Indicate(formula_big, color=C_V, scale_factor=1.04), run_time=0.5)
        self.wait_beat(2, bgn)  # FadeOut 由 ReplacementTransform→hud 在 Beat 3 自然完成

        # Beat 3
        bgn = self.time
        hud = FormulaHUD()
        qkv_row = VGroup(
            Text("Q (红)", font="PingFang SC", font_size=22, color=C_Q),
            Text("K (蓝)", font="PingFang SC", font_size=22, color=C_K),
            Text("V (绿)", font="PingFang SC", font_size=22, color=C_V),
        ).arrange(RIGHT, buff=0.7).next_to(row, DOWN, buff=0.45)
        self.play(ReplacementTransform(formula_big, hud), LaggedStart(*[FadeIn(l, shift=UP*0.2) for l in qkv_row], lag_ratio=0.2))
        self.wait_beat(3, bgn)

        # Beat 4 — P0: 补过渡动画（问号 + token 变灰），演示「没有注意力机制会怎样」
        bgn = self.time
        q_mark = Text("❓", font_size=72).move_to(DOWN*0.8)
        # 台词: "如果不使用这套复杂的注意力机制，大模型的世界会是什么样的？"
        self.play_at(EVENTS["4"]["show_question"], bgn, FadeIn(q_mark, scale=0.5))
        # token 变灰，暗示失去语义辨别能力
        self.play_at(EVENTS["4"]["dim_tokens"], bgn,
            *[t.animate.set_color(GREY_D) for t in tokens],
            run_time=0.8
        )
        self.wait_beat(4, bgn)
        self.play(FadeOut(VGroup(row, qkv_row, q_mark)))
        return hud

    def scene1(self, hud):
        title = self._title("假设没有注意力", "静态词嵌入的绝境")
        self.play(Write(title))

        # Beat 5
        bgn = self.time
        row = self._sentence_row(font_size=24).move_to(UP*1.2)
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN*0.2) for t in row], lag_ratio=0.08))
        arrows = VGroup(*[Arrow(t.get_bottom(), t.get_bottom()+DOWN*0.85, color=GREY_B, stroke_width=4, buff=0) for t in row])
        self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.06))
        self.wait_beat(5, bgn)

        # Beat 6
        bgn = self.time
        box3 = SurroundingRectangle(row[2], color=RED, buff=0.08, stroke_width=3)
        box6 = SurroundingRectangle(row[6], color=RED, buff=0.08, stroke_width=3)
        eq   = Text("⬇ 同一向量", font="PingFang SC", font_size=20, color=RED).move_to(ORIGIN + DOWN*2.3)
        self.play(ShowCreation(box3), ShowCreation(box6))
        self.play(arrows[2].animate.set_color(RED), arrows[6].animate.set_color(RED), FadeIn(eq))
        self.wait_beat(6, bgn)

        # Beat 7
        bgn = self.time
        mascot = AlienBody()
        mascot.set_outfit_style("detective")
        mascot.scale(0.24).move_to(RIGHT*5.2+DOWN*1.0)
        cross = Text("❌", font_size=56).next_to(mascot, UP, buff=0.1)
        self.play(FadeIn(mascot, shift=LEFT*0.5), FadeIn(cross, scale=1.4))
        self.wait_beat(7, bgn)

        # Beat 8 — P1: 补「加权组合」概念：多条弧线汇聚到苹果₆
        bgn = self.time
        self.play(FadeOut(VGroup(arrows, box3, box6, eq, cross, mascot)), hud.pulse())
        # 台词: "每个词的最终表示，由整个句子中所有词的加权组合来动态生成"
        merge_arcs = VGroup(*[
            CurvedArrow(
                row[i].get_bottom() + DOWN*0.1,
                row[6].get_bottom() + DOWN*0.5,
                angle=(-PI/5 if i < 6 else PI/5),
                color=interpolate_color(BLUE_E, C_HI, i/7),
                stroke_width=2.5,
            )
            for i in range(8) if i != 6
        ])
        self.play_at(EVENTS["8"]["show_merge_hint"], bgn,
            LaggedStart(*[ShowCreation(a) for a in merge_arcs], lag_ratio=0.07),
            run_time=1.2
        )
        # FadeOut 在 wait_beat 之前完成，避免 beat 外漂移
        self.play(FadeOut(merge_arcs, run_time=0.5))
        self.wait_beat(8, bgn)

        # Beat 9
        bgn = self.time
        self.play(Indicate(row[6], color=C_HI, scale_factor=1.3))
        self.play(FadeOut(VGroup(title, row)))
        self.wait_beat(9, bgn)

    def scene2(self, hud):
        title = self._title("身份裂变", "Q / K / V 的线性投影")
        self.play(Write(title))

        # Beat 10
        bgn = self.time
        row = self._sentence_row(font_size=22, active_idx=6, dim_others=True).move_to(UP*2.0)
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN*0.2) for t in row], lag_ratio=0.06))
        self.wait_beat(10, bgn)

        # Beat 11
        bgn = self.time
        apple = row[6]
        wq = WordToken("Wq", bg_color="#7A2020", font_size=22).move_to(apple.get_center()+DOWN*1.5+LEFT*1.8)
        wk = WordToken("Wk", bg_color="#1A3A7A", font_size=22).move_to(apple.get_center()+DOWN*1.5)
        wv = WordToken("Wv", bg_color="#1A5A2A", font_size=22).move_to(apple.get_center()+DOWN*1.5+RIGHT*1.8)
        aq = Arrow(apple.get_bottom(), wq.get_top(), buff=0.08, color=C_Q, stroke_width=3)
        ak = Arrow(apple.get_bottom(), wk.get_top(), buff=0.08, color=C_K, stroke_width=3)
        av = Arrow(apple.get_bottom(), wv.get_top(), buff=0.08, color=C_V, stroke_width=3)
        self.play(GrowArrow(aq), FadeIn(wq, shift=DOWN*0.3))
        self.play(GrowArrow(ak), FadeIn(wk, shift=DOWN*0.3))
        self.play(GrowArrow(av), FadeIn(wv, shift=DOWN*0.3))
        self.wait_beat(11, bgn)

        # Beat 12
        bgn = self.time
        q_out = WordToken("Q", bg_color=C_Q, font_size=24).next_to(wq, DOWN, buff=0.45)
        k_out = WordToken("K", bg_color=C_K, font_size=24).next_to(wk, DOWN, buff=0.45)
        v_out = WordToken("V", bg_color=C_V, font_size=24).next_to(wv, DOWN, buff=0.45)
        aq2 = Arrow(wq.get_bottom(), q_out.get_top(), buff=0.05, color=C_Q, stroke_width=3)
        ak2 = Arrow(wk.get_bottom(), k_out.get_top(), buff=0.05, color=C_K, stroke_width=3)
        av2 = Arrow(wv.get_bottom(), v_out.get_top(), buff=0.05, color=C_V, stroke_width=3)
        self.play(GrowArrow(aq2), FadeIn(q_out, shift=DOWN*0.3))
        self.play(GrowArrow(ak2), FadeIn(k_out, shift=DOWN*0.3))
        self.play(GrowArrow(av2), FadeIn(v_out, shift=DOWN*0.3))
        self.wait_beat(12, bgn)

        # Beat 13
        bgn = self.time
        self.play(FadeOut(VGroup(row, wq, wk, wv, aq, ak, av, aq2, ak2, av2, q_out, k_out, v_out)))
        all_t = VGroup(*[WordToken(w, font_size=18) for w in SENTENCE]).arrange(RIGHT, buff=0.16).move_to(UP*2.2)
        q_row = VGroup(*[WordToken("Q", bg_color=C_Q, font_size=12) for _ in SENTENCE]).arrange(RIGHT, buff=0.16).move_to(UP*1.3)
        k_row = VGroup(*[WordToken("K", bg_color=C_K, font_size=12) for _ in SENTENCE]).arrange(RIGHT, buff=0.16).move_to(UP*0.4)
        v_row = VGroup(*[WordToken("V", bg_color=C_V, font_size=12) for _ in SENTENCE]).arrange(RIGHT, buff=0.16).move_to(DOWN*0.5)
        for i, t in enumerate(all_t):
            for r in [q_row, k_row, v_row]:
                r[i].set_x(t.get_x())
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN*0.2) for t in all_t], lag_ratio=0.06))
        self.play(*[LaggedStart(*[FadeIn(x) for x in r], lag_ratio=0.04) for r in [q_row, k_row, v_row]])
        self.wait_beat(13, bgn)

        # Beat 14 — P1 (安全版): 先清除 Beat 13 的矩阵视图，再演示 QKᵀ 点积碰撞
        bgn = self.time
        # ① 清除 Beat 13 遗留的 all_t/q_row/k_row/v_row（避免叠加混叠）
        self.play(FadeOut(VGroup(all_t, q_row, k_row, v_row)))
        # ② HUD 公式 Indicate，对齐台词「QKᵀ」
        self.play_at(EVENTS["14"]["indicate_QKt"], bgn, Indicate(hud, color=C_Q, scale_factor=1.08))
        # ③ 演示点积碰撞：苹果·Q 碰 吃·K → 弹出分数
        demo_q = WordToken("苹果·Q", bg_color=C_Q, font_size=18).move_to(LEFT*2.2 + DOWN*0.5)
        demo_k = WordToken("吃·K",   bg_color=C_K, font_size=18).move_to(RIGHT*2.2 + DOWN*0.5)
        demo_score = Text("· = 0.6", font="Consolas", font_size=24, color=YELLOW).move_to(DOWN*0.5)
        self.play_at(EVENTS["14"]["show_matrix_outline"], bgn,
            FadeIn(demo_q, shift=RIGHT*0.4),
            FadeIn(demo_k, shift=LEFT*0.4),
        )
        self.play(Write(demo_score, run_time=0.5))
        # ④ FadeOut demo 内容在 wait_beat 之前，避免时间漂移
        self.play(FadeOut(VGroup(demo_q, demo_k, demo_score), run_time=0.4))
        self.wait_beat(14, bgn)

        # Beat 15 — 矩阵轮廓 + 苹果行高亮（使用与 outline 相同的坐标公式）
        bgn = self.time
        CELL = 0.42
        CELL_STEP = CELL + 0.04  # = 0.46
        outline = VGroup(*[
            Square(side_length=CELL, color=GREY_E, fill_opacity=0.18, stroke_width=1).move_to(
                RIGHT*(c-3.5)*CELL_STEP + DOWN*0.3 + UP*(3.5-r)*CELL_STEP
            )
            for r in range(8) for c in range(8)
        ])
        # 苹果 index=6 → r=6，行中心 y = DOWN*0.3 + UP*(3.5-6)*CELL_STEP = DOWN*0.3 + DOWN*2.5*CELL_STEP
        apple_row_y = DOWN*0.3 + UP*(3.5 - 6)*CELL_STEP  # = DOWN*0.3 + DOWN*1.15 = DOWN*1.45
        apple_outline_hl = Rectangle(
            width=8*CELL_STEP, height=CELL,
            color=C_HI, fill_opacity=0.15, stroke_width=2.5
        ).move_to(apple_row_y)
        self.play(FadeIn(outline, scale=0.5))
        self.play_at(EVENTS["15"]["highlight_apple_row_outline"], bgn, ShowCreation(apple_outline_hl))
        self.play(FadeOut(VGroup(title, outline, apple_outline_hl)))
        self.wait_beat(15, bgn)

    def scene3(self, hud):
        title = self._title("雷达全开", "点积 · 缩放 · Softmax")
        self.play(Write(title))

        # Beat 16
        bgn = self.time
        q_node = WordToken("苹果 · Q", bg_color=C_Q, font_size=22).move_to(LEFT*4+UP*0.5)
        k_nodes = VGroup(*[WordToken(f"{w} · K", bg_color=C_K, font_size=16).move_to(RIGHT*1.5+UP*(1.9-i*0.65)) for i, w in enumerate(SENTENCE)])
        self.play(FadeIn(q_node, shift=RIGHT*0.4), LaggedStart(*[FadeIn(k, shift=LEFT*0.2) for k in k_nodes], lag_ratio=0.07))
        self.wait_beat(16, bgn)

        # Beat 17 — P0修正: Indicate 顺序对齐台词（自身2.1→苹果手机1.4→吃0.6→小明0.8）
        bgn = self.time
        raw_scores = [0.8, 0.3, 1.4, 0.9, 0.5, 0.2, 2.1, 0.6]
        score_labels = VGroup()
        for i, (k, s) in enumerate(zip(k_nodes, raw_scores)):
            ghost = q_node.copy().set_opacity(0.5)
            self.play(ghost.animate.move_to(k.get_left()+LEFT*0.25), run_time=0.25)
            lbl = Text(f"{s}", font="Consolas", font_size=17, color=YELLOW).next_to(k, RIGHT, buff=0.28)
            score_labels.add(lbl)
            self.play(FadeIn(lbl, scale=1.4), FadeOut(ghost), run_time=0.18)
        # 台词顺序: "自身2.1（最高）→ 苹果和手机1.4（高）→ 吃0.6 → 小明0.8"
        # indicate_apple_self 最早（2460ms） → phone（9600ms） → eat（12520ms） → xiaoming（18500ms）
        self.play_at(EVENTS["17"]["indicate_apple_self"], bgn, Indicate(k_nodes[6], color=C_HI,      scale_factor=1.3))
        self.play_at(EVENTS["17"]["indicate_phone"],      bgn, Indicate(k_nodes[2], color="#E07B2A",  scale_factor=1.2))
        self.play_at(EVENTS["17"]["indicate_eat"],        bgn, Indicate(k_nodes[7], color=C_V,        scale_factor=1.1))
        self.play_at(EVENTS["17"]["indicate_xiaoming"],   bgn, Indicate(k_nodes[0], color=BLUE_B,     scale_factor=1.1))
        self.play_at(EVENTS["17"]["indicate_establish"],  bgn, Indicate(score_labels[6], color=YELLOW, scale_factor=1.3))
        self.wait_beat(17, bgn)

        # Beat 18 — P1: 三段节奏（数值爆炸 → 梯度消失警告 → 除以√dk压缩）
        bgn = self.time
        bars1 = VGroup(*[Rectangle(width=s*0.38, height=0.42, color=BLUE_D, fill_opacity=0.7, stroke_width=1).move_to(RIGHT*4.5+UP*(1.9-i*0.65)).align_to(RIGHT*3.8, LEFT) for i, s in enumerate(raw_scores)])
        self.play(FadeOut(score_labels))
        self.play(LaggedStart(*[FadeIn(b) for b in bars1], lag_ratio=0.06))
        # 台词: "原始点积值会随维度增大而呈线性爆炸"
        warn_lbl = Text("⚠ 数值爆炸", font="PingFang SC", font_size=18, color=RED).move_to(RIGHT*5.3+UP*2.7)
        self.play_at(EVENTS["18"]["warn_explode"], bgn,
            Indicate(bars1[6], color=RED, scale_factor=1.35),
            FadeIn(warn_lbl),
        )
        # 台词: "导致Softmax进入梯度消失的死亡陷阱"
        grad_lbl = Text("梯度消失 ☠", font="PingFang SC", font_size=18, color="#FF6B6B").move_to(RIGHT*5.3+UP*2.2)
        self.play_at(EVENTS["18"]["warn_gradient"], bgn, FadeIn(grad_lbl))
        # 台词: "除以维度的平方根，在这里也就是除以8"
        div8 = Text("\u00f7 8  (= \u221a64)", font="Consolas", font_size=20, color=YELLOW).move_to(RIGHT*5.6+UP*1.6)
        self.play(FadeOut(VGroup(warn_lbl, grad_lbl)), FadeIn(div8))
        scaled_b = VGroup(*[Rectangle(width=(s/8)*0.38*8*0.5, height=0.42, color=TEAL_D, fill_opacity=0.7, stroke_width=1).move_to(RIGHT*4.5+UP*(1.9-i*0.65)).align_to(RIGHT*3.8, LEFT) for i, s in enumerate(raw_scores)])
        self.play_at(EVENTS["18"]["animate_scale_down"], bgn, ReplacementTransform(bars1, scaled_b), run_time=0.8)
        self.wait_beat(18, bgn)

        # Beat 19
        bgn = self.time
        sw = [0.10, 0.04, 0.16, 0.06, 0.05, 0.03, 0.45, 0.11]
        sm_bars = VGroup()
        sm_pcts  = VGroup()
        for i, (w, p) in enumerate(zip(k_nodes, sw)):
            b = Rectangle(width=p*6.5, height=0.42, color=GREEN_D, fill_opacity=0.75, stroke_width=1).move_to(RIGHT*4.5+UP*(1.9-i*0.65)).align_to(RIGHT*3.8, LEFT)
            lbl = Text(f"{int(p*100)}%", font="Consolas", font_size=15, color=GREEN).next_to(b, RIGHT, buff=0.08)
            sm_bars.add(b); sm_pcts.add(lbl)
        self.play(FadeOut(VGroup(div8, scaled_b)))
        # play_at 词级触发：softmax 出现 + 关键扇区 Indicate
        self.play_at(EVENTS["19"]["start_softmax"], bgn,
            LaggedStart(*[FadeIn(b, shift=RIGHT*0.2) for b in sm_bars], lag_ratio=0.05),
            LaggedStart(*[FadeIn(p) for p in sm_pcts], lag_ratio=0.05),
        )
        self.play_at(EVENTS["19"]["indicate_42pct"], bgn, Indicate(sm_bars[6], color=C_HI,     scale_factor=1.2))
        self.play_at(EVENTS["19"]["indicate_18pct"], bgn, Indicate(sm_bars[3], color="#E07B2A", scale_factor=1.1))
        self.play_at(EVENTS["19"]["indicate_12pct"], bgn, Indicate(sm_bars[7], color=C_V,       scale_factor=1.1))
        self.wait_beat(19, bgn)

        # Beat 20
        bgn = self.time
        HEAT = np.array([
            [0.60,0.10,0.05,0.02,0.03,0.10,0.05,0.05],
            [0.05,0.50,0.15,0.05,0.05,0.10,0.05,0.05],
            [0.05,0.10,0.45,0.15,0.05,0.05,0.10,0.05],
            [0.05,0.10,0.15,0.50,0.05,0.05,0.05,0.05],
            [0.05,0.10,0.10,0.05,0.50,0.10,0.05,0.05],
            [0.05,0.10,0.10,0.05,0.05,0.55,0.05,0.05],
            [0.10,0.04,0.16,0.06,0.05,0.03,0.45,0.11],
            [0.05,0.10,0.10,0.05,0.05,0.05,0.10,0.50],
        ])
        CS = 0.44
        heat_cells = VGroup(*[Square(side_length=CS, fill_opacity=0.88, stroke_width=0.5, stroke_color=GREY_E).set_fill(interpolate_color(BLUE_E, YELLOW, HEAT[r,c]/0.6)).move_to(RIGHT*(c-3.5)*(CS+0.05)+DOWN*0.1+UP*(3.5-r)*(CS+0.05)) for r in range(8) for c in range(8)])
        row_lbls = VGroup(*[Text(SENTENCE[i], font="PingFang SC", font_size=13, color=GREY_A).move_to(LEFT*2.0+DOWN*0.1+UP*(3.5-i)*(CS+0.05)) for i in range(8)])
        col_lbls = VGroup(*[Text(SENTENCE[j], font="PingFang SC", font_size=13, color=GREY_A).move_to(RIGHT*(j-3.5)*(CS+0.05)+UP*2.3) for j in range(8)])
        apple_row_hl = Rectangle(width=8*(CS+0.05), height=CS, color=C_HI, fill_opacity=0.12, stroke_width=2).move_to(DOWN*0.1+DOWN*2.5*(CS+0.05))
        self.play(FadeOut(VGroup(k_nodes, sm_bars, sm_pcts, q_node)), LaggedStart(*[FadeIn(cell, scale=0.8) for cell in heat_cells], lag_ratio=0.01), FadeIn(row_lbls), FadeIn(col_lbls), run_time=1.5)
        self.play_at(EVENTS["20"]["highlight_apple_row"], bgn, ShowCreation(apple_row_hl))
        self.wait_beat(20, bgn)

        # Beat 21
        bgn = self.time
        mascot = AlienBody()
        mascot.set_outfit_style("judge")
        mascot.scale(0.21).move_to(RIGHT*5.5+DOWN*1.5)
        self.play(FadeIn(mascot, shift=LEFT*0.4))
        self.play(FadeOut(VGroup(title, heat_cells, row_lbls, col_lbls, apple_row_hl, mascot)))
        self.wait_beat(21, bgn)

    def scene3_5(self, hud):
        title = self._title("未知的远方", "深层网络的提纯魔法")
        self.play(Write(title))

        # Beat 22 — P1: 37s 超长段全面填充，三段叙事
        bgn = self.time
        CS = 0.35
        fuzzy_cells = VGroup(*[Square(side_length=CS, fill_opacity=0.55, stroke_width=0.5, stroke_color=GREY_E).set_fill(interpolate_color(BLUE_E, YELLOW, 0.18)).move_to(RIGHT*(c-5.5)*(CS+0.04)+UP*0.4+UP*(3.5-r)*(CS+0.04)) for r in range(8) for c in range(8)])
        layer1_lbl = Text("Layer 1\n（语义模糊）", font="PingFang SC", font_size=20, color=GREY_A).next_to(fuzzy_cells, DOWN, buff=0.3)
        HEAT_DEEP = np.array([
            [0.80,0.05,0.03,0.01,0.03,0.04,0.01,0.03],
            [0.03,0.82,0.04,0.01,0.03,0.03,0.01,0.03],
            [0.02,0.04,0.78,0.06,0.04,0.01,0.01,0.04],
            [0.02,0.04,0.05,0.80,0.04,0.01,0.01,0.03],
            [0.03,0.04,0.03,0.01,0.80,0.04,0.01,0.04],
            [0.02,0.02,0.02,0.01,0.02,0.85,0.02,0.04],
            [0.06,0.02,0.10,0.02,0.04,0.01,0.66,0.09],
            [0.02,0.04,0.04,0.01,0.04,0.01,0.04,0.80],
        ])
        deep_cells = VGroup(*[Square(side_length=CS, fill_opacity=0.88, stroke_width=0.5, stroke_color=GREY_E).set_fill(interpolate_color(BLUE_E, YELLOW, HEAT_DEEP[r,c]/0.8)).move_to(RIGHT*(c+0.5)*(CS+0.04)+UP*0.4+UP*(3.5-r)*(CS+0.04)) for r in range(8) for c in range(8)])
        layer12_lbl = Text("Layer 12+\n（语义立体清晰）", font="PingFang SC", font_size=20, color=C_HI).next_to(deep_cells, DOWN, buff=0.3)
        arrow_lr = Arrow(fuzzy_cells.get_right(), deep_cells.get_left(), buff=0.18, color=GREY_B, stroke_width=4)

        # ① 台词: "仅仅是在第一层网络中刚刚建立的，它还非常粗糙和模糊"
        self.play_at(EVENTS["22"]["show_fuzzy"], bgn,
            LaggedStart(*[FadeIn(cell, scale=0.8) for cell in fuzzy_cells], lag_ratio=0.01),
            FadeIn(layer1_lbl),
            run_time=1.0
        )
        self.play(GrowArrow(arrow_lr))

        # ② 层数递增计数器，演示「十几层甚至上百层」的过程
        layer_counter = Text("Layer  1", font="Consolas", font_size=26, color=YELLOW).move_to(arrow_lr.get_center() + UP*0.55)
        self.play(FadeIn(layer_counter))
        for target_txt, ev_key in [("Layer  4", "layer_count_4"), ("Layer  8", "layer_count_8"), ("Layer 12+", "layer_count_12")]:
            new_ctr = Text(target_txt, font="Consolas", font_size=26, color=YELLOW).move_to(arrow_lr.get_center() + UP*0.55)
            self.play_at(EVENTS["22"][ev_key], bgn, ReplacementTransform(layer_counter, new_ctr))
            layer_counter = new_ctr

        # ③ 台词: "立体的语意，才会随着层数加深，逐渐变得清晰"
        self.play_at(EVENTS["22"]["show_deep"], bgn,
            LaggedStart(*[FadeIn(cell, scale=0.8) for cell in deep_cells], lag_ratio=0.01),
            FadeIn(layer12_lbl),
            run_time=1.0
        )
        self.play(FadeOut(VGroup(title, fuzzy_cells, layer1_lbl, deep_cells, layer12_lbl, arrow_lr, layer_counter)))
        self.wait_beat(22, bgn)

    def scene4(self, hud):
        title = self._title("吸收上下文", "Value 的加权汇聚")
        self.play(Write(title))
        weights   = [0.10, 0.04, 0.18, 0.07, 0.03, 0.42, 0.12]
        BASE_W    = 2.8

        # Beat 23 — P0: 消灭空帧！补「进入最后一步·V」过渡动画
        bgn = self.time
        # 台词: "回到此刻，带着这些初级的权重，我们进入公式的最后一步——矩阵乘以V、加权求和"
        self.play(hud.pulse(color=C_V))
        last_step_lbl = Text("最后一步：· V", font="Consolas", font_size=30, color=C_V).move_to(ORIGIN)
        self.play(FadeIn(last_step_lbl, shift=UP*0.4))
        self.wait(1.5)
        self.play(FadeOut(last_step_lbl))
        self.wait_beat(23, bgn)

        # Beat 24
        bgn = self.time
        v_bars  = VGroup()
        w_lbls  = VGroup()
        sw2 = [0.10, 0.04, 0.16, 0.06, 0.05, 0.03, 0.45, 0.11]
        for i, (w, p) in enumerate(zip(SENTENCE, sw2)):
            bar = Rectangle(width=max(BASE_W*p/max(sw2), 0.18), height=0.45, color=C_V, fill_opacity=0.72, stroke_width=1).move_to(LEFT*0.3+UP*(2.1-i*0.65)).align_to(LEFT*2.8, LEFT)
            lbl = Text(f"V({w})  {int(p*100)}%", font="PingFang SC", font_size=16, color=WHITE).move_to(bar)
            v_bars.add(bar); w_lbls.add(lbl)
        self.play(LaggedStart(*[FadeIn(VGroup(b,l), shift=RIGHT*0.3) for b,l in zip(v_bars,w_lbls)], lag_ratio=0.1))
        self.play_at(EVENTS["24"]["scale_v_apple"], bgn,
            *[bar.animate.scale([0.3 + p/max(sw2), 1, 1], about_edge=LEFT) for bar, p in zip(v_bars, sw2)],
            run_time=1.2
        )
        self.play_at(EVENTS["24"]["silence_v_yige"], bgn,
            v_bars[5].animate.set_opacity(0.3),
            w_lbls[5].animate.set_opacity(0.3),
        )
        self.wait_beat(24, bgn)

        # Beat 25 — P2: 输出框加弹性 pulse，强化「吸满上下文」感
        bgn = self.time
        out_box = RoundedRectangle(corner_radius=0.3, width=3.4, height=1.4, color=PURPLE, fill_opacity=0.28, stroke_width=3).move_to(RIGHT*3.6)
        out_lbl = Text("全新表示\n（吸满上下文）", font="PingFang SC", font_size=22, weight=BOLD).move_to(out_box)
        self.play_at(EVENTS["25"]["merge_vectors"], bgn,
            LaggedStart(*[b.animate.move_to(out_box).set_opacity(0) for b in v_bars], lag_ratio=0.07),
            LaggedStart(*[l.animate.move_to(out_box).set_opacity(0) for l in w_lbls], lag_ratio=0.07),
            run_time=1.0
        )
        self.play(FadeIn(out_box), Write(out_lbl))
        # 台词: "像海绵一样，吸饱了整个序列中…上下文信息" → 弹性 pulse 强化吸收感
        self.play_at(EVENTS["25"]["pulse_out_box"], bgn,
            out_box.animate.scale(1.18).set_stroke(color=PURPLE, width=5),
            run_time=0.35
        )
        self.play(out_box.animate.scale(1/1.18).set_stroke(width=3), run_time=0.3)
        self.wait_beat(25, bgn)

        # Beat 26
        bgn = self.time
        pl = Rectangle(width=3.1, height=1.7, color=GREY_E, fill_opacity=0.28).move_to(LEFT*3.5+UP*0.2)
        pr = Rectangle(width=3.1, height=1.7, color=PURPLE,  fill_opacity=0.28).move_to(RIGHT*0.1+UP*0.2)
        ll = Text("静态嵌入", font="PingFang SC", font_size=21, color=GREY_A).move_to(pl.get_top()+DOWN*0.32)
        lr = Text("高维输出", font="PingFang SC", font_size=21, color=PURPLE).move_to(pr.get_top()+DOWN*0.32)
        same = Text("苹果₂ \u2248 苹果₆", font="PingFang SC", font_size=24, color=RED).move_to(pl)
        diff = Text("苹果₂ \u2260 苹果₆  \u2705", font="PingFang SC", font_size=24, color=GREEN).move_to(pr)
        self.play(FadeOut(VGroup(out_box, out_lbl)), FadeIn(pl), FadeIn(pr), Write(ll), Write(lr))
        self.play_at(EVENTS["26"]["show_panel_left"],  bgn, Write(same))
        self.play_at(EVENTS["26"]["show_panel_right"], bgn, Write(diff))
        self.wait_beat(26, bgn)

        # Beat 27
        bgn = self.time
        formula_s4 = Text("Attention(Q,K,V) = softmax(QK\u1d40/\u221adk)\u00b7V", font="Consolas", font_size=30, color=WHITE).move_to(DOWN*0.5)
        self.play(FadeOut(VGroup(pl, pr, ll, lr, same, diff)), Write(formula_s4))
        self.play(Indicate(formula_s4, color=YELLOW, scale_factor=1.06))
        self.play(FadeOut(VGroup(title, formula_s4)))
        self.wait_beat(27, bgn)

    def scene5(self, hud):
        title = self._title("三步，读懂一个词", "Self-Attention 巅峰复盘")
        self.play(Write(title))

        # Beat 28
        bgn = self.time
        steps = VGroup(
            Text("✅ 第一步：Q·K 点积 + 缩放 —— 计算每对词之间的原始分数", font="PingFang SC", font_size=23, color=WHITE),
            Text("✅ 第二步：Softmax 归一化 —— 将分数提纯为概率分布", font="PingFang SC", font_size=23, color=WHITE),
            Text("✅ 第三步：\u00b7V 加权求和 —— 输出融合了全局信息的新特征", font="PingFang SC", font_size=23, color=YELLOW),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to(ORIGIN+UP*0.3)
        # play_at 词级触发：三步按时间戳飞入
        self.play_at(EVENTS["28"]["step1_flyIn"], bgn, FadeIn(steps[0], shift=RIGHT*0.5))
        self.play_at(EVENTS["28"]["step2_flyIn"], bgn, FadeIn(steps[1], shift=RIGHT*0.5))
        self.play_at(EVENTS["28"]["step3_flyIn"], bgn, FadeIn(steps[2], shift=RIGHT*0.5))
        self.wait_beat(28, bgn)

        # Beat 29 — P1: O(n²) 出现后，用「全对全连线网格」可视化指数爆炸感
        bgn = self.time
        on2 = Text("O(N\u00b2)", font="Consolas", font_size=52, color=RED).move_to(LEFT*1.5+UP*0.5)
        self.play_at(EVENTS["29"]["on2_appear"], bgn, FadeIn(on2, scale=0.5))
        # 台词: "序列中每一对单词都需要两两计算相关性"
        # 6×6 节点网格 + 全连线，演示「全对全」的指数爆炸
        g_sz = 6
        grid_dots = VGroup(*[
            Dot(radius=0.09, color=GREY_A).move_to(RIGHT*(j*0.55 + 1.9) + UP*(i*0.55 - 1.15))
            for i in range(g_sz) for j in range(g_sz)
        ])
        self.play_at(EVENTS["29"]["show_grid_explode"], bgn,
            LaggedStart(*[FadeIn(d, scale=1.5) for d in grid_dots], lag_ratio=0.02),
            run_time=0.8
        )
        # 用稀疏抽样的连线（避免36²=1296条线导致卡顿）演示「两两计算」
        grid_lines = VGroup(*[
            Line(grid_dots[i].get_center(), grid_dots[j].get_center(),
                 stroke_width=0.7, stroke_opacity=0.3, color=RED)
            for i in range(len(grid_dots)) for j in range(i+1, len(grid_dots), 3)
        ])
        self.play(
            LaggedStart(*[ShowCreation(ln) for ln in grid_lines], lag_ratio=0.003),
            run_time=1.8
        )
        # FadeOut 在 wait_beat 之前，避免漂移
        self.play(FadeOut(VGroup(grid_dots, grid_lines), run_time=0.4))
        self.wait_beat(29, bgn)

        # Beat 30
        bgn = self.time
        self.play(FadeOut(on2))
        cliff = Text("单一的注意力视角只能捕捉到特定的某种模式。", font="PingFang SC", font_size=28, color=WHITE).move_to(UP*1.2)
        sub   = Text("句法、情感、指代……这些如星空般浩瀚的语言特征，\n需要截然不同的视角来同时审视。", font="PingFang SC", font_size=24, color=GREY_A).next_to(cliff, DOWN, buff=0.3)
        multi = VGroup(*[
            VGroup(Square(side_length=0.82, color=c, fill_opacity=0.5).shift(RIGHT*(i-1.5)*1.1+DOWN*1.5), Text(f"头{i+1}", font="PingFang SC", font_size=15).move_to(RIGHT*(i-1.5)*1.1+DOWN*1.5))
            for i, c in enumerate([C_Q, C_K, C_V, GOLD])
        ])
        self.play(Write(cliff), Write(sub))
        self.play_at(EVENTS["30"]["show_multi_heads"], bgn, LaggedStart(*[FadeIn(m, scale=0.6) for m in multi], lag_ratio=0.1))
        self.wait_beat(30, bgn)

        # Beat 31 — P1: 结尾补多头方块向外扩散 + 字幕，呼应台词「三头六臂，多个平行维度」
        bgn = self.time
        end = Text("下一集：Multi-Head Attention 多头注意力", font="PingFang SC", font_size=27, color=C_HI).to_edge(DOWN, buff=0.5)
        self.play(Write(end, run_time=1))
        # 台词: "大模型是如何掌除三头六臂，同时从多个平行维度理解人类语言的"
        # 4 个头方块各自向外扩散 + 边框加粗
        self.play_at(EVENTS["31"]["expand_heads"], bgn,
            LaggedStart(*[
                m[0].animate.scale(1.35).set_stroke(width=4)
                for m in multi
            ], lag_ratio=0.08),
            run_time=0.9
        )
        self.play(FadeOut(VGroup(title, cliff, sub, multi, end, hud)))
        self.wait_beat(31, bgn)

    def construct(self):
        hud = self.scene0()
        self.scene1(hud)
        self.scene2(hud)
        self.scene3(hud)
        self.scene3_5(hud)
        self.scene4(hud)
        self.scene5(hud)
