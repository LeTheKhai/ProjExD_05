import pygame as pg
import sys
import os
MAIN_DIR = os.path.split(os.path.abspath(__file__))[0]


class Ship(pg.sprite.Sprite):
    """
    船作成
    """

    def __init__(self, num: int, xy: tuple[int, int], speed_up_key: int, max_speed: int = 20):
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(
            f"{MAIN_DIR}/fig/{num}.png"), 0, 1.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (-1, 0): img0,  # 左
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 1
        self.max_speed = max_speed
        self.speed_up_key = speed_up_key



    def update(self, key_lst: list[bool], ctrl_keys: dict, screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        current_speed = self.speed if not key_lst[self.speed_up_key] else self.max_speed
        for k, mv in ctrl_keys.items():
            if key_lst[k]:
                self.rect.move_ip(+current_speed * mv[0], +current_speed * mv[1])  # Use current_speed here
        screen.blit(self.image, self.rect)
