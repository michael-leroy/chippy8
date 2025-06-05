import time
import tkinter as tk
from tkinter import filedialog

import sdl2
import sdl2.ext
import ctypes
import math
import array

import chip8_hw

CYCLE_HZ = 700.0

# Mapping of host keyboard keys to CHIP-8 keypad indices.
# This follows the common layout:
# 1 2 3 4 -> 1 2 3 C
# Q W E R -> 4 5 6 D
# A S D F -> 7 8 9 E
# Z X C V -> A 0 B F
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

# Map Tk "keysym" names to SDL key constants for the same
# CHIP-8 keypad layout. This allows keyboard input to work
# when the SDL window is embedded within a Tk frame.
TK_KEY_MAP = {
    "1": sdl2.SDLK_1,
    "2": sdl2.SDLK_2,
    "3": sdl2.SDLK_3,
    "4": sdl2.SDLK_4,
    "q": sdl2.SDLK_q,
    "w": sdl2.SDLK_w,
    "e": sdl2.SDLK_e,
    "r": sdl2.SDLK_r,
    "a": sdl2.SDLK_a,
    "s": sdl2.SDLK_s,
    "d": sdl2.SDLK_d,
    "f": sdl2.SDLK_f,
    "z": sdl2.SDLK_z,
    "x": sdl2.SDLK_x,
    "c": sdl2.SDLK_c,
    "v": sdl2.SDLK_v,
}


def process_key_event(
    cpu: chip8_hw.ChipEightCpu, key_sym, pressed: bool
) -> bool:
    """Update CHIP-8 key state for a host keyboard event.

    ``key_sym`` may be an SDL key code or a Tk ``keysym`` string.
    The function returns ``True`` if the key was mapped to a CHIP-8
    keypad entry.
    """
    if isinstance(key_sym, str):
        key_sym = TK_KEY_MAP.get(key_sym.lower())

    chip_key = KEY_MAP.get(key_sym)
    if chip_key is not None:
        cpu.key[chip_key] = 1 if pressed else 0
        return True
    return False


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
    debug_win.geometry("500x500")

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

    labels["CPS"] = tk.Label(debug_win, text="CPS: 0")
    labels["CPS"].grid(row=row, column=0, columnspan=2, sticky="w")
    row += 1
    labels["FPS"] = tk.Label(debug_win, text="FPS: 0")
    labels["FPS"].grid(row=row, column=0, columnspan=2, sticky="w")
    row += 1

    for i in range(16):
        tk.Label(debug_win, text=f"V{i:X}:").grid(row=row + i // 2, column=(i % 2) * 2, sticky="e")
        labels[f"V{i}"] = tk.Label(debug_win, text="00")
        labels[f"V{i}"].grid(row=row + i // 2, column=(i % 2) * 2 + 1, sticky="w")
    row += 8

    tk.Label(debug_win, text="ROM").grid(row=row, column=0, sticky="w")
    row += 1
    rom_text = tk.Text(debug_win, width=48, height=10, font=("Courier", 8))
    rom_text.grid(row=row, column=0, columnspan=4, sticky="nsew")
    debug_win.rowconfigure(row, weight=1)
    debug_win.columnconfigure(3, weight=1)
    row += 1

    debug_win.withdraw()

    perf = {"cps": 0, "fps": 0}

    def update_rom_view(cpu):
        rom_text.delete("1.0", tk.END)
        for offset in range(0, len(cpu.rom), 16):
            addr = 0x200 + offset
            chunk = cpu.rom[offset : offset + 16]
            chunk_hex = " ".join(f"{b:02X}" for b in chunk)
            rom_text.insert(tk.END, f"{addr:03X}: {chunk_hex}\n")

    def update_debug(cpu=None):
        if cpu is not None:
            labels["PC"].config(text=f"PC: {cpu.pc:03X}")
            labels["I"].config(text=f"I: {cpu.I:03X}")
            labels["DT"].config(text=f"DT: {cpu.delay_timer:02X}")
            labels["ST"].config(text=f"ST: {cpu.sound_timer:02X}")
            for i in range(16):
                labels[f"V{i}"].config(text=f"{cpu.V[i]:02X}")


        labels["CPS"].config(text=f"CPS: {perf['cps']:.0f}")
        labels["FPS"].config(text=f"FPS: {perf['fps']:.0f}")

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

    return debug_win, update_debug, update_rom_view, toggle_debug, file_menu, perf


def draw_screen(renderer, chip8, window, texture, framebuffer):
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

    for i, pixel in enumerate(chip8.gfx):
        framebuffer[i] = 0xFFFFFFFF if pixel else 0xFF000000

    sdl2.SDL_UpdateTexture(texture, None, framebuffer, CHIP8_WIDTH * 4)

    dest = sdl2.SDL_Rect(off_x, off_y, draw_w, draw_h)
    sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
    sdl2.SDL_RenderClear(renderer)
    sdl2.SDL_RenderCopy(renderer, texture, None, dest)
    sdl2.SDL_RenderPresent(renderer)


def main():
    root = tk.Tk()
    root.title("Chippy8")

    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_AUDIO)

    frame = tk.Frame(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
    frame.pack(fill="both", expand=True)
    root.update_idletasks()
    root.update()

    window = sdl2.SDL_CreateWindowFrom(ctypes.c_void_p(frame.winfo_id()))
    renderer = sdl2.SDL_CreateRenderer(
        window, -1, sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC
    )
    texture = sdl2.SDL_CreateTexture(
        renderer,
        sdl2.SDL_PIXELFORMAT_RGBA8888,
        sdl2.SDL_TEXTUREACCESS_STREAMING,
        CHIP8_WIDTH,
        CHIP8_HEIGHT,
    )
    framebuffer = (ctypes.c_uint32 * (CHIP8_WIDTH * CHIP8_HEIGHT))()

    # --------------------
    # Audio setup
    sample_rate = 44100
    frame_samples = sample_rate // 60
    freq = 440
    beep_samples = array.array(
        "h",
        [
            int(0.25 * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
            for i in range(frame_samples)
        ],
    )
    beep_bytes = beep_samples.tobytes()

    # SDL_AudioSpec requires defaults provided via constructor
    desired = sdl2.SDL_AudioSpec(
        sample_rate,
        sdl2.AUDIO_S16SYS,
        1,
        frame_samples,
        None,
        None,
    )

    audio_device = sdl2.SDL_OpenAudioDevice(None, 0, desired, None, 0)
    sound_playing = False

    chip8_ref = [chip8_hw.ChipEightCpu()]
    rom_loaded = False

    def on_frame_resize(event):
        sdl2.SDL_SetWindowSize(window, event.width, event.height)

    frame.bind("<Configure>", on_frame_resize)

    def on_key_press(event):
        nonlocal paused, step_once
        key = event.keysym.lower()
        if key == "p":
            paused = not paused
        elif key == "i":
            step_once = True
        else:
            process_key_event(chip8_ref[0], event.keysym, True)

    def on_key_release(event):
        key = event.keysym.lower()
        if key not in {"p", "i"}:
            process_key_event(chip8_ref[0], event.keysym, False)

    root.bind_all("<KeyPress>", on_key_press)
    root.bind_all("<KeyRelease>", on_key_release)
    frame.focus_set()

    debug_win, update_debug, update_rom_view, toggle_debug, file_menu, perf = create_menu(root, chip8_ref)

    running = True
    paused = False
    step_once = False
    frame_delay = 1 / 60.0
    cycle_hz = CYCLE_HZ

    last_time = time.time()
    cycle_accum = 0.0
    last_frame = last_time
    cycles_executed = 0
    last_cps_update = last_time
    fps_count = 0
    last_fps_update = last_time

    def load_rom():
        nonlocal rom_loaded, last_time, last_frame, cycle_accum, cycles_executed, last_cps_update, fps_count, last_fps_update
        path = select_rom()
        if path:
            chip8_ref[0] = chip8_hw.ChipEightCpu(debug_callback=update_debug)
            chip8_ref[0].load_rom(path)
            # Ensure the CPU debug flag matches the UI state so the memory view
            # updates immediately after loading a ROM.
            toggle_debug()
            update_rom_view(chip8_ref[0])
            update_debug(chip8_ref[0])
            rom_loaded = True
            chip8_ref[0].update_screen = True
            last_time = time.time()
            cycle_accum = 0.0
            last_frame = last_time
            cycles_executed = 0
            last_cps_update = last_time
            fps_count = 0
            last_fps_update = last_time

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
            elif event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_p:
                    paused = not paused
                elif event.key.keysym.sym == sdl2.SDLK_i:
                    step_once = True
                else:
                    process_key_event(chip8_ref[0], event.key.keysym.sym, True)
            elif event.type == sdl2.SDL_KEYUP:
                if event.key.keysym.sym not in (sdl2.SDLK_p, sdl2.SDLK_i):
                    process_key_event(chip8_ref[0], event.key.keysym.sym, False)

        now = time.time()
        dt = now - last_time
        last_time = now

        if rom_loaded:
            if paused:
                if step_once:
                    chip8_ref[0].emulate_cycle()
                    step_once = False
                    cycles_executed += 1
            else:
                cycle_accum += dt * cycle_hz
                while cycle_accum >= 1.0:
                    chip8_ref[0].emulate_cycle()
                    cycle_accum -= 1.0
                    cycles_executed += 1

            if now - last_cps_update >= 1.0:
                perf["cps"] = cycles_executed / (now - last_cps_update)
                cycles_executed = 0
                last_cps_update = now

            if now - last_frame >= frame_delay or chip8_ref[0].update_screen:
                draw_screen(renderer, chip8_ref[0], window, texture, framebuffer)
                chip8_ref[0].update_screen = False
                last_frame = now
                fps_count += 1

            if now - last_fps_update >= 1.0:
                perf["fps"] = fps_count / (now - last_fps_update)
                fps_count = 0
                last_fps_update = now

            # handle sound timer -> play beep
            if chip8_ref[0].sound_timer > 0:
                sdl2.SDL_QueueAudio(audio_device, beep_bytes, len(beep_bytes))
                if not sound_playing:
                    sdl2.SDL_PauseAudioDevice(audio_device, 0)
                    sound_playing = True
            elif sound_playing:
                sdl2.SDL_ClearQueuedAudio(audio_device)
                sdl2.SDL_PauseAudioDevice(audio_device, 1)
                sound_playing = False

        if chip8_ref[0].debug:
            update_debug(chip8_ref[0])

        root.update_idletasks()
        root.update()
        sdl2.SDL_Delay(1)

    root.destroy()
    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_CloseAudioDevice(audio_device)
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()


if __name__ == "__main__":
    main()
