import time
import tkinter as tk
from tkinter import filedialog

import sdl2
import sdl2.ext
import ctypes

import chip8_hw

CHIP8_WIDTH = 64
CHIP8_HEIGHT = 32
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480


def select_rom():
    """Open a file dialog and return the selected ROM path."""
    return filedialog.askopenfilename(title="Select CHIP-8 ROM")


def create_menu(root, chip8_ref):
    debug_var = tk.BooleanVar(value=False)
    debug_win = tk.Toplevel(root)
    debug_win.title("Debug")
    debug_win.geometry("300x260")

    labels = {}
    row = 0
    labels["PC"] = tk.Label(debug_win, text="PC: 000")
    labels["PC"].grid(row=row, column=0, columnspan=2, sticky="w")
    row += 1
    labels["I"] = tk.Label(debug_win, text="I: 000")
    labels["I"].grid(row=row, column=0, columnspan=2, sticky="w")
    row += 1
    labels["DT"] = tk.Label(debug_win, text="DT: 00")
    labels["DT"].grid(row=row, column=0, columnspan=2, sticky="w")
    row += 1
    labels["ST"] = tk.Label(debug_win, text="ST: 00")
    labels["ST"].grid(row=row, column=0, columnspan=2, sticky="w")
    row += 1

    for i in range(16):
        tk.Label(debug_win, text=f"V{i:X}:").grid(row=row + i // 2, column=(i % 2) * 2, sticky="e")
        labels[f"V{i}"] = tk.Label(debug_win, text="00")
        labels[f"V{i}"].grid(row=row + i // 2, column=(i % 2) * 2 + 1, sticky="w")
    row += 8

    debug_win.withdraw()

    def update_debug(cpu):
        labels["PC"].config(text=f"PC: {cpu.pc:03X}")
        labels["I"].config(text=f"I: {cpu.I:03X}")
        labels["DT"].config(text=f"DT: {cpu.delay_timer:02X}")
        labels["ST"].config(text=f"ST: {cpu.sound_timer:02X}")
        for i in range(16):
            labels[f"V{i}"].config(text=f"{cpu.V[i]:02X}")

    def toggle_debug():
        chip8_ref[0].debug = debug_var.get()
        if chip8_ref[0].debug:
            debug_win.deiconify()
        else:
            debug_win.withdraw()

    def on_debug_close():
        debug_var.set(False)
        toggle_debug()

    debug_win.protocol("WM_DELETE_WINDOW", on_debug_close)

    menu_bar = tk.Menu(root)
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Load")
    file_menu.add_separator()
    file_menu.add_command(label="Exit")
    menu_bar.add_cascade(label="File", menu=file_menu)

    settings = tk.Menu(menu_bar, tearoff=0)
    settings.add_checkbutton(label="Debug", variable=debug_var, command=toggle_debug)
    menu_bar.add_cascade(label="Settings", menu=settings)
    root.config(menu=menu_bar)

    chip8_ref[0].debug_callback = update_debug

    return debug_win, update_debug, file_menu


def draw_screen(renderer, chip8, window):
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
    root = tk.Tk()
    root.title("Chippy8")

    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)

    frame = tk.Frame(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
    frame.pack(fill="both", expand=True)
    root.update_idletasks()
    root.update()

    window = sdl2.SDL_CreateWindowFrom(ctypes.c_void_p(frame.winfo_id()))
    renderer = sdl2.SDL_CreateRenderer(
        window, -1, sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC
    )

    chip8_ref = [chip8_hw.ChipEightCpu()]
    rom_loaded = False

    def on_frame_resize(event):
        sdl2.SDL_SetWindowSize(window, event.width, event.height)

    frame.bind("<Configure>", on_frame_resize)

    debug_win, update_debug, file_menu = create_menu(root, chip8_ref)

    running = True
    last_cycle = time.time()
    last_frame = time.time()
    frame_delay = 1 / 60.0

    def load_rom():
        nonlocal rom_loaded, last_cycle, last_frame
        path = select_rom()
        if path:
            chip8_ref[0] = chip8_hw.ChipEightCpu(debug_callback=update_debug)
            chip8_ref[0].load_rom(path)
            rom_loaded = True
            chip8_ref[0].update_screen = True
            last_cycle = time.time()
            last_frame = time.time()

    file_menu.entryconfig(0, command=load_rom)

    def exit_app():
        nonlocal running
        running = False

    file_menu.entryconfig(2, command=exit_app)


    def on_close():
        nonlocal running
        running = False

    root.protocol("WM_DELETE_WINDOW", on_close)

    while running:
        for event in sdl2.ext.get_events():
            if event.type == sdl2.SDL_QUIT:
                running = False

        now = time.time()
        if rom_loaded and now - last_cycle >= 1 / 500.0:
            chip8_ref[0].emulate_cycle()
            last_cycle = now

        if rom_loaded and (now - last_frame >= frame_delay or chip8_ref[0].update_screen):
            draw_screen(renderer, chip8_ref[0], window)
            chip8_ref[0].update_screen = False
            last_frame = now

        root.update_idletasks()
        root.update()
        sdl2.SDL_Delay(1)

    root.destroy()
    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()


if __name__ == "__main__":
    main()
