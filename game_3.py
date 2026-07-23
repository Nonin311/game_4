import tkinter as tk
from tkinter import ttk, messagebox
import random


class Stock:
    def __init__(self, name, code, init_price, volatility, trend=0.0):
        self.name = name
        self.code = code
        self.price = init_price
        self.last_price = init_price
        self.volatility = volatility
        self.trend = trend
        self.event_effect = 0.0

    def update_price(self):
        self.last_price = self.price
        random_factor = random.uniform(-self.volatility, self.volatility)
        change_percent = self.trend + random_factor + self.event_effect
        change_percent = max(-0.20, min(0.20, change_percent))
        self.price = self.price * (1 + change_percent)
        if self.price < 0.1:
            self.price = 0.1
        self.event_effect *= 0.3

    @property
    def change_rate(self):
        return (self.price - self.last_price) / self.last_price


class StockMarketGame:
    def __init__(self, root):
        self.root = root
        self.root.title("轻量级股市模拟交易器")
        self.root.state('zoomed')
        self.root.minsize(1000, 650)
        self.root.resizable(True, True)

        # 游戏数据
        self.cash = 100000.0
        self.day = 1

        # 10只股票
        self.stocks = [
            Stock("泰坦科技", "600123", 50.0, 0.08, 0.005),
            Stock("民生百货", "600456", 15.0, 0.03, 0.001),
            Stock("环球石油", "600789", 100.0, 0.05, 0.002),
            Stock("绿能电力", "600111", 30.0, 0.06, 0.003),
            Stock("星际硬币", "300999", 5.0, 0.18, -0.01),
            Stock("深蓝医药", "600222", 45.0, 0.05, 0.003),
            Stock("云端数据", "300888", 80.0, 0.10, 0.006),
            Stock("中铁基建", "600333", 12.0, 0.04, 0.001),
            Stock("先锋农业", "300777", 8.0, 0.07, -0.002),
            Stock("环球传媒", "600555", 22.0, 0.06, 0.002),
        ]

        self.portfolio = {stock.code: 0 for stock in self.stocks}
        self.hold_prices = {stock.code: 0.0 for stock in self.stocks}
        self.stock_widgets = {}

        # 计时器（5分钟 = 300秒）
        self.timer_remaining = 300
        self.timer_job = None

        self.init_ui()
        self.update_all_displays()
        self.start_timer()

    # ═══════════════════════════════════════════════════════════
    #  UI 初始化
    # ═══════════════════════════════════════════════════════════

    def init_ui(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Microsoft YaHei", 10))
        style.configure("Header.TLabel", font=("Microsoft YaHei", 12, "bold"))
        style.configure("Timer.TLabel", font=("Microsoft YaHei", 14, "bold"))
        style.configure("TRow.TLabel", font=("Microsoft YaHei", 10))
        style.configure("Up.TLabel", foreground="#e74c3c", font=("Microsoft YaHei", 10, "bold"))
        style.configure("Down.TLabel", foreground="#27ae60", font=("Microsoft YaHei", 10, "bold"))
        style.configure("Small.TButton", font=("Microsoft YaHei", 9), padding=(6, 2))

        # ── 顶部看板 ──
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=15, pady=(10, 5))

        # 左侧：资产信息
        self.asset_frame = ttk.LabelFrame(top_frame, text=" 个人资产看板 ")
        self.asset_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_day = ttk.Label(self.asset_frame, text="第 1 天", style="Header.TLabel")
        self.lbl_day.grid(row=0, column=0, padx=15, pady=8)

        self.lbl_total_assets = ttk.Label(self.asset_frame, text="总资产: ¥100,000.00", style="Header.TLabel")
        self.lbl_total_assets.grid(row=0, column=1, padx=15, pady=8)

        self.lbl_cash = ttk.Label(self.asset_frame, text="可用资金: ¥100,000.00")
        self.lbl_cash.grid(row=0, column=2, padx=15, pady=8)

        self.lbl_stock_value = ttk.Label(self.asset_frame, text="持股市值: ¥0.00")
        self.lbl_stock_value.grid(row=0, column=3, padx=15, pady=8)

        self.lbl_profit = ttk.Label(self.asset_frame, text="今日盈亏: ¥0.00 (0.00%)")
        self.lbl_profit.grid(row=0, column=4, padx=15, pady=8)

        # 右侧：计时器 + 下一日按钮
        timer_frame = ttk.LabelFrame(top_frame, text=" 市场时钟 ")
        timer_frame.pack(side=tk.RIGHT, padx=(15, 0))

        self.lbl_timer = ttk.Label(timer_frame, text="距开盘: 05:00", style="Timer.TLabel",
                                   foreground="#2980b9")
        self.lbl_timer.grid(row=0, column=0, padx=20, pady=5)

        self.btn_next_day = tk.Button(
            timer_frame,
            text="▶ 下一交易日（开盘）",
            bg="#2980b9", fg="white",
            font=("Microsoft YaHei", 11, "bold"),
            command=self.manual_next_day,
            height=2
        )
        self.btn_next_day.grid(row=0, column=1, padx=(5, 15), pady=8)

        # ── 主区域：左侧滚动股票列表 + 右侧新闻 ──
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self._build_stock_table()
        self._build_news_panel()

        # ── 图例 ──
        legend_frame = ttk.Frame(self.root)
        legend_frame.pack(fill=tk.X, padx=15, pady=(0, 5))
        ttk.Label(legend_frame, text="● 红色背景 = 上涨", foreground="#e74c3c").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(legend_frame, text="● 绿色背景 = 下跌", foreground="#27ae60").pack(side=tk.LEFT)

    def _build_stock_table(self):
        """构建可滚动的股票列表（Canvas + Frame，每行带交易按钮）"""
        self.table_outer = ttk.LabelFrame(self.main_frame, text=" 股市实时行情 ")
        self.table_outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Canvas + Scrollbar
        self.canvas = tk.Canvas(self.table_outer, highlightthickness=0, bg="#ffffff")
        self.scrollbar = ttk.Scrollbar(self.table_outer, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)

        self.scroll_frame.bind("<Configure>",
                               lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Canvas 宽度跟随外层
        self.table_outer.bind("<Configure>", self._on_table_resize)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 鼠标滚轮
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        # 触摸板/触屏滚动也支持
        self.canvas.bind("<Enter>", lambda _: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda _: self._unbind_mousewheel())

        # 表头
        header_bg = "#ecf0f1"
        self._make_header_cell(self.scroll_frame, 0, "股票名称", 95, header_bg)
        self._make_header_cell(self.scroll_frame, 1, "代码", 70, header_bg)
        self._make_header_cell(self.scroll_frame, 2, "当前价格", 95, header_bg)
        self._make_header_cell(self.scroll_frame, 3, "涨跌幅", 100, header_bg)
        self._make_header_cell(self.scroll_frame, 4, "持仓", 70, header_bg)
        self._make_header_cell(self.scroll_frame, 5, "持仓均价", 90, header_bg)
        self._make_header_cell(self.scroll_frame, 6, "交易操作", 370, header_bg)

        # 为每只股票创建行
        for i, stock in enumerate(self.stocks):
            self._create_stock_row(stock, i + 1)

    def _make_header_cell(self, parent, col, text, width, bg):
        lbl = tk.Label(parent, text=text, font=("Microsoft YaHei", 10, "bold"),
                       bg=bg, fg="#2c3e50", relief="ridge", bd=1, padx=6, pady=6)
        lbl.grid(row=0, column=col, sticky="nsew")
        # 设置列宽（使用临时占位）
        parent.grid_columnconfigure(col, minsize=width)

    def _create_stock_row(self, stock, row_idx):
        """为一只股票创建一整行（信息 + 按钮）"""
        widgets = {}

        # 行背景（偶数行浅灰）
        base_bg = "#f8f9fa" if row_idx % 2 == 0 else "#ffffff"

        # 股票名称
        w = tk.Label(self.scroll_frame, text=stock.name, font=("Microsoft YaHei", 10),
                     bg=base_bg, relief="solid", bd=1, padx=6, pady=8)
        w.grid(row=row_idx, column=0, sticky="nsew")
        widgets['name'] = w

        # 代码
        w = tk.Label(self.scroll_frame, text=stock.code, font=("Microsoft YaHei", 10),
                     bg=base_bg, relief="solid", bd=1, padx=6, pady=8)
        w.grid(row=row_idx, column=1, sticky="nsew")
        widgets['code'] = w

        # 当前价格
        w = tk.Label(self.scroll_frame, text=f"¥{stock.price:.2f}", font=("Microsoft YaHei", 10),
                     bg=base_bg, relief="solid", bd=1, padx=6, pady=8)
        w.grid(row=row_idx, column=2, sticky="nsew")
        widgets['price'] = w

        # 涨跌幅
        w = tk.Label(self.scroll_frame, text="—", font=("Microsoft YaHei", 10),
                     bg=base_bg, relief="solid", bd=1, padx=6, pady=8)
        w.grid(row=row_idx, column=3, sticky="nsew")
        widgets['change'] = w

        # 持仓
        w = tk.Label(self.scroll_frame, text="0", font=("Microsoft YaHei", 10),
                     bg=base_bg, relief="solid", bd=1, padx=6, pady=8)
        w.grid(row=row_idx, column=4, sticky="nsew")
        widgets['hold'] = w

        # 持仓均价
        w = tk.Label(self.scroll_frame, text="—", font=("Microsoft YaHei", 10),
                     bg=base_bg, relief="solid", bd=1, padx=6, pady=8)
        w.grid(row=row_idx, column=5, sticky="nsew")
        widgets['hold_cost'] = w

        # 按钮区域（放在一个子 Frame 中）
        btn_frame = tk.Frame(self.scroll_frame, bg=base_bg, relief="solid", bd=1)
        btn_frame.grid(row=row_idx, column=6, sticky="nsew", padx=0, pady=0)

        b1 = tk.Button(btn_frame, text="买入100", font=("Microsoft YaHei", 9),
                       bg="#e74c3c", fg="white", padx=6,
                       command=lambda s=stock: self.trade_action(s, "BUY", 100))
        b1.pack(side=tk.LEFT, padx=3, pady=4)

        b2 = tk.Button(btn_frame, text="全仓买入", font=("Microsoft YaHei", 9),
                       bg="#c0392b", fg="white", padx=6,
                       command=lambda s=stock: self.trade_action(s, "BUY_MAX", 0))
        b2.pack(side=tk.LEFT, padx=3, pady=4)

        b3 = tk.Button(btn_frame, text="卖出100", font=("Microsoft YaHei", 9),
                       bg="#27ae60", fg="white", padx=6,
                       command=lambda s=stock: self.trade_action(s, "SELL", 100))
        b3.pack(side=tk.LEFT, padx=3, pady=4)

        b4 = tk.Button(btn_frame, text="清仓卖出", font=("Microsoft YaHei", 9),
                       bg="#1e8449", fg="white", padx=6,
                       command=lambda s=stock: self.trade_action(s, "SELL_MAX", 0))
        b4.pack(side=tk.LEFT, padx=3, pady=4)

        widgets['btn_frame'] = btn_frame
        widgets['base_bg'] = base_bg

        self.stock_widgets[stock.code] = widgets

    def _build_news_panel(self):
        """右侧新闻面板"""
        self.right_frame = ttk.Frame(self.main_frame, width=280)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        self.right_frame.pack_propagate(False)

        self.news_frame = ttk.LabelFrame(self.right_frame, text=" 每日参考新闻 ")
        self.news_frame.pack(fill=tk.BOTH, expand=True)

        self.news_text = tk.Text(self.news_frame, wrap=tk.WORD, width=28,
                                 font=("Microsoft YaHei", 10), bg="#fafafa",
                                 state=tk.DISABLED, padx=8, pady=8)
        self.news_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_news("🎉 股市模拟启动！\n\n欢迎入市，初始资金 ¥100,000.00。\n投资需谨慎，祝你好运！")

    def _on_table_resize(self, event):
        """外层容器大小变化时，让 Canvas 填充"""
        canvas_width = event.width - self.scrollbar.winfo_width() - 5
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _on_canvas_resize(self, event):
        """Canvas 大小变化时，更新内部 frame 的宽度"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _bind_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel_scroll)

    def _unbind_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel_scroll(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ═══════════════════════════════════════════════════════════
    #  计时器
    # ═══════════════════════════════════════════════════════════

    def start_timer(self):
        """启动/重启 5 分钟倒计时"""
        self.timer_remaining = 300
        self._tick()

    def _tick(self):
        """每秒更新一次倒计时"""
        if self.timer_remaining > 0:
            mins = self.timer_remaining // 60
            secs = self.timer_remaining % 60
            self.lbl_timer.config(text=f"距开盘: {mins:02d}:{secs:02d}")

            # 最后30秒变红闪烁提示
            if self.timer_remaining <= 30:
                if self.timer_remaining % 2 == 0:
                    self.lbl_timer.config(foreground="#e74c3c")
                else:
                    self.lbl_timer.config(foreground="#c0392b")
            else:
                self.lbl_timer.config(foreground="#2980b9")

            self.timer_remaining -= 1
            self.timer_job = self.root.after(1000, self._tick)
        else:
            # 倒计时结束，自动进入下一日
            self.lbl_timer.config(text="正在开盘...", foreground="#e74c3c")
            self.next_day()

    def reset_timer(self):
        """重置计时器（手动/自动进入下一日后调用）"""
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        self.start_timer()

    # ═══════════════════════════════════════════════════════════
    #  交易逻辑
    # ═══════════════════════════════════════════════════════════

    def trade_action(self, stock, action_type, amount):
        price = stock.price

        if action_type == "BUY":
            cost = price * amount
            if self.cash < cost:
                messagebox.showwarning("交易失败", f"可用资金不足！\n需要 ¥{cost:,.2f}，当前可用 ¥{self.cash:,.2f}")
                return
            self.cash -= cost
            old_qty = self.portfolio[stock.code]
            old_cost = self.hold_prices[stock.code] * old_qty
            new_qty = old_qty + amount
            self.hold_prices[stock.code] = (old_cost + cost) / new_qty if new_qty > 0 else 0
            self.portfolio[stock.code] = new_qty

        elif action_type == "BUY_MAX":
            max_qty = int(self.cash // (price * 100)) * 100
            if max_qty == 0:
                messagebox.showwarning("交易失败", "可用资金不够购买整手 (100股)！")
                return
            cost = price * max_qty
            self.cash -= cost
            old_qty = self.portfolio[stock.code]
            old_cost = self.hold_prices[stock.code] * old_qty
            new_qty = old_qty + max_qty
            self.hold_prices[stock.code] = (old_cost + cost) / new_qty
            self.portfolio[stock.code] = new_qty

        elif action_type == "SELL":
            if self.portfolio[stock.code] < amount:
                messagebox.showwarning("交易失败", "持股不足，无法卖出！")
                return
            income = price * amount
            self.cash += income
            self.portfolio[stock.code] -= amount
            if self.portfolio[stock.code] == 0:
                self.hold_prices[stock.code] = 0.0

        elif action_type == "SELL_MAX":
            amount = self.portfolio[stock.code]
            if amount == 0:
                messagebox.showwarning("交易失败", "您并未持有该股票！")
                return
            income = price * amount
            self.cash += income
            self.portfolio[stock.code] = 0
            self.hold_prices[stock.code] = 0.0

        self.update_all_displays()

    # ═══════════════════════════════════════════════════════════
    #  界面刷新
    # ═══════════════════════════════════════════════════════════

    def update_all_displays(self):
        """刷新所有 UI：股票行 + 资产看板"""
        total_market_value = 0.0

        for stock in self.stocks:
            w = self.stock_widgets.get(stock.code)
            if not w:
                continue

            hold_qty = self.portfolio[stock.code]
            hold_cost = self.hold_prices[stock.code]
            market_value = hold_qty * stock.price
            total_market_value += market_value

            change_rate = stock.change_rate
            if change_rate > 0.001:
                change_text = f"▲ +{change_rate * 100:.2f}%"
                row_bg = "#ffeaea"
                fg_color = "#c0392b"
            elif change_rate < -0.001:
                change_text = f"▼ {change_rate * 100:.2f}%"
                row_bg = "#eafaf1"
                fg_color = "#1e8449"
            else:
                change_text = "— 0.00%"
                row_bg = w['base_bg']
                fg_color = "#555555"

            w['name'].config(text=stock.name, bg=row_bg, fg=fg_color)
            w['code'].config(text=stock.code, bg=row_bg, fg=fg_color)
            w['price'].config(text=f"¥{stock.price:.2f}", bg=row_bg, fg=fg_color)
            w['change'].config(text=change_text, bg=row_bg, fg=fg_color)
            w['hold'].config(text=str(hold_qty), bg=row_bg, fg=fg_color)
            w['hold_cost'].config(
                text=f"¥{hold_cost:.2f}" if hold_qty > 0 else "—",
                bg=row_bg, fg=fg_color
            )
            w['btn_frame'].config(bg=row_bg)

        # 资产看板
        total_assets = self.cash + total_market_value
        self.lbl_day.config(text=f"第 {self.day} 天")
        self.lbl_total_assets.config(text=f"总资产: ¥{total_assets:,.2f}")
        self.lbl_cash.config(text=f"可用资金: ¥{self.cash:,.2f}")
        self.lbl_stock_value.config(text=f"持股市值: ¥{total_market_value:,.2f}")

        yesterday_assets = getattr(self, 'yesterday_assets', 100000.0)
        profit_value = total_assets - yesterday_assets
        profit_rate = (profit_value / yesterday_assets) * 100 if yesterday_assets > 0 else 0

        if profit_value > 0.01:
            self.lbl_profit.config(text=f"今日盈亏: +¥{profit_value:,.2f} (+{profit_rate:.2f}%)",
                                   foreground='#e74c3c')
        elif profit_value < -0.01:
            self.lbl_profit.config(text=f"今日盈亏: -¥{abs(profit_value):,.2f} ({profit_rate:.2f}%)",
                                   foreground='#27ae60')
        else:
            self.lbl_profit.config(text=f"今日盈亏: ¥0.00 (0.00%)", foreground='#555555')

    # ═══════════════════════════════════════════════════════════
    #  市场推进
    # ═══════════════════════════════════════════════════════════

    def manual_next_day(self):
        """手动推进到下一日"""
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None
        self.next_day()

    def next_day(self):
        """执行一日市场更新"""
        total_market_value = sum(self.portfolio[s.code] * s.price for s in self.stocks)
        self.yesterday_assets = self.cash + total_market_value

        self.day += 1

        # 触发随机事件
        event_msg = self.trigger_random_event()
        self.log_news(f"【第 {self.day} 天早报】\n\n{event_msg}")

        # 更新股价
        for stock in self.stocks:
            stock.update_price()

        self.update_all_displays()
        self.reset_timer()

    # ═══════════════════════════════════════════════════════════
    #  新闻 & 事件
    # ═══════════════════════════════════════════════════════════

    def log_news(self, text):
        self.news_text.config(state=tk.NORMAL)
        self.news_text.delete(1.0, tk.END)
        self.news_text.insert(tk.END, text)
        self.news_text.config(state=tk.DISABLED)

    def trigger_random_event(self):
        events = [
            # ── 原有事件 ──
            ("🚀 科技行业发布新一代突破性AI芯片，市场热情高涨！",
             {"600123": 0.12, "300999": 0.05}),
            ("🚫 监管层表示将严厉打击空气币炒作，洗钱风险担忧加剧！",
             {"300999": -0.15}),
            ("⛽ 原油主产国宣布达成减产协议，供应预期偏紧！",
             {"600789": 0.08}),
            ("📉 百货巨头因物流成本增加、季度利润不达预期，评级遭到下调！",
             {"600456": -0.05}),
            ("🌿 绿色新能源法案通过，政府将大力补贴风电与光伏企业！",
             {"600111": 0.10}),
            ("🐂 大盘牛市氛围浓厚，投资者信心大增，资金全线入场！",
             {"ALL": 0.04}),
            ("🏦 宏观经济数据表现不及预期，央行释放加息信号以抑制通胀！",
             {"ALL": -0.04}),
            ("🐦 星际硬币迎来马斯克发推力挺，高调宣布将支持其作为购买载体！",
             {"300999": 0.18}),

            # ── 新增事件 ──
            ("💊 深蓝医药新药临床试验取得突破性进展，股价受振！",
             {"600222": 0.10}),
            ("🏥 医药集采政策加码，仿制药企业利润空间被大幅压缩！",
             {"600222": -0.10}),
            ("☁️ 云端数据中标大型政府数字化项目，市场预期营收翻倍！",
             {"300888": 0.12}),
            ("🔓 云端数据遭遇黑客攻击，用户数据泄露引发信任危机！",
             {"300888": -0.14}),
            ("🏗️ 中铁基建中标一带一路重点工程，海外订单大幅增长！",
             {"600333": 0.10}),
            ("📉 基础设施投资增速放缓，建材需求低于预期！",
             {"600333": -0.08}),
            ("🌾 先锋农业推出新型抗旱种子，有望大幅提升粮食产量！",
             {"300777": 0.11}),
            ("🐛 蝗灾预警！农业板块遭受重创，农作物大面积受损！",
             {"300777": -0.13}),
            ("🎬 环球传媒旗下影视作品获国际大奖，广告收入创历史新高！",
             {"600555": 0.09}),
            ("📰 互联网短视频冲击传统媒体，环球传媒用户流失严重！",
             {"600555": -0.09}),
            ("💹 美联储释放降息信号，全球股市集体大涨！",
             {"ALL": 0.05}),
            ("🌍 地缘冲突升级，全球避险情绪升温，资金逃离风险资产！",
             {"ALL": -0.06}),
            ("🤖 泰坦科技联手深蓝医药开发AI制药平台，跨界合作引关注！",
             {"600123": 0.08, "600222": 0.06}),
            ("🔋 绿能电力与云端数据合作建设绿色数据中心，双赢格局！",
             {"600111": 0.07, "300888": 0.05}),
        ]

        # 60% 概率触发事件
        if random.random() < 0.60:
            event = random.choice(events)
            headline, impacts = event

            for code, effect in impacts.items():
                if code == "ALL":
                    for stock in self.stocks:
                        stock.event_effect = effect
                else:
                    for stock in self.stocks:
                        if stock.code == code:
                            stock.event_effect = effect
            return headline
        else:
            return "☀️ 市场暂无重大突发消息，各板块处于技术性调整阶段。"


if __name__ == "__main__":
    root = tk.Tk()
    game = StockMarketGame(root)
    root.mainloop()
