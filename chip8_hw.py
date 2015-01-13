#!/usr/bin/python


class chip8(object):
    def __init__(self):
        #chip8 has 4k of system ram
        '''Systems memory map:
        0x000-0x1FF - Chip 8 interpreter (contains font set in emu)
        0x050-0x0A0 - Used for the built in 4x5 pixel font set (0-F)
        0x200-0xFFF - Program ROM and work RAM
        '''
        self.memory = [0] * 4096

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

        #TODO: load font set.

    def emulate_cycle(self):
        #One opcode is 2 bytes long. We need to fetch two
        #sucessive bytes and merge them to get the full opcode
        #First we add 8 bits to the end so its 2bytes long, then merge the second
        #half
        opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1] 

        #Now that we have the opcode we need one big if statement to handle
        #all the various opcodes. Maybe this can be cleaned up later since python
        #has no 'switch' statement.

        #Some cases we cannot rely on the first 4 bits to see what an opcode does.
        #If the first 4 bits are all zero we must look at the second 4 bits.

        if (opcode & 0xF000) == 0x0000:
            #If the 4 first bits are zero...
            if (opcode & 0x000F) == 0x0000:
                #0x0000 == 0x00E0: Clears the screen
                #Assuming clearing sets all gfx bits to zero
                self.gfx = [0] * (64*32)
                self.pc += 2

            elif (opcode & 0x000F) == 0x000E:
                #0x000E == 0x00EE: returns from subroutine
                self.pc = self.stack.pop()
            #Ignore 0x0NNN it is not used.
            else:
                print('Unknown/Invalid opcode ' + str(opcode))
        elif (opcode & 0xF000) == 0x1000:
            #0x1000 == 0x1NNN Jump to location NNN
            self.pc = opcode & 0x0FFF
        elif (opcode & 0xF000) == 0x2000:
            #0x2000 == 0x2NNN CALL addr, call subroutine at NNN
            self.stack.append(self.pc)
            self.pc = opcode & 0x0FFF
        elif (opcode & 0xF000) == 0x3000:
            #0x3000 == 3xkk, Skip next instruction if Vx == kk.
            if self.V[opcode & ????] == opcode & 0x00FF:
                self.pc += 2
            else:
                self.pc += 1
        elif (opcode & 0xF000) == 0x4000:
            #0x4000 == 4xkk, Skip next instruction if Vx != kk.
            if self.V[stack_pointer] != opcode & 0x00FF:
                self
        elif (opcode & 0xF000) == 0xA000:
            #0xA000 == ANNN: Sets I to the address NNN
            self.I = opcode & 0x0FFF
            self.pc += 2
        else:
            print('Unknown/Invalid opcode ' + str(opcode))

     
        if self.delay_timer > 0:
            delay_timer -= 1
            if self.sound_timer == 1:
                #TODO: have sound and graphics
                print("BEEP!\n")
                self.sound -= 1



