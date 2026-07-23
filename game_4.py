import tkinter as tk
from tkinter import messagebox
import random

# ==========================================
# 1. 基础卡牌与评估逻辑
# ==========================================
SUITS = {'♠': 4, '♥': 3, '♣': 2, '♦': 1}
RANKS = {'8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.val = RANKS[rank]
        self.suit_val = SUITS[suit]

    def __repr__(self):
        return f"{self.suit}{self.rank}"

def evaluate_5_cards(cards):
    """
    对5张牌进行强弱评估。返回一个可直接进行大小比较的元组。
    格式: (牌型等级, 主牌值, 辅助值1, ..., 花色值)
    """
    if len(cards) < 5:
        sorted_cards = sorted(cards, key=lambda c: (c.val, c.suit_val), reverse=True)
        return (1, sorted_cards[0].val if sorted_cards else 0, sorted_cards[0].suit_val if sorted_cards else 0)

    sorted_cards = sorted(cards, key=lambda c: c.val, reverse=True)
    vals = [c.val for c in sorted_cards]
    suits = [c.suit for c in sorted_cards]

    is_flush = len(set(suits)) == 1
    is_straight = len(set(vals)) == 5 and (vals[0] - vals[4] == 4)

    freq = {}
    for v in vals:
        freq[v] = freq.get(v, 0) + 1
    sorted_by_freq = sorted(freq.items(), key=lambda x: (x[1], x[0]), reverse=True)

    # 1. 同花顺
    if is_flush and is_straight:
        return (9, sorted_cards[0].val, sorted_cards[0].suit_val)
    # 2. 四条 (铁支)
    if sorted_by_freq[0][1] == 4:
        return (8, sorted_by_freq[0][0], sorted_by_freq[1][0])
    # 3. 葫芦
    if sorted_by_freq[0][1] == 3 and sorted_by_freq[1][1] == 2:
        return (7, sorted_by_freq[0][0], sorted_by_freq[1][0])
    # 4. 同花
    if is_flush:
        return (6, sorted_cards[0].val, sorted_cards[0].suit_val)
    # 5. 顺子
    if is_straight:
        return (5, sorted_cards[0].val, sorted_cards[0].suit_val)
    # 6. 三条
    if sorted_by_freq[0][1] == 3:
        return (4, sorted_by_freq[0][0], sorted_by_freq[1][0])
    # 7. 两对
    if sorted_by_freq[0][1] == 2 and sorted_by_freq[1][1] == 2:
        return (3, sorted_by_freq[0][0], sorted_by_freq[1][0], sorted_by_freq[2][0])
    # 8. 对子
    if sorted_by_freq[0][1] == 2:
        return (2, sorted_by_freq[0][0], [v for v, _ in sorted_by_freq[1:]])
    # 9. 单牌
    return (1, sorted_cards[0].val, sorted_cards[0].suit_val)

# ==========================================
# 2. AI名称池与玩家类定义
# ==========================================
AI_NAME_POOL = [
    "暗夜伯爵",     # 神秘莫测，喜欢在关键时刻出手
    "沙漠之狐",     # 狡猾机敏，善于在绝境中翻盘
    "幽灵赌徒",     # 行踪飘忽，无法预测下一步
    "深海巨鳄",     # 潜伏等待，一击致命
    "霓虹魅影",     # 华丽而致命，让人捉摸不透
    "风暴之眼",     # 表面平静，内心暗流涌动
    "寂静刺客",     # 沉默寡言，出手狠辣
    "迷雾行者",     # 让人看不清虚实
    "火焰判官",     # 作风强硬，不拖泥带水
    "冰霜女爵",     # 冷静如冰，计算精准
    "雷霆战将",     # 风格暴烈，速战速决
    "午夜魔术师",   # 牌桌上变幻莫测
    "铁壁守卫",     # 防守严密，滴水不漏
    "猎豹狙击手",   # 耐心等待，精准出击
    "混沌使者",     # 打乱一切秩序
]

SKILLS_INFO = {
    "偷梁换柱": {"desc": "随机抽3张牌，选1张替换自己的底牌", "cooldown": 6},
    "知己知彼": {"desc": "可以暗中偷看一名对手的底牌", "cooldown": 4},
    "洞烛先机": {"desc": "查看所有存活角色下一张将获得的牌", "cooldown": 6},
    "金蝉脱壳": {"desc": "本局若进入结算且输掉，退回本局下注的50%", "cooldown": 6},
    "瞒天过海": {"desc": "查看自己下次将要获得的牌，并可与牌堆中同点数不同花色的牌交换", "cooldown": 6},
    "移花接木": {"desc": "查看一名角色下一次要获得的牌，并可与自己的底牌交换", "cooldown": 4}
}

class Player:
    def __init__(self, name, chips, is_human=False, personality='Mathematical'):
        self.name = name
        self.chips = chips
        self.is_human = is_human
        self.personality = personality  # Conservative, Aggressive, Mathematical, Sneaky, Bluffer, CallingStation, Rock
        self.cards = []
        self.is_active = True
        self.is_bankrupt = False
        self.current_bet_contribution = 0  # 本局已投入的筹码

        # 技能冷却系统
        self.skill = None
        self.skill_ready = True           # 技能是否可用
        self.skill_cooldown = 0           # 需要获得多少张明牌才能刷新
        self.skill_cards_seen = 0         # 已获得的明牌计数
        self.golden_cicada_active = False  # 金蝉脱壳保险标记

    def reset_hand(self):
        self.cards = []
        self.current_bet_contribution = 0
        self.golden_cicada_active = False
        if self.chips <= 0 and not self.is_bankrupt:
            self.is_bankrupt = True
            self.is_active = False

# ==========================================
# 3. 主游戏界面与逻辑
# ==========================================
class ShowHandGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("沙蟹对决 - 电影级策略游戏")
        self.root.geometry("1150x750")
        self.root.configure(bg="#0d3326")
        self.root.minsize(1000, 650)

        self.init_game_state()
        self.build_ui()
        self.start_new_hand()

    def init_game_state(self):
        # 初始化玩家 (1人 + 3名AI)
        personalities = ['Conservative', 'Aggressive', 'Mathematical', 'Sneaky',
                         'Bluffer', 'CallingStation', 'Rock']
        random.shuffle(personalities)

        # 从名称池中随机抽取3个不重复的名称
        ai_names = random.sample(AI_NAME_POOL, 3)

        self.players = [
            Player("玩家(你)", 10000, is_human=True),
            Player(ai_names[0], 10000, is_human=False, personality=personalities[0]),
            Player(ai_names[1], 10000, is_human=False, personality=personalities[1]),
            Player(ai_names[2], 10000, is_human=False, personality=personalities[2])
        ]

        # 随机分配技能（初始即可用）
        all_skills = list(SKILLS_INFO.keys())
        random.shuffle(all_skills)
        for i, p in enumerate(self.players):
            p.skill = all_skills[i % len(all_skills)]
            p.skill_ready = True
            p.skill_cooldown = SKILLS_INFO[p.skill]["cooldown"]
            p.skill_cards_seen = 0

        self.deck = []
        self.pot = 0
        self.current_call_amount = 0  # 当前需要跟注的总额
        self.game_stage = 2           # 当前发牌张数阶段 (2, 3, 4, 5)
        self.current_turn_index = 0   # 轮到谁行动

    # ==========================================
    # 辅助：计算某玩家下一张将获得的牌
    # ==========================================
    def get_player_next_card_index(self, player):
        """返回某玩家在牌堆中的下一张牌索引（按发牌顺序）。"""
        idx = 0
        for p in self.players:
            if p == player:
                break
            if p.is_active:
                idx += 1
        return idx

    def get_player_next_card(self, player):
        """获取某玩家下一张将获得的牌，若无则返回None。"""
        idx = self.get_player_next_card_index(player)
        if idx < len(self.deck):
            return self.deck[idx]
        return None

    def find_matching_cards_in_deck(self, target_card):
        """在牌堆中寻找与target_card同点数但不同花色的牌。"""
        result = []
        for i, c in enumerate(self.deck):
            if c.val == target_card.val and c.suit != target_card.suit:
                result.append((i, c))
        return result

    # ==========================================
    # 4. 界面构建
    # ==========================================
    def build_ui(self):
        BG = "#0b0f19"      # 主背景·深蓝黑
        GOLD = "#c9a96e"     # 金色·标题/边框
        CARD_TABLE = "#111827"  # 牌桌区
        PANEL_BG = "#1a1f35"    # 玩家面板
        LOG_BG = "#0d1117"      # 日志背景

        # === 顶部标题栏 ===
        self.title_bar = tk.Frame(self.root, bg="#060910", height=48)
        self.title_bar.pack(fill=tk.X)
        tk.Label(self.title_bar, text="◆  沙 蟹 对 决  ◆",
                 font=("Georgia", 22, "bold"), fg=GOLD, bg="#060910").pack(pady=6)

        # === 信息栏（紧凑一行） ===
        self.info_bar = tk.Frame(self.root, bg=BG)
        self.info_bar.pack(fill=tk.X, padx=20, pady=(6, 0))
        self.pot_label = tk.Label(self.info_bar, text="奖池: $0", font=("Georgia", 16, "bold"),
                                  fg=GOLD, bg=BG)
        self.pot_label.pack(side=tk.LEFT)
        self.status_label = tk.Label(self.info_bar, text="准备开始...", font=("Microsoft YaHei", 10),
                                     fg="#8899aa", bg=BG)
        self.status_label.pack(side=tk.RIGHT)
        self.stage_label = tk.Label(self.info_bar, text="第2张牌", font=("Georgia", 13, "bold"),
                                    fg="#ccd6e0", bg=BG)
        self.stage_label.pack(side=tk.RIGHT, padx=(0, 20))

        # === 中部主区域 ===
        self.main_area = tk.Frame(self.root, bg=BG)
        self.main_area.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        # 左侧：牌桌
        self.table_frame = tk.Frame(self.main_area, bg=CARD_TABLE, bd=1,
                                    relief=tk.SOLID, highlightbackground=GOLD,
                                    highlightthickness=1)
        self.table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 右侧：日志面板
        self.log_frame = tk.Frame(self.main_area, bg=LOG_BG, width=255, bd=1,
                                  relief=tk.SOLID, highlightbackground=GOLD,
                                  highlightthickness=1)
        self.log_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        tk.Label(self.log_frame, text="◆ 战局实录 ◆", font=("Georgia", 11, "bold"),
                 fg=GOLD, bg=LOG_BG).pack(pady=6)
        self.log_text = tk.Text(self.log_frame, width=28, bg="#060910", fg="#7eb8a0",
                                font=("Consolas", 10), state=tk.DISABLED,
                                relief=tk.FLAT, bd=0, wrap=tk.WORD,
                                insertbackground="#7eb8a0")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # 创建4个玩家面板
        self.player_panels = []
        for i in range(4):
            frame = tk.LabelFrame(self.table_frame, text="", bg=PANEL_BG, fg=GOLD,
                                  font=("Microsoft YaHei", 10, "bold"), bd=1,
                                  relief=tk.SOLID, labelanchor="n")
            frame.grid(row=i // 2, column=i % 2, padx=14, pady=14, sticky="nsew")

            lbl_info = tk.Label(frame, text="", bg=PANEL_BG, fg="#ccd6e0",
                                justify=tk.LEFT, font=("Microsoft YaHei", 9))
            lbl_info.pack(anchor=tk.W, padx=10, pady=(6, 0))

            card_container = tk.Frame(frame, bg=PANEL_BG)
            card_container.pack(fill=tk.BOTH, expand=True, pady=6)

            self.player_panels.append({
                "frame": frame, "info": lbl_info, "card_container": card_container
            })

        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(1, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(1, weight=1)

        # === 底部控制栏 ===
        self.control_frame = tk.Frame(self.root, bg="#0d1117", height=65)
        self.control_frame.pack(fill=tk.X)

        B = {"font": ("Microsoft YaHei", 10, "bold"), "width": 13, "height": 2,
             "relief": tk.FLAT, "bd": 0, "cursor": "hand2", "fg": "white",
             "activeforeground": "white"}

        self.btn_fold = tk.Button(self.control_frame, text="弃牌 Fold", bg="#c0392b",
                                  activebackground="#e74c3c", command=self.action_fold, **B)
        self.btn_fold.pack(side=tk.LEFT, padx=(18, 4), pady=12)

        self.btn_call = tk.Button(self.control_frame, text="跟注 Call", bg="#2980b9",
                                  activebackground="#3498db", command=self.action_call, **B)
        self.btn_call.pack(side=tk.LEFT, padx=4, pady=12)

        self.btn_raise = tk.Button(self.control_frame, text="加注 Raise", bg="#8e44ad",
                                   activebackground="#9b59b6", command=self.show_raise_dialog, **B)
        self.btn_raise.pack(side=tk.LEFT, padx=4, pady=12)

        self.btn_allin = tk.Button(self.control_frame, text="梭哈 All-in", bg="#d35400",
                                   activebackground="#e67e22", command=self.action_allin, **B)
        self.btn_allin.pack(side=tk.LEFT, padx=4, pady=12)

        # 右侧：查看底牌 + 技能
        self.btn_peek = tk.Button(self.control_frame, text="👁 底牌", bg="#1a6b52",
                                  activebackground="#1abc9c", command=self.peek_hole_card, **B)
        self.btn_peek.config(width=10)
        self.btn_peek.pack(side=tk.RIGHT, padx=(4, 18), pady=12)

        self.btn_skill = tk.Button(self.control_frame, text="◆ 特权技能 ◆", bg="#8a6d10",
                                   activebackground="#c9a96e", fg="#f5e6c8",
                                   font=("Microsoft YaHei", 10, "bold"), width=14, height=2,
                                   relief=tk.FLAT, bd=0, cursor="hand2",
                                   command=self.use_player_skill)
        self.btn_skill.pack(side=tk.RIGHT, padx=4, pady=12)

    def log_message(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def skill_popup(self, title, message):
        """技能触发弹窗提示 + 刷新整个界面"""
        messagebox.showinfo(title, message)
        self.update_ui_display()

    # ==========================================
    # 5. 核心对局控制
    # ==========================================
    def start_new_hand(self):
        self.log_message("\n━━━━━━━━ 新一局游戏开始 ━━━━━━━━")

        # 检查游戏结束
        human = self.players[0]
        if human.is_bankrupt:
            self.log_message("[游戏结束] 你已经破产！")
            messagebox.showerror("游戏结束", "您已破产，无力偿还赌债，游戏结束。")
            self.root.quit()
            return

        alive_opponents = [p for p in self.players if not p.is_human and not p.is_bankrupt]
        if not alive_opponents:
            self.log_message("[游戏结束] 你击败了所有对手！")
            messagebox.showinfo("大获全胜", "恭喜！您成功击败了所有对手，成为了新一代赌神！")
            self.root.quit()
            return

        # 洗牌与初始化
        self.deck = [Card(suit, rank) for suit in SUITS.keys() for rank in RANKS.keys()]
        random.shuffle(self.deck)
        random.shuffle(self.deck)  # 二次洗牌确保完全随机

        # 2人对局底注500，多人局200
        alive_count = len([p for p in self.players if not p.is_bankrupt])
        ante = 500 if alive_count <= 2 else 200

        self.pot = 0
        self.current_call_amount = ante
        self.game_stage = 2

        for p in self.players:
            p.reset_hand()
            if not p.is_bankrupt:
                p.is_active = True
                p.chips -= ante
                p.current_bet_contribution = ante
                self.pot += ante
                # 发两张初始牌
                p.cards.append(self.deck.pop(0))
                p.cards.append(self.deck.pop(0))

        self.update_ui_display()
        self.start_betting_round()

    def update_ui_display(self):
        self.pot_label.config(text=f"奖池筹码: ${self.pot}")
        self.stage_label.config(text=f"第{self.game_stage}张牌阶段")

        for i, p in enumerate(self.players):
            if i >= len(self.player_panels):
                continue
            panel = self.player_panels[i]

            # 清理旧牌
            for widget in panel["card_container"].winfo_children():
                widget.destroy()

            if p.is_bankrupt:
                panel["frame"].config(text=f"{p.name} (出局)", bg="#3a3a3a", fg="#777")
                panel["info"].config(text="资产: 已破产", bg="#3a3a3a", fg="#777")
                continue

            # 更新面板标题和状态
            status_text = "【已弃牌】" if not p.is_active else ""
            if p.is_human:
                if p.skill_ready:
                    skill_text = f"技能: {p.skill} [就绪]"
                else:
                    skill_text = f"技能: 冷却中({p.skill_cards_seen}/{p.skill_cooldown})"
                if p.golden_cicada_active:
                    skill_text += " [金蝉护体]"
            else:
                skill_text = "技能: ???"
                if p.golden_cicada_active:
                    skill_text += " [???]"

            panel["frame"].config(text=f"{p.name} {status_text}", bg="#1a1f35", fg="#c9a96e")

            role_desc = "玩家" if p.is_human else "AI (风格: ???)"
            chips_display = "无限" if p.name == "无限庄家" else f"${p.chips}"
            info_str = f"性质: {role_desc}\n筹码: {chips_display}\n投入: ${p.current_bet_contribution}\n{skill_text}"
            panel["info"].config(text=info_str, bg="#1a1f35", fg="#ccd6e0")

            # 绘制卡牌
            if p.is_active:
                for idx, card in enumerate(p.cards):
                    is_hidden = (idx == 0)

                    if is_hidden:
                        card_bg = "#2a3040"
                        card_fg = "#6b7d95"
                        card_text = "？"
                    else:
                        card_bg = "#faf8f5"
                        card_fg = "#c0392b" if card.suit in ['♥', '♦'] else "#1a1a2e"
                        card_text = f"{card.suit}{card.rank}"

                    card_lbl = tk.Label(panel["card_container"], text=card_text,
                                        font=("Georgia", 18, "bold"),
                                        bg=card_bg, fg=card_fg, width=4, height=2,
                                        relief=tk.RAISED, bd=4)
                    card_lbl.pack(side=tk.LEFT, padx=6)

        # 玩家控制按钮状态切换
        human = self.players[0]
        if self.is_human_turn() and human.is_active:
            self.enable_controls(True)
        else:
            self.enable_controls(False)

    def is_human_turn(self):
        return self.players[self.current_turn_index].is_human

    def enable_controls(self, enable=True):
        state = tk.NORMAL if enable else tk.DISABLED
        human = self.players[0]

        if enable and human.is_active:
            to_call = self.current_call_amount - human.current_bet_contribution
            active_count = len([p for p in self.players if p.is_active])
            self.btn_fold.config(state=state)
            self.btn_raise.config(state=state)
            self.btn_allin.config(state=state)
            self.btn_peek.config(state=tk.NORMAL)
            # 2人对局不允许看牌（禁止连续check），必须下注或弃牌
            if to_call <= 0 and active_count > 2:
                self.btn_call.config(text="看牌 Check", bg="#27ae60", state=state)
            elif to_call <= 0 and active_count <= 2:
                self.btn_call.config(text="看牌(禁止) 请加注", bg="#555555", state=tk.DISABLED)
            else:
                self.btn_call.config(text=f"跟注 Call (${to_call})", bg="#2980b9", state=state)
        else:
            for btn in [self.btn_fold, self.btn_call, self.btn_raise, self.btn_allin]:
                btn.config(state=tk.DISABLED)
            self.btn_peek.config(state=tk.NORMAL)

        # 技能按钮
        if human.skill_ready and not human.is_bankrupt and human.is_active:
            self.btn_skill.config(state=tk.NORMAL, bg="#8a6d10",
                                  text=f"◆ {human.skill} ◆")
        elif human.skill and not human.is_bankrupt:
            self.btn_skill.config(state=tk.DISABLED, bg="#444",
                                  text=f"◆ 冷却中 ({human.skill_cards_seen}/{human.skill_cooldown}) ◆")
        else:
            self.btn_skill.config(state=tk.DISABLED)

    def peek_hole_card(self):
        """弹窗显示底牌，3秒后自动关闭"""
        human = self.players[0]
        if not human.is_active or not human.cards:
            return
        hole_card = human.cards[0]

        popup = tk.Toplevel(self.root)
        popup.title("查看底牌")
        popup.geometry("240x150")
        popup.configure(bg="#1a1a2e")
        popup.transient(self.root)
        popup.grab_set()

        card_fg = "#e74c3c" if hole_card.suit in ['♥', '♦'] else "#ecf0f1"
        tk.Label(popup, text="你的底牌", font=("Microsoft YaHei", 12),
                 fg="#f1c40f", bg="#1a1a2e").pack(pady=(18, 8))
        tk.Label(popup, text=f"{hole_card.suit}{hole_card.rank}",
                 font=("Georgia", 28, "bold"), fg=card_fg, bg="#1a1a2e").pack(pady=5)
        tk.Label(popup, text="(3秒后自动关闭)", font=("Microsoft YaHei", 9),
                 fg="#7f8c8d", bg="#1a1a2e").pack(pady=(2, 0))

        popup.after(3000, popup.destroy)

    # ==========================================
    # 6. 下注逻辑与决策循环
    # ==========================================
    def start_betting_round(self):
        self.log_message(f"\n[牌局] 进入第 {self.game_stage} 张牌下注阶段...")
        # 寻找拥有最强明牌的玩家作为先行者
        best_rank = (-1,)
        first_player_idx = 0
        for i, p in enumerate(self.players):
            if p.is_active:
                temp_score = evaluate_5_cards(p.cards[1:])
                if temp_score > best_rank:
                    best_rank = temp_score
                    first_player_idx = i

        self.current_turn_index = first_player_idx
        self.round_start_player = first_player_idx  # 记录本轮起始玩家
        self.start_player_acted = False             # 起始玩家是否已经行动过
        self.has_completed_orbit = False            # 是否已完成一整圈
        self.log_message(f"[秩序] 牌面最大者【{self.players[first_player_idx].name}】首先行动。")
        self.next_turn()

    def next_turn(self):
        # 检查是否所有人都完成了下注匹配
        active_players = [p for p in self.players if p.is_active]
        if len(active_players) <= 1:
            self.settle_hand()
            return

        # 检测是否完成一整圈：第一次到达起始玩家标记"已行动"，
        # 再次回到起始玩家时才标记"完成一圈"
        if self.current_turn_index == self.round_start_player:
            if self.start_player_acted:
                self.has_completed_orbit = True
            else:
                self.start_player_acted = True

        # 判断是否本轮所有人的筹码已经对齐
        all_aligned = True
        for p in active_players:
            if p.current_bet_contribution < self.current_call_amount:
                if p.chips > 0:
                    all_aligned = False
                    break

        # 只有完成一整圈且所有人筹码对齐，才进入下一阶段
        if all_aligned and self.has_completed_orbit:
            self.advance_stage()
            return

        current_player = self.players[self.current_turn_index]
        if not current_player.is_active:
            self.pass_turn()
            return

        self.status_label.config(text=f"等待 【{current_player.name}】 做出决策...")
        self.update_ui_display()

        if current_player.is_human:
            self.log_message("[提示] 轮到你做出决策。")
        else:
            self.root.after(3000, self.ai_decision)

    def pass_turn(self):
        self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
        self.next_turn()

    def advance_stage(self):
        if self.game_stage < 5:
            self.game_stage += 1
            self.log_message(f"\n[发牌] 开始发放第 {self.game_stage} 张明牌...")
            for p in self.players:
                if p.is_active:
                    p.cards.append(self.deck.pop(0))
                    # 冷却计数：累计获得的明牌数，达到阈值刷新技能
                    if not p.skill_ready:
                        p.skill_cards_seen += 1
                        if p.skill_cards_seen >= p.skill_cooldown:
                            p.skill_ready = True
                            p.skill_cards_seen = 0
                            if p.is_human:
                                self.log_message(f"[技能刷新] 你的技能【{p.skill}】冷却完毕，可以再次使用！")
                            else:
                                self.log_message("[特权提示] 虚空中有一股空气流动。")
            self.update_ui_display()
            self.start_betting_round()
        else:
            self.settle_hand()

    # ==========================================
    # 7. AI 行为机制
    # ==========================================
    def ai_decision(self):
        ai = self.players[self.current_turn_index]
        if not ai.is_active:
            self.pass_turn()
            return

        score = evaluate_5_cards(ai.cards)
        to_call = self.current_call_amount - ai.current_bet_contribution

        # 技能触发概率：各性格不同
        skill_chance = {"Conservative": 0.10, "Aggressive": 0.22,
                        "Mathematical": 0.15, "Sneaky": 0.18,
                        "Bluffer": 0.20, "CallingStation": 0.06,
                        "Rock": 0.05}
        # 各性格触发技能的时机偏好
        should_use_skill = False
        if ai.skill_ready and random.random() < skill_chance.get(ai.personality, 0.15):
            if ai.personality == 'Conservative':
                # 保守型：手牌弱时用技能保命（评分<3时触发）
                should_use_skill = (score[0] < 3)
            elif ai.personality == 'Aggressive':
                # 狂妄型：随时用技能，尤其手牌强时乘胜追击
                should_use_skill = True
            elif ai.personality == 'Mathematical':
                # 数学型：前期牌少时用技能获取信息优势
                should_use_skill = (len(ai.cards) <= 3)
            elif ai.personality == 'Sneaky':
                # 阴险型：手牌中等时用技能制造变数
                should_use_skill = (2 <= score[0] <= 5)
            elif ai.personality == 'Bluffer':
                # 诈唬型：手牌弱时用技能制造混乱假象
                should_use_skill = (score[0] <= 3)
            elif ai.personality == 'CallingStation':
                # 跟注站型：很少主动用技能，手牌较强时才想起来
                should_use_skill = (score[0] >= 5)
            elif ai.personality == 'Rock':
                # 岩石型：几乎不用技能，只在顶级手牌时才用
                should_use_skill = (score[0] >= 7)
        if should_use_skill:
            self.trigger_ai_skill(ai)
            if not ai.is_active:
                return

        # AI性格行为策略决策
        decision = "fold"
        active_count = len([p for p in self.players if p.is_active])
        if to_call == 0 and active_count > 2:
            decision = "check"
        elif to_call == 0 and active_count <= 2:
            # 2人对局不允许看牌：按性格决定加注/弃牌
            if ai.personality == 'Conservative':
                decision = "fold" if random.random() < 0.30 else "raise"
            elif ai.personality == 'Aggressive':
                decision = "fold" if random.random() < 0.08 else "raise"
            elif ai.personality == 'Mathematical':
                # 数学型：牌力估值决定
                if score[0] >= 2:
                    decision = "raise"
                else:
                    decision = "fold" if random.random() < 0.25 else "raise"
            elif ai.personality == 'Sneaky':
                # 阴险型：手牌弱也敢加注诈唬
                if score[0] >= 3:
                    decision = "raise"  # 有好牌，正常加注
                else:
                    decision = "fold" if random.random() < 0.20 else "raise"  # 80%诈唬加注
            elif ai.personality == 'Bluffer':
                # 诈唬型：2人局更是疯狂加注
                decision = "fold" if random.random() < 0.10 else "raise"
            elif ai.personality == 'CallingStation':
                # 跟注站型：2人局被迫加注，但很不情愿
                if score[0] >= 3:
                    decision = "raise"
                else:
                    decision = "fold" if random.random() < 0.40 else "raise"
            elif ai.personality == 'Rock':
                # 岩石型：2人局适当放宽，但弱牌仍有顾虑
                if score[0] >= 2:
                    decision = "raise"
                else:
                    decision = "fold" if random.random() < 0.50 else "raise"

        # 底池赔率
        pot_after_call = self.pot + to_call
        pot_odds_ratio = to_call / max(pot_after_call, 1)

        if ai.personality == 'Conservative':
            # 保守型：两对以上才主动，但大幅提高弃牌线
            if score[0] >= 3:  # 两对+
                decision = "call" if to_call < ai.chips else "fold"
                if score[0] >= 5 and random.random() < 0.3:
                    decision = "raise"
            elif score[0] >= 2:  # 一对
                decision = "call" if to_call < 3000 else "fold"
            else:
                # 高牌：小额就跟，大额才弃
                decision = "call" if to_call < 1500 else "fold"

        elif ai.personality == 'Aggressive':
            # 狂妄型：几乎不弃牌，高概率加注/全押
            if score[0] >= 2 or random.random() < 0.45:
                if random.random() < 0.25:
                    decision = "allin"
                elif random.random() < 0.45:
                    decision = "raise"
                else:
                    decision = "call"
            else:
                decision = "fold" if to_call > 4000 else "call"

        elif ai.personality == 'Mathematical':
            # 数学型：用底池赔率+牌力综合判断
            win_rate_est = max(score[0] / 9.0, 0.1)  # 最低10%胜率估计
            # 加上不确定性：前期牌少时提高胜率估计
            if len(ai.cards) <= 3:
                win_rate_est = max(win_rate_est, 0.25)
            if win_rate_est > pot_odds_ratio * 0.8:
                if win_rate_est > 0.6:
                    decision = "raise"
                else:
                    decision = "call"
            else:
                decision = "fold" if to_call > 2500 else "call"

        elif ai.personality == 'Sneaky':
            # 阴险型：持大牌假装示弱，持弱牌反而可能加注诈唬
            if score[0] >= 6:  # 同花/葫芦
                decision = "call"  # 慢打诱敌
            elif score[0] >= 3:  # 两对+
                decision = "raise" if random.random() < 0.4 else "call"
            elif score[0] >= 2:  # 一对
                if random.random() < 0.3:
                    decision = "raise"  # 诈唬
                else:
                    decision = "call" if to_call < 3000 else "fold"
            else:
                # 高牌：有一定概率诈唬加注
                if random.random() < 0.2:
                    decision = "raise"
                else:
                    decision = "call" if to_call < 2000 else "fold"

        elif ai.personality == 'Bluffer':
            # 诈唬型：频繁加注虚张声势，手牌强弱都敢打
            if score[0] >= 5:  # 顺子+
                # 有好牌反而假装犹豫，偶尔慢打
                decision = "raise" if random.random() < 0.5 else "call"
            elif score[0] >= 3:  # 两对+
                # 中等牌力混合策略
                if random.random() < 0.45:
                    decision = "raise"
                elif random.random() < 0.3:
                    decision = "allin" if to_call > 3000 else "raise"
                else:
                    decision = "call"
            elif score[0] >= 2:  # 一对
                # 一对时高频率诈唬加注
                if random.random() < 0.55:
                    decision = "raise"
                elif random.random() < 0.15:
                    decision = "allin"
                else:
                    decision = "call" if to_call < 2500 else "fold"
            else:
                # 高牌也敢诈唬，但大额跟注时会退缩
                if random.random() < 0.40:
                    decision = "raise"
                else:
                    decision = "call" if to_call < 1500 else "fold"

        elif ai.personality == 'CallingStation':
            # 跟注站型：几乎不弃牌，但也很少主动加注
            if score[0] >= 6:  # 同花/葫芦
                # 超强牌才偶尔加注
                decision = "raise" if random.random() < 0.25 else "call"
            elif score[0] >= 3:  # 两对+
                decision = "call"  # 有牌就跟
            elif score[0] >= 2:  # 一对
                decision = "call" if to_call < 5000 else "fold"
            else:
                # 高牌也跟，只有超大额才弃
                decision = "call" if to_call < 3500 else "fold"

        elif ai.personality == 'Rock':
            # 岩石型：偏爱强牌，但也会适当参与中等牌力局
            if score[0] >= 7:  # 葫芦/四条/同花顺
                decision = "raise" if random.random() < 0.6 else "allin"
            elif score[0] >= 5:  # 顺子/同花
                decision = "raise" if random.random() < 0.5 else "call"
            elif score[0] >= 3:  # 两对
                # 两对值得参与，偶尔加注施压
                if random.random() < 0.3:
                    decision = "raise"
                else:
                    decision = "call" if to_call < 6000 else "fold"
            elif score[0] >= 2:  # 一对
                # 一对根据跟注金额决定，不再过度弃牌
                if to_call < 3000:
                    decision = "call"
                elif to_call < 6000:
                    decision = "call" if random.random() < 0.5 else "fold"
                else:
                    decision = "fold" if random.random() < 0.70 else "call"
            else:
                # 高牌小额可观望，大额则弃
                if to_call < 1200:
                    decision = "call" if random.random() < 0.35 else "fold"
                else:
                    decision = "fold" if random.random() < 0.85 else "call"

        # 执行动作
        if decision == "fold":
            self.execute_fold(ai)
        elif decision in ["check", "call"]:
            self.execute_call(ai)
        elif decision == "raise":
            self.execute_raise(ai, 500)
        elif decision == "allin":
            self.execute_allin(ai)

    def trigger_ai_skill(self, ai):
        """AI 暗中自主选择使用技能"""
        if not ai.skill_ready:
            return
        ai.skill_ready = False
        ai.skill_cards_seen = 0

        if ai.skill == "偷梁换柱":
            candidates = [self.deck.pop(0) for _ in range(3)]
            best_card = ai.cards[0]
            best_score = evaluate_5_cards(ai.cards)

            for c in candidates:
                temp_cards = list(ai.cards)
                temp_cards[0] = c
                if evaluate_5_cards(temp_cards) > best_score:
                    best_card = c
                    best_score = evaluate_5_cards(temp_cards)

            ai.cards[0] = best_card
            for c in candidates:
                if c != best_card:
                    self.deck.append(c)
            random.shuffle(self.deck)
            self.skill_popup("⚠ 技能发动", "虚空中有一股空气流动。")

        elif ai.skill == "知己知彼":
            self.skill_popup("⚠ 技能发动", "虚空中有一股空气流动。")

        elif ai.skill == "洞烛先机":
            self.skill_popup("⚠ 技能发动", "虚空中有一股空气流动。")

        elif ai.skill == "金蝉脱壳":
            ai.golden_cicada_active = True
            self.skill_popup("⚠ 技能发动", "虚空中有一股空气流动。")

        elif ai.skill == "瞒天过海":
            next_card = self.get_player_next_card(ai)
            if next_card:
                matches = self.find_matching_cards_in_deck(next_card)
                if matches:
                    best_match = max(matches, key=lambda m: m[1].suit_val)
                    deck_idx, new_card = best_match
                    self.deck[deck_idx] = next_card
                    ai_next_idx = self.get_player_next_card_index(ai)
                    if ai_next_idx < len(self.deck):
                        self.deck[ai_next_idx] = new_card
            self.skill_popup("⚠ 技能发动", "虚空中有一股空气流动。")

        elif ai.skill == "移花接木":
            targets = [p for p in self.players if p != ai and p.is_active]
            if targets:
                target = random.choice(targets)
                target_next_idx = self.get_player_next_card_index(target)
                if target_next_idx < len(self.deck):
                    target_next_card = self.deck[target_next_idx]
                    temp_cards = list(ai.cards)
                    old_hole = temp_cards[0]
                    temp_cards[0] = target_next_card
                    new_score = evaluate_5_cards(temp_cards)
                    old_score = evaluate_5_cards(ai.cards)
                    if new_score > old_score:
                        ai.cards[0] = target_next_card
                        self.deck[target_next_idx] = old_hole
            self.skill_popup("⚠ 技能发动", "虚空中有一股空气流动。")

    # ==========================================
    # 8. 玩家/AI 动作执行
    # ==========================================
    def execute_fold(self, player):
        player.is_active = False
        self.log_message(f"[行动] 【{player.name}】 选择折牌(弃牌)。")
        self.update_ui_display()
        self.pass_turn()

    def execute_call(self, player):
        to_call = self.current_call_amount - player.current_bet_contribution
        if to_call > player.chips:
            to_call = player.chips

        player.chips -= to_call
        player.current_bet_contribution += to_call
        self.pot += to_call
        self.log_message(f"[行动] 【{player.name}】 跟注了 ${to_call}。")
        self.update_ui_display()
        self.pass_turn()

    def execute_raise(self, player, amount):
        to_call = self.current_call_amount - player.current_bet_contribution
        total_needed = to_call + amount

        if total_needed > player.chips:
            total_needed = player.chips

        player.chips -= total_needed
        player.current_bet_contribution += total_needed
        self.pot += total_needed
        self.current_call_amount = player.current_bet_contribution
        self.log_message(f"[行动] 【{player.name}】 额外加注了 ${amount} (当前需跟注 ${self.current_call_amount})。")
        self.update_ui_display()
        self.pass_turn()

    def execute_allin(self, player):
        allin_amount = player.chips
        player.chips = 0
        player.current_bet_contribution += allin_amount
        self.pot += allin_amount
        if player.current_bet_contribution > self.current_call_amount:
            self.current_call_amount = player.current_bet_contribution
        self.log_message(f"[惊呼] 【{player.name}】 押上了全部财产，选择 梭哈(ShowHand)！！")
        self.update_ui_display()
        self.pass_turn()

    # 人类动作映射
    def action_fold(self):
        self.execute_fold(self.players[0])

    def action_call(self):
        self.execute_call(self.players[0])

    def action_allin(self):
        self.execute_allin(self.players[0])

    # ==========================================
    # 9. 加注对话框（多档位）
    # ==========================================
    def show_raise_dialog(self):
        """弹出加注档位选择对话框"""
        human = self.players[0]
        to_call = self.current_call_amount - human.current_bet_contribution
        pot_size = self.pot

        dialog = tk.Toplevel(self.root)
        dialog.title("选择加注金额")
        dialog.geometry("420x320")
        dialog.configure(bg="#0b0f19")
        dialog.transient(self.root)
        dialog.grab_set()

        # 信息区
        info_frame = tk.Frame(dialog, bg="#0b0f19")
        info_frame.pack(fill=tk.X, padx=20, pady=(15, 8))
        tk.Label(info_frame, text=f"当前底池: ${pot_size}    需跟注: ${to_call}",
                 font=("Microsoft YaHei", 11), fg="#c9a96e", bg="#0b0f19").pack()

        # 预设档位按钮
        presets = [
            ("轻注  $300", 300, "#27ae60"),
            ("中注  $600", 600, "#2980b9"),
            ("重注  $1200", 1200, "#8e44ad"),
            ("超重注 $2500", 2500, "#d35400"),
        ]

        btn_frame = tk.Frame(dialog, bg="#0b0f19")
        btn_frame.pack(pady=5)

        for text, amount, color in presets:
            available = amount <= human.chips
            btn_text = text if available else f"{text} (余额不足)"
            state = tk.NORMAL if available else tk.DISABLED
            btn = tk.Button(btn_frame, text=btn_text, font=("Microsoft YaHei", 11, "bold"),
                            width=16, bg=color, fg="white", relief=tk.FLAT, bd=0,
                            activebackground=color, cursor="hand2", state=state,
                            command=lambda a=amount: self.execute_raise_amount(dialog, a))
            btn.pack(pady=3)

        # 分隔线
        tk.Frame(dialog, bg="#c9a96e", height=1).pack(fill=tk.X, padx=30, pady=8)

        # 自定义金额
        custom_frame = tk.Frame(dialog, bg="#0b0f19")
        custom_frame.pack()
        tk.Label(custom_frame, text="自定义金额: $", font=("Microsoft YaHei", 10),
                 fg="#ccd6e0", bg="#0b0f19").pack(side=tk.LEFT)
        entry = tk.Entry(custom_frame, font=("Microsoft YaHei", 12, "bold"), width=10,
                         bg="#1a1f35", fg="#c9a96e", insertbackground="#c9a96e",
                         relief=tk.FLAT, bd=2, justify=tk.CENTER)
        entry.pack(side=tk.LEFT, padx=8)

        tk.Button(custom_frame, text="确认", font=("Microsoft YaHei", 10, "bold"),
                  width=6, bg="#c9a96e", fg="#0b0f19", relief=tk.FLAT, bd=0,
                  cursor="hand2", activebackground="#d4b87a",
                  command=lambda: self._custom_raise(dialog, entry)).pack(side=tk.LEFT, padx=5)

        # 底部提示
        tk.Label(dialog, text="💡 轻注不易吓跑对手 · 重注容易清场",
                 font=("Microsoft YaHei", 9), fg="#667788", bg="#0b0f19").pack(pady=(10, 8))

    def _custom_raise(self, dialog, entry):
        """处理自定义加注金额"""
        try:
            amount = int(entry.get())
            if amount > 0:
                self.execute_raise_amount(dialog, amount)
            else:
                messagebox.showwarning("无效金额", "请输入大于0的整数金额。")
        except ValueError:
            messagebox.showwarning("无效金额", "请输入有效的整数金额。")

    def execute_raise_amount(self, dialog, amount):
        """执行指定金额的加注"""
        dialog.destroy()
        human = self.players[0]
        if amount > human.chips:
            amount = human.chips
        self.execute_raise(human, amount)

    # ==========================================
    # 10. 玩家专属特权技能应用
    # ==========================================
    def use_player_skill(self):
        human = self.players[0]
        if not human.skill_ready:
            messagebox.showwarning("冷却中",
                f"技能【{human.skill}】冷却中！\n还需获得 {human.skill_cooldown - human.skill_cards_seen} 张明牌后刷新。")
            return
        if not human.is_active:
            messagebox.showwarning("限制", "您已经弃牌，无法使用技能！")
            return

        skill = human.skill

        # 统一技能发动提示
        self.skill_popup("⚠ 技能发动", "虚空中有一股空气流动。")

        # 技能进入冷却
        human.skill_ready = False
        human.skill_cards_seen = 0

        if skill == "偷梁换柱":
            if len(self.deck) < 3:
                messagebox.showwarning("牌不够", "牌堆剩余牌不足3张，无法发动偷梁换柱！")
                human.skill_ready = True  # 发动失败，恢复可用
                return
            candidates = [self.deck.pop(0) for _ in range(3)]
            self.show_swap_dialog(candidates)

        elif skill == "知己知彼":
            targets = [p for p in self.players if not p.is_human and p.is_active]
            if not targets:
                messagebox.showinfo("没人", "当前没有能窥视的目标。")
                human.skill_ready = True
                return
            self.show_peep_dialog(targets)

        elif skill == "洞烛先机":
            predictions = []
            for p in self.players:
                if p.is_active:
                    next_card = self.get_player_next_card(p)
                    if next_card:
                        predictions.append(f"{p.name} 的下一张牌预测为: {next_card}")
                    else:
                        predictions.append(f"{p.name}: 牌堆已空，无下一张牌")
            if not predictions:
                predictions.append("当前无存活玩家或牌堆已空。")
            messagebox.showinfo("洞烛先机 · 预测结果", "\n".join(predictions))
            self.log_message("[系统提示] 开启【洞烛先机】！已探知未来牌组命运。")
            self.update_ui_display()

        elif skill == "金蝉脱壳":
            human.golden_cicada_active = True
            self.log_message("[特权] 【金蝉脱壳】启用！本局结算若失利，可获得50%投入返还。")
            messagebox.showinfo("金蝉护体", "金蝉脱壳护体生效！\n本局若进入结算且战败，将退回您本局下注的50%。")
            self.update_ui_display()

        elif skill == "瞒天过海":
            if len(self.deck) == 0:
                messagebox.showwarning("牌不够", "牌堆已空，无法发动瞒天过海！")
                human.skill_ready = True
                return
            next_card = self.get_player_next_card(human)
            if next_card is None:
                messagebox.showwarning("牌不够", "无法确定您的下一张牌！")
                human.skill_ready = True
                return
            matches = self.find_matching_cards_in_deck(next_card)
            if not matches:
                messagebox.showinfo("瞒天过海", f"您下一张将获得: {next_card}\n\n牌堆中未找到同点数不同花色的可交换牌，技能效果为空。")
                self.log_message(f"[特权] 【瞒天过海】发动，下一张牌为 {next_card}，但无可交换对象。")
                self.update_ui_display()
                return
            self.show_deceive_dialog(next_card, matches)

        elif skill == "移花接木":
            targets = [p for p in self.players if p != human and p.is_active]
            if not targets:
                messagebox.showinfo("没人", "当前没有可移花接木的目标。")
                human.skill_ready = True
                return
            if len(self.deck) == 0:
                messagebox.showwarning("牌不够", "牌堆已空，无法发动移花接木！")
                human.skill_ready = True
                return
            self.show_transplant_dialog(targets)

    # --- 偷梁换柱对话框 ---
    def show_swap_dialog(self, candidates):
        dialog = tk.Toplevel(self.root)
        dialog.title("偷梁换柱 · 选择替换底牌")
        dialog.geometry("380x180")
        dialog.configure(bg="#1a1a2e")
        dialog.transient(self.root)
        dialog.grab_set()

        lbl = tk.Label(dialog, text="请挑选一张卡牌替换您目前的底牌:",
                       font=("Microsoft YaHei", 12), fg="#f1c40f", bg="#1a1a2e")
        lbl.pack(pady=15)

        frame = tk.Frame(dialog, bg="#1a1a2e")
        frame.pack()

        for card in candidates:
            card_fg = "#e74c3c" if card.suit in ['♥', '♦'] else "#ecf0f1"
            btn = tk.Button(frame, text=f"{card.suit}{card.rank}",
                            font=("Georgia", 16, "bold"), width=7, fg=card_fg,
                            bg="#2c3e50", relief=tk.RAISED, bd=3, cursor="hand2",
                            command=lambda c=card: self.confirm_swap(dialog, c, candidates))
            btn.pack(side=tk.LEFT, padx=10)

    def confirm_swap(self, dialog, new_card, candidates):
        human = self.players[0]
        old_card = human.cards[0]
        human.cards[0] = new_card
        # 【BUG修复】未选中的牌放回牌堆并洗牌
        for c in candidates:
            if c != new_card:
                self.deck.append(c)
        random.shuffle(self.deck)
        self.log_message(f"[特权] 你动用了换牌绝技，将原底牌【{old_card}】换成了【{new_card}】！")
        dialog.destroy()
        self.update_ui_display()

    # --- 知己知彼对话框 ---
    def show_peep_dialog(self, targets):
        dialog = tk.Toplevel(self.root)
        dialog.title("知己知彼 · 选择窥视目标")
        dialog.geometry("320x200")
        dialog.configure(bg="#1a1a2e")
        dialog.transient(self.root)
        dialog.grab_set()

        lbl = tk.Label(dialog, text="您要窥视谁的底牌？", font=("Microsoft YaHei", 12),
                       fg="#f1c40f", bg="#1a1a2e")
        lbl.pack(pady=15)

        for t in targets:
            btn = tk.Button(dialog, text=t.name, font=("Microsoft YaHei", 11), width=16,
                            bg="#2c3e50", fg="#ecf0f1", relief=tk.RAISED, bd=2, cursor="hand2",
                            command=lambda tp=t: self.confirm_peep(dialog, tp))
            btn.pack(pady=4)

    def confirm_peep(self, dialog, target_player):
        peek_card = target_player.cards[0]
        messagebox.showinfo("知己知彼 · 透视结果",
                            f"【{target_player.name}】的秘密底牌是:\n\n{peek_card}")
        self.log_message(f"[特权] 你偷偷掀开了【{target_player.name}】的底牌，尽在掌控！")
        dialog.destroy()

    # --- 瞒天过海对话框 ---
    def show_deceive_dialog(self, next_card, matches):
        dialog = tk.Toplevel(self.root)
        dialog.title("瞒天过海 · 选择交换牌")
        dialog.geometry("420x220")
        dialog.configure(bg="#1a1a2e")
        dialog.transient(self.root)
        dialog.grab_set()

        lbl = tk.Label(dialog,
                       text=f"您下一张将获得的牌:  {next_card.suit}{next_card.rank}\n\n"
                            f"牌堆中找到以下同点数({next_card.rank})不同花色的牌，\n请选择一张交换（或关闭窗口放弃）:",
                       font=("Microsoft YaHei", 12), fg="#f1c40f", bg="#1a1a2e", justify=tk.CENTER)
        lbl.pack(pady=15)

        frame = tk.Frame(dialog, bg="#1a1a2e")
        frame.pack()

        for deck_idx, card in matches:
            cf = "#e74c3c" if card.suit in ['♥', '♦'] else "#ecf0f1"
            btn = tk.Button(frame, text=f"{card.suit}{card.rank}",
                            font=("Georgia", 16, "bold"), width=7, fg=cf,
                            bg="#2c3e50", relief=tk.RAISED, bd=3, cursor="hand2",
                            command=lambda d=dialog, di=deck_idx, nc=next_card, c=card:
                            self.confirm_deceive(d, di, nc, c))
            btn.pack(side=tk.LEFT, padx=10)

        # 取消按钮
        cancel_btn = tk.Button(dialog, text="放弃交换", font=("Microsoft YaHei", 10),
                               bg="#7f8c8d", fg="white", relief=tk.RAISED, bd=2, cursor="hand2",
                               command=dialog.destroy)
        cancel_btn.pack(pady=12)

    def confirm_deceive(self, dialog, deck_idx, old_card, new_card):
        human = self.players[0]
        # 交换：玩家下张牌位置放入new_card，牌堆deck_idx位置放入old_card
        player_next_idx = self.get_player_next_card_index(human)
        if player_next_idx < len(self.deck):
            self.deck[player_next_idx] = new_card
        self.deck[deck_idx] = old_card
        self.log_message(f"[特权] 【瞒天过海】成功！将即将到来的 {old_card} 替换为 {new_card}。")
        dialog.destroy()
        self.update_ui_display()

    # --- 移花接木对话框 ---
    def show_transplant_dialog(self, targets):
        dialog = tk.Toplevel(self.root)
        dialog.title("移花接木 · 选择目标角色")
        dialog.geometry("340x240")
        dialog.configure(bg="#1a1a2e")
        dialog.transient(self.root)
        dialog.grab_set()

        lbl = tk.Label(dialog, text="选择一名角色，查看其下一张牌\n并决定是否与自己的底牌交换:",
                       font=("Microsoft YaHei", 12), fg="#f1c40f", bg="#1a1a2e", justify=tk.CENTER)
        lbl.pack(pady=15)

        for t in targets:
            btn = tk.Button(dialog, text=t.name, font=("Microsoft YaHei", 11), width=18,
                            bg="#2c3e50", fg="#ecf0f1", relief=tk.RAISED, bd=2, cursor="hand2",
                            command=lambda d=dialog, tp=t: self.confirm_transplant_step2(d, tp))
            btn.pack(pady=4)

    def confirm_transplant_step2(self, dialog, target):
        human = self.players[0]
        target_next_card = self.get_player_next_card(target)
        if target_next_card is None:
            messagebox.showinfo("移花接木", f"【{target.name}】已无下一张牌可查看。", parent=dialog)
            return

        dialog.destroy()

        # 第二步：显示目标的下张牌，询问是否交换
        result = messagebox.askyesno(
            "移花接木 · 确认交换",
            f"【{target.name}】下一张将获得的牌是:\n\n"
            f"         {target_next_card.suit}{target_next_card.rank}\n\n"
            f"您当前的底牌是:\n\n"
            f"         {human.cards[0]}\n\n"
            f"是否将自己的底牌与目标的下张牌交换？"
        )

        if result:
            target_next_idx = self.get_player_next_card_index(target)
            old_hole = human.cards[0]
            human.cards[0] = target_next_card
            if target_next_idx < len(self.deck):
                self.deck[target_next_idx] = old_hole
            self.log_message(f"[特权] 【移花接木】成功！将底牌【{old_hole}】与"
                             f"【{target.name}】的下张牌【{target_next_card}】互换。")
        else:
            self.log_message(f"[特权] 【移花接木】窥视了【{target.name}】的下一张牌，选择放弃交换。")

        self.update_ui_display()

    # ==========================================
    # 10. 牌局结算与赢家裁定
    # ==========================================
    def settle_hand(self):
        self.log_message("\n━━━━━━ 开始翻牌决战 (Showdown) ━━━━━━")

        active_players = [p for p in self.players if p.is_active]

        # 翻开并展现底牌
        for p in active_players:
            self.log_message(f"【{p.name}】底牌为: {p.cards[0]} (手牌总成: {p.cards})")

        # 评估各家牌力
        scores = []
        for p in active_players:
            p_score = evaluate_5_cards(p.cards)
            scores.append((p_score, p))

        # 排序寻找最强手牌
        scores.sort(key=lambda x: x[0], reverse=True)
        winner = scores[0][1]

        # 触发金蝉脱壳返还判定
        for p in active_players:
            if p != winner and p.golden_cicada_active:
                refund_amount = p.current_bet_contribution // 2
                p.chips += refund_amount
                self.pot -= refund_amount
                self.log_message(f"[金蝉脱壳] 【{p.name}】触发金蝉护体，在落败后获得退回筹码 ${refund_amount}。")

        # 奖金注入赢家
        winner.chips += self.pot
        self.log_message(f"\n[加冕] 本局由 【{winner.name}】 获得胜利！夺走筹码 ${self.pot}。")

        # 清除破产玩家
        for p in self.players:
            if p.chips <= 0 and p.name != "无限庄家":
                p.is_bankrupt = True
                p.is_active = False
                self.log_message(f"[洗牌] 选手 【{p.name}】 输光所有赌资，宣告破产淘汰出局！")

        messagebox.showinfo("本局结束",
                            f"本局胜利者: 【{winner.name}】\n获得总池筹码: ${self.pot}\n\n点击确定进入下一局")

        # 进入下一局
        self.start_new_hand()


# ==========================================
# 11. 启动入口
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = ShowHandGUI(root)
    root.mainloop()
