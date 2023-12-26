import pygame as pg
import sys
from screen import *
from ship import *
import os
import random
WIDTH, HEIGHT = 1600, 900
MAIN_DIR = os.path.split(os.path.abspath(__file__))[0]

idle_image_paths = {
    1: 'Idle1.png',  # The path to the idle image for ship1
    2: 'Idle2.png'   # The path to the idle image for ship2
}
move_image_paths = {
    1: 'Move1.png',  # The path to the move image for ship1
    2: 'Move2.png'   # The path to the move image for ship2
}


def restrict_ship_movement(ship, ship_num):
    if ship_num == 1:
        # Bounds for ship1: (0, 0) to (1600, 400)
        min_x, min_y = 0, 0
        max_x, max_y = WIDTH, 400
    elif ship_num == 2:
        # Bounds for ship2: (0, 500) to (1600, 900)
        min_x, min_y = 0, 500
        max_x, max_y = WIDTH, HEIGHT

    # Correct the ship's position if it's outside the bounds
    if ship.rect.left < min_x:
        ship.rect.left = min_x
    if ship.rect.right > max_x:
        ship.rect.right = max_x
    if ship.rect.top < min_y:
        ship.rect.top = min_y
    if ship.rect.bottom > max_y:
        ship.rect.bottom = max_y


class Explosion(pg.sprite.Sprite):
    def __init__(self, center, size=(100, 100)):
        super().__init__()
        self.images = []
        self.load_images()
        self.current_frame = 0
        self.image = self.images[self.current_frame]
        self.rect = self.image.get_rect(center=center)
        self.frame_count = 0
        self.animation_speed = 1
        # Total frames for the explosion animation
        self.total_frames = 10 * 5  # Number of images times desired frames per image

    def load_images(self):
        for i in range(1, 11):  # Assuming you have 10 images for the explosion
            img = pg.image.load(
                f'{MAIN_DIR}/fig/Explosion_{i}.png').convert_alpha()
            img = pg.transform.scale(img, (100, 100))  # Scale to desired size
            self.images.append(img)

    def update(self):
        if self.frame_count < self.total_frames or self.current_frame < len(self.images) - 1:
            self.current_frame = (self.frame_count // 5) % len(self.images)
            self.image = self.images[int(self.current_frame)]
            self.frame_count += 1
        else:
            self.kill()  # Kill the sprite after the animation


class Blink(pg.sprite.Sprite):
    def __init__(self, ship: Ship, image_path, frame_count):
        super().__init__()
        self.ship = ship
        self.spritesheet = pg.image.load(image_path).convert_alpha()
        self.frame_count = frame_count
        self.frames = self.load_frames(self.frame_count)
        self.current_frame = 0
        self.animation_speed = 1
        self.active = False  # Indicates if the blink is active

    def animate(self):
        if self.active:
            self.current_frame += self.animation_speed
            if self.current_frame >= len(self.frames):
                self.current_frame = 0
            self.image = self.frames[int(self.current_frame)]
            self.rect = self.image.get_rect(center=self.ship.rect.center)

    def start_blink(self, direction):
        self.active = True
        self.ship.blinking = True  # Tell the ship it's blinking
        self.ship.blink_direction = direction
        self.current_frame = 0  # Reset animation frame

        # Flip the animation frames if the blink direction is to the left
        self.frames = [pg.transform.flip(
            frame, True, False) if direction[0] < 0 else frame for frame in self.original_frames]

    def stop_blink(self):
        self.active = False
        self.ship.blinking = False  # Tell the ship it's done blinking

    def load_frames(self, frame_count):
        # Split the spritesheet into frames and resize if new_size is provided.
        frames = []
        frame_width = self.spritesheet.get_width() // frame_count
        frame_height = self.spritesheet.get_height()
        for i in range(frame_count):
            frame = self.spritesheet.subsurface(
                (i * frame_width, 0, frame_width, frame_height))
            frame = pg.transform.rotozoom(frame, 225, 1.0)
            frames.append(frame)
        # Store the original frames for flipping
        self.original_frames = list(frames)
        return frames

    def update(self, screen: pg.Surface):
        self.animate()
        if self.active:
            # Position the animation on the edge of the ship's rect based on direction
            if self.ship.blink_direction[0] > 0:  # If moving left
                self.rect.right = self.ship.rect.left
            else:  # If moving right
                self.rect.left = self.ship.rect.right
            screen.blit(self.image, self.rect)


class Bird(pg.sprite.Sprite):
    def __init__(self, image_path, xy, frame_count, speed):
        super().__init__()
        self.spritesheet = pg.image.load(
            image_path).convert_alpha()  # ファイル読み込み
        self.frame_count = frame_count
        self.frames = self.load_frames(self.frame_count)
        self.current_frame = 0
        self.animation_speed = 0.2
        # 最初のフレームから
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(center=xy)
        self.speed = speed

    def load_frames(self, frame_count):
        # spritesheetからフレームを取得
        frames = []
        frame_width = self.spritesheet.get_width() // frame_count
        frame_height = self.spritesheet.get_height()

        for i in range(frame_count):
            frame = self.spritesheet.subsurface(
                (i * frame_width, 0, frame_width, frame_height))
            frames.append(frame)

        return frames

    def animate(self):
        # Sprite動かし
        self.current_frame += self.animation_speed
        if self.current_frame >= len(self.frames):
            self.current_frame = 0

        self.image = self.frames[int(self.current_frame)]

    def update(self):
        # アップデート
        self.animate()  # sprite動かし
        self.rect.x += self.speed[0]
        #self.rect.y += self.speed[1]

        if self.rect.right < 0:
            self.rect.left = WIDTH
        if self.rect.left > WIDTH:
            self.rect.right = 0
        if self.rect.bottom < 0:
            self.rect.top = HEIGHT
        if self.rect.top > HEIGHT:
            self.rect.bottom = 0


class Ship(pg.sprite.Sprite):
    def __init__(self, num: int, xy: tuple[int, int], idle_frames, move_frames, ship_num, new_size):
        super().__init__()
        self.idle_images = self.load_images(
            f"{MAIN_DIR}/fig/Idle{num}.png", idle_frames, new_size)
        self.move_images = self.load_images(
            f"{MAIN_DIR}/fig/Move{num}.png", move_frames, new_size)
        self.images = self.idle_images  # Start with idle images
        self.current_frame = 0
        self.animation_speed = 0.2
        self.image = self.images[self.current_frame]
        self.rect = self.image.get_rect(center=xy)
        self.speed = 10
        self.moving = False  # Indicates whether the ship is moving
        self.moving_left = False  # Indicates whether the ship is moving to the right

        self.blinking = False
        self.blink_distance = 500  # Updated blink distance
        self.blink_direction = (1, 0)  # Default blink direction to the right

        self.last_direction = (+1, 0)

        self.blink_speed = 20  # How fast the ship blinks per frame

        self.ship_num = ship_num

    def load_images(self, image_path, frame_count, new_size=None):
        images = []
        spritesheet = pg.image.load(image_path).convert_alpha()
        frame_width = spritesheet.get_width() // frame_count
        frame_height = spritesheet.get_height()
        for i in range(frame_count):
            frame = spritesheet.subsurface(
                (i * frame_width, 0, frame_width, frame_height))
            if new_size:
                frame = pg.transform.scale(frame, new_size)
            images.append(frame)
        return images

    def animate(self):
        self.current_frame += self.animation_speed
        if self.current_frame >= len(self.images):
            self.current_frame = 0
        self.image = self.images[int(self.current_frame)]
        if self.moving and self.moving_left:
            self.image = pg.transform.flip(self.image, True, False)

    def update(self, key_lst: list[bool], ctrl_keys: dict, screen: pg.Surface):
        self.moving = False  # Reset moving state
        sum_mv = [0, 0]
        if not self.blinking:
            for k, mv in ctrl_keys.items():
                if key_lst[k]:
                    self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                    sum_mv[0] += mv[0]
                    sum_mv[1] += mv[1]
                    self.moving = True
                    self.moving_left = mv[0] < 0
                if sum_mv != [0, 0]:
                    # Update the last direction when moving
                    self.last_direction = (sum_mv[0], sum_mv[1])
        else:
            # Blinking movement code
            self.rect.x += self.blink_direction[0] * self.blink_speed
            self.blink_distance -= self.blink_speed
            if self.blink_distance <= 0:
                self.blinking = False
                self.blink_distance = 500  # Reset blink distance
                self.blink_direction = (1, 0)  # Reset blink direction
                # Trigger the stop_blink method of the Blink instance
                self.blink_instance.stop_blink()

        if self.moving:
            self.images = self.move_images
        else:
            self.images = self.idle_images
        restrict_ship_movement(self, self.ship_num)
        self.animate()
        screen.blit(self.image, self.rect)


class Shield(pg.sprite.Sprite):
    # シールドのクラスを作成
    def __init__(self, ship: Ship, radius: int = 75, color=(0, 0, 255), width=2):
        super().__init__()
        # ship自体、半径、色、幅を設定
        self.ship = ship
        self.radius = radius
        self.color = color
        self.width = width

    def update(self, screen: pg.Surface):
        # 円を描く
        pg.draw.circle(screen, self.color, self.ship.rect.center,
                       self.radius, self.width)


class AnimatedShield(pg.sprite.Sprite):
    def __init__(self, ship: Ship, image_path, frame_count, new_size=None):
        super().__init__()
        self.ship = ship
        self.spritesheet = pg.image.load(image_path).convert_alpha()
        self.frame_count = frame_count
        self.frames = self.load_frames(self.frame_count, new_size)
        self.current_frame = 0
        self.animation_speed = 0.2
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(center=self.ship.rect.center)

    def load_frames(self, frame_count, new_size):
        frames = []
        frame_width = self.spritesheet.get_width() // frame_count
        frame_height = self.spritesheet.get_height()
        for i in range(frame_count):
            frame = self.spritesheet.subsurface(
                (i * frame_width, 0, frame_width, frame_height))
            if new_size:
                frame = pg.transform.scale(frame, new_size)
            frames.append(frame)
        return frames

    def animate(self):
        self.current_frame += self.animation_speed
        if self.current_frame >= len(self.frames):
            self.current_frame = 0
        self.image = self.frames[int(self.current_frame)]
        self.rect = self.image.get_rect(center=self.ship.rect.center)

    def update(self):
        self.animate()
        self.rect = self.image.get_rect(center=self.ship.rect.center)


def main():

    # Walk.pngを読み込み
    bird_image_path = os.path.join(MAIN_DIR, 'fig/Walk.png')
    birds = pg.sprite.Group()
    screen = pg.display.set_mode((WIDTH, HEIGHT))

    bg_img_original = pg.image.load(f"{MAIN_DIR}/imgs/bg_ocean.png")
    bg_img = pg.transform.scale(bg_img_original, (WIDTH, HEIGHT))
    bg_img_flipped = pg.transform.flip(bg_img, True, False)
    bg_x = 0
    bg_x_flipped = bg_img.get_width()
    bg_tile_width = bg_img.get_width()
    bg_tile_height = bg_img.get_height()

    # Calculate how many tiles are needed to cover the screen
    tiles_x = -(-WIDTH // bg_tile_width)  # Ceiling division
    tiles_y = -(-HEIGHT // bg_tile_height)  # Ceiling division
    new_ship_size = (40, 40)
    ship1_frame_count = 8  # Update this if your sprite sheet has a different number of frames
    ship2_frame_count = 4  # Update this if your sprite sheet has a different number of frames
    explosions = pg.sprite.Group()
    ship1_frame_count_idle = 10  # Replace with the number of idle frames for ship1
    ship1_frame_count_move = 10  # Replace with the number of move frames for ship1
    ship1 = Ship(1, (100, 200), ship1_frame_count_idle,
                 ship1_frame_count_move, ship_num=1, new_size=(250, 250))

    ship2_frame_count_idle = 10  # Replace with the number of idle frames for ship2
    ship2_frame_count_move = 10  # Replace with the number of move frames for ship2
    ship2 = Ship(2, (1000, 500), ship2_frame_count_idle,
                 ship2_frame_count_move, ship_num=2, new_size=(250, 250))

    ships = pg.sprite.Group(ship1, ship2)

    ship1_controls = {
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (1, 0),
    }
    ship2_controls = {
        pg.K_w: (0, -1),
        pg.K_s: (0, +1),
        pg.K_a: (-1, 0),
        pg.K_d: (1, 0),
    }
    for _ in range(5):  # 鳥数が５に
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        # スピードをランダムに
        speed_x = random.choice([1, 2, 3])
        speed_y = random.choice([-3, -2, -1, 1, 2, 3])
        bird = Bird(bird_image_path, (x, y), frame_count=6,
                    speed=(speed_x, speed_y))
        birds.add(bird)

    shield1_sprite_path = os.path.join(MAIN_DIR, 'fig/shield1.png')
    shield1_frame_count = 8  # The number of frames in the shield1 sprite sheet
    shield2_sprite_path = os.path.join(MAIN_DIR, 'fig/shield2.png')
    shield2_frame_count = 7  # The number of frames in the shield2 sprite sheet

    # Example size, adjust this to your preference
    new_shield_size = (200, 200)

    ship1_shield = AnimatedShield(
        ship1, shield1_sprite_path, shield1_frame_count, new_size=(300, 300))
    ship2_shield = AnimatedShield(
        ship2, shield2_sprite_path, shield2_frame_count, new_size=(280, 280))
    # Update with your blink sprite sheet file name
    blink_image_path = os.path.join(MAIN_DIR, 'fig/blink.png')
    blink_frame_count = 8  # Update with the correct number of frames

    ship1_blink = Blink(ship1, blink_image_path, blink_frame_count)
    ship2_blink = Blink(ship2, blink_image_path, blink_frame_count)
    ship1.blink_instance = ship1_blink
    ship2.blink_instance = ship2_blink

    explosion1 = Explosion(center=ship1.rect.center)
    explosion2 = Explosion(center=ship2.rect.center)

    tmr = 0
    clock = pg.time.Clock()

    while True:
        bg_x -= 1
        bg_x_flipped -= 1
        ships.draw(screen)
        # イベントハンドラー
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
         # 背景をブリット

        for y in range(tiles_y):
            for x in range(tiles_x):
                screen.blit(bg_img, (x * bg_tile_width, y * bg_tile_height))

        if bg_x < -bg_img.get_width():
            bg_x = bg_img.get_width()
        if bg_x_flipped < -bg_img.get_width():
            bg_x_flipped = bg_img.get_width()
        screen.blit(bg_img, (bg_x, 0))
        screen.blit(bg_img_flipped, (bg_x_flipped, 0))

        if key_lst[pg.K_LSHIFT]:
            direction = (-1, 0) if key_lst[pg.K_a] else (1, 0)
            if not ship2.blinking:
                ship2_blink.start_blink(direction)

        if key_lst[pg.K_RSHIFT]:
            direction = (-1, 0) if key_lst[pg.K_LEFT] else (1, 0)
            if not ship1.blinking:
                ship1_blink.start_blink(direction)

        # Inside the game loop
        collision = pg.sprite.collide_rect(ship1, ship2)
        for explosion in explosions:
            explosion.update()
            screen.blit(explosion.image, explosion.rect)

        if collision:
            # Add the explosions to the explosions group
            explosions.add(explosion1, explosion2)
            explosions.update()

            explosion1.rect.center = ship1.rect.center
            explosion2.rect.center = ship2.rect.center
            # Kill both ships to remove them from the game
            ship1.kill()
            ship2.kill()

        explosions.update()
        ship1_blink.update(screen)
        ship2_blink.update(screen)
        birds.update()  # 鳥をアップデート
        birds.draw(screen)
        if ship1.alive():
            ship1.update(key_lst, ship1_controls, screen)
        if ship2.alive():
            ship2.update(key_lst, ship2_controls, screen)
        for ship in ships:
            if ship.alive():
                screen.blit(ship.image, ship.rect)
            else:
                ship.kill()
        if ship1.alive():
            if key_lst[pg.K_RETURN]:
                ship1_shield.update()
                screen.blit(ship1_shield.image, ship1_shield.rect)

        if ship2.alive():
            if key_lst[pg.K_TAB]:
                ship2_shield.update()
                screen.blit(ship2_shield.image, ship2_shield.rect)
        explosions.draw(screen)

        pg.display.update()
        tmr += 1
        clock.tick(50)
#


if __name__ == "__main__":

    pg.init()
    main()
    pg.quit()
    sys.exit()
