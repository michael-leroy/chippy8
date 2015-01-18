#!/usr/bin/python

import chip8_hw

chip = chip8_hw.ChipEightCpu()
print(chip.pc)
chip.memory[0x200] = 0x0000
chip.gfx[0] = 1
chip.gfx[1] = 1
chip.gfx[2] = 1
chip.gfx[3] = 1
chip.emulate_cycle()
print(chip.pc)
print(chip.gfx[0])
print(chip.gfx[1])
print(chip.gfx[2])
print(chip.gfx[3])

