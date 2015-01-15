#!/usr/bin/python

import random

class ChipEightCpu(object):
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

	#Vx and Vy are used very often here are some shortcuts
	v_x = (opcode & 0x0F00) >> 8
        v_y = (opcode & 0x00F0) >> 4
        #Some cases we cannot rely on the first 4 bits to see what an opcode does.
        #If the first 4 bits are all zero we must look at the second 4 bits.

        if (opcode & 0xF000) == 0x0000:
            #If the 4 first bits are zero...
            if (opcode & 0x000F) == 0x0000:
                #0x0000 == 0x00E0: Clears the screen
                #Assuming clearing sets all gfx bits to zero
                self.gfx = [0] * (64*32)
                self.pc += 2
                self.update_screen = True

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
            if self.V[x_v] == opcode & 0x00FF:
                self.pc += 4
            else:
		self.pc += 2
        elif (opcode & 0xF000) == 0x4000:
            #0x4000 == 4xkk, Skip next instruction if Vx != kk.
            if self.V[x_v] != opcode & 0x00FF:
                self.pc += 4
            else:
	        self.pc += 2
        elif (opcode & 0xF000) == 0x5000:
	    #0x5000 = 5xy0 SE, skip next instruction if Vx = Vy
            if self.V[x_v] == self.V[v_y]:
                self.pc += 4
            else:
                self.pc += 2
        elif (opcode & 0xF000) == 0x6000:
            #0x6000 = 6xkk put value kk in to register Vx
            self.V[x_v] = opcode & 0x00FF
            self.pc += 2
	elif (opcode & 0xF000) == 0x7000:
	    #0x7000 = 7xkk Add Vx. Add value kk to register Vx and store value
	    #in Vx
	    self.V[x_v] += opcode & 0x00FF 
	    self.pc += 2
	elif (opcode & 0xF000) == 0x8000 and (opcode & 0x000F) == 0x0:
	    #0x8000 = 8xy0 Set Vx = Vy
            self.V[x_v] = selv.V[x_y]
            self.pc += 2
        elif (opcode & 0xF000) == 0x8000 and (opcode & 0x000F) == 0x1:
            #8xy1 Set Vx = Vx or Vy
            self.V[x_v] = self.V[x_v] | self.V[x_y]
            self.pc += 2
        elif (opcode & 0xF000) == 0x8000 and (opcode & 0x000F) == 0x2:
            #8xy2 Set Vx = Vx and Vy
            self.V[x_v] = self.V[x_v] & self.V[x_y]
            self.pc += 2
        elif (opcode & 0xF000) == 0x8000 and (opcode & 0x000F) == 0x3:
            #8xy3 Set Vx = Vx XOR Vy
            self.V[x_v] = self.V[x_v] ^ self.V[x_y]
            self.pc += 2
        elif (opcode & 0xF000) == 0x8000 and (opcode & 0x000F) == 0x4:
            #8xy4 Set Vx = Vx + Vy set VF = carry is over 255
            #if the two value are over 8 bit (255) carry the result in VF
            if (self.V[x_v] + self.V[x_y]) > 0xFF:
                self.V[0xF] = 1
                self.V[x_v] += (self.V[x_y] & 0xFF)
            else:
                self.V[x_v] += self.V[x_y]
                self.V[0xF] = 0
            self.pc += 2
        elif (opcode & 0xF000) == 0x8000 and (opcode & 0x000F) == 0x5:
            #8xy5 - Sub Vx, Vy.
            #Set Vx = Vx - Vy, set Vf = if it does NOT borrow
            if (self.V[x_v] > self.V[x_y]):
                self.V[0xF] = 1 #NOT BORROW
            else:
                self.V[0xF] = 0 #Brrow
            self.V[x_v] -= self.V[x_y]
            self.pc += 2
        elif (opcode & 0xF000) == 0x8000 and (opcode & 0x000F) == 0x6:
            #8xy6 - SHR Vx {, Vy}
            #If the least significant bit of Vx is 1, set VF = 1
            #otherwise 0. Then divide Vx by 2
            if self.V[x_v] & 0b00000001 == 0b1:
                self.V[0xF] = 1
            else:
                self.V[0xF] = 0
            self.V[x_v] /= 2
            self.pc += 2
        elif (opcode & 0xF000) == 0x8000 and (opcode & 0x000F) == 0x7:
            #Set Vx = Vy - Vx, set VF = NOT BORROW
            if selv.V[x_y] > self.V[x_v]:
                self.V[0xF] = 1 #NOT BOROW
            else:
                self.V[0xF] = 0
            self.V[x_v] = selv.V[x_y] - self.V[x_v]
            self.pc += 2
        elif (opcode & 0xF000) == 0x8000 and (opcode & 0x000F) == 0xE:
            #8xyE - SHL Vx {, Vy}
            if (self.V[x_v] >> 7) == 1:
                self.V[0xF] = 1
            else:
                self.V[0xF] = 0
            self.V[x_v] = self.V[x_v] << 1
            self.pc += 2
        elif (opcode & 0xF000) == 0x9000:
            #9xy0 - SNE Vx, Vy
            #Skip next instruction if Vx != Vy
            if self.V[x_v] != selv.V[x_y]:
                self.pc += 4
            else:
                self.pc += 2
        elif (opcode & 0xF000) == 0xA000:
            #0xA000 == ANNN: Sets I to the address NNN
            self.I = opcode & 0x0FFF
            self.pc += 2
        elif (opcode & 0xF000) == 0xB000:
            #Bnnn - Jp V0, addr
            self.pc = (opcode & 0x0FFF) + self.V[0x0]
        elif (opcode & 0xF000) == 0xC000:
            #Cxkk - RND Vx, byte
            #Gen number between 0x0 and 0xFF and & it with the value of kk then
            #store in Vx
            self.V[x_v] = random.randrange(0x0, 0xFF) & (opcode & 0x00FF)
            self.pc += 2
        elif (opcode & 0xF000) == 0xD000:
            # DRW Vx, Vy. nibble
            drw_x = self.V[x_v]
            drw_y = self.V[x_y]
            drw_height = opcode & 0x000F
            sprite_data = []
            #set VF to zero because there has been no collision yet
            self.V[0xF] = 0
            #Read the sprite data from memory
            for x in xrange(drw_height):
                sprite_data.append(self.memory[self.I + x])
            for sprite_row in xrange(len(sprite_data)):
                #Sprites are always 8 pixels wide
                for pixel_offset in xrange(8):
                    location = drw_x + pixel_offset + ((drw_y + sprite_row) * 64)
                    if (drw_y + sprite_row) >= 32 or (drw_x + pixel_offset -1) >= 64:
                        #Don't do anything for pixels that are off the screen
                        #I think they should loop to the other side.
                        continue
                    drw_mask = 1 << 8 - pixel_offset
                    curr_pixel = (sprite_data[sprite_row] & mask) >> (8 - pixel_offset)
                    self.gfx[location] ^= curr_pixel
                    if self.gfx[location] == 0:
                        self.V[0xF] = 1
                    else:
                        self.V[0xF] = 0
            self.update_screen = True
	    self.pc += 2

        elif (opcode & 0xF000) == 0xE000 and (opcode & 0x000F) == 0xE:
	    #Ex9E - SKP Vx, skip next instruction if key is pressed.
	    if self.keys[v_x] == 1:
		self.pc += 4
	    else:
		self.pc += 2
        elif (opcode & 0xF000) == 0xE000 and (opcode & 0x000F) == 0x1:
	    #ExA1, SKNP Vx skip next instruction if key is NOT pressed.
	    if self.keys[v_x] != 1:
		self.pc += 4
	    else:
		self.pc += 2
        elif (opcode & 0xF000) == 0xF000 and (opcode & 0x000F) == 0x7:
	    #Fx07 set Vx = delay timer value
	    self.V[v_x] = self.delay_timer
	    self.pc += 2
        elif (opcode & 0xF000) == 0xF000 and (opcode & 0x000F) == 0xA:
	    #Fx0A wait for a key press and store value in Vx
	    key_wait_pressed = 0
	    for key in self.keys:
		if key == 1:
		    self.V[v_x] = 1
		    key_wait_pressed = 1
	    	    break
	    if key_wait_pressed == 1:
		self.pc += 2
        elif (opcode & 0xF000) == 0xF000 and (opcode & 0x00FF) == 0x15:
            #Fx15 - LD DT, Vx, set DT to the value of Vx.
            self.delay_timer = self.V[v_x]
            self.pc += 2
        elif (opcode & 0xF000) == 0xF000 and (opcode & 0x000F) == 0x8:
            #Fx18 Set sound timer = Vx
            self.sound_timer = self.V[v_x]
            self.pc += 2
        elif (opcode & 0xF000) == 0xF000 and (opcode & 0x000F) == 0xE:
            #Fx1E - ADD I, Vx
            #Set I = I + Vx
            self.I = self.I + self.V[v_x]
            self.pc += 2
        elif (opcode & 0xF000) == 0xF000 and (opcode & 0x000F) == 0x9:
            #Fx29 - LD F, Vx
            self.I = self.V[v_x]
            self.pc += 2
        elif (opcode & 0xF000) == 0xF000 and (opcode & 0x000F) == 0x3:
            #Fx33 - LD B, Vx
            #Store BCD rep of Vx in memory locaton I/I+1/I+2
            self.memory[self.I] = (self.V[v_x] / 100) #hundreds digit
            self.memory[self.I + 1] = ((self.V[v_x] % 100) / 10) #tens digit
            self.memory[self.I + 2] = (self.V[v_x] % 10) # ones digit
            self.pc += 2
        elif (opcode & 0xF000) == 0xF000 and (opcode & 0x00FF) == 0x55:
            #Fx55 - LD [I], Vx
            #Store registers V0-Vx from memory starting at location I
            for registers in xrange(v_x  + 1):
                self.memory[self.I + registers] = self.V[registers]
            self.pc += 2

        elif (opcode & 0xF000) == 0xF000 and (opcode & 0x00FF) == 0x65:
            for registers in xrange(v_x  + 1):
                self.V[registers] = self.memory[self.I + registers]
            self.pc += 2
        else:
            print('Unknown/Invalid opcode ' + str(opcode))

     
        if self.delay_timer > 0:
            delay_timer -= 1
            if self.sound_timer == 1:
                #TODO: have sound and graphics
                print("BEEP!\n")
                self.sound -= 1



