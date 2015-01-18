#!/usr/bin/python
#uses pytest/py.test - pytest.org
import chip8_hw

def test_reset():
    chip = chip8_hw.ChipEightCpu()
    chip.memory = [1] * 4096
    chip.V = [1] * 16
    chip.I = 1
    chip.pc = 0x202
    chip.gfx = [1] * (64*32)
    chip.update_screen = True
    chip.delay_timer = 10
    chip.sound_timer = 10
    chip.stack = [0x1]
    chip.key = [1] * 16   
    chip.reset()
    for mem in chip.memory:
        assert mem == 0
    for registers in chip.V:
        assert registers == 0
    assert chip.I == 0
    assert chip.pc == 0x200
    for gfx_bits in chip.gfx:
        assert gfx_bits == 0
    assert chip.update_screen == False
    assert chip.delay_timer == 0
    assert chip.sound_timer == 0
    assert chip.stack == []
    for k in chip.key:
        assert k == 0
    chip = None

def test_0x00E0():
    chip = chip8_hw.ChipEightCpu()
    chip.memory[0x200] = 0x00
    chip.memory[0x201] = 0xE0
    #set a few bits of gfx to see if
    #the instruction clears them
    chip.gfx = [1] * (32 * 64)
    for gfx_bits in chip.gfx:
        assert gfx_bits == 1
    chip.emulate_cycle()
    assert chip.pc == 514
    for gfx_bits in chip.gfx:
        assert gfx_bits == 0
    assert chip.update_screen == True
    chip = None

def test_0x00EE():
    chip = chip8_hw.ChipEightCpu()
    chip.memory[0x200] = 0x00
    chip.memory[0x201] = 0xEE
    chip.memory[0x205] = 0xFF
    chip.stack.append(0x205)
    chip.emulate_cycle()
    assert chip.pc == 0x205
