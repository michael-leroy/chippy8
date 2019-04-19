
import random
import time
import chip8_hw
import pprint

import pygame
import pygame.gfxdraw

def timed_loop():
    print('ran')
    time.sleep(random.randint(1, 10) / 1000)


if __name__ == '__main__':

    width = 64
    height = 32

    screen = pygame.display.set_mode((320,160))

    time_since_last_cycle = 0
    loop_count = 0

    chip8 = chip8_hw.ChipEightCpu()
    #chip8.load_rom('breakout.ch8')
    chip8.load_rom('maze_demo.ch8')

    # Simulate key press
    chip8.key = [1] * 16

    while loop_count < 10000:
        timer = time.time()
        if (timer - time_since_last_cycle) >= (2.0 / 1000.0):
            chip8.emulate_cycle()
            time_since_last_cycle = time.time()
            loop_count += 1
            print(chip8.pc)

            x_draw = 0
            col = 0

            for i in chip8.gfx:
                if i:
                    pygame.gfxdraw.pixel(screen, x_draw * i, col * i, (255, 255, 255, 255))
                else:
                    pygame.gfxdraw.pixel(screen, x_draw * i, col * i, (0, 0, 0, 255))

                x_draw += 1
                if x_draw >= 64:
                    col +=1
                    x_draw = 0
            pygame.display.update()

    raw_input("Hit enter to close.")


