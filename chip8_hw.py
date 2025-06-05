#!/usr/bin/python

import random

class ChipEightCpu(object):
    def __init__(self, debug_callback=None):
        #chip8 has 4k of system ram
        '''Systems memory map:
        0x000-0x1FF - Chip 8 interpreter (contains font set in emu)
        0x050-0x0A0 - Used for the built in 4x5 pixel font set (0-F)
        0x200-0xFFF - Program ROM and work RAM
        '''
        self.CHIP8MAXMEM = 4096
        self.memory = bytearray(self.CHIP8MAXMEM)

        #Chip8 has 15, 8-bit registers and a 16th register used as a 
        #'carry flag.'
        #The 15 registers are named V0-VE
        self.V = [0] * 16

        #Chip8 has an index register and a program counter.
        #The PC can have a value from 0x000 to 0xFFF.
        self.I = 0
        #Start program counter at 0x200
        self.pc = 0x200

        #The graphics are single color with a screen rez of 64 * 32
        self.gfx = [0] * (64*32)
        #Used to determine when to update the screen
        self.update_screen = False
        #The chip8 has no Interrupts, but there are two timer registers
        #that count at 60hz. When set above zero they must count down back to
        #zero
        self.delay_timer = 0
        self.sound_timer = 0
        
        #The stack has 16 levels
        #I am unsure if I need stack pointer?
        self.stack = []
        #self.stack_pointer = 0

        #The chip8 system has 16 keys (0x0 - 0xF)
        self.key = [0] * 16

        # debug support
        self.debug = False
        self.debug_callback = debug_callback

        self._load_fontset()

        self.instruction_dispatch = {
                0x0000 : self.x0_dispatch,
                0x00E0 : self.cls,
                0x00EE : self.ret,
                0x1000 : self.jp_addr,
                0x2000 : self.call_addr,
                0x3000 : self.se_vx_byte,
                0x4000 : self.sne_vx_byte,
                0x5000 : self.se_vx_vy,
                0x6000 : self.ld_vx_byte,
                0x7000 : self.add_vx_byte,
                0x8000 : self.x8_dispatch,
                # 0x8XY0 handled in x8_dispatch
                0x8001 : self.or_vx_vy,
                0x8002 : self.and_vx_vy,
                0x8003 : self.xor_vx_vy,
                0x8004 : self.add_vx_vy,
                0x8005 : self.sub_vx_vy,
                0x8006 : self.shr_vx,
                0x8007 : self.subn_vx_vy,
                0x800E : self.shl_vx,
                0x9000 : self.sne_vx_vy,
                0xA000 : self.ld_I,
                0xB000 : self.jp_v0,
                0xC000 : self.rnd_vx_byte,
                0xD000 : self.drw_vx_vy_safe,
                0xE000 : self.xE_dispatch,
                0xE00E : self.skp_vx,
                0xE001 : self.sknp_vx,
                0xF000 : self.xF_dispatch,
                0xF007 : self.ld_vx_dt,
                0xF00A : self.ld_vx_k,
                0xF015 : self.ld_dt_vx,
                0xF018 : self.ld_st_vx,
                0xF01E : self.add_I_vx,
                0xF029 : self.ld_f_vx,
                0xF033 : self.ld_b_vx,
                0xF055 : self.ld_i_vx,
                0xF065 : self.ld_vx_i
        }

    def _load_fontset(self):
        """Load the CHIP-8 fontset into memory starting at address 0."""
        fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80   # F
        ]

        start = 0x000
        for i, byte in enumerate(fontset):
            self.memory[start + i] = byte

    def reset(self):
        self.memory = bytearray(self.CHIP8MAXMEM)
        self.V = [0] * 16
        self.I = 0
        self.pc = 0x200
        self.gfx = [0] * (64*32)
        self.update_screen = False
        self.delay_timer = 0
        self.sound_timer = 0
        self.stack = []
        self.key = [0] * 16

        self._load_fontset()

        self.debug = False

    def load_rom(self, rom_file_path):
        #0x200-0xFFF - Program ROM and work RAM
        #0x200 == 512
        memory_offset = 512

        with open(rom_file_path, "rb") as f:
            byte = f.read(1)
            while byte != b"":
                self.memory[memory_offset] = byte[0]
                memory_offset += 1
                byte = f.read(1)


    def get_opcode(self):
        #One opcode is 2 bytes long. We need to fetch two
        #sucessive bytes and merge them to get the full opcode
        #First we add 8 bits to the end so its 2bytes long, then merge the second
        #half 
        opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]
        return opcode

    def emulate_cycle(self):
        opcode = self.get_opcode()
        old_pc = self.pc
        #Now that we have the opcode we need one big if statement to handle
        #all the various opcodes. Maybe this can be cleaned up later since python
        #has no 'switch' statement.

        #Vx and Vy are used very often here are some shortcuts
        self.v_x = (opcode & 0x0F00) >> 8
        self.v_y = (opcode & 0x00F0) >> 4
    
        handler = self.instruction_dispatch.get(opcode & 0xF000)
        if handler:
            handler(opcode)
        else:
            print('Unknown/Invalid opcode ' + "0x%0.4X" % opcode)
        #Decrement timer.
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            if self.sound_timer == 1:
                # TODO: have sound and graphics
                print("BEEP!\n")
            self.sound_timer -= 1

        if self.debug and self.debug_callback:
            self.debug_callback(self)



    def x0_dispatch(self, opcode):
        '''
        Runs the correct instruction for 0x00E0 and
        0x00EE
        We are ignoring 0x0NNN because its not often used.
        '''
        handler = self.instruction_dispatch.get(opcode & 0xF0FF)
        if handler:
            handler(opcode)
        else:
            print('Unknown/Invalid opcode ' + str(opcode))

    def cls(self, opcode):
        '''
        0x0000 == 0x00E0: Clears the screen
        Assuming clearing sets all gfx bits to zero
        '''
        self.gfx = [0] * (64*32)
        self.pc += 2
        self.update_screen = True

    def ret(self, opcode):
        '''
        0x000E == 0x00EE: returns from subroutine
        '''
        self.pc = self.stack.pop()

    def jp_addr(self, opcode):
        '''
        0x1000 == 0x1NNN Jump to location NNN
        '''
        self.pc = opcode & 0x0FFF

    def call_addr(self, opcode):
        '''
        0x2000 == 0x2NNN CALL addr, call subroutine at NNN
        '''
        # push the address of the next instruction onto the stack
        self.stack.append(self.pc + 2)
        self.pc = opcode & 0x0FFF

    def se_vx_byte(self, opcode):
        '''
        0x3000 == 3xkk, Skip next instruction if Vx == kk.
        '''
        if self.V[self.v_x] == (opcode & 0x00FF):
            self.pc += 4
        else:
            self.pc += 2

    def sne_vx_byte(self, opcode):
        '''
        0x4000 == 4xkk, Skip next instruction if Vx != kk.
        '''
        if self.V[self.v_x] != (opcode & 0x00FF):
            self.pc += 4
        else:
            self.pc += 2

    def se_vx_vy(self, opcode):
        '''
        0x5000 = 5xy0 SE, skip next instruction if Vx = Vy
        '''
        if self.V[self.v_x] == self.V[self.v_y]:
            self.pc += 4
        else:
            self.pc += 2

    def ld_vx_byte(self, opcode):
        '''
        0x6000 = 6xkk put value kk in to register Vx
        '''
        self.V[self.v_x] = opcode & 0x00FF
        self.pc += 2

    def add_vx_byte(self, opcode):
        '''
        0x7000 = 7xkk Add Vx. Add value kk to register Vx and store value
        in Vx
        '''
        self.V[self.v_x] = (self.V[self.v_x] + (opcode & 0x00FF)) & 0xFF
        self.pc += 2

    def ld_vx_vy(self, opcode):
        '''
        0x8000 = 8xy0 Set Vx = Vy
        '''
        self.V[self.v_x] = self.V[self.v_y]
        self.pc += 2

    def or_vx_vy(self, opcode):
        '''
        8xy1 Set Vx = Vx or Vy
        '''
        self.V[self.v_x] = self.V[self.v_x] | self.V[self.v_y]
        self.pc += 2

    def and_vx_vy(self, opcode):
        '''
        8xy2 Set Vx = Vx and Vy
        '''
        self.V[self.v_x] = self.V[self.v_x] & self.V[self.v_y]
        self.pc += 2

    def xor_vx_vy(self, opcode):
        '''
        8xy3 Set Vx = Vx XOR Vy
        '''
        self.V[self.v_x] = self.V[self.v_x] ^ self.V[self.v_y]
        self.pc += 2

    def add_vx_vy(self, opcode):
        '''
        8xy4 Set Vx = Vx + Vy 
        set VF = carry is over 255
        If the two value are over 8 bit (255) carry the result in VF
        '''
        total = self.V[self.v_x] + self.V[self.v_y]
        if total > 0xFF:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0
        self.V[self.v_x] = total & 0xFF
        self.pc += 2

    def sub_vx_vy(self, opcode):
        '''
        8xy5 - Sub Vx, Vy.
        Set Vx = Vx - Vy, set Vf = if it does NOT borrow
        '''
        if self.V[self.v_x] >= self.V[self.v_y]:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0
        self.V[self.v_x] = (self.V[self.v_x] - self.V[self.v_y]) & 0xFF
        self.pc += 2

    def shr_vx(self, opcode):
        '''
        8xy6 - SHR Vx {, Vy}
        If the least significant bit of Vx is 1, set VF = 1
        otherwise 0. Then divide Vx by 2
        '''
        self.V[0xF] = self.V[self.v_x] & 0x1
        self.V[self.v_x] = (self.V[self.v_x] >> 1) & 0xFF
        self.pc += 2

    def subn_vx_vy(self, opcode):
        '''
        8xy7 - SUBN Vx, Vy
        Set Vx = Vy - Vx, set VF = NOT BORROW
        '''
        if self.V[self.v_y] >= self.V[self.v_x]:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0
        self.V[self.v_x] = (self.V[self.v_y] - self.V[self.v_x]) & 0xFF
        self.pc += 2

    def shl_vx(self, opcode):
        '''
        8xyE - SHL Vx {, Vy}
        '''
        self.V[0xF] = (self.V[self.v_x] >> 7) & 0x1
        self.V[self.v_x] = (self.V[self.v_x] << 1) & 0xFF
        self.pc += 2

    def x8_dispatch(self, opcode):
        '''
        Runs the correct 0x8000 instruction.
        '''
        if (opcode & 0xF00F) == 0x8000:
            self.ld_vx_vy(opcode)
        else:
            try:
                self.instruction_dispatch[(opcode & 0xF00F)](opcode)
            except KeyError:
                print('Unknown/Invalid opcode ' + str(opcode))

    def sne_vx_vy(self, opcode):
        '''
        9xy0 - SNE Vx, Vy
        Skip next instruction if Vx != Vy
        '''
        if self.V[self.v_x] != self.V[self.v_y]:
            self.pc += 4
        else:
            self.pc += 2

    def ld_I(self, opcode):
        '''
        0xA000 == ANNN: Sets I to the address NNN
        '''
        self.I = opcode & 0x0FFF
        self.pc += 2

    def jp_v0(self, opcode):
        '''
        Bnnn - Jp V0, addr
        '''
        self.pc = (opcode & 0x0FFF) + self.V[0x0]

    def rnd_vx_byte(self, opcode):
        '''
        Cxkk - RND Vx, byte
        Gen number between 0x0 and 0xFF and & it with the value of kk then
        store in Vx
        '''
        rand_byte = random.randint(0x0, 0xFF)
        self.V[self.v_x] = rand_byte & (opcode & 0x00FF)
        self.pc += 2

    def drw_vx_vy(self, opcode):
        '''
        DRW Vx, Vy. nibble
        This is mostly based off other examples seen on 
        the net.
        TODO: test if this actually works
        '''
        drw_x = self.V[self.v_x]
        drw_y = self.V[self.v_y]
        drw_height = opcode & 0x000F
        sprite_data = []
        #set VF to zero because there has been no collision yet
        self.V[0xF] = 0
        #Read the sprite data from memory
        for x in range(drw_height):
            sprite_data.append(self.memory[self.I + x])
        for sprite_row in range(len(sprite_data)):
            for pixel_offset in range(8):
                location = drw_x + pixel_offset + ((drw_y + sprite_row) * 64)
                if (drw_y + sprite_row) >= 32 or (drw_x + pixel_offset - 1) >= 64:
                    continue
                drw_mask = 1 << (7 - pixel_offset)
                curr_pixel = (sprite_data[sprite_row] & drw_mask) >> (7 - pixel_offset)
                if curr_pixel:
                    if self.gfx[location] == 1:
                        self.V[0xF] = 1
                    self.gfx[location] ^= 1

        self.update_screen = True
        self.pc += 2

    def drw_vx_vy_safe(self, opcode):
        """
        Safer DRW routine that prevents drawing past the screen bounds.
        """
        drw_x = self.V[self.v_x]
        drw_y = self.V[self.v_y]
        drw_height = opcode & 0x000F
        self.V[0xF] = 0
        sprite_data = [self.memory[self.I + x] for x in range(drw_height)]

        for sprite_row in range(len(sprite_data)):
            y = drw_y + sprite_row
            if y >= 32:
                continue
            for pixel_offset in range(8):
                x = drw_x + pixel_offset
                if x >= 64:
                    continue
                location = x + (y * 64)
                drw_mask = 1 << (7 - pixel_offset)
                curr_pixel = (sprite_data[sprite_row] & drw_mask) >> (7 - pixel_offset)
                if curr_pixel:
                    if self.gfx[location] == 1:
                        self.V[0xF] = 1
                    self.gfx[location] ^= 1

        self.update_screen = True
        self.pc += 2

    def skp_vx(self, opcode):
        '''
        Ex9E - SKP Vx, skip next instruction if key is pressed.
        '''
        if self.key[self.V[self.v_x]] == 1:
            self.pc += 4
        else:
            self.pc += 2

    def sknp_vx(self, opcode):
        '''
        ExA1, SKNP Vx skip next instruction if key is NOT pressed.
        '''
        if self.key[self.V[self.v_x]] != 1:
            self.pc += 4
        else:
            self.pc += 2


    def xE_dispatch(self, opcode):
        '''
        Runs the correct 0xE000 instruction.
        '''
        handler = self.instruction_dispatch.get(opcode & 0xF00F)
        if handler:
            handler(opcode)
        else:
            print('Unknown/Invalid opcode ' + str(opcode))

    def ld_vx_dt(self, opcode):
        '''
        Fx07 set Vx = delay timer value
        '''
        self.V[self.v_x] = self.delay_timer
        self.pc += 2
    
    def ld_vx_k(self, opcode):
        '''
        Fx0A wait for a key press and store value in Vx
        '''
        for idx, k in enumerate(self.key):
            if k == 1:
                self.V[self.v_x] = idx
                self.pc += 2
                break

    def ld_dt_vx(self, opcode):
        '''
        Fx15 - LD DT, Vx, set DT to the value of Vx.
        '''
        self.delay_timer = self.V[self.v_x]
        self.pc += 2

    def ld_st_vx(self, opcode):
        '''
        Fx18 Set sound timer = Vx
        '''
        self.sound_timer = self.V[self.v_x]
        self.pc += 2

    def add_I_vx(self, opcode):
        '''
        Fx1E - ADD I, Vx
        Set I = I + Vx
        '''
        self.I = self.I + self.V[self.v_x]
        self.pc += 2

    def ld_f_vx(self, opcode):
        '''
        Fx29 - LD F, Vx
        '''
        self.I = self.V[self.v_x] * 5
        self.pc += 2

    def ld_b_vx(self, opcode):
        '''
        Fx33 - LD B, Vx
        Store BCD rep of Vx in memory locaton I/I+1/I+2
        '''
        self.memory[self.I] = (self.V[self.v_x] // 100) #hundreds digit
        self.memory[self.I + 1] = ((self.V[self.v_x] % 100) // 10) #tens digit
        self.memory[self.I + 2] = (self.V[self.v_x] % 10) # ones digit
        self.pc += 2

    def ld_i_vx(self, opcode):
        '''
        Fx55 - LD [I], Vx
        Store registers V0-Vx from memory starting at location I.
        '''
        for registers in range(self.v_x + 1):
            self.memory[self.I + registers] = self.V[registers]
        # The original CHIP-8 increments I after execution
        self.I += self.v_x + 1
        self.pc += 2

    def ld_vx_i(self, opcode):
        '''
        Fx65 - LD Vx, [I]
        Read regisers V0-Vx from memory starting at location I.
        '''
        for registers in range(self.v_x + 1):
            self.V[registers] = self.memory[self.I + registers]
        # Increment I like the original interpreter for compatibility
        self.I += self.v_x + 1
        self.pc += 2


    def xF_dispatch(self, opcode):
        handler = self.instruction_dispatch.get(opcode & 0xF0FF)
        if handler:
            handler(opcode)
        else:
            print('Unknown/Invalid opcode ' + str(opcode))


