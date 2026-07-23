"""
游戏大厅 —— 统筹调度 game_1 到 game_4
点击按钮秒开游戏窗口，各游戏在同一进程内独立运行。
"""
import tkinter as tk
import traceback

# ── 直接导入游戏模块（PyInstaller 自动包含，无需 datas / sys._MEIPASS）──
import game_1
import game_2
import game_3
import game_4

# ── 游戏注册表 ────────────────────────────────────────────
GAMES = {
    "game-1": {
        "name": "扫雷",
        "icon": "💣",
        "desc": "12×12 无猜解优化版\n16颗雷 · 左右键操作",
        "klass": game_1.Minesweeper,
        "color": "#e74c3c",
        "color_dark": "#c0392b",
    },
    "game-2": {
        "name": "五子棋",
        "icon": "♟",
        "desc": "15×15 棋盘 · 人机对战\n你执黑子 · AI执白子",
        "klass": game_2.Gomoku,
        "color": "#2ecc71",
        "color_dark": "#27ae60",
    },
    "game-3": {
        "name": "股市模拟",
        "icon": "📈",
        "desc": "轻量级股市模拟交易器\n10只股票 · 5分钟一交易日",
        "klass": game_3.StockMarketGame,
        "color": "#3498db",
        "color_dark": "#2980b9",
    },
    "game-4": {
        "name": "沙蟹对决",
        "icon": "🃏",
        "desc": "电影级策略扑克游戏\n1v3 AI · 6种特权技能",
        "klass": game_4.ShowHandGUI,
        "color": "#f39c12",
        "color_dark": "#e67e22",
    },
}

# ── 主题色板（白色主题）──
BG_MAIN   = "#f0f2f5"
BG_CARD   = "#ffffff"
BG_HEADER = "#ffffff"
BG_STATUS = "#ffffff"
ACCENT    = "#2563eb"
TEXT_PRIMARY   = "#1a1a2e"
TEXT_SECONDARY = "#6b7280"
TEXT_MUTED     = "#9ca3af"
BORDER         = "#e5e7eb"
CARD_HOVER_BG  = "#f8fafc"
CARD_SHADOW    = "#d1d5db"


class GameHub:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Hub · 游戏大厅")
        self.root.geometry("720x560")
        self.root.minsize(640, 480)
        self.root.configure(bg=BG_MAIN)

        self.open_windows = {}
        self.card_buttons = {}
        self.card_frames = {}

        self._center_window()
        self.build_ui()

    # ═══════════════════════════════════════════════════════════
    #  窗口居中
    # ═══════════════════════════════════════════════════════════
    def _center_window(self):
        self.root.update_idletasks()
        w, h = 720, 560
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ═══════════════════════════════════════════════════════════
    #  UI 构建
    # ═══════════════════════════════════════════════════════════
    def build_ui(self):
        # ── 顶部 ──
        header = tk.Frame(self.root, bg=BG_HEADER)
        header.pack(fill=tk.X)

        header_inner = tk.Frame(header, bg=BG_HEADER)
        header_inner.pack(fill=tk.X, padx=32, pady=(24, 20))

        tk.Label(
            header_inner,
            text="🎮",
            font=("Segoe UI Emoji", 32),
            bg=BG_HEADER,
        ).pack(side=tk.LEFT, padx=(0, 14))

        title_col = tk.Frame(header_inner, bg=BG_HEADER)
        title_col.pack(side=tk.LEFT)

        tk.Label(
            title_col,
            text="游戏大厅",
            font=("Microsoft YaHei", 22, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_HEADER,
        ).pack(anchor="w")

        tk.Label(
            title_col,
            text="选择一个游戏开始吧  ·  支持同时运行多个游戏窗口",
            font=("Microsoft YaHei", 9),
            fg=TEXT_SECONDARY,
            bg=BG_HEADER,
        ).pack(anchor="w", pady=(2, 0))

        # 分隔线
        sep = tk.Frame(self.root, bg=BORDER, height=1)
        sep.pack(fill=tk.X)

        # ── 卡片区域 ──
        cards_frame = tk.Frame(self.root, bg=BG_MAIN)
        cards_frame.pack(fill=tk.BOTH, expand=True, padx=28, pady=(20, 12))

        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for (gid, info), (row, col) in zip(GAMES.items(), positions):
            self._create_game_card(cards_frame, gid, info, row, col)

        cards_frame.grid_rowconfigure(0, weight=1)
        cards_frame.grid_rowconfigure(1, weight=1)
        cards_frame.grid_columnconfigure(0, weight=1, uniform="card")
        cards_frame.grid_columnconfigure(1, weight=1, uniform="card")

        # ── 底部状态栏 ──
        self.status_frame = tk.Frame(self.root, bg=BG_STATUS)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # 状态栏分隔线
        tk.Frame(self.status_frame, bg=BORDER, height=1).pack(fill=tk.X)

        status_inner = tk.Frame(self.status_frame, bg=BG_STATUS)
        status_inner.pack(fill=tk.X, padx=24, pady=10)

        self.status_dot = tk.Label(
            status_inner,
            text="●",
            font=("", 10),
            fg="#3fb950",
            bg=BG_STATUS,
        )
        self.status_dot.pack(side=tk.LEFT, padx=(0, 8))

        self.status_label = tk.Label(
            status_inner,
            text="就绪 — 点击任意游戏卡片启动",
            font=("Microsoft YaHei", 9),
            fg=TEXT_SECONDARY,
            bg=BG_STATUS,
        )
        self.status_label.pack(side=tk.LEFT)

        # 版本号
        tk.Label(
            status_inner,
            text="v1.0",
            font=("Consolas", 9),
            fg=TEXT_MUTED,
            bg=BG_STATUS,
        ).pack(side=tk.RIGHT)

    def _create_game_card(self, parent, game_id, info, row, col):
        """创建一个游戏卡片"""
        color = info["color"]

        # 外层容器 — 用于卡片边框发光效果
        outer = tk.Frame(parent, bg=BG_MAIN)
        outer.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        # 卡片主体
        card = tk.Frame(outer, bg=BG_CARD, bd=0, relief=tk.FLAT,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # 左边色条
        stripe = tk.Frame(card, bg=color, width=4)
        stripe.pack(side=tk.LEFT, fill=tk.Y)

        # 卡片内容区
        body = tk.Frame(card, bg=BG_CARD)
        body.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=18, pady=16)

        # 图标 + 名称 行
        top_row = tk.Frame(body, bg=BG_CARD)
        top_row.pack(fill=tk.X)

        tk.Label(
            top_row,
            text=info["icon"],
            font=("Segoe UI Emoji", 28),
            bg=BG_CARD,
        ).pack(side=tk.LEFT, padx=(0, 10))

        name_col = tk.Frame(top_row, bg=BG_CARD)
        name_col.pack(side=tk.LEFT)

        tk.Label(
            name_col,
            text=info["name"],
            font=("Microsoft YaHei", 15, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_CARD,
        ).pack(anchor="w")

        # 描述
        tk.Label(
            body,
            text=info["desc"],
            font=("Microsoft YaHei", 9),
            fg=TEXT_SECONDARY,
            bg=BG_CARD,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(10, 14))

        # 启动按钮
        btn = tk.Button(
            body,
            text="▶  启 动 游 戏",
            font=("Microsoft YaHei", 10, "bold"),
            bg=color,
            fg="#ffffff",
            activebackground=info["color_dark"],
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=18,
            pady=6,
            borderwidth=0,
            highlightthickness=0,
        )
        btn.config(command=lambda gid=game_id, b=btn: self._on_launch_click(gid, b))
        btn.pack(anchor="w")

        # 按钮悬停效果
        def on_enter(e, b=btn, c=info["color_dark"]):
            b.config(bg=c)

        def on_leave(e, b=btn, c=color):
            b.config(bg=c)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        self.card_buttons[game_id] = btn
        self.card_frames[game_id] = card

        # 卡片悬停效果
        def card_enter(e, c=card, f=outer):
            c.config(bg=CARD_HOVER_BG)
            for child in c.winfo_children():
                if isinstance(child, tk.Frame):
                    for sub in child.winfo_children():
                        try:
                            sub.config(bg=CARD_HOVER_BG)
                        except tk.TclError:
                            pass

        def card_leave(e, c=card, f=outer):
            c.config(bg=BG_CARD)
            for child in c.winfo_children():
                if isinstance(child, tk.Frame):
                    for sub in child.winfo_children():
                        try:
                            sub.config(bg=BG_CARD)
                        except tk.TclError:
                            pass

        for widget in (card, body, top_row, name_col):
            widget.bind("<Enter>", card_enter)
            widget.bind("<Leave>", card_leave)

        # 整个卡片可点击
        for widget in (card, body, top_row, name_col):
            widget.bind(
                "<Button-1>",
                lambda _e, gid=game_id, b=btn: self._on_launch_click(gid, b),
            )
            widget.config(cursor="hand2")

    # ═══════════════════════════════════════════════════════════
    #  游戏启动
    # ═══════════════════════════════════════════════════════════
    def _on_launch_click(self, game_id, btn):
        """按钮点击：即时反馈 + 启动游戏"""
        info = GAMES[game_id]

        # 检查是否已打开
        if game_id in self.open_windows:
            win = self.open_windows[game_id]
            try:
                if win.winfo_exists():
                    win.lift()
                    win.focus_force()
                    self._set_status("warning", f"{info['name']} 已在运行中，已切换到该窗口")
                    self.root.after(3000, self._reset_status)
                    return
            except tk.TclError:
                pass
            del self.open_windows[game_id]

        # 即时视觉反馈
        btn.config(text="⏳ 启动中...", state=tk.DISABLED, bg="#484f58")
        self._set_status("loading", f"正在打开 {info['name']} ...")
        self.root.update_idletasks()

        # 延迟一帧启动，确保 UI 先刷新
        self.root.after(30, lambda: self._do_launch(game_id, info, btn))

    def _do_launch(self, game_id, info, btn):
        """实际执行游戏启动"""
        try:
            # 创建 Toplevel
            game_win = tk.Toplevel(self.root)
            game_win.quit = game_win.destroy  # 保护大厅

            game_win.bind(
                "<Destroy>",
                lambda e, gid=game_id, gw=game_win: self._on_game_destroyed(e, gid, gw),
            )

            # 直接使用导入的类
            self.open_windows[game_id] = game_win
            info["klass"](game_win)

            self._set_status("success", f"{info['name']} 已启动！")

        except Exception as e:
            # 输出到 stderr 以便控制台可见
            traceback.print_exc()
            self._set_status("error", f"启动失败: {e}")
            self.open_windows.pop(game_id, None)

        finally:
            self._set_button_normal(game_id, btn)
            self.root.after(3000, self._reset_status)

    # ═══════════════════════════════════════════════════════════
    #  窗口销毁回调
    # ═══════════════════════════════════════════════════════════
    def _on_game_destroyed(self, event, game_id, game_win):
        if event.widget is not game_win:
            return

        if self.open_windows.get(game_id) is game_win:
            del self.open_windows[game_id]

        self._reset_card_button(game_id)
        self._set_status("idle", f"{GAMES[game_id]['name']} 已关闭")

    # ═══════════════════════════════════════════════════════════
    #  辅助方法
    # ═══════════════════════════════════════════════════════════
    def _set_status(self, kind, text):
        colors = {
            "idle":    "#3fb950",
            "loading": "#d29922",
            "success": "#3fb950",
            "warning": "#d29922",
            "error":   "#f85149",
        }
        dot_color = colors.get(kind, "#3fb950")
        self.status_dot.config(fg=dot_color)
        self.status_label.config(text=text)

    def _reset_status(self):
        self._set_status("idle", "就绪 — 点击任意游戏卡片启动")

    def _set_button_normal(self, game_id, btn):
        info = GAMES[game_id]
        try:
            btn.config(
                text="▶  启 动 游 戏",
                state=tk.NORMAL,
                bg=info["color"],
                cursor="hand2",
            )
        except tk.TclError:
            pass

    def _reset_card_button(self, game_id):
        btn = self.card_buttons.get(game_id)
        if btn:
            self._set_button_normal(game_id, btn)


# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    hub = GameHub(root)
    root.mainloop()
