import tkinter as tk
from tkinter import messagebox

class Gomoku:
    def __init__(self, root):
        self.root = root
        self.root.title("五子棋人机对战")
        self.root.resizable(False, False)
        
        # 棋盘参数
        self.grid_size = 15
        self.cell_pixel = 35  # 每个格子的像素大小
        self.margin = 25      # 边距
        self.board_width = self.cell_pixel * (self.grid_size - 1) + self.margin * 2
        
        # 游戏状态
        self.board = [[0] * self.grid_size for _ in range(self.grid_size)] # 0:空, 1:玩家(黑), 2:AI(白)
        self.game_over = False
        self.turn = 1  # 1: 玩家, 2: AI
        
        self.init_ui()

    def init_ui(self):
        # 状态栏
        self.status_frame = tk.Frame(self.root, bg="#f0f0f0", height=40)
        self.status_frame.pack(fill=tk.X)
        
        self.label_status = tk.Label(
            self.status_frame, 
            text=" 轮到您执黑子下棋 ", 
            font=("Arial", 11, "bold"), 
            bg="#f0f0f0"
        )
        self.label_status.pack(side=tk.LEFT, padx=15)
        
        self.btn_restart = tk.Button(
            self.status_frame, 
            text="🔄 重新开始", 
            command=self.reset_game,
            font=("Arial", 10)
        )
        self.btn_restart.pack(side=tk.RIGHT, padx=15, pady=5)
        
        # 棋盘画布 (经典木质黄)
        self.canvas = tk.Canvas(
            self.root, 
            width=self.board_width, 
            height=self.board_width, 
            bg="#e6b800"
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)
        
        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        # 绘制网格线
        for i in range(self.grid_size):
            start = self.margin + i * self.cell_pixel
            end = self.board_width - self.margin
            # 横线
            self.canvas.create_line(self.margin, start, end, start, fill="black")
            # 竖线
            self.canvas.create_line(start, self.margin, start, end, fill="black")
            
        # 绘制星位 (九个标准的定位点，15x15取5个常用点即可)
        stars = [(3, 3), (3, 11), (7, 7), (11, 3), (11, 11)]
        for r, c in stars:
            cx = self.margin + c * self.cell_pixel
            cy = self.margin + r * self.cell_pixel
            self.canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill="black")

    def draw_stone(self, r, c, color_code):
        cx = self.margin + c * self.cell_pixel
        cy = self.margin + r * self.cell_pixel
        r_pixel = self.cell_pixel // 2 - 2
        
        if color_code == 1: # 黑棋
            # 渐变高光效果让棋子更具立体感
            self.canvas.create_oval(cx-r_pixel, cy-r_pixel, cx+r_pixel, cy+r_pixel, fill="#2c3e50", outline="black")
            self.canvas.create_oval(cx-r_pixel+3, cy-r_pixel+3, cx-r_pixel+8, cy-r_pixel+8, fill="#7f8c8d", outline="")
        else: # 白棋
            self.canvas.create_oval(cx-r_pixel, cy-r_pixel, cx+r_pixel, cy+r_pixel, fill="#fbfcfc", outline="#bdc3c7")
            self.canvas.create_oval(cx-r_pixel+3, cy-r_pixel+3, cx-r_pixel+8, cy-r_pixel+8, fill="#ffffff", outline="")

    def on_click(self, event):
        if self.game_over or self.turn != 1:
            return
            
        # 将鼠标点击坐标转换为行列索引
        c = round((event.x - self.margin) / self.cell_pixel)
        r = round((event.y - self.margin) / self.cell_pixel)
        
        if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
            if self.board[r][c] == 0:
                self.make_move(r, c, 1)
                if not self.game_over:
                    self.turn = 2
                    self.label_status.config(text=" AI 正在思考中... ")
                    self.root.after(500, self.ai_move)

    def make_move(self, r, c, player):
        self.board[r][c] = player
        self.draw_stone(r, c, player)
        
        if self.check_win(r, c, player):
            self.game_over = True
            if player == 1:
                self.label_status.config(text=" 恭喜！您赢了！ 🎉")
                messagebox.showinfo("游戏结束", "恭喜，您击败了 AI！")
            else:
                self.label_status.config(text=" AI 赢了，再接再厉！ 🤖")
                messagebox.showinfo("游戏结束", "AI 赢了，再试一次吧！")
        elif self.is_board_full():
            self.game_over = True
            self.label_status.config(text=" 和棋！ 🤝")
            messagebox.showinfo("游戏结束", "棋盘已满，平局！")

    def check_win(self, r, c, player):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)] # 水平、垂直、正对角线、反对角线
        for dr, dc in directions:
            count = 1
            # 正方向探索
            nr, nc = r + dr, c + dc
            while 0 <= nr < self.grid_size and 0 <= nc < self.grid_size and self.board[nr][nc] == player:
                count += 1
                nr += dr
                nc += dc
            # 反方向探索
            nr, nc = r - dr, c - dc
            while 0 <= nr < self.grid_size and 0 <= nc < self.grid_size and self.board[nr][nc] == player:
                count += 1
                nr -= dr
                nc -= dc
                
            if count >= 5:
                return True
        return False

    def is_board_full(self):
        return all(self.board[r][c] != 0 for r in range(self.grid_size) for c in range(self.grid_size))

    # --- AI 简单决策算法 ---
    def ai_move(self):
        if self.game_over:
            return
            
        best_score = -1
        best_moves = []
        
        # 遍历棋盘寻找最优落子点
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.board[r][c] == 0:
                    # 评分公式：进攻分数 * 权重 + 防守分数
                    # 稍微偏向于进攻，从而让AI更有攻击性
                    ai_score = self.evaluate_point(r, c, 2)
                    player_score = self.evaluate_point(r, c, 1)
                    
                    total_score = ai_score * 1.1 + player_score
                    
                    if total_score > best_score:
                        best_score = total_score
                        best_moves = [(r, c)]
                    elif total_score == best_score:
                        best_moves.append((r, c))
                        
        if best_moves:
            # 如果有多个相同最高分，随机选择一个，增加棋局多样性
            import random
            br, bc = random.choice(best_moves)
            self.make_move(br, bc, 2)
            
        if not self.game_over:
            self.turn = 1
            self.label_status.config(text=" 轮到您执黑子下棋 ")

    def evaluate_point(self, r, c, player):
        """
        评估如果 player 在 (r, c) 落子，其潜在的威胁程度/得分
        """
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            # 在一个方向上，检查包含 (r, c) 在内的连续 5 个格子的所有可能组合
            # 每个方向有 5 种可能的“五子相连”路径覆盖 (r, c)
            for offset in range(5):
                start_r = r - offset * dr
                start_c = c - offset * dc
                
                my_stones = 0
                opponent_stones = 0
                
                # 检查该路径下的 5 个连续位置
                for i in range(5):
                    curr_r = start_r + i * dr
                    curr_c = start_c + i * dc
                    
                    if 0 <= curr_r < self.grid_size and 0 <= curr_c < self.grid_size:
                        stone = self.board[curr_r][curr_c]
                        if curr_r == r and curr_c == c:
                            # 假设我们要下在这里
                            my_stones += 1
                        elif stone == player:
                            my_stones += 1
                        elif stone != 0:
                            opponent_stones += 1
                    else:
                        opponent_stones += 1 # 越界视为被敌方封堵
                        
                # 依据该段区间内的棋子组合进行评分
                score += self.get_shape_score(my_stones, opponent_stones)
                
        return score

    def get_shape_score(self, mine, opp):
        """
        静态启发式评分表。根据一段长度为5的区域里，己方和对方棋子的数量分配分数
        """
        if mine > 0 and opp > 0:
            return 0  # 混合情况（互相堵塞，无价值路径）
        if mine == 5:
            return 100000  # 五连（致胜）
        if mine == 4:
            return 10000   # 活四或冲四
        if mine == 3:
            return 1000    # 活三
        if mine == 2:
            return 100     # 活二
        if mine == 1:
            return 10      # 活一
        return 0

    def reset_game(self):
        self.board = [[0] * self.grid_size for _ in range(self.grid_size)]
        self.game_over = False
        self.turn = 1
        self.label_status.config(text=" 轮到您执黑子下棋 ")
        self.draw_board()


if __name__ == "__main__":
    root = tk.Tk()
    game = Gomoku(root)
    root.mainloop()