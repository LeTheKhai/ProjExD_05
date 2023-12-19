import pygame as pg
import sys
from screen import *
from ship import *
import os
WIDTH, HEIGHT = 1400, 600
MAIN_DIR = os.path.split(os.path.abspath(__file__))[0]


def main():
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"{MAIN_DIR}/imgs/bg_ocean.png")
    # クロックの作成

    ship1 = Ship(2, (100, 200), pg.K_DOWN, 7)
    ship2 = Ship(2, (1000, 500), pg.K_s, 7)
    ship1_controls = {
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (1, 0),
    }
    ship2_controls = {
        pg.K_a: (-1, 0),
        pg.K_d: (1, 0),
    }

    tmr = 0
    clock = pg.time.Clock()

    while True:
        # イベントハンドラー
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return

        # 背景をブリット
        screen.blit(bg_img, [0, 0])

        ship1.update(key_lst, ship1_controls, screen)
        ship2.update(key_lst, ship2_controls, screen)

        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":

    pg.init()
    main()
    pg.quit()
    sys.exit()
