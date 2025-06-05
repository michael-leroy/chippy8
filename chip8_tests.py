#!/usr/bin/python
#uses pytest/py.test - pytest.org
import chip8_hw
import os
import pytest
from unittest import mock



def initalize_system(ins, ins_two):
    chip = chip8_hw.ChipEightCpu()
    chip.memory[0x200] = ins
    chip.memory[0x201] = ins_two
    return chip

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

def test_x0_dispatch():
    '''
    Test if the correct functions are called when a 0x00E0 or
    0x00EE opcode is given.

    Using mock to override the 'stock' functions and see if they
    are called. Remember that you have to also update the reference
    to the function is the instruction_dispatch dict or else it will
    still run the 'stock' function since a reference to it still
    exists.
    '''
    chip = initalize_system(0x00, 0xE0)
    chip.x0_dispatch = mock.MagicMock()
    #updating the instruction_dispatch to ensure mock, not
    #the original function is called.
    chip.instruction_dispatch[0x0000] = chip.x0_dispatch
    chip.emulate_cycle()
    chip.x0_dispatch.assert_called_once_with(0x00E0)
    chip = None

    chip = initalize_system(0x00, 0xE0)
    chip.cls = mock.MagicMock()
    chip.instruction_dispatch[0x00E0] = chip.cls
    chip.emulate_cycle()
    chip.cls.assert_called_once_with(0x00E0)
    chip = None

    chip = initalize_system(0x00, 0xEE)
    chip.ret = mock.MagicMock()
    chip.instruction_dispatch[0x00EE] = chip.ret
    chip.emulate_cycle()
    chip.ret.assert_called_once_with(0x00EE)

# def test_x8_dispatch():
#     '''
#     Test if the correct functions are called when a 0x00E0 or
#     0x00EE opcode is given.

#     Using mock to override the 'stock' functions and see if they
#     are called. Remember that you have to also update the reference
#     to the function is the instruction_dispatch dict or else it will
#     still run the 'stock' function since a reference to it still
#     exists.
#     '''
#     chip = initalize_system(0x81, 0x10)
#     chip.x0_dispatch = mock.MagicMock()
#     #updating the instruction_dispatch to ensure mock, not
#     #the original function is called.
#     chip.instruction_dispatch[0x0000] = chip.x0_dispatch
#     chip.emulate_cycle()
#     chip.x0_dispatch.assert_called_once_with(0x00E0)
#     chip = None

#     chip = initalize_system(0x00, 0xE0)
#     chip.cls = mock.MagicMock()
#     chip.instruction_dispatch[0x00E0] = chip.cls
#     chip.emulate_cycle()
#     chip.cls.assert_called_once_with(0x00E0)
#     chip = None

#     chip = initalize_system(0x00, 0xEE)
#     chip.ret = mock.MagicMock()
#     chip.instruction_dispatch[0x00EE] = chip.ret
#     chip.emulate_cycle()
#     chip.ret.assert_called_once_with(0x00EE)

def test_cls():
    '''
    test if screen is cleared properly
    '''
    chip = initalize_system(0x00, 0xE0)
    chip.gfx = [1] * (64*32)
    chip.emulate_cycle()
    for bits in chip.gfx:
        assert bits == 0
    assert chip.pc == 514
    assert chip.update_screen == True
    chip = None

def test_ret():
    '''
    test if the top item in the stack is returned
    to the program counter.
    '''
    chip = initalize_system(0x00, 0xEE)
    #add someting to the stack
    chip.stack.append(514)
    chip.emulate_cycle()
    assert chip.pc == 514
    assert len(chip.stack) == 0
    chip = None

def test_jmp_addr():
    '''
    test if program counter is set to the jump
    '''
    chip = initalize_system(0x12, 0x00)
    chip.emulate_cycle()
    assert chip.pc == 512
    chip = None

def test_call_addr():
    chip = initalize_system(0x22, 0x1C)
    chip.emulate_cycle()
    assert chip.stack[0] == 514
    assert chip.pc == 540
    chip.ret(0x00EE)
    assert chip.pc == 514
    chip = None

def test_se_vx_byte():
    '''
    test skip next instruction if v_x == kk
    '''
    chip = initalize_system(0x31, 0x22)
    chip.V[1] = 0x22
    chip.emulate_cycle()
    assert chip.pc == 516
    chip = None

    chip = initalize_system(0x31, 0x22)
    chip.V[1] = 0x23
    chip.emulate_cycle()
    assert chip.pc == 514
    chip = None

def test_ne_vx_byte():
    '''
    test skip next instruction if v_x != kk
    '''
    chip = initalize_system(0x41, 0x22)
    chip.V[1] = 0x22
    chip.emulate_cycle()
    assert chip.pc == 514
    chip = None

    chip = initalize_system(0x41, 0x22)
    chip.V[1] = 0x23
    chip.emulate_cycle()
    assert chip.pc == 516
    chip = None

def test_se_vx_vy():
    '''
    test skip next instruction if vx == vy
    '''
    chip = initalize_system(0x51, 0x20)
    chip.V[1] = 0xFF
    chip.V[2] = 0xFF
    chip.emulate_cycle()
    assert chip.pc == 516
    chip = None

    chip = initalize_system(0x51, 0x20)
    chip.V[1] = 0xFF
    chip.V[2] = 0xFE
    chip.emulate_cycle()
    assert chip.pc == 514
    chip = None

def test_ld_vx_byte():
    '''
    test putting value kk into register vx
    '''
    chip = initalize_system(0x61, 0xFF)
    assert chip.V[1] == 0
    chip.emulate_cycle()
    assert chip.V[1] == 0xFF
    assert chip.pc == 514
    chip = None

def test_add_vx_byte():
    '''
    test adding to vx
    '''
    chip = initalize_system(0x71, 0x05)
    chip.V[1] = 0x01
    chip.emulate_cycle()
    assert chip.V[1] == 0x06
    assert chip.pc == 514
    chip = None

def test_ld_vx_vy():
    '''
    test setting vx to the value of vy.
    '''
    chip = initalize_system(0x81, 0x20)
    chip.V[1] = 0x00
    chip.V[2] = 0xFE
    chip.emulate_cycle()
    assert chip.V[1] == 0xFE
    assert chip.pc == 514
    chip = None

def test_add_vx_byte_wrap():
    chip = initalize_system(0x71, 0x01)
    chip.V[1] = 0xFF
    chip.emulate_cycle()
    assert chip.V[1] == 0x00
    chip = None

def test_sub_vx_vy():
    chip = initalize_system(0x81, 0x25)
    chip.V[1] = 0x05
    chip.V[2] = 0x03
    chip.emulate_cycle()
    assert chip.V[1] == 0x02
    assert chip.V[0xF] == 1
    chip = None

    chip = initalize_system(0x81, 0x25)
    chip.V[1] = 0x02
    chip.V[2] = 0x05
    chip.emulate_cycle()
    assert chip.V[1] == 0xFD
    assert chip.V[0xF] == 0
    chip = None

def test_shift_operations():
    chip = initalize_system(0x81, 0x06)
    chip.V[1] = 0x03
    chip.emulate_cycle()
    assert chip.V[1] == 0x01
    assert chip.V[0xF] == 1
    chip = None

    chip = initalize_system(0x81, 0x0E)
    chip.V[1] = 0x81
    chip.emulate_cycle()
    assert chip.V[1] == 0x02
    assert chip.V[0xF] == 1
    chip = None

def test_key_skip():
    chip = initalize_system(0xE1, 0x9E)
    chip.V[1] = 0x2
    chip.key[2] = 1
    chip.emulate_cycle()
    assert chip.pc == 516
    chip = None

    chip = initalize_system(0xE1, 0xA1)
    chip.V[1] = 0x3
    chip.key[3] = 1
    chip.emulate_cycle()
    assert chip.pc == 514
    chip = None

def test_rom_load():
    rom_path = "breakout.ch8"
    if not os.path.exists(rom_path):
        pytest.skip("ROM file not available")

    chip = chip8_hw.ChipEightCpu()
    chip.load_rom(rom_path)

    memory_offset = 512

    assert chip.memory[memory_offset] > 0

    while chip.memory[memory_offset] > 0:
        opcode = chip.get_opcode()
        memory_offset += 2
        chip.pc += 2
        assert opcode




# def test_0x00E0():
#     chip = chip8_hw.ChipEightCpu()
#     chip.memory[0x200] = 0x00
#     chip.memory[0x201] = 0xE0
#     #set a few bits of gfx to see if
#     #the instruction clears them
#     chip.gfx = [1] * (32 * 64)
#     for gfx_bits in chip.gfx:
#         assert gfx_bits == 1
#     chip.emulate_cycle()
#     assert chip.pc == 514
#     for gfx_bits in chip.gfx:
#         assert gfx_bits == 0
#     assert chip.update_screen == True
#     chip = None

# def test_0x00EE():
#     chip = chip8_hw.ChipEightCpu()
#     chip.memory[0x200] = 0x00
#     chip.memory[0x201] = 0xEE
#     chip.memory[0x205] = 0xFF
#     chip.stack.append(0x205)
#     chip.emulate_cycle()
#     assert chip.pc == 0x205
#     chip = None
# def test_1nnn():
#     chip = chip8_hw.ChipEightCpu()
#     chip.memory[0x200] = 0x15
#     chip.memory[0x201] = 0x55
#     chip.emulate_cycle()
#     assert chip.pc == 0x555
#     chip = None

# def test_2NNN():
#     chip = chip8_hw.ChipEightCpu()
#     chip.memory[0x200] = 0x25
#     chip.memory[0x201] = 0x55
#     chip.emulate_cycle()
#     assert chip.stack[0] == 0x200
#     assert chip.pc == 0x555
#     chip = None

# def test_3xkk():
#     chip = chip8_hw.ChipEightCpu()
#     chip.memory[0x200] = 0x30
#     chip.memory[0x201] = 0x55
#     chip.V[0x0] == 0x55
#     chip.emulate_cycle()
#     assert chip.pc == 0x204
#     chip.memory[0x202] = 0x30
#     chip.memory[0x203] = 0x55
#     chip.emulate_cycle()
#     assert chip.pc == 0x204
