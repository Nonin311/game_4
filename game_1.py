import tkinter as tk
from tkinter import messagebox
import random

class Minesweeper:
    def __init__(self, root):
        self.root = root
        self.root.title("扫雷 (12x12 - 无猜解优化版)")
        self.root.resizable(False, False)
        
        self.rows = 12
        self.cols = 12
        self.total_mines = 16
        
        # 颜色配置
        self.colors = {
            1: "#0000FF",  # 蓝
            2: "#008000",  # 绿
            3: "#FF0000",  # 红
            4: "#000080",  # 深蓝
            5: "#800000",  # 深红
            6: "#008080",  # 青
            7: "#000000",  # 黑
            8: "#808080"   # 灰
        }
        
        self.reset_game()

    def reset_game(self):
        # 清除旧界面（如果是重新开始）
        for widget in self.root.winfo_children():
            widget.destroy()
            
        self.mines = set()       # 存放雷的坐标 (r, c)
        self.flagged = set()     # 存放插旗的坐标 (r, c)
        self.revealed = set()    # 存放已翻开的坐标 (r, c)
        self.first_click = True  # 是否为第一次点击
        self.game_over = False
        self.remaining_flags = self.total_mines
        
        # 创建顶部状态栏
        self.status_frame = tk.Frame(self.root, bg="#eee", height=40)
        self.status_frame.pack(fill=tk.X)
        
        self.label_mines = tk.Label(
            self.status_frame, 
            text=f" 剩余雷数: {self.remaining_flags} ", 
            font=("Arial", 12, "bold"), 
            bg="#eee"
        )
        self.label_mines.pack(side=tk.LEFT, padx=10)
        
        self.btn_restart = tk.Button(
            self.status_frame, 
            text="😊 重新开始", 
            command=self.reset_game,
            font=("Arial", 10, "bold")
        )
        self.btn_restart.pack(side=tk.RIGHT, padx=10, pady=5)

        # 创建游戏棋盘网格
        self.grid_frame = tk.Frame(self.root, bd=2, relief=tk.SUNKEN)
        self.grid_frame.pack()
        
        self.buttons = {}
        for r in range(self.rows):
            for c in range(self.cols):
                btn = tk.Button(
                    self.grid_frame, 
                    width=3, 
                    height=1, 
                    font=("Courier", 12, "bold"),
                    bg="#ccc", 
                    relief=tk.RAISED
                )
                # 绑定左键和右键
                btn.bind("<Button-1>", lambda event, r=r, c=c: self.left_click(r, c))
                btn.bind("<Button-3>", lambda event, r=r, c=c: self.right_click(r, c))
                # 针对 macOS 的右键/双指点击绑定
                btn.bind("<Button-2>", lambda event, r=r, c=c: self.right_click(r, c))
                
                btn.grid(row=r, column=c, padx=1, pady=1)
                self.buttons[(r, c)] = btn

    def generate_mines(self, start_r, start_c):
        """
        在玩家第一次点击后生成雷。
        确保起始点击位置及其周围的 8 个格子（共 9 格）绝对没有雷。
        """
        forbidden_zone = set()
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = start_r + dr, start_c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    forbidden_zone.add((nr, nc))
                    
        all_positions = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        valid_positions = [pos for pos in all_positions if pos not in forbidden_zone]
        
        # 随机抽取 12 个位置作为雷
        self.mines = set(random.sample(valid_positions, self.total_mines))

    def count_adjacent_mines(self, r, c):
        """计算某个格子周围 8 个方向的雷数"""
        count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if (nr, nc) in self.mines:
                    count += 1
        return count

    def left_click(self, r, c):
        if self.game_over or (r, c) in self.flagged or (r, c) in self.revealed:
            return
            
        if self.first_click:
            self.first_click = False
            self.generate_mines(r, c)
            
        if (r, c) in self.mines:
            self.reveal_all_mines(loss_pos=(r, c))
            self.game_loss()
        else:
            self.reveal_cell(r, c)
            self.check_win()

    def right_click(self, r, c):
        if self.game_over or (r, c) in self.revealed:
            return
            
        btn = self.buttons[(r, c)]
        if (r, c) in self.flagged:
            self.flagged.remove((r, c))
            btn.config(text="", bg="#ccc")
            self.remaining_flags += 1
        else:
            if len(self.flagged) < self.total_mines:
                self.flagged.add((r, c))
                btn.config(text="🚩", fg="red", bg="#bbb")
                self.remaining_flags -= 1
                
        self.label_mines.config(text=f" 剩余雷数: {self.remaining_flags} ")

    def reveal_cell(self, r, c):
        """递归翻开格子（自动展开安全区域）"""
        if (r, c) in self.revealed or (r, c) in self.flagged:
            return
            
        self.revealed.add((r, c))
        btn = self.buttons[(r, c)]
        
        mines_count = self.count_adjacent_mines(r, c)
        
        if mines_count > 0:
            btn.config(
                text=str(mines_count), 
                fg=self.colors.get(mines_count, "#000"), 
                bg="#eee", 
                relief=tk.SUNKEN
            )
        else:
            btn.config(text="", bg="#eee", relief=tk.SUNKEN)
            # 周围无雷，触发连锁翻开
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        self.reveal_cell(nr, nc)

    def reveal_all_mines(self, loss_pos=None):
        for (r, c) in self.mines:
            btn = self.buttons[(r, c)]
            if (r, c) == loss_pos:
                btn.config(text="💥", bg="red")  # 踩中的雷
            elif (r, c) not in self.flagged:
                btn.config(text="💣", bg="#ddd")  # 其他未标记的雷

    def check_win(self):
        # 胜利条件：所有非雷格子都被翻开
        if len(self.revealed) == (self.rows * self.cols - self.total_mines):
            self.game_over = True
            self.btn_restart.config(text="😎 胜利！")
            # 自动将所有未标记的雷插上旗子
            for r, c in self.mines:
                if (r, c) not in self.flagged:
                    self.buttons[(r, c)].config(text="🚩", fg="red")
            self.label_mines.config(text=" 剩余雷数: 0 ")
            messagebox.showinfo("扫雷", "恭喜你，成功排除了所有雷！")

    def game_loss(self):
        self.game_over = True
        self.btn_restart.config(text="😵 失败")
        messagebox.showerror("扫雷", "很遗憾，你踩到了雷！")


if __name__ == "__main__":
    root = tk.Tk()
    game = Minesweeper(root)
    root.mainloop()