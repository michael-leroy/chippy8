import chip8_hw
import pytest


def init_cpu(op_hi, op_lo):
    cpu = chip8_hw.ChipEightCpu()
    cpu.memory[0x200] = op_hi
    cpu.memory[0x201] = op_lo
    return cpu


def test_add_vx_vy_with_carry():
    cpu = init_cpu(0x81, 0x24)  # 8XY4 where X=1,Y=2
    cpu.V[1] = 0xFE
    cpu.V[2] = 0x04
    cpu.emulate_cycle()
    assert cpu.V[1] == 0x02
    assert cpu.V[0xF] == 1
    assert cpu.pc == 0x202


def test_add_vx_vy_no_carry():
    cpu = init_cpu(0x81, 0x24)
    cpu.V[1] = 0x10
    cpu.V[2] = 0x0F
    cpu.emulate_cycle()
    assert cpu.V[1] == 0x1F
    assert cpu.V[0xF] == 0


def test_subn_vx_vy_sets_borrow_flag():
    cpu = init_cpu(0x81, 0x27)  # 8XY7 where X=1,Y=2
    cpu.V[1] = 0x01
    cpu.V[2] = 0x02
    cpu.emulate_cycle()
    assert cpu.V[1] == 0x01
    assert cpu.V[0xF] == 1


def test_ld_b_vx_bcd_representation():
    cpu = chip8_hw.ChipEightCpu()
    cpu.I = 0x300
    cpu.v_x = 1
    cpu.V[1] = 254
    cpu.ld_b_vx(0xF133)
    assert cpu.memory[0x300] == 2
    assert cpu.memory[0x301] == 5
    assert cpu.memory[0x302] == 4


def test_rnd_vx_byte_masks_random_value(monkeypatch):
    cpu = chip8_hw.ChipEightCpu()
    cpu.v_x = 1

    def fake_randint(a, b):
        return 0xAB

    monkeypatch.setattr(chip8_hw.random, "randint", fake_randint)
    cpu.rnd_vx_byte(0xC1F0)
    assert cpu.V[1] == 0xA0


def test_add_I_vx_allows_overflow():
    cpu = chip8_hw.ChipEightCpu()
    cpu.I = 0xFFE
    cpu.v_x = 1
    cpu.V[1] = 0x04
    cpu.add_I_vx(0xF11E)
    assert cpu.I == 0x1002


def test_ld_i_vx_increments_index():
    cpu = chip8_hw.ChipEightCpu()
    cpu.I = 0x300
    cpu.v_x = 2
    cpu.V[0] = 1
    cpu.V[1] = 2
    cpu.V[2] = 3
    cpu.ld_i_vx(0xF255)
    assert cpu.memory[0x300] == 1
    assert cpu.memory[0x301] == 2
    assert cpu.memory[0x302] == 3
    assert cpu.I == 0x303


def test_ld_vx_i_increments_index():
    cpu = chip8_hw.ChipEightCpu()
    cpu.I = 0x400
    cpu.memory[0x400:0x403] = bytearray([4, 5, 6])
    cpu.v_x = 2
    cpu.ld_vx_i(0xF265)
    assert cpu.V[0] == 4
    assert cpu.V[1] == 5
    assert cpu.V[2] == 6
    assert cpu.I == 0x403


def test_draw_collision_and_bounds():
    cpu = chip8_hw.ChipEightCpu()
    cpu.I = 0x300
    cpu.memory[0x300] = 0x80
    cpu.v_x = 1
    cpu.v_y = 2
    cpu.V[1] = 63
    cpu.V[2] = 0
    cpu.drw_vx_vy_safe(0xD121)
    assert sum(cpu.gfx) == 1
    assert cpu.gfx[63] == 1
    assert cpu.gfx[64] == 0
    assert cpu.V[0xF] == 0
    cpu.drw_vx_vy_safe(0xD121)
    assert sum(cpu.gfx) == 0
    assert cpu.V[0xF] == 1
