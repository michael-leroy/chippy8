import time
import tkinter as tk
from tkinter import filedialog

import sdl2
import sdl2.ext
import ctypes

import chip8_hw

# Size of the CHIP-8 display
CHIP8_WIDTH = 64
CHIP8_HEIGHT = 32

# Initial window size (4:3 aspect ratio)
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480


def select_rom():
    """Open a file dialog and return the selected ROM path."""
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title="Select CHIP-8 ROM")
    root.destroy()
    return path


def draw_screen(renderer, chip8, window):
    """Render the current CHIP-8 framebuffer with window scaling."""
    win_w = ctypes.c_int()
    win_h = ctypes.c_int()
    sdl2.SDL_GetWindowSize(window, ctypes.byref(win_w), ctypes.byref(win_h))
    win_w = win_w.value
    win_h = win_h.value

    aspect = 4 / 3
    draw_w = win_w
    draw_h = int(draw_w / aspect)
    if draw_h > win_h:
        draw_h = win_h
        draw_w = int(draw_h * aspect)

    off_x = (win_w - draw_w) // 2
    off_y = (win_h - draw_h) // 2
    scale_x = draw_w / CHIP8_WIDTH
    scale_y = draw_h / CHIP8_HEIGHT
    px_w = max(1, int(scale_x))
    px_h = max(1, int(scale_y))

    sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
    sdl2.SDL_RenderClear(renderer)

    for y in range(CHIP8_HEIGHT):
        for x in range(CHIP8_WIDTH):
            pixel = chip8.gfx[y * CHIP8_WIDTH + x]
            if pixel:
                sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)
            else:
                sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
            rect = sdl2.SDL_Rect(
                int(off_x + x * scale_x),
                int(off_y + y * scale_y),
                px_w,
                px_h,
            )
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
        sdl2.SDL_WINDOW_RESIZABLE,
    )
    renderer = sdl2.SDL_CreateRenderer(
        window, -1, sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC
    )

    running = True
    last_cycle = time.time()
    last_frame = time.time()
    frame_delay = 1 / 60.0
    while running:
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                running = False

        now = time.time()
        if now - last_cycle >= 1 / 500.0:
            chip8.emulate_cycle()
            last_cycle = now

        if now - last_frame >= frame_delay or chip8.update_screen:
            draw_screen(renderer, chip8, window)
            chip8.update_screen = False
            last_frame = now

        sdl2.SDL_Delay(1)

    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()


if __name__ == "__main__":
    main()
