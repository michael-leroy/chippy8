import time
import tkinter as tk
from tkinter import filedialog

import sdl2
import sdl2.ext

import chip8_hw

# Size of the CHIP-8 display
CHIP8_WIDTH = 64
CHIP8_HEIGHT = 32

# Each CHIP-8 pixel will be drawn as a square of this size
SCALE = 10

WINDOW_WIDTH = CHIP8_WIDTH * SCALE
WINDOW_HEIGHT = CHIP8_HEIGHT * SCALE


def select_rom():
    """Open a file dialog and return the selected ROM path."""
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title="Select CHIP-8 ROM")
    root.destroy()
    return path


def draw_screen(renderer, chip8):
    """Render the current CHIP-8 framebuffer."""
    sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
    sdl2.SDL_RenderClear(renderer)

    for y in range(CHIP8_HEIGHT):
        for x in range(CHIP8_WIDTH):
            pixel = chip8.gfx[y * CHIP8_WIDTH + x]
            if pixel:
                sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)
            else:
                sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
            rect = sdl2.SDL_Rect(x * SCALE, y * SCALE, SCALE, SCALE)
            sdl2.SDL_RenderFillRect(renderer, rect)
    sdl2.SDL_RenderPresent(renderer)


def main():
    rom_path = select_rom()
    if not rom_path:
        print("No ROM selected. Exiting.")
        return

    chip8 = chip8_hw.ChipEightCpu()
    chip8.load_rom(rom_path)

    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
    window = sdl2.SDL_CreateWindow(
        b"Chippy8",
        sdl2.SDL_WINDOWPOS_CENTERED,
        sdl2.SDL_WINDOWPOS_CENTERED,
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        0,
    )
    renderer = sdl2.SDL_CreateRenderer(window, -1, 0)

    running = True
    last_cycle = time.time()
    while running:
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                running = False

        now = time.time()
        if now - last_cycle >= 1 / 500.0:
            chip8.emulate_cycle()
            last_cycle = now

        if chip8.update_screen:
            draw_screen(renderer, chip8)
            chip8.update_screen = False

        sdl2.SDL_Delay(1)

    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()


if __name__ == "__main__":
    main()
