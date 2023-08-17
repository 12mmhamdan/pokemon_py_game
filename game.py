import pygame
import requests
import io
import random
from collections import deque
from pygame.locals import KEYDOWN, K_RETURN

# Global Colors
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
TAN = (210, 180, 140)
DARK_TAN = (175, 150, 115)
DARK_RED = (204,0,0)
DARK_YELLOW = (179, 161, 37)

# Window Size
WIDTH, HEIGHT = 1100, 900

class Pokemon:
    all_pokemon = []
    all_pokemon_ids = set()

    def __init__(self):
        random_id = random.randint(1, 151)
        while random_id in Pokemon.all_pokemon_ids:
            random_id = random.randint(1, 151)
        self.create_from_id(random_id)
        Pokemon.all_pokemon.append(self)
        Pokemon.all_pokemon_ids.add(random_id)

    def create_from_id(self, id):
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{id}")
        if not response.ok:
            return False
        data = response.json()
        self.name = data["name"]
        self.id = data["id"]
        self.hit_points = data["stats"][0]["base_stat"]
        self.attack_points = data["stats"][1]["base_stat"]
        self.defense_points = data["stats"][2]["base_stat"]
        self.sprite = self.set_and_scale_sprite(data["sprites"]["other"]["home"]["front_default"], 80)
        return True
    
    def set_and_scale_sprite(self, url, max_height):
        # Fetch the sprite
        response = requests.get(url)
        image_data = io.BytesIO(response.content)
        sprite = pygame.image.load(image_data)

        # Scale the sprite to fit the max height
        scale_factor = max_height / sprite.get_height()
        scaled_width = int(sprite.get_width() * scale_factor)
        scaled_height = max_height  # Since you want to scale by height.

        
        return pygame.transform.scale(sprite, (scaled_width, scaled_height))




class Pokeball:
    def __init__(self, is_pokeball=True):
        self.is_pokeball = is_pokeball
        self.pokemon = Pokemon()

class BackgroundItem:
    all_background_items = []

    def __init__(self, sprite_path, pokeball):
        self.sprite = pygame.image.load(sprite_path)
        self.rect = self.sprite.get_rect()
        self.pokeball = pokeball
        BackgroundItem.all_background_items.append(self)

    def has_pokeball(self):
        return self.pokeball is not None

    def draw(self, screen):
        screen.blit(self.sprite, self.rect.topleft)

def create_random_background_items(num_items):
    items = []
    for _ in range(num_items):
        pokeball = Pokeball() if len(BackgroundItem.all_background_items) <= 5 else None
        item = BackgroundItem('./sprites/tree-green.png', pokeball)
        item.rect.x = random.randint(0, WIDTH - item.rect.width)
        item.rect.y = random.randint(0, HEIGHT - item.rect.height - 100) 

        items.append(item)
    return items

def load_sprite_from_file(path):
    image = pygame.image.load(path)
    image_rect = image.get_rect()
    return image, image_rect

class Trainer:
    SPEED = 5

    def __init__(self, sprite_path):
        self.image, self.rect = load_sprite_from_file(sprite_path)
        self.target_pos = (self.rect.x, self.rect.y)
        self.captured_pokemon = deque(maxlen=6)

    def move(self):
        dx, dy = self.target_pos[0] - self.rect.x, self.target_pos[1] - self.rect.y
        # Direct Line Distance using pyGatherom Theorem
        dist = (dx**2 + dy**2)**0.5

        if dist != 0:
            dx /= dist
            dy /= dist

            new_x = self.rect.x + dx * Trainer.SPEED
            new_y = self.rect.y + dy * Trainer.SPEED

            # Restrict the movement to not go beyond the bottom bar area.
            if new_y + self.rect.height > HEIGHT - 100:
                new_y = HEIGHT - self.rect.height - 100

            self.rect.x = new_x
            self.rect.y = new_y
            if abs(self.rect.x - self.target_pos[0]) < Trainer.SPEED and abs(self.rect.y - self.target_pos[1]) < Trainer.SPEED:
                self.rect.x, self.rect.y = self.target_pos

    def get_captured_sprites(self):
        return [pokemon.sprite for pokemon in self.captured_pokemon]


    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Gotta Katchem All")

        self.background_items = create_random_background_items(10)
        self.trainer = Trainer('./sprites/ashe.png')
        self.pokeball_sprite = pygame.image.load('./sprites/pokeball.png')
        self.pokeball_rect = self.pokeball_sprite.get_rect()
        self.discovered_pokeballs = []
        pygame.font.init()
        self.font = pygame.font.SysFont('Roboto', 36)
        # self.message = None

    def draw_bottom_bar(self):
        bar_height = 100  # height of the bar at the bottom
        border_height = 5
        pygame.draw.rect(self.screen, DARK_RED, (0, HEIGHT - bar_height, WIDTH, bar_height))
        pygame.draw.rect(self.screen, DARK_YELLOW, (0, HEIGHT - bar_height, WIDTH, border_height))

        captured_sprites = self.trainer.get_captured_sprites()
        sprite_x_position = 10  # Start position
        for sprite in captured_sprites:
            self.screen.blit(sprite, (sprite_x_position, HEIGHT - bar_height + (bar_height - sprite.get_height()) // 2))
            sprite_x_position += sprite.get_width() + 10  # Adjust x position for the next sprite


    def show_captured_message(self,pokemon_name):
        waiting_for_input = True
        message=f"You caught {pokemon_name.title()}!"
        sub_message=f"Press ENTER to continue."
        while waiting_for_input:
            self.screen.fill(TAN)  

            # Render main message
            main_font = pygame.font.Font(None, 50)
            main_label = main_font.render(message, True, (0, 0, 0))
            main_label_rect = main_label.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
            
            # Render sub message (smaller font and placed below the main message)
            sub_font = pygame.font.Font(None, 30)
            sub_label = sub_font.render(sub_message, True, (0, 0, 0))
            sub_label_rect = sub_label.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))

            # Draw to screen
            self.screen.blit(main_label, main_label_rect.topleft)
            self.screen.blit(sub_label, sub_label_rect.topleft)

            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == KEYDOWN:
                    if event.key == K_RETURN:  # Enter key
                        waiting_for_input = False
                        return True

    def handle_events(self):
        # Control Movement with Mouse
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.trainer.target_pos = pygame.mouse.get_pos()
        return True

    def run(self):
        # Main loop following the update-draw paradigm
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            pygame.time.Clock().tick(60)
        pygame.quit()

    def update(self):
        # Make changes to object positions before redrawing screen
        self.trainer.move()

        for item in self.background_items:
            collision_rect = item.rect.inflate(20, 20)
            if self.trainer.rect.colliderect(collision_rect) and item.has_pokeball() and item.pokeball.is_pokeball:
                if item.rect.right + self.pokeball_rect.width <= WIDTH:
                    self.pokeball_rect.topleft = (item.rect.right, item.rect.y)
                else:
                    self.pokeball_rect.topright = (item.rect.left, item.rect.y)

                self.discovered_pokeballs.append((item.pokeball, self.pokeball_rect.topleft))

        for item, position in self.discovered_pokeballs:
            if item.is_pokeball and self.trainer.rect.colliderect(pygame.Rect(position, self.pokeball_rect.size)):
                item.is_pokeball = False
                self.discovered_pokeballs.remove((item, position))
                self.trainer.captured_pokemon.append(item.pokemon)
                self.show_captured_message(item.pokemon.name)


    def draw(self):
        # Draw/redraw all the elements on the screen after updating thier information
        self.screen.fill(GREEN)
        self.draw_bottom_bar()

        for item in self.background_items:
            item.draw(self.screen)
        self.trainer.draw(self.screen)

        for item, position in self.discovered_pokeballs:
            if item.is_pokeball:
                self.screen.blit(self.pokeball_sprite, position)


def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
