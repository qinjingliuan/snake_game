import pygame
import random
import time
import json
from enum import Enum
from math import sin, cos, radians
from pygame import gfxdraw

# 初始化Pygame
pygame.init()

# 全局配置
CONFIG = {
    "WIDTH": 1920,           # 窗口宽度
    "HEIGHT": 1080,          # 窗口高度
    "GRID_SIZE": 24,         # 网格尺寸
    "FPS": 6,                # 基础帧率
    "SAVE_FILE": "save.json" # 存档文件
}

# 高级颜色配置
COLORS = {
    "背景色": (12, 20, 30),
    "文字色": (200, 220, 240),
    "障碍色": (80, 90, 100),
    "蛇头渐变": [(80, 255, 160), (40, 180, 110)],
    "蛇身渐变": [(60, 200, 140), (30, 150, 90)],
    "食物": {
        "普通": (255, 100, 100),
        "加速": (100, 200, 255),
        "减速": (180, 100, 255),
        "无敌": (255, 220, 100)
    }
}

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class GameMode(Enum):
    CLASSIC = "经典模式"
    MAZE = "迷宫挑战"
    FREESTYLE = "自由模式"

class FoodType(Enum):
    NORMAL = 1
    SPEED_UP = 2
    SPEED_DOWN = 3
    GHOST = 4

class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((CONFIG["WIDTH"], CONFIG["HEIGHT"]))
        pygame.display.set_caption("幻光贪吃蛇")
        self.clock = pygame.time.Clock()
        self.load_game_data()
        self.current_mode = GameMode.CLASSIC
        self.init_game_state()
        self.glow_phase = 0

    def load_game_data(self):
        try:
            with open(CONFIG["SAVE_FILE"], 'r') as f:
                data = json.load(f)
                self.high_scores = data.get("scores", {mode.name:0 for mode in GameMode})
        except:
            self.high_scores = {mode.name:0 for mode in GameMode}

    def save_game_data(self):
        data = {"scores": self.high_scores}
        with open(CONFIG["SAVE_FILE"], 'w') as f:
            json.dump(data, f)

    def init_game_state(self):
        self.snake = [self.calculate_grid_center()]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.score = 0
        self.speed = CONFIG["FPS"]
        self.ghost_mode = False
        self.game_active = True
        self.food_count = 1  # 初始化食物数量
        self.generate_obstacles()
        self.food = self.spawn_food()

    def calculate_grid_center(self):
        grid_x = (CONFIG["WIDTH"] // (2*CONFIG["GRID_SIZE"])) * CONFIG["GRID_SIZE"]
        grid_y = (CONFIG["HEIGHT"] // (2*CONFIG["GRID_SIZE"])) * CONFIG["GRID_SIZE"]
        return (grid_x, grid_y)

    def generate_obstacles(self):
        self.obstacles = []
        if self.current_mode == GameMode.MAZE:
            pattern = [
                (i*CONFIG["GRID_SIZE"], j*CONFIG["GRID_SIZE"])
                for i in range(5, CONFIG["WIDTH"]//CONFIG["GRID_SIZE"]-5, 4)
                for j in [5, 10, 15]
            ]
            self.obstacles.extend(pattern)

    def spawn_food(self):
        food_list = []
        existing_positions = set(self.snake + self.obstacles)
        
        # 计算所有可能的有效位置
        available_positions = []
        for x in range(1, (CONFIG["WIDTH"] - CONFIG["GRID_SIZE"]) // CONFIG["GRID_SIZE"]):
            for y in range(1, (CONFIG["HEIGHT"] - CONFIG["GRID_SIZE"]) // CONFIG["GRID_SIZE"]):
                pos = (x * CONFIG["GRID_SIZE"], y * CONFIG["GRID_SIZE"])
                if pos not in existing_positions:
                    available_positions.append(pos)
        
        random.shuffle(available_positions)
        
        # 生成指定数量的食物
        for _ in range(min(self.food_count, len(available_positions))):
            if not available_positions:
                break
            pos = available_positions.pop()
            food_type = random.choices(
                list(FoodType),
                weights=[70, 15, 10, 5]
            )[0]
            food_list.append((pos, food_type))
            existing_positions.add(pos)
        
        return food_list

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and self.direction != Direction.DOWN:
                    self.next_direction = Direction.UP
                elif event.key == pygame.K_DOWN and self.direction != Direction.UP:
                    self.next_direction = Direction.DOWN
                elif event.key == pygame.K_LEFT and self.direction != Direction.RIGHT:
                    self.next_direction = Direction.LEFT
                elif event.key == pygame.K_RIGHT and self.direction != Direction.LEFT:
                    self.next_direction = Direction.RIGHT
                if event.key == pygame.K_1: self.change_mode(GameMode.CLASSIC)
                if event.key == pygame.K_2: self.change_mode(GameMode.MAZE)
                if event.key == pygame.K_3: self.change_mode(GameMode.FREESTYLE)

    def change_mode(self, new_mode):
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.init_game_state()

    def update_snake(self):
        self.direction = self.next_direction
        
        dx, dy = self.direction.value
        new_head = (
            self.snake[0][0] + dx * CONFIG["GRID_SIZE"],
            self.snake[0][1] + dy * CONFIG["GRID_SIZE"]
        )
        
        if self.current_mode == GameMode.FREESTYLE:
            new_head = (
                new_head[0] % CONFIG["WIDTH"],
                new_head[1] % CONFIG["HEIGHT"]
            )
        else:
            if not (0 <= new_head[0] < CONFIG["WIDTH"] and 0 <= new_head[1] < CONFIG["HEIGHT"]):
                self.game_over()
                return

        if self.check_collision(new_head):
            self.game_over()
            return

        self.snake.insert(0, new_head)
        
        # 检查是否吃到任何食物
        eaten = False
        for food in self.food:
            if new_head == food[0]:
                self.process_food(food[1])
                eaten = True
                break
        if eaten:
            self.food_count += 5  # 每次增加5个食物
            self.food = self.spawn_food()
        else:
            self.snake.pop()

    def check_collision(self, pos):
        obstacle_check = not self.ghost_mode and pos in self.obstacles
        return pos in self.snake[1:] or (obstacle_check and self.current_mode != GameMode.FREESTYLE)

    def process_food(self, food_type):
        self.score += 10
        if food_type == FoodType.SPEED_UP:
            self.speed = min(120, self.speed + 5)
        elif food_type == FoodType.SPEED_DOWN:
            self.speed = max(30, self.speed - 5)
        elif food_type == FoodType.GHOST:
            self.ghost_mode = True
            pygame.time.set_timer(pygame.USEREVENT, 5000)

    def draw_glow_effect(self, surface, pos, color):
        radius = CONFIG["GRID_SIZE"]//2 + int(4 * sin(radians(self.glow_phase)))
        for alpha in range(50, 0, -10):
            glow_color = (*color, alpha)
            gfxdraw.filled_circle(
                surface,
                pos[0] + CONFIG["GRID_SIZE"]//2,
                pos[1] + CONFIG["GRID_SIZE"]//2,
                radius,
                glow_color
            )
        self.glow_phase = (self.glow_phase + 5) % 360

    def draw_snake(self):
        for i, pos in enumerate(self.snake):
            if i == 0:
                color = COLORS["蛇头渐变"][0] if i % 2 == 0 else COLORS["蛇头渐变"][1]
            else:
                ratio = i / len(self.snake)
                color = [
                    int(a + (b - a) * ratio)
                    for a, b in zip(COLORS["蛇身渐变"][0], COLORS["蛇身渐变"][1])
                ]
            rect = pygame.Rect(pos, (CONFIG["GRID_SIZE"], CONFIG["GRID_SIZE"]))
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            if i == 0:
                self.draw_glow_effect(self.screen, pos, color)

    def draw_food(self):
        for pos, food_type in self.food:
            color_map = {
                FoodType.NORMAL: COLORS["食物"]["普通"],
                FoodType.SPEED_UP: COLORS["食物"]["加速"],
                FoodType.SPEED_DOWN: COLORS["食物"]["减速"],
                FoodType.GHOST: COLORS["食物"]["无敌"]
            }
            color = color_map[food_type]
            center = (
                pos[0] + CONFIG["GRID_SIZE"]//2,
                pos[1] + CONFIG["GRID_SIZE"]//2
            )
            pygame.draw.circle(self.screen, color, center, CONFIG["GRID_SIZE"]//3)
            self.draw_glow_effect(self.screen, pos, color)

    def draw_ui(self):
        self.screen.fill(COLORS["背景色"])
        for obstacle in self.obstacles:
            pygame.draw.rect(self.screen, COLORS["障碍色"], 
                           (obstacle[0]+2, obstacle[1]+2, CONFIG["GRID_SIZE"], CONFIG["GRID_SIZE"]),
                           border_radius=3)
            pygame.draw.rect(self.screen, (100, 110, 120), 
                           (obstacle[0], obstacle[1], CONFIG["GRID_SIZE"], CONFIG["GRID_SIZE"]),
                           border_radius=3)
        self.draw_snake()
        self.draw_food()
        self.draw_text(
            f"{self.current_mode.value} | 分数: {self.score} | 当前食物数: {len(self.food)} | 最高记录: {self.high_scores[self.current_mode.name]}",
            (20, 20)
        )
        self.draw_text(
            "[1]经典模式 [2]迷宫挑战 [3]自由模式",
            (20, CONFIG["HEIGHT"] - 40)
        )

    def draw_text(self, text, pos):
        font = pygame.font.SysFont("simhei", 24)
        text_surface = font.render(text, True, (30, 40, 50))
        self.screen.blit(text_surface, (pos[0]+2, pos[1]+2))
        text_surface = font.render(text, True, COLORS["文字色"])
        self.screen.blit(text_surface, pos)

    def game_over(self):
        self.game_active = False
        if self.score > self.high_scores[self.current_mode.name]:
            self.high_scores[self.current_mode.name] = self.score
            self.save_game_data()
        self.show_game_over_animation()
        self.init_game_state()

    def show_game_over_animation(self):
        for alpha in range(0, 200, 5):
            overlay = pygame.Surface((CONFIG["WIDTH"], CONFIG["HEIGHT"]))
            overlay.set_alpha(alpha)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            self.draw_text("游戏结束 - 按任意键继续", 
                          (CONFIG["WIDTH"]//4, CONFIG["HEIGHT"]//2))
            pygame.display.flip()
            pygame.time.wait(30)

    def run(self):
        while True:
            self.handle_input()
            if self.game_active:
                self.update_snake()
            self.draw_ui()
            pygame.display.flip()
            self.clock.tick(self.speed)

    def quit_game(self):
        self.save_game_data()
        pygame.quit()
        exit()

if __name__ == "__main__":
    game = SnakeGame()
    game.run()
