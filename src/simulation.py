import pygame
import random
import sys
import time
import os
import csv
from datetime import datetime
from logic import TrafficLogic
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Initialize Pygame
pygame.init()

# Setup Display
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Adaptive Traffic Simulation")
font = pygame.font.SysFont("segoeui", 22, bold=True)

# Beautified Colors
ASPHALT = (45, 45, 45)
JUNCTION = (55, 55, 55)
WHITE = (240, 240, 240)
YELLOW_LINE = (240, 180, 0)
RED = (220, 20, 60)
YELLOW = (255, 165, 0)
GREEN = (0, 200, 50)
GRASS = (50, 120, 60)

# Intersection boundaries
ROAD_WIDTH = 160
LANE_WIDTH = 40
CENTER = WIDTH // 2

# Simulation settings
SIMULATION_DURATION = 300  # 5 minutes in seconds


class Vehicle:
    def __init__(self, direction):
        self.direction = direction
        self.original_direction = direction
        self.origin_road = direction  # Track where vehicle came from for logging
        self.speed = 2
        self.color = (random.randint(80, 220), random.randint(80, 220), random.randint(80, 220))
        self.width, self.length = 20, 32
        self.stopped = False
        self.has_turned = False

        self.turn_intent = random.choices(['straight', 'left', 'right'], weights=[0.6, 0.2, 0.2])[0]

        # Right-Hand Traffic Lane Assignments
        if self.turn_intent == 'right':
            self.offset = 60
        elif self.turn_intent == 'left':
            self.offset = 20
        else:
            self.offset = random.choice([20, 60])

        self.turn_point = None

        if direction == 'N':
            self.x = CENTER - self.offset - self.width // 2
            self.y = -self.length
            if self.turn_intent == 'right':
                self.turn_point = CENTER - self.offset
            if self.turn_intent == 'left':
                self.turn_point = CENTER + self.offset

        elif direction == 'S':
            self.x = CENTER + self.offset - self.width // 2
            self.y = HEIGHT
            if self.turn_intent == 'right':
                self.turn_point = CENTER + self.offset
            if self.turn_intent == 'left':
                self.turn_point = CENTER - self.offset

        elif direction == 'E':
            self.x = WIDTH
            self.y = CENTER - self.offset - self.width // 2
            self.width, self.length = 32, 20
            if self.turn_intent == 'right':
                self.turn_point = CENTER + self.offset
            if self.turn_intent == 'left':
                self.turn_point = CENTER - self.offset

        elif direction == 'W':
            self.x = -self.width
            self.y = CENTER + self.offset - self.width // 2
            self.width, self.length = 32, 20
            if self.turn_intent == 'right':
                self.turn_point = CENTER - self.offset
            if self.turn_intent == 'left':
                self.turn_point = CENTER + self.offset

    def execute_turn(self):
        self.width, self.length = self.length, self.width
        self.has_turned = True

        if self.original_direction == 'N':
            self.direction = 'E' if self.turn_intent == 'right' else 'W'
        elif self.original_direction == 'S':
            self.direction = 'W' if self.turn_intent == 'right' else 'E'
        elif self.original_direction == 'E':
            self.direction = 'S' if self.turn_intent == 'right' else 'N'
        elif self.original_direction == 'W':
            self.direction = 'N' if self.turn_intent == 'right' else 'S'

    def move(self, all_vehicles, current_lights):
        self.stopped = False

        # Universal Collision Sensor
        vision_len = 15
        if self.direction == 'N':
            vision = pygame.Rect(self.x, self.y + self.length, self.width, vision_len)
        elif self.direction == 'S':
            vision = pygame.Rect(self.x, self.y - vision_len, self.width, vision_len)
        elif self.direction == 'E':
            vision = pygame.Rect(self.x - vision_len, self.y, vision_len, self.length)
        elif self.direction == 'W':
            vision = pygame.Rect(self.x + self.width, self.y, vision_len, self.length)

        for v in all_vehicles:
            if v is self:
                continue
            other_rect = pygame.Rect(v.x, v.y, v.width, v.length)

            if vision.colliderect(other_rect):
                if self.turn_intent == 'left' and v.turn_intent == 'left':
                    opposing = [('N', 'S'), ('S', 'N'), ('E', 'W'), ('W', 'E')]
                    if (self.original_direction, v.original_direction) in opposing:
                        continue

                self.stopped = True
                break

        # Red Light Stop Lines
        stop_dist = 12
        if not self.has_turned and not self.stopped:
            if self.direction == 'N':
                stop_y = CENTER - ROAD_WIDTH // 2 - stop_dist
                if current_lights['N'] != 1 and self.y + self.length >= stop_y - self.speed and self.y < stop_y:
                    self.stopped = True
            elif self.direction == 'S':
                stop_y = CENTER + ROAD_WIDTH // 2 + stop_dist
                if current_lights['S'] != 1 and self.y <= stop_y + self.speed and self.y > stop_y:
                    self.stopped = True
            elif self.direction == 'E':
                stop_x = CENTER + ROAD_WIDTH // 2 + stop_dist
                if current_lights['E'] != 1 and self.x <= stop_x + self.speed and self.x > stop_x:
                    self.stopped = True
            elif self.direction == 'W':
                stop_x = CENTER - ROAD_WIDTH // 2 - stop_dist
                if current_lights['W'] != 1 and self.x + self.width >= stop_x - self.speed and self.x < stop_x:
                    self.stopped = True

        # Movement & Pivoting
        if not self.stopped:
            if not self.has_turned and self.turn_point is not None:
                if self.direction == 'N' and self.y >= self.turn_point:
                    self.execute_turn()
                elif self.direction == 'S' and self.y <= self.turn_point:
                    self.execute_turn()
                elif self.direction == 'E' and self.x <= self.turn_point:
                    self.execute_turn()
                elif self.direction == 'W' and self.x >= self.turn_point:
                    self.execute_turn()

            if self.direction == 'N':
                self.y += self.speed
            elif self.direction == 'S':
                self.y -= self.speed
            elif self.direction == 'E':
                self.x -= self.speed
            elif self.direction == 'W':
                self.x += self.speed

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.length), border_radius=6)

        # Blinker Visuals
        if not self.has_turned and self.turn_intent != 'straight':
            blinker_color = (255, 200, 0)
            if pygame.time.get_ticks() % 600 < 300:
                if self.original_direction == 'N':
                    bx = self.x if self.turn_intent == 'right' else self.x + self.width - 4
                    pygame.draw.rect(surface, blinker_color, (bx, self.y + self.length - 4, 4, 4))
                elif self.original_direction == 'S':
                    bx = self.x + self.width - 4 if self.turn_intent == 'right' else self.x
                    pygame.draw.rect(surface, blinker_color, (bx, self.y, 4, 4))
                elif self.original_direction == 'E':
                    by = self.y if self.turn_intent == 'right' else self.y + self.length - 4
                    pygame.draw.rect(surface, blinker_color, (self.x, by, 4, 4))
                elif self.original_direction == 'W':
                    by = self.y + self.length - 4 if self.turn_intent == 'right' else self.y
                    pygame.draw.rect(surface, blinker_color, (self.x + self.width - 4, by, 4, 4))


def draw_intersection():
    screen.fill(GRASS)

    # Draw Asphalt Roads
    pygame.draw.rect(screen, ASPHALT, (CENTER - ROAD_WIDTH // 2, 0, ROAD_WIDTH, HEIGHT))
    pygame.draw.rect(screen, ASPHALT, (0, CENTER - ROAD_WIDTH // 2, WIDTH, ROAD_WIDTH))

    # Draw Central Junction Box
    pygame.draw.rect(screen, JUNCTION, (CENTER - ROAD_WIDTH // 2, CENTER - ROAD_WIDTH // 2, ROAD_WIDTH, ROAD_WIDTH))

    # Draw Solid Stop Lines
    pygame.draw.rect(screen, WHITE, (CENTER - ROAD_WIDTH // 2, CENTER - ROAD_WIDTH // 2 - 8, ROAD_WIDTH // 2, 6))
    pygame.draw.rect(screen, WHITE, (CENTER, CENTER + ROAD_WIDTH // 2 + 2, ROAD_WIDTH // 2, 6))
    pygame.draw.rect(screen, WHITE, (CENTER + ROAD_WIDTH // 2 + 2, CENTER - ROAD_WIDTH // 2, 6, ROAD_WIDTH // 2))
    pygame.draw.rect(screen, WHITE, (CENTER - ROAD_WIDTH // 2 - 8, CENTER, 6, ROAD_WIDTH // 2))

    # Draw Lane Lines
    for i in range(0, HEIGHT, 40):
        if i < CENTER - ROAD_WIDTH // 2 or i > CENTER + ROAD_WIDTH // 2:
            pygame.draw.rect(screen, YELLOW_LINE, (CENTER - 3, i, 2, 20))
            pygame.draw.rect(screen, YELLOW_LINE, (CENTER + 1, i, 2, 20))
            pygame.draw.rect(screen, WHITE, (CENTER - ROAD_WIDTH // 4 - 1, i, 2, 20))
            pygame.draw.rect(screen, WHITE, (CENTER + ROAD_WIDTH // 4 - 1, i, 2, 20))

        if i < CENTER - ROAD_WIDTH // 2 or i > CENTER + ROAD_WIDTH // 2:
            pygame.draw.rect(screen, YELLOW_LINE, (i, CENTER - 3, 20, 2))
            pygame.draw.rect(screen, YELLOW_LINE, (i, CENTER + 1, 20, 2))
            pygame.draw.rect(screen, WHITE, (i, CENTER - ROAD_WIDTH // 4 - 1, 20, 2))
            pygame.draw.rect(screen, WHITE, (i, CENTER + ROAD_WIDTH // 4 - 1, 20, 2))


def draw_lights(current_lights):
    def draw_light_set(x, y, state, horizontal=False):
        pygame.draw.rect(screen, (20, 20, 20), (x, y, 60 if horizontal else 20, 20 if horizontal else 60),
                         border_radius=4)
        for i, color in enumerate([RED, YELLOW, GREEN]):
            circ_color = color if state == i else (40, 40, 40)
            if horizontal:
                pygame.draw.circle(screen, circ_color, (x + 10 + i * 20, y + 10), 6)
            else:
                pygame.draw.circle(screen, circ_color, (x + 10, y + 10 + i * 20), 6)

    draw_light_set(CENTER - ROAD_WIDTH // 2 - 30, CENTER - ROAD_WIDTH // 2 - 70, current_lights['N'])
    draw_light_set(CENTER + ROAD_WIDTH // 2 + 10, CENTER + ROAD_WIDTH // 2 + 10, current_lights['S'])
    draw_light_set(CENTER + ROAD_WIDTH // 2 + 10, CENTER - ROAD_WIDTH // 2 - 30, current_lights['E'], True)
    draw_light_set(CENTER - ROAD_WIDTH // 2 - 70, CENTER + ROAD_WIDTH // 2 + 10, current_lights['W'], True)


def save_results(passed_counts):
    """Save simulation results to CSV file and MongoDB Cloud."""
    # --- 1. Save to Local CSV ---
    csv_path = "data/simulation_results.csv"
    os.makedirs("data", exist_ok=True)
    file_exists = os.path.exists(csv_path)
    total = sum(passed_counts.values())

    row = {
        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Mode': 'Adaptive',
        'Lane 1 (N)': passed_counts['N'],
        'Lane 2 (E)': passed_counts['E'],
        'Lane 3 (S)': passed_counts['S'],
        'Lane 4 (W)': passed_counts['W'],
        'Total': total
    }

    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Timestamp', 'Mode', 'Lane 1 (N)', 'Lane 2 (E)', 'Lane 3 (S)', 'Lane 4 (W)', 'Total'])
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    print(f"Results saved locally: N={passed_counts['N']}, E={passed_counts['E']}, S={passed_counts['S']}, W={passed_counts['W']}, Total={total}")

    # --- 2. Sync to MongoDB Cloud ---
    try:
        print("Attempting to sync data to MongoDB Atlas...")
        load_dotenv()
        uri = os.getenv("MONGO_URI")
        
        client = MongoClient(uri, server_api=ServerApi('1'))
        db = client['traffic_dashboard']
        collection = db['simulation_results']
        
        sim_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "Adaptive",
            "lanes": {
                "north": passed_counts['N'],
                "east": passed_counts['E'],
                "south": passed_counts['S'],
                "west": passed_counts['W']
            },
            "total_vehicles": total
        }
        
        collection.insert_one(sim_data)
        print("✅ Data successfully synced to MongoDB Cloud!")
        
    except Exception as e:
        print(f"❌ Cloud Sync Failed: {e}")


def main():
    clock = pygame.time.Clock()
    vehicles = []

    # Initialize traffic controller
    traffic_controller = TrafficLogic()
    current_lights = {'N': 1, 'S': 0, 'E': 0, 'W': 0}

    # Track vehicles that successfully pass through intersection
    passed_counts = {'N': 0, 'S': 0, 'E': 0, 'W': 0}

    # Start timer for auto-close
    start_time = time.time()

    running = True
    while running:
        # Check for 5-minute timeout
        elapsed_time = time.time() - start_time
        if elapsed_time >= SIMULATION_DURATION:
            print(f"Simulation auto-closing after {SIMULATION_DURATION} seconds.")
            running = False
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

        if not running:
            break

        # Spawn vehicles (2% chance per frame)
        if random.randint(1, 100) <= 2:
            vehicles.append(Vehicle(random.choice(['N', 'S', 'E', 'W'])))

        # Calculate live counts
        counts = {'N': 0, 'S': 0, 'E': 0, 'W': 0}
        for v in vehicles:
            if v.direction == 'N' and v.y < CENTER:
                counts['N'] += 1
            elif v.direction == 'S' and v.y > CENTER:
                counts['S'] += 1
            elif v.direction == 'E' and v.x > CENTER:
                counts['E'] += 1
            elif v.direction == 'W' and v.x < CENTER:
                counts['W'] += 1

        # Update traffic lights based on counts
        current_lights = traffic_controller.update_lights(counts)

        # Draw environment
        draw_intersection()
        draw_lights(current_lights)

        # Update and draw vehicles
        for v in vehicles[:]:
            v.move(vehicles, current_lights)
            v.draw(screen)

            # Check if vehicle has exited the screen (successfully passed)
            if v.y > HEIGHT + 50 or v.y < -50 or v.x > WIDTH + 50 or v.x < -50:
                # Increment passed count based on origin road
                passed_counts[v.origin_road] += 1
                vehicles.remove(v)

        # Draw counters
        screen.blit(font.render(f"North Queue: {counts['N']}", True, WHITE), (20, 20))
        screen.blit(font.render(f"South Queue: {counts['S']}", True, WHITE), (WIDTH - 180, HEIGHT - 40))
        screen.blit(font.render(f"East Queue: {counts['E']}", True, WHITE), (WIDTH - 180, 20))
        screen.blit(font.render(f"West Queue: {counts['W']}", True, WHITE), (20, HEIGHT - 40))

        # Draw timer
        remaining = max(0, SIMULATION_DURATION - int(elapsed_time))
        minutes = remaining // 60
        seconds = remaining % 60
        timer_text = f"Time: {minutes:02d}:{seconds:02d}"
        screen.blit(font.render(timer_text, True, WHITE), (WIDTH // 2 - 50, 20))

        # Draw passed counts
        total_passed = sum(passed_counts.values())
        screen.blit(font.render(f"Passed: {total_passed}", True, GREEN), (WIDTH // 2 - 50, HEIGHT - 40))

        pygame.display.flip()
        clock.tick(60)

    # Save results before exiting
    save_results(passed_counts)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()


    