import pygame
 
import random
import time
import json

from enum import Enum

from math import sin, cos, radians

from pygame import gfxdraw

# Initialize Pygame

pygame.init()



# Global configuration

CONFIG = {

    "INIT_WIDTH": 1280,

    "INIT_HEIGHT": 720,

    "GRID_SIZE": 24,

    "FPS": 12,

    "SAVE_FILE": "save.json"

}



# Color palette

COLORS = {

    "bg": (12, 20, 30),

    "text": (200, 220, 240),

    "obstacle": (80, 90, 100),

    "snake_head": [(80, 255, 160), (40, 180, 110)],

    "snake_body": [(60, 200, 140), (30, 150, 90)],

    "food": {

        "normal": (255, 100, 100),

        "speed_up": (100, 200, 255),

        "speed_down": (180, 100, 255),

        "ghost": (255, 220, 100)

    }

}



class Direction(Enum):

    UP = (0, -1)

    DOWN = (0, 1)

    LEFT = (-1, 0)

    RIGHT = (1, 0)



class GameMode(Enum):

    CLASSIC = "Classic"

    MAZE = "Maze"

    FREESTYLE = "Freestyle"



class FoodType(Enum):

    NORMAL = 1

    SPEED_UP = 2

    SPEED_DOWN = 3

    GHOST = 4



class SnakeGame:

    def __init__(self):

        # Window initialization

        self.screen = pygame.display.set_mode(

            (CONFIG["INIT_WIDTH"], CONFIG["INIT_HEIGHT"]),

            pygame.RESIZABLE

        )

        pygame.display.set_caption("Adaptive Snake Game")

        self.clock = pygame.time.Clock()

        self.current_size = self.screen.get_size()

        self.high_scores = self.load_game_data()

        self.current_mode = GameMode.CLASSIC

        self.init_game_state()

        self.glow_phase = 0



    def load_game_data(self):

        """Load or initialize game save data"""

        try:

            with open(CONFIG["SAVE_FILE"], 'r') as f:

                data = json.load(f)

                # Convert legacy Chinese keys to English

                key_map = {

                    "经典模式": "Classic",

                    "迷宫挑战": "Maze",

                    "自由模式": "Freestyle"

                }

                scores = {

                    key_map.get(k, k): v 

                    for k, v in data.get("scores", {}).items()

                }

                # Ensure all modes have records

                for mode in GameMode:

                    if mode.value not in scores:

                        scores[mode.value] = 0

                return scores

        except:

            return {mode.value: 0 for mode in GameMode}



    def save_game_data(self):

        """Save high scores to file"""

        with open(CONFIG["SAVE_FILE"], 'w') as f:

            json.dump({"scores": self.high_scores}, f)



    def init_game_state(self):

        """Initialize game objects and state"""

        self.snake = [self.calculate_grid_center()]

        self.direction = Direction.RIGHT

        self.next_direction = Direction.RIGHT

        self.score = 0

        self.speed = CONFIG["FPS"]

        self.ghost_mode = False

        self.game_active = True

        self.food_count = 1

        self.generate_obstacles()

        self.food = self.spawn_food()



    def calculate_grid_center(self):

        """Calculate center position aligned to grid"""

        w, h = self.current_size

        return (

            (w // 2 // CONFIG["GRID_SIZE"]) * CONFIG["GRID_SIZE"],

            (h // 2 // CONFIG["GRID_SIZE"]) * CONFIG["GRID_SIZE"]

        )



    def generate_obstacles(self):

        """Generate maze obstacles based on current window size"""

        self.obstacles = []

        if self.current_mode == GameMode.MAZE:

            w, h = self.current_size

            max_col = (w - CONFIG["GRID_SIZE"]) // CONFIG["GRID_SIZE"]

            max_row = (h - CONFIG["GRID_SIZE"]) // CONFIG["GRID_SIZE"]

            for i in range(5, max_col, 4):

                for j in [5, 10, 15]:

                    if j < max_row:

                        self.obstacles.append((

                            i * CONFIG["GRID_SIZE"],

                            j * CONFIG["GRID_SIZE"]

                        ))



    def spawn_food(self):

        """Generate new food positions ensuring no overlaps"""

        w, h = self.current_size

        cols = (w - CONFIG["GRID_SIZE"]) // CONFIG["GRID_SIZE"]

        rows = (h - CONFIG["GRID_SIZE"]) // CONFIG["GRID_SIZE"]

        

        occupied = {*self.snake, *self.obstacles}

        available = [

            (x * CONFIG["GRID_SIZE"], y * CONFIG["GRID_SIZE"])

            for x in range(1, cols)

            for y in range(1, rows)

            if (x * CONFIG["GRID_SIZE"], y * CONFIG["GRID_SIZE"]) not in occupied

        ]

        random.shuffle(available)

        

        foods = []

        for _ in range(min(self.food_count, len(available))):

            pos = available.pop()

            foods.append((

                pos,

                random.choices(

                    list(FoodType),

                    weights=[70, 15, 10, 5]

                )[0]

            ))

        return foods



    def handle_input(self):

        """Process user input and window events"""

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                self.quit_game()

            elif event.type == pygame.VIDEORESIZE:

                # Handle window resize

                self.current_size = (event.w, event.h)

                self.screen = pygame.display.set_mode(

                    self.current_size, 

                    pygame.RESIZABLE

                )

                self.adjust_positions()

            elif event.type == pygame.KEYDOWN:

                # Direction controls

                if event.key == pygame.K_UP and self.direction != Direction.DOWN:

                    self.next_direction = Direction.UP

                elif event.key == pygame.K_DOWN and self.direction != Direction.UP:

                    self.next_direction = Direction.DOWN

                elif event.key == pygame.K_LEFT and self.direction != Direction.RIGHT:

                    self.next_direction = Direction.LEFT

                elif event.key == pygame.K_RIGHT and self.direction != Direction.LEFT:

                    self.next_direction = Direction.RIGHT

                # Mode switching

                if event.key == pygame.K_1: 

                    self.current_mode = GameMode.CLASSIC

                    self.init_game_state()

                elif event.key == pygame.K_2: 

                    self.current_mode = GameMode.MAZE

                    self.init_game_state()

                elif event.key == pygame.K_3: 

                    self.current_mode = GameMode.FREESTYLE

                    self.init_game_state()



    def adjust_positions(self):

        """Adjust game elements after window resize"""

        w, h = self.current_size

        # Convert positions proportionally

        self.snake = [

            (

                int((x / CONFIG["INIT_WIDTH"]) * w) // CONFIG["GRID_SIZE"] * CONFIG["GRID_SIZE"],

                int((y / CONFIG["INIT_HEIGHT"]) * h) // CONFIG["GRID_SIZE"] * CONFIG["GRID_SIZE"]

            )

            for (x, y) in self.snake

        ]

        # Regenerate obstacles and food

        self.generate_obstacles()

        self.food = self.spawn_food()



    def update_snake(self):

        """Update snake position and check collisions"""

        self.direction = self.next_direction

        dx, dy = self.direction.value

        

        new_head = (

            self.snake[0][0] + dx * CONFIG["GRID_SIZE"],

            self.snake[0][1] + dy * CONFIG["GRID_SIZE"]

        )

        

        w, h = self.current_size

        # Boundary handling

        if self.current_mode == GameMode.FREESTYLE:

            new_head = (

                new_head[0] % w,

                new_head[1] % h

            )

        else:

            if not (0 <= new_head[0] < w and 0 <= new_head[1] < h):

                self.game_over()

                return



        # Collision detection

        if (new_head in self.snake[1:] or 

            (not self.ghost_mode and new_head in self.obstacles)):

            self.game_over()

            return



        self.snake.insert(0, new_head)

        

        # Check food consumption

        eaten = False

        for idx, (pos, ftype) in enumerate(self.food):

            if new_head == pos:

                self.process_food(ftype)

                eaten = True

                del self.food[idx]

                break

        

        if eaten:

            self.food_count += 5

            new_food = self.spawn_food()

            self.food += new_food

        else:

            self.snake.pop()



    def process_food(self, ftype):

        """Apply food effects"""

        self.score += 10

        # Speed adjustments

        if ftype == FoodType.SPEED_UP:

            self.speed = min(30, self.speed + 2)

        elif ftype == FoodType.SPEED_DOWN:

            self.speed = max(8, self.speed - 2)

        elif ftype == FoodType.GHOST:

            self.ghost_mode = True

            pygame.time.set_timer(pygame.USEREVENT, 5000)



    def draw_glow(self, surface, pos, color):

        """Draw glowing effect around objects"""

        radius = CONFIG["GRID_SIZE"]//2 + int(4 * sin(radians(self.glow_phase)))

        for alpha in range(50, 0, -10):

            gfxdraw.filled_circle(

                surface,

                pos[0] + CONFIG["GRID_SIZE"]//2,

                pos[1] + CONFIG["GRID_SIZE"]//2,

                radius,

                (*color, alpha)

            )

        self.glow_phase = (self.glow_phase + 5) % 360



    def draw_snake(self):

        """Render snake with gradient colors"""

        for i, pos in enumerate(self.snake):

            # Head color

            if i == 0:

                color = COLORS["snake_head"][0]

            else:

                # Body gradient

                ratio = i / len(self.snake)

                color = [

                    int(COLORS["snake_body"][0][j] + 

                    (COLORS["snake_body"][1][j] - COLORS["snake_body"][0][j]) * ratio)

                    for j in range(3)

                ]

            # Draw segment

            pygame.draw.rect(

                self.screen, color,

                pygame.Rect(pos, (CONFIG["GRID_SIZE"], CONFIG["GRID_SIZE"])),

                border_radius=4

            )

            # Glow effect for head

            if i == 0:

                self.draw_glow(self.screen, pos, color)



    def draw_food(self):

        """Draw all food items with effects"""

        for pos, ftype in self.food:

            # Get color based on type

            color = COLORS["food"]["normal"]

            if ftype == FoodType.SPEED_UP:

                color = COLORS["food"]["speed_up"]

            elif ftype == FoodType.SPEED_DOWN:

                color = COLORS["food"]["speed_down"]

            elif ftype == FoodType.GHOST:

                color = COLORS["food"]["ghost"]

            

            # Draw food circle

            center = (

                pos[0] + CONFIG["GRID_SIZE"]//2,

                pos[1] + CONFIG["GRID_SIZE"]//2

            )

            pygame.draw.circle(

                self.screen, color,

                center,

                CONFIG["GRID_SIZE"]//3

            )

            self.draw_glow(self.screen, pos, color)



    def draw_ui(self):

        """Render game interface"""

        self.screen.fill(COLORS["bg"])

        w, h = self.current_size

        

        # Draw obstacles

        for obst in self.obstacles:

            pygame.draw.rect(self.screen, COLORS["obstacle"], 

                (obst[0]+2, obst[1]+2, CONFIG["GRID_SIZE"], CONFIG["GRID_SIZE"]),

                border_radius=3)

            pygame.draw.rect(self.screen, (100, 110, 120), 

                (obst[0], obst[1], CONFIG["GRID_SIZE"], CONFIG["GRID_SIZE"]),

                border_radius=3)

        

        # Draw game objects

        self.draw_snake()

        self.draw_food()

        

        # Display UI text

        self.draw_text(

            f"{self.current_mode.value} | Score: {self.score} | Food: {len(self.food)} | High: {self.high_scores[self.current_mode.value]}",

            (20, 20)

        )

        self.draw_text(

            "[1]Classic [2]Maze [3]Freestyle",

            (20, h - 40)

        )



    def draw_text(self, text, pos):

        """Helper method to draw text with shadow"""

        font = pygame.font.Font(None, 24)  # Use default font

        # Shadow

        text_surface = font.render(text, True, (30, 40, 50))

        self.screen.blit(text_surface, (pos[0]+2, pos[1]+2))

        # Main text

        text_surface = font.render(text, True, COLORS["text"])

        self.screen.blit(text_surface, pos)



    def game_over(self):

        """Handle game over state"""

        self.game_active = False

        # Update high score

        current_mode = self.current_mode.value

        if self.score > self.high_scores[current_mode]:

            self.high_scores[current_mode] = self.score

            self.save_game_data()

        # Show animation and reset

        self.show_game_over_animation()

        self.init_game_state()



    def show_game_over_animation(self):

        """Animated game over screen"""

        for alpha in range(0, 200, 5):

            overlay = pygame.Surface(self.current_size)

            overlay.set_alpha(alpha)

            overlay.fill((0, 0, 0))

            self.screen.blit(overlay, (0, 0))

            # Center text

            w, h = self.current_size

            self.draw_text("Game Over - Press Any Key",

                (w//4, h//2))

            pygame.display.flip()

            pygame.time.wait(30)



    def run(self):

        """Main game loop"""

        while True:

            self.handle_input()

            if self.game_active:

                self.update_snake()

            self.draw_ui()

            pygame.display.flip()

            self.clock.tick(self.speed)



    def quit_game(self):

        """Clean exit procedure"""

        self.save_game_data()

        pygame.quit()

        exit()



if __name__ == "__main__":

    game = SnakeGame()

    game.run()

