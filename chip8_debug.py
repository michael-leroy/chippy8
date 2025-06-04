import time
import tkinter as tk
from tkinter import filedialog
import math

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

# CPU execution speed in cycles per second
CPU_HZ = 700

# Mapping from keyboard keys to CHIP-8 keypad values
KEY_MAP = {
    sdl2.SDLK_1: 0x1,
    sdl2.SDLK_2: 0x2,
    sdl2.SDLK_3: 0x3,
    sdl2.SDLK_4: 0xC,
    sdl2.SDLK_q: 0x4,
    sdl2.SDLK_w: 0x5,
    sdl2.SDLK_e: 0x6,
    sdl2.SDLK_r: 0xD,
    sdl2.SDLK_a: 0x7,
    sdl2.SDLK_s: 0x8,
    sdl2.SDLK_d: 0x9,
    sdl2.SDLK_f: 0xE,
    sdl2.SDLK_z: 0xA,
    sdl2.SDLK_x: 0x0,
    sdl2.SDLK_c: 0xB,
    sdl2.SDLK_v: 0xF,
}


def beep():
    """Play a short beep using the best available method."""
    try:
        import winsound

        winsound.Beep(1000, 100)
    except Exception:
        # Fallback to console bell if platform support is missing
        print("\a", end="", flush=True)


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
    chip8.sound_callback = beep
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
    cycles = 0
    debug_root = None
    debug_label = None
    last_debug = time.time()

    def toggle_debug():
        nonlocal debug_root, debug_label
        if debug_root:
            debug_root.destroy()
            debug_root = None
            return

        debug_root = tk.Toplevel(control_root)
        debug_root.title("Debug")
        debug_label = tk.Label(debug_root, text="")
        debug_label.pack()
        def on_close():
            nonlocal debug_root
            debug_root.destroy()
            debug_root = None
        debug_root.protocol("WM_DELETE_WINDOW", on_close)

    control_root = tk.Tk()
    control_root.title("Chippy8")
    menubar = tk.Menu(control_root)
    settings_menu = tk.Menu(menubar, tearoff=0)
    settings_menu.add_command(label="Toggle Debug", command=toggle_debug)
    menubar.add_cascade(label="Settings", menu=settings_menu)
    control_root.config(menu=menubar)
    def on_control_close():
        nonlocal running
        running = False
    control_root.protocol("WM_DELETE_WINDOW", on_control_close)
    while running:
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    running = False
                elif event.key.keysym.sym == sdl2.SDLK_F1:
                    toggle_debug()
                key = KEY_MAP.get(event.key.keysym.sym)
                if key is not None:
                    chip8.key[key] = 1
            elif event.type == sdl2.SDL_KEYUP:
                key = KEY_MAP.get(event.key.keysym.sym)
                if key is not None:
                    chip8.key[key] = 0

        now = time.time()
        if now - last_cycle >= 1 / CPU_HZ:
            chip8.emulate_cycle()
            cycles += 1
            last_cycle = now

        if now - last_frame >= frame_delay or chip8.update_screen:
            draw_screen(renderer, chip8, window)
            chip8.update_screen = False
            last_frame = now

        if debug_root and now - last_debug >= 1:
            cps = cycles / (now - last_debug)
            regs = " ".join(
                f"V{idx:X}:{val:02X}" for idx, val in enumerate(chip8.V)
            )
            debug_label.config(
                text=(
                    f"PC: {chip8.pc:03X} I:{chip8.I:03X}\n"
                    f"DT:{chip8.delay_timer} ST:{chip8.sound_timer}\n"
                    f"{regs}\nCycles/s: {cps:.0f}"
                )
            )
            cycles = 0
            last_debug = now
            try:
                debug_root.update()
            except tk.TclError:
                debug_root = None

        try:
            control_root.update()
        except tk.TclError:
            running = False

        sdl2.SDL_Delay(1)

    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()


if __name__ == "__main__":
    main()
