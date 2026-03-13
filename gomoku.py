#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五子棋游戏
支持双人对战模式
"""

import tkinter as tk
from tkinter import messagebox

class GomokuGame:
    def __init__(self, root):
        self.root = root
        self.root.title("五子棋")
        self.root.geometry("600x700")
        
        # 棋盘大小
        self.board_size = 15
        self.cell_size = 40
        self.padding = 30
        
        # 棋盘状态：0-空，1-黑棋，2-白棋
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        
        # 当前玩家：1-黑棋，2-白棋
        self.current_player = 1
        self.game_over = False
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        """创建游戏界面"""
        # 顶部信息栏
        self.info_frame = tk.Frame(self.root)
        self.info_frame.pack(pady=10)
        
        self.player_label = tk.Label(self.info_frame, text="当前玩家：黑棋", 
                                     font=("Arial", 14, "bold"))
        self.player_label.pack()
        
        # 棋盘画布
        self.canvas = tk.Canvas(self.root, 
                               width=self.cell_size * (self.board_size - 1) + 2 * self.padding,
                               height=self.cell_size * (self.board_size - 1) + 2 * self.padding,
                               bg="#DEB887")
        self.canvas.pack(pady=10)
        
        # 绘制棋盘
        self.draw_board()
        
        # 绑定点击事件
        self.canvas.bind("<Button-1>", self.on_click)
        
        # 底部按钮
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=10)
        
        self.restart_button = tk.Button(self.button_frame, text="重新开始", 
                                       command=self.restart_game,
                                       font=("Arial", 12))
        self.restart_button.pack(side=tk.LEFT, padx=10)
        
        self.quit_button = tk.Button(self.button_frame, text="退出", 
                                    command=self.root.quit,
                                    font=("Arial", 12))
        self.quit_button.pack(side=tk.LEFT, padx=10)
        
    def draw_board(self):
        """绘制棋盘"""
        self.canvas.delete("all")
        
        # 绘制网格线
        for i in range(self.board_size):
            # 横线
            x1 = self.padding
            y1 = self.padding + i * self.cell_size
            x2 = self.padding + (self.board_size - 1) * self.cell_size
            y2 = y1
            self.canvas.create_line(x1, y1, x2, y2, fill="black", width=1)
            
            # 竖线
            x1 = self.padding + i * self.cell_size
            y1 = self.padding
            x2 = x1
            y2 = self.padding + (self.board_size - 1) * self.cell_size
            self.canvas.create_line(x1, y1, x2, y2, fill="black", width=1)
        
        # 绘制天元和星位
        star_points = [(3, 3), (3, 7), (3, 11),
                      (7, 3), (7, 7), (7, 11),
                      (11, 3), (11, 7), (11, 11)]
        
        for x, y in star_points:
            cx = self.padding + x * self.cell_size
            cy = self.padding + y * self.cell_size
            self.canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill="black")
        
        # 绘制已下的棋子
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i][j] != 0:
                    self.draw_piece(i, j, self.board[i][j])
    
    def draw_piece(self, row, col, player):
        """绘制棋子"""
        x = self.padding + col * self.cell_size
        y = self.padding + row * self.cell_size
        radius = self.cell_size // 2 - 2
        
        if player == 1:  # 黑棋
            color = "black"
        else:  # 白棋
            color = "white"
        
        self.canvas.create_oval(x - radius, y - radius, 
                               x + radius, y + radius,
                               fill=color, outline="black")
    
    def on_click(self, event):
        """处理点击事件"""
        if self.game_over:
            return
        
        # 计算点击的格子位置
        col = round((event.x - self.padding) / self.cell_size)
        row = round((event.y - self.padding) / self.cell_size)
        
        # 检查是否在有效范围内
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            # 检查该位置是否为空
            if self.board[row][col] == 0:
                # 下棋
                self.board[row][col] = self.current_player
                self.draw_piece(row, col, self.current_player)
                
                # 检查是否获胜
                if self.check_win(row, col):
                    winner = "黑棋" if self.current_player == 1 else "白棋"
                    messagebox.showinfo("游戏结束", f"{winner}获胜！")
                    self.game_over = True
                    return
                
                # 切换玩家
                self.current_player = 3 - self.current_player
                player_text = "黑棋" if self.current_player == 1 else "白棋"
                self.player_label.config(text=f"当前玩家：{player_text}")
    
    def check_win(self, row, col):
        """检查是否获胜"""
        player = self.board[row][col]
        
        # 检查四个方向：水平、垂直、对角线、反对角线
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dx, dy in directions:
            count = 1
            
            # 正向检查
            i, j = row + dx, col + dy
            while 0 <= i < self.board_size and 0 <= j < self.board_size and self.board[i][j] == player:
                count += 1
                i += dx
                j += dy
            
            # 反向检查
            i, j = row - dx, col - dy
            while 0 <= i < self.board_size and 0 <= j < self.board_size and self.board[i][j] == player:
                count += 1
                i -= dx
                j -= dy
            
            if count >= 5:
                return True
        
        return False
    
    def restart_game(self):
        """重新开始游戏"""
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.current_player = 1
        self.game_over = False
        self.player_label.config(text="当前玩家：黑棋")
        self.draw_board()

def main():
    root = tk.Tk()
    game = GomokuGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
