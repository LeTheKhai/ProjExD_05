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
    # 異なる船の境界を定義する辞書
    ship_bounds = {
        1: (0, 0, WIDTH, 400),   # 船1の境界：(左、上、右、下)
        2: (0, 500, WIDTH, HEIGHT)  # 船2の境界：(左、上、右、下)
    }

    # ship_numに基づいて船の境界を取得；見つからない場合はデフォルト値を使用
    min_x, min_y, max_x, max_y = ship_bounds.get(ship_num, (0, 0, WIDTH, HEIGHT))

    # 船の左、上、右、下の位置が境界内にあることを確認
    ship.rect.left = max(min_x, min(ship.rect.left, max_x))
    ship.rect.top = max(min_y, min(ship.rect.top, max_y))
    ship.rect.right = min(max_x, max(ship.rect.right, min_x))
    ship.rect.bottom = min(max_y, max(ship.rect.bottom, min_y))



class Explosion(pg.sprite.Sprite):
    def __init__(self, center, size=(100, 100)):
        super().__init__()

        # 爆発アニメーションの画像を格納するリスト
        self.images = []

        # 爆発アニメーションの画像を読み込み、アニメーションパラメータを初期化
        self.load_images()
        self.current_frame = 0
        self.image = self.images[self.current_frame]
        self.rect = self.image.get_rect(center=center)
        self.frame_count = 0
        self.animation_speed = 1

        # 爆発アニメーションの総フレーム数
        self.total_frames = 10 * 5  # 画像の数 × 画像ごとの希望フレーム数

    def load_images(self):
        # ファイルから爆発画像を読み込み、指定のサイズにスケーリング
        for i in range(1, 11):  # 10枚の爆発用画像があると仮定
            img = pg.image.load(
                f'{MAIN_DIR}/fig/Explosion_{i}.png').convert_alpha()
            img = pg.transform.scale(img, (100, 100))  # 希望のサイズにスケーリング
            self.images.append(img)

    def update(self):
        # 爆発アニメーションのフレームを更新
        if self.frame_count < self.total_frames or self.current_frame < len(self.images) - 1:
            self.current_frame = (self.frame_count // 5) % len(self.images)
            self.image = self.images[int(self.current_frame)]
            self.frame_count += 1
        else:
            # アニメーション後にスプライトを削除するために kill メソッドを呼び出す
            self.kill()


class Blink(pg.sprite.Sprite):
    def __init__(self, ship: Ship, image_path, frame_count):
        super().__init__()
        self.ship = ship  # 関連する船への参照
        self.spritesheet = pg.image.load(image_path).convert_alpha()
        self.frame_count = frame_count
        self.frames = self.load_frames(self.frame_count)
        self.current_frame = 0
        self.animation_speed = 1
        self.active = False  # 点滅アニメーションがアクティブかどうかを制御するフラグ

    def animate(self):
        # アクティブな場合、スプライトをアニメーション化
        if self.active:
            self.current_frame += self.animation_speed
            if self.current_frame >= len(self.frames):
                self.current_frame = 0
            self.image = self.frames[int(self.current_frame)]
            self.rect = self.image.get_rect(center=self.ship.rect.center)

    def start_blink(self, direction):
        # 点滅アニメーションを開始
        self.active = True
        self.ship.blinking = True  # 船の点滅フラグを設定
        self.ship.blink_direction = direction  # 点滅の方向を設定
        self.current_frame = 0  # 現在のフレームをリセット
        # 点滅の方向が左の場合、フレームを水平に反転
        self.frames = [pg.transform.flip(
            frame, True, False) if direction[0] < 0 else frame for frame in self.original_frames]

    def stop_blink(self):
        # 点滅アニメーションを停止
        self.active = False
        self.ship.blinking = False  # 船の点滅フラグをリセット

    def load_frames(self, frame_count):
        # アニメーション用のフレームを読み込み、変換
        frames = []
        frame_width = self.spritesheet.get_width() // frame_count
        frame_height = self.spritesheet.get_height()
        for i in range(frame_count):
            frame = self.spritesheet.subsurface(
                (i * frame_width, 0, frame_width, frame_height))
            frame = pg.transform.rotozoom(frame, 225, 1.0)
            frames.append(frame)

        self.original_frames = list(frames)
        return frames

    def update(self, screen: pg.Surface):
        self.animate()
        if self.active:
            # 点滅の方向に基づいてスプライトを配置
            if self.ship.blink_direction[0] > 0:
                self.rect.right = self.ship.rect.left
            else:
                self.rect.left = self.ship.rect.right
            screen.blit(self.image, self.rect)


class Bird(pg.sprite.Sprite):
    def __init__(self, image_path, xy, frame_count, speed):
        super().__init__()

        # スプライトシートを読み込む
        self.spritesheet = pg.image.load(
            image_path).convert_alpha()  

        # アニメーション用のフレーム数
        self.frame_count = frame_count

        # フレームを読み込む
        self.frames = self.load_frames(self.frame_count)

        # 現在のフレームとアニメーション速度を初期化
        self.current_frame = 0
        self.animation_speed = 0.2

        # イメージを設定し、矩形をセンターに配置
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(center=xy)

        # 速度を設定
        self.speed = speed

    def load_frames(self, frame_count):
        frames = []
        frame_width = self.spritesheet.get_width() // frame_count
        frame_height = self.spritesheet.get_height()

        # フレームをスプライトシートから読み込む
        for i in range(frame_count):
            frame = self.spritesheet.subsurface(
                (i * frame_width, 0, frame_width, frame_height))
            frames.append(frame)

        return frames

    def animate(self):
        # アニメーションを進める
        self.current_frame += self.animation_speed
        if self.current_frame >= len(self.frames):
            self.current_frame = 0

        self.image = self.frames[int(self.current_frame)]

    def update(self):
        # アップデート関数
        self.animate()  # アニメーションを実行
        self.rect.x += self.speed[0]

        # 画面外に出た場合、反対側に移動
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

        # アイドル時の画像と移動中の画像を読み込む
        self.idle_images = self.load_images(
            f"{MAIN_DIR}/fig/Idle{num}.png", idle_frames, new_size)
        self.move_images = self.load_images(
            f"{MAIN_DIR}/fig/Move{num}.png", move_frames, new_size)

        # 現在の画像セットをアイドル画像に初期化
        self.images = self.idle_images

        # アニメーション用の変数を初期化
        self.current_frame = 0
        self.animation_speed = 0.2
        self.image = self.images[self.current_frame]
        self.rect = self.image.get_rect(center=xy)

        # 移動速度を設定
        self.speed = 10

        # 移動中と左に移動中のフラグを初期化
        self.moving = False
        self.moving_left = False

        # 点滅用の変数を初期化
        self.blinking = False
        self.blink_distance = 500
        self.blink_direction = (1, 0)

        # 最後の方向を記録
        self.last_direction = (+1, 0)

        # 点滅速度を設定
        self.blink_speed = 20

        # 船の番号を保持
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
        self.moving = False
        sum_mv = [0, 0]

        # 点滅中でない場合、キー入力に応じて船を移動
        if not self.blinking:
            for k, mv in ctrl_keys.items():
                if key_lst[k]:
                    self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                    sum_mv[0] += mv[0]
                    sum_mv[1] += mv[1]
                    self.moving = True
                    self.moving_left = mv[0] < 0
                if sum_mv != [0, 0]:
                    self.last_direction = (sum_mv[0], sum_mv[1])

        # 点滅中の場合、指定された方向に移動
        else:
            self.rect.x += self.blink_direction[0] * self.blink_speed
            self.blink_distance -= self.blink_speed
            if self.blink_distance <= 0:
                self.blinking = False
                self.blink_distance = 500
                self.blink_direction = (1, 0)

                # 点滅アニメーションを停止
                self.blink_instance.stop_blink()

        # 移動中の場合、移動中の画像セットを使用
        if self.moving:
            self.images = self.move_images
        else:
            self.images = self.idle_images

        # 船の移動を制限
        restrict_ship_movement(self, self.ship_num)

        # アニメーションを実行して船を画面に描画
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

        # 関連する船への参照を保持
        self.ship = ship

        # スプライトシートを読み込む
        self.spritesheet = pg.image.load(image_path).convert_alpha()

        # アニメーション用のフレーム数
        self.frame_count = frame_count

        # フレームを読み込む
        self.frames = self.load_frames(self.frame_count, new_size)

        # 現在のフレームとアニメーション速度を初期化
        self.current_frame = 0
        self.animation_speed = 0.2

        # イメージを設定し、矩形を船の中心に配置
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

    # 背景画像の読み込みと設定
    bg_img_original = pg.image.load(f"{MAIN_DIR}/imgs/bg_ocean.png")
    bg_img = pg.transform.scale(bg_img_original, (WIDTH, HEIGHT))
    bg_img_flipped = pg.transform.flip(bg_img, True, False)
    bg_x = 0
    bg_x_flipped = bg_img.get_width()
    bg_tile_width = bg_img.get_width()
    bg_tile_height = bg_img.get_height()

    # 画面を覆うために必要なタイルの数を計算
    tiles_x = -(-WIDTH // bg_tile_width)  # 切り上げの除算
    tiles_y = -(-HEIGHT // bg_tile_height)  # 切り上げの除算

    new_ship_size = (40, 40)
    ship1_frame_count = 8  # スプライトシートのフレーム数に合わせて調整
    ship2_frame_count = 4  # スプライトシートのフレーム数に合わせて調整

    # 爆発アニメーション用のスプライトグループ
    explosions = pg.sprite.Group()

    # Ship1のアイドルおよび移動のフレーム数
    ship1_frame_count_idle = 10  # Ship1のアイドルのフレーム数に合わせて調整
    ship1_frame_count_move = 10  # Ship1の移動のフレーム数に合わせて調整

    # Ship1の初期化
    ship1 = Ship(1, (100, 200), ship1_frame_count_idle,
                 ship1_frame_count_move, ship_num=1, new_size=(250, 250))

    # Ship2のアイドルおよび移動のフレーム数
    ship2_frame_count_idle = 10  # Ship2のアイドルのフレーム数に合わせて調整
    ship2_frame_count_move = 10  # Ship2の移動のフレーム数に合わせて調整

    # Ship2の初期化
    ship2 = Ship(2, (1000, 500), ship2_frame_count_idle,
                 ship2_frame_count_move, ship_num=2, new_size=(250, 250))

    # 船のスプライトグループ
    ships = pg.sprite.Group(ship1, ship2)

    # Ship1およびShip2のコントロール設定
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

    # 5羽の鳥を生成
    for _ in range(5):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        # スピードをランダムに設定
        speed_x = random.choice([1, 2, 3])
        speed_y = random.choice([-3, -2, -1, 1, 2, 3])
        bird = Bird(bird_image_path, (x, y), frame_count=6,
                    speed=(speed_x, speed_y))
        birds.add(bird)

    # Shield1およびShield2のスプライトパス
    shield1_sprite_path = os.path.join(MAIN_DIR, 'fig/shield1.png')
    shield2_sprite_path = os.path.join(MAIN_DIR, 'fig/shield2.png')

    # Shield1およびShield2のフレーム数
    shield1_frame_count = 8  # Shield1のスプライトシートのフレーム数に合わせて調整
    shield2_frame_count = 7  # Shield2のスプライトシートのフレーム数に合わせて調整

    # シールドの新しいサイズ（例）
    new_shield_size = (200, 200)

    # Ship1およびShip2のシールドの初期化
    ship1_shield = AnimatedShield(
        ship1, shield1_sprite_path, shield1_frame_count, new_size=(300, 300))
    ship2_shield = AnimatedShield(
        ship2, shield2_sprite_path, shield2_frame_count, new_size=(280, 280))

    # 点滅アニメーション用のスプライトパス
    blink_image_path = os.path.join(MAIN_DIR, 'fig/blink.png')

    # 点滅アニメーションのフレーム数
    blink_frame_count = 8  # フレーム数に合わせて調整

    # Ship1およびShip2の点滅アニメーションの初期化
    ship1_blink = Blink(ship1, blink_image_path, blink_frame_count)
    ship2_blink = Blink(ship2, blink_image_path, blink_frame_count)
    ship1.blink_instance = ship1_blink
    ship2.blink_instance = ship2_blink

    # 爆発エフェクトの初期化
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

        # 背景を描画
        for y in range(tiles_y):
            for x in range(tiles_x):
                screen.blit(bg_img, (x * bg_tile_width, y * bg_tile_height))

        if bg_x < -bg_img.get_width():
            bg_x = bg_img.get_width()
        if bg_x_flipped < -bg_img.get_width():
            bg_x_flipped = bg_img.get_width()
        screen.blit(bg_img, (bg_x, 0))
        screen.blit(bg_img_flipped, (bg_x_flipped, 0))

        # Shiftキーが押された場合、Ship2の点滅アニメーションを開始
        if key_lst[pg.K_LSHIFT]:
            direction = (-1, 0) if key_lst[pg.K_a] else (1, 0)
            if not ship2.blinking:
                ship2_blink.start_blink(direction)

        # Shiftキーが押された場合、Ship1の点滅アニメーションを開始
        if key_lst[pg.K_RSHIFT]:
            direction = (-1, 0) if key_lst[pg.K_LEFT] else (1, 0)
            if not ship1.blinking:
                ship1_blink.start_blink(direction)

        # 爆発の衝突検出
        collision = pg.sprite.collide_rect(ship1, ship2)

        # 爆発のアニメーションを更新し、画面に描画
        for explosion in explosions:
            explosion.update()
            screen.blit(explosion.image, explosion.rect)

        if collision:
            # 爆発エフェクトをスプライトグループに追加
            explosions.add(explosion1, explosion2)
            explosions.update()

            explosion1.rect.center = ship1.rect.center
            explosion2.rect.center = ship2.rect.center

            # 両方の船を削除してゲームから除外
            ship1.kill()
            ship2.kill()

        explosions.update()
        ship1_blink.update(screen)
        ship2_blink.update(screen)
        birds.update()  # 鳥をアップデート
        birds.draw(screen)

        # Ship1が生存している場合、アニメーションとコントロールを更新
        if ship1.alive():
            ship1.update(key_lst, ship1_controls, screen)

        # Ship2が生存している場合、アニメーションとコントロールを更新
        if ship2.alive():
            ship2.update(key_lst, ship2_controls, screen)

        for ship in ships:
            if ship.alive():
                screen.blit(ship.image, ship.rect)
            else:
                ship.kill()

        # Ship1が生存している場合、シールドを表示
        if ship1.alive():
            if key_lst[pg.K_RETURN]:
                ship1_shield.update()
                screen.blit(ship1_shield.image, ship1_shield.rect)

        # Ship2が生存している場合、シールドを表示
        if ship2.alive():
            if key_lst[pg.K_TAB]:
                ship2_shield.update()
                screen.blit(ship2_shield.image, ship2_shield.rect)

        explosions.draw(screen)

        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":

    pg.init()
    main()
    pg.quit()
    sys.exit()
