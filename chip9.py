import struct
import time
import os
import numpy as np
import matplotlib.pyplot as plt
import traceback


class Processor:
	A=0x00
	B=0x00
	C=0x00
	D=0x00
	E=0x00
	H=0x00
	L=0x00
	PC=0x0000
	SP=0xfffe
	F=[0,0,0,0,0,0,0,0]
	FlagPos={"Z":7,"N":6,"H":5,"C":4}
	RAM=[0x00 for i in range(65536)]
	Serial=0x00
	Last=""
	output=""
	printChar="a"
	updatesCount=0
	invalidInstr=[0x10,0xa0,0xb0,0x01,0x11,0x02,0x12,0x32,0x42,0xe2,0xf2,0xb3,0xe3,0xf3,0x87,0x97,0x98,0xd8,0xe8,0xf8,0x2e,0x3e,0x4e,0x5e,0x6e,0x7e,0x8e,0x9e,0xae,0xbe,0xce,0xde,0x8d,0x9d,0xad,0xbd,0xcd,0xdd]

	
	def carryFlag(self,num):
		self.F[self.FlagPos["C"]]=int((num&0x100)>0)
	
	def negativeFlag(self,num):
		self.F[self.FlagPos["N"]]=int((num&0x80)>0)
	
	def zeroFlag(self,num):
		self.F[self.FlagPos["Z"]]=int((num&0xff)==0)
	
	def hB0(self,byte):
		return byte&0xf0
	
	def hB1(self,byte):
		return byte&0x0f
	
	def signed(self,byte):
		if byte&0x80:
			return byte - 256
		else:
			return byte
	
	def extractBits(self,byte):
		t="{0:b}".format(byte)
		t="0"*(8-len(t))+t
		return [int(i) for i in t]
	
	def DRAW(self,screen):
		#signed X in (128) in C
		#signed Y (64) in B
		ycord=self.signed(self.C)
		xcord=self.signed(self.B)
		printBits=self.extractBits(self.A)
		for i in range(8):
			screen[xcord][i+ycord]=printBits[i]
		if self.updatesCount%16==0:
			plt.imshow(screen)
			plt.pause(0.0001)
		self.updatesCount+=1

	def CLRSCR(self,screen):
		screen=np.zeros((128,128))
		plt.imshow(screen)
		plt.pause(0.0001)
		# plt.show()
		# screen=[[0x00 for i in range(128)] for j in range(64)]
	
	def LDI(self,R,xx):
		R=xx
	
	def LDX(self,R1,R2,xx,yy):
		R1=xx
		R2=yy
		# return
	
	def PUSH(self,R):
		self.RAM[self.SP]=R
		self.SP=self.SP-2
	
	def PUSH2(self,R1,R2):
		self.RAM[self.SP]=R2
		self.RAM[self.SP+1]=R1
		self.SP=self.SP-2
	
	def POP(self,R):
		self.SP=self.SP+2
		R=self.RAM[self.SP]
		self.RAM[self.SP]=0
		self.RAM[self.SP+1]=0
		return R
	
	def POP2(self,R1,R2):
		self.SP=self.SP+2
		R1=self.RAM[self.SP+1]
		R2=self.RAM[self.SP]
		self.RAM[self.SP]=0
		self.RAM[self.SP+1]=0
		return R1,R2
	
	def CLRFLAG(self):
		self.F=[0,0,0,0,0,0,0,0]
	
	def SETFLAG(self,f,x):
		self.F[self.FlagPos[f]]=int(x>0)
	
	def ADD(self,R):
		half=((self.A&0xf)+(R&0xf))&0x10
		self.SETFLAG("H",half)
		R=R+self.A 
		carry=int(R>255)
		self.carryFlag(R)
		self.SETFLAG("C",carry)
		R=R&0xff
		self.negativeFlag(R)
		self.zeroFlag(R)
		return R
	
	def ADDI(self,xx):
		# half=(self.A&0xf+xx&0xf)&0x10
		half=((self.A&0xf)+(xx&0xf))&0x10
		self.SETFLAG("H",half)
		self.A=xx+self.A 
		carry=int(self.A>255)
		self.A=self.A&0xff
		self.SETFLAG("C",carry)
		# self.carryFlag(self.A)
		self.negativeFlag(self.A)
		self.zeroFlag(self.A)

	def ADDX(self,R1,R2):
		half=((self.A&0xf)+(R2&0xf))&0x10
		t=R1*256+R2+self.A
		R2=t&0xff
		R1=t&0xff00
		R1=R1//256
		carry=t&10000
		zero=int((R1==0)&(R2==0))
		self.negativeFlag(R1)
		self.SETFLAG("H",half)
		self.SETFLAG("C",carry)
		self.SETFLAG("Z",zero)
		return R1,R2

	
	def SUB(self,R):
		half=((R&0xf)-(self.A&0xf))&0x10
		self.SETFLAG("H",half)
		R=R-self.A
		self.carryFlag(R)
		R=R&0xff
		self.negativeFlag(R)
		self.zeroFlag(R)
		return R
	
	def SUBI(self,xx):
		half=((self.A&0xf)-(xx&0xf))&0x10
		self.SETFLAG("H",half)
		self.A=self.A-xx
		self.carryFlag(self.A)
		self.negativeFlag(self.A)
		self.A=self.A&0xff
		self.zeroFlag(self.A)
	
	def INC(self,R):
		half=((R&0xf)+(0x1&0xf))&0x10
		self.SETFLAG("H",half)
		R=R+1
		self.carryFlag(R)
		self.negativeFlag(R)
		R=R&0xff
		self.zeroFlag(R)
		return R
	
	def INX(self,R1,R2):
		t=(R1*256+R2+1)&0xffff
		R1=t//256
		R2=t&0xff
		return R1,R2
	
	def DEC(self,R):
		half=((R&0xf)-(0x1&0xf))&0x10
		self.SETFLAG("H",half)
		R=R-1
		self.carryFlag(R)
		R=R&0xff
		self.negativeFlag(R)
		self.zeroFlag(R)
		return R
	
	def AND(self,R):
		R=R&self.A
		self.SETFLAG("H",0)
		self.SETFLAG("C",0)
		self.negativeFlag(R)
		self.zeroFlag(R)
		return R
	
	def ANDI(self,xx):
		self.A=self.A&xx
		self.SETFLAG("H",0)
		self.SETFLAG("C",0)
		self.negativeFlag(self.A)
		self.zeroFlag(self.A)
	
	def OR(self,R):
		R=R|self.A
		self.SETFLAG("H",0)
		self.SETFLAG("C",0)
		self.negativeFlag(R)
		self.zeroFlag(R)
		return R
	
	def ORI(self,xx):
		self.A=self.A|xx
		self.SETFLAG("H",0)
		self.SETFLAG("C",0)
		self.negativeFlag(self.A)
		self.zeroFlag(self.A)
	
	def XOR(self,R):
		R=R^self.A	
		self.SETFLAG("H",0)
		self.SETFLAG("C",0)
		self.negativeFlag(R)
		self.zeroFlag(R)	
		return R
	
	def XORI(self,xx):
		self.A=self.A^xx
		self.SETFLAG("H",0)
		self.SETFLAG("C",0)
		self.negativeFlag(self.A)
		self.zeroFlag(self.A)
	
	def CMP(self,R):
		self.SUB(R)

	
	def CMPI(self,xx):
		self.CMP(xx)
	
	def CMPS(self,R):
		if self.signed(R)==self.signed(self.A):
			self.SETFLAG("Z",1)
		elif self.signed(R)<self.signed(self.A):
			self.SETFLAG("Z",0)
			self.SETFLAG("N",1)
		else:
			self.SETFLAG("Z",0)
			self.SETFLAG("N",0)
	
	def SIN(self,Serial):
		self.A=Serial
	
	def SOUT(self):
		self.printChar=chr(self.A)
		print(self.printChar,end="")
		self.output+=self.printChar
	
	def JMP(self,xx,yy):
		self.PC=xx*256+yy
	
	def JMPC(self,f,cc,xx,yy):
		if self.F[self.FlagPos[f]]==cc:
			self.PC=xx*256+yy
		else:
			self.PC+=3
	
	def JMPNear(self,xx):
		self.PC+=2
		self.PC+=self.signed(xx)
	
	def JMPNearC(self,f,cc,xx):
		self.PC+=2
		if self.F[self.FlagPos[f]]==cc:
			self.PC+=self.signed(xx)
		
	
	def CALL(self,xx,yy):
		self.PC+=3
		self.PUSH2(self.PC//256,self.PC&0xff)
		self.PC=xx*256+yy
	
	def RET(self):
		self.SP=self.SP+2
		a=self.RAM[self.SP+1]
		b=self.RAM[self.SP]
		self.RAM[self.SP]=0
		self.RAM[self.SP+1]=0
		self.PC=a*256+b
	
	def HCF(self):
		input("THE MACHINE IS BURNING!!!!!")

	def DisplayState(self):
		print("LastInst:",self.Last, "\tCHR=",self.printChar)
		print("A:",hex(self.A),"\tB:",hex(self.B),"\tC:",hex(self.C),"\tD:",hex(self.D),"\tE:",hex(self.E),"\tH:",hex(self.H),"\tL:",hex(self.L),"\t[HL]",hex(self.RAM[self.H*256+self.L]),"\tF",self.F)
		print("PC:",hex(self.PC),"\tSP:",hex(self.SP),"\tinstr:",hex(self.RAM[self.PC]),hex(self.RAM[self.PC+1]),hex(self.RAM[self.PC+2]),"\n")

	def DisplayRAM(self,addr,num):
		print([hex(i)[2:] for i in self.RAM[addr:addr+num]])

	def DisplayStack(self,x):
		for i in range(x):
			t=self.SP+2*i
			u=self.SP+2*i+1
			if t< 65536:
				print("stack addr:",hex(t),hex(u),"\tval",hex(self.RAM[t]),hex(self.RAM[u]))



def ParseInst(byte1,byte2,byte3,proc,screen):	
	v=byte1&0x0f
	if v==0x0:
		if byte1 == 0x00 :
			#proc.Last="NOP"
			proc.PC+=1
		elif byte1 == 0x20 :
			# proc.LDI(proc.B,byte2)
			#proc.Last="LDI "+"B "+hex(byte2)
			proc.B=byte2
			proc.PC+=2
		elif byte1 == 0x30 :
			# proc.LDI(proc.C,byte2)
			#proc.Last="LDI "+"C "+hex(byte2)
			proc.C=byte2
			proc.PC+=2
		elif byte1 == 0x40 :
			#proc.Last="LDI "+"D "+hex(byte2)
			# proc.LDI(proc.D,byte2)
			proc.D=byte2
			proc.PC+=2
		elif byte1 == 0x50 :
			#proc.Last="LDI "+"E "+hex(byte2)
			# proc.LDI(proc.E,byte2)
			proc.E=byte2
			proc.PC+=2
		elif byte1 == 0x60 :
			#proc.Last="LDI "+"H "+hex(byte2)
			# proc.LDI(proc.H,byte2)
			proc.H=byte2
			proc.PC+=2
		elif byte1 == 0x70 :
			#proc.Last="LDI "+"L "+hex(byte2)
			# proc.LDI(proc.L,byte2)
			proc.L=byte2
			proc.PC+=2
		elif byte1 == 0x80 :
			#proc.Last="LDI "+"[HL] "+hex(byte2)
			proc.RAM[proc.H*256+proc.L]=byte2
			proc.PC+=2
		elif byte1 == 0x90 :
			#proc.Last="LDI "+"A "+hex(byte2)
			proc.A=byte2
			proc.PC+=2
		elif byte1 == 0xc0 :
			#proc.Last="PUSH "+"[HL]"
			proc.PUSH(proc.RAM[proc.H*256+proc.L])
			proc.PC+=1
		elif byte1 == 0xd0 :
			#proc.Last="PUSH "+"A"
			proc.PUSH(proc.A)
			proc.PC+=1
		elif byte1 == 0xe0 :
			#proc.Last="SIN"
			# proc.SIN(proc.A)
			proc.PC+=1
		elif byte1 == 0xf0 :
			#proc.Last="CLRSCR"
			proc.CLRSCR(screen)
			proc.PC+=1
	
	elif v==0x1:
		if byte1 == 0x21 :
			#proc.Last="LDX "+"BC "+hex(byte3)+" "+hex(byte2)
			# proc.LDX(proc.B,proc.C,byte3,byte2)
			# print(byte3,byte2,proc.B,proc.C)
			proc.B=byte3
			proc.C=byte2
			# print(byte3,byte2,proc.B,proc.C)
			proc.PC+=3
		elif byte1 == 0x31 :
			# proc.LDX(proc.D,proc.E,byte3,byte2)
			#proc.Last="LDX "+"DE "+hex(byte3)+" "+hex(byte2)
			proc.D,proc.E=byte3,byte2
			proc.PC+=3
		elif byte1 == 0x41 :
			# proc.LDX(proc.H,proc.L,byte3,byte2)
			#proc.Last="LDX "+"HL "+hex(byte3)+" "+hex(byte2)
			proc.H=byte3
			proc.L=byte2
			# print(byte3,byte2,proc.H,proc.L)
			proc.PC+=3
		elif byte1 == 0x51 :
			#proc.Last="PUSH "+"B C"
			proc.PUSH2(proc.B,proc.C)
			proc.PC+=1
		elif byte1 == 0x61 :
			#proc.Last="PUSH "+"D E"			
			proc.PUSH2(proc.D,proc.E)
			proc.PC+=1
		elif byte1 == 0x71 :
			proc.PUSH2(proc.H,proc.L)
			#proc.Last="PUSH "+"H L"
			proc.PC+=1
		elif byte1 == 0x81 :
			#proc.Last="PUSH "+"B"
			proc.PUSH(proc.B)
			proc.PC+=1
		elif byte1 == 0x91 :
			#proc.Last="PUSH "+"C"
			proc.PUSH(proc.C)
			proc.PC+=1
		elif byte1 == 0xa1 :
			#proc.Last="PUSH "+"D"
			proc.PUSH(proc.D)
			proc.PC+=1
		elif byte1 == 0xb1 :
			#proc.Last="PUSH "+"E"
			proc.PUSH(proc.E)
			proc.PC+=1
		elif byte1 == 0xc1 :
			#proc.Last="PUSH "+"H"
			proc.PUSH(proc.H)
			proc.PC+=1
		elif byte1 == 0xd1 :
			proc.PUSH(proc.L)
			#proc.Last="PUSH "+"L"
			proc.PC+=1
		elif byte1 == 0xe1 :
			#proc.Last="SOUT"
			proc.SOUT()
			proc.PC+=1
		elif byte1 == 0xf1 :
			#proc.Last="DRAW"
			proc.DRAW(screen)
			proc.PC+=1
	
	elif v==0x2:
		if byte1 == 0x22 :
			#proc.Last="LDX SP"+hex(byte3)+" "+hex(byte2)
			proc.SP=byte3*256+byte2
			proc.PC+=3
		elif byte1 == 0x52 :
			#proc.Last="POP B C"
			proc.B,proc.C=proc.POP2(proc.B,proc.C)
			proc.PC+=1
		elif byte1 == 0x62 :
			#proc.Last="POP D E"
			proc.D,proc.E=proc.POP2(proc.D,proc.E)
			proc.PC+=1
		elif byte1 == 0x72 :
			#proc.Last="POP H L"
			proc.D,proc.E=proc.POP2(proc.H,proc.L)
			proc.PC+=1
		elif byte1 == 0x82 :
			#proc.Last="POP B "
			proc.B=proc.POP(proc.B)
			proc.PC+=1
		elif byte1 == 0x92 :
			#proc.Last="POP C"
			proc.C=proc.POP(proc.C)
			proc.PC+=1
		elif byte1 == 0xa2 :
			#proc.Last="POP D"
			proc.D=proc.POP(proc.D)
			proc.PC+=1
		elif byte1 == 0xb2 :
			#proc.Last="POP E"
			proc.E=proc.POP(proc.E)
			proc.PC+=1
		elif byte1 == 0xc2 :
			#proc.Last="POP H"
			proc.H=proc.POP(proc.H)
			proc.PC+=1
		elif byte1 == 0xd2 :
			#proc.Last="POP L"
			proc.L=proc.POP(proc.L)
			proc.PC+=1
	
	elif v==0x3:
		if byte1 == 0x03 :
			#proc.Last="INC B"
			proc.B=proc.INC(proc.B)
			proc.PC+=1
		elif byte1 == 0x13 :
			#proc.Last="INC C"
			proc.C=proc.INC(proc.C)
			proc.PC+=1
		elif byte1 == 0x23 :
			#proc.Last="INC D"
			proc.D=proc.INC(proc.D)
			proc.PC+=1
		elif byte1 == 0x33 :
			#proc.Last="INC E"
			proc.E=proc.INC(proc.E)
			proc.PC+=1
		elif byte1 == 0x43 :
			#proc.Last="INC H"
			proc.H=proc.INC(proc.H)
			proc.PC+=1
		elif byte1 == 0x53 :
			proc.INC(proc.L)
			#proc.Last="INC L"
			proc.PC+=1
		elif byte1 == 0x63 :
			#proc.Last="INC [HL]"
			proc.RAM[proc.H*256+proc.L]=proc.INC(proc.RAM[proc.H*256+proc.L])
			proc.PC+=1
		elif byte1 == 0x73 :
			#proc.Last="INC A"
			proc.A=proc.INC(proc.A)
			proc.PC+=1
		elif byte1 == 0x83 :
			#proc.Last="ADDX B C"
			proc.B,proc.C=proc.ADDX(proc.B,proc.C)
			proc.PC+=1
		elif byte1 == 0x93 :
			#proc.Last="ADDX D E"
			proc.D,proc.E=proc.ADDX(proc.D,proc.E)
			proc.PC+=1
		elif byte1 == 0xa3 :
			#proc.Last="ADDX H L"
			proc.H,proc.L=proc.ADDX(proc.H,proc.L)
			proc.PC+=1
		elif byte1 == 0xc3 :
			#proc.Last="POP [HL]"
			proc.RAM[proc.H*256+proc.L]=proc.POP(a)
			proc.PC+=1
		elif byte1 == 0xd3 :
			#proc.Last="POP A"
			proc.POP(proc.A)
			proc.PC+=1
	
	elif v==0x4:
		if byte1 == 0x04 :
			#proc.Last="ADD B"
			proc.B=proc.ADD(proc.B)
			proc.PC+=1
		elif byte1 == 0x14 :
			#proc.Last="ADD C"
			proc.C=proc.ADD(proc.C)
			proc.PC+=1
		elif byte1 == 0x24 :
			#proc.Last="ADD D"
			proc.D=proc.ADD(proc.D)
			proc.PC+=1
		elif byte1 == 0x34 :
			#proc.Last="ADD E"
			proc.E=proc.ADD(proc.E)
			proc.PC+=1
		elif byte1 == 0x44 :
			#proc.Last="ADD H"
			proc.H=proc.ADD(proc.H)
			proc.PC+=1
		elif byte1 == 0x54 :
			#proc.Last="ADD L"
			proc.L=proc.ADD(proc.L)
			proc.PC+=1
		elif byte1 == 0x64 :
			#proc.Last="ADD [HL]"
			proc.RAM[proc.H*256+proc.L]=proc.ADD(proc.RAM[proc.H*256+proc.L])
			proc.PC+=1
		elif byte1 == 0x74 :
			#proc.Last="ADD A"
			proc.A=proc.ADD(proc.A)
			proc.PC+=1
		elif byte1 == 0x84 :
			#proc.Last="SUB B"
			proc.B=proc.SUB(proc.B)
			proc.PC+=1
		elif byte1 == 0x94 :
			#proc.Last="SUB C"
			proc.C=proc.SUB(proc.C)
			proc.PC+=1
		elif byte1 == 0xa4 :
			#proc.Last="SUB D"
			proc.D=proc.SUB(proc.D)
			proc.PC+=1
		elif byte1 == 0xb4 :
			#proc.Last="SUB E"
			proc.E=proc.SUB(proc.E)
			proc.PC+=1
		elif byte1 == 0xc4 :
			#proc.Last="SUB H"
			proc.H=proc.SUB(proc.H)
			proc.PC+=1
		elif byte1 == 0xd4 :
			#proc.Last="SUB L"
			proc.L=proc.SUB(proc.L)
			proc.PC+=1
		elif byte1 == 0xe4 :
			#proc.Last="SUB [HL]"
			proc.RAM[proc.H*256+proc.L]=proc.SUB(proc.RAM[proc.H*256+proc.L])
			proc.PC+=1
		elif byte1 == 0xf4 :
			#proc.Last="SUB A"
			proc.A=proc.SUB(proc.A)
			proc.PC+=1
	
	elif v==0x5:
		if byte1 == 0x05 :
			#proc.Last="AND B"
			proc.B=proc.AND(proc.B)
			proc.PC+=1
		elif byte1 == 0x15 :
			#proc.Last="AND C"
			proc.C=proc.AND(proc.C)
			proc.PC+=1
		elif byte1 == 0x25 :
			#proc.Last="AND D"
			proc.D=proc.AND(proc.D)
			proc.PC+=1
		elif byte1 == 0x35 :
			#proc.Last="AND E"
			proc.E=proc.AND(proc.E)
			proc.PC+=1
		elif byte1 == 0x45 :
			#proc.Last="AND H"
			proc.H=proc.AND(proc.H)
			proc.PC+=1
		elif byte1 == 0x55 :
			#proc.Last="AND L"
			proc.L=proc.AND(proc.L)
			proc.PC+=1
		elif byte1 == 0x65 :
			#proc.Last="AND [HL]"
			proc.RAM[proc.H*256+proc.L]=proc.AND(proc.RAM[proc.H*256+proc.L])
			proc.PC+=1
		elif byte1 == 0x75 :
			#proc.Last="AND A"
			proc.A=proc.AND(proc.A)
			proc.PC+=1
		elif byte1 == 0x85 :
			#proc.Last="OR B"
			proc.B=proc.OR(proc.B)
			proc.PC+=1
		elif byte1 == 0x95 :
			#proc.Last="OR C"
			proc.C=proc.OR(proc.C)
			proc.PC+=1
		elif byte1 == 0xa5 :
			#proc.Last="OR D"
			proc.D=proc.OR(proc.D)
			proc.PC+=1
		elif byte1 == 0xb5 :
			#proc.Last="OR E"
			proc.E=proc.OR(proc.E)
			proc.PC+=1
		elif byte1 == 0xc5 :
			#proc.Last="OR H"
			proc.H=proc.OR(proc.H)
			proc.PC+=1
		elif byte1 == 0xd5 :
			#proc.Last="OR L"
			proc.L=proc.OR(proc.L)
			proc.PC+=1
		elif byte1 == 0xe5 :
			#proc.Last="OR [HL]"
			proc.RAM[proc.H*256+proc.L]=proc.OR(proc.RAM[proc.H*256+proc.L])
			proc.PC+=1
		elif byte1 == 0xf5 :
			#proc.Last="OR A"
			proc.A=proc.OR(proc.A)
			proc.PC+=1
	
	elif v==0x6:
		if byte1 == 0x06 :
			#proc.Last="XOR B"
			proc.B=proc.XOR(proc.B)
			proc.PC+=1
		elif byte1 == 0x16 :
			#proc.Last="XOR C"
			proc.C=proc.XOR(proc.C)
			proc.PC+=1
		elif byte1 == 0x26 :
			#proc.Last="XOR D"
			proc.D=proc.XOR(proc.D)
			proc.PC+=1
		elif byte1 == 0x36 :
			#proc.Last="XOR E"
			proc.E=proc.XOR(proc.E)
			proc.PC+=1
		elif byte1 == 0x46 :
			#proc.Last="XOR H"
			proc.H=proc.XOR(proc.H)
			proc.PC+=1
		elif byte1 == 0x56 :
			#proc.Last="XOR L"
			proc.L=proc.XOR(proc.L)
			proc.PC+=1
		elif byte1 == 0x66 :
			#proc.Last="XOR [HL]"
			proc.RAM[proc.H*256+proc.L]=proc.XOR(proc.RAM[proc.H*256+proc.L])
			proc.PC+=1
		elif byte1 == 0x76 :
			#proc.Last="XOR A"
			proc.A=proc.XOR(proc.A)
			proc.PC+=1
		elif byte1 == 0x86 :
			#proc.Last="CMP B"
			proc.CMP(proc.B)
			proc.PC+=1
		elif byte1 == 0x96 :
			#proc.Last="CMP C"
			proc.CMP(proc.C)
			proc.PC+=1
		elif byte1 == 0xa6 :
			#proc.Last="CMP D"
			proc.CMP(proc.D)
			proc.PC+=1
		elif byte1 == 0xb6 :
			#proc.Last="CMP E"
			proc.CMP(proc.E)
			proc.PC+=1
		elif byte1 == 0xc6 :
			#proc.Last="CMP H"
			proc.CMP(proc.H)
			proc.PC+=1
		elif byte1 == 0xd6 :
			#proc.Last="CMP L"
			proc.CMP(proc.L)
			proc.PC+=1
		elif byte1 == 0xe6 :
			#proc.Last="CMP [HL]"
			proc.CMP(proc.RAM[proc.H*256+proc.L])
			proc.PC+=1
		elif byte1 == 0xf6 :
			#proc.Last="CMP A"
			proc.CMP(proc.A)
			proc.PC+=1
	
	elif v==0x7:
		if byte1 == 0x07 :
			#proc.Last="DEC B"
			proc.B=proc.DEC(proc.B)
			proc.PC+=1
		elif byte1 == 0x17 :
			#proc.Last="DEC C"
			proc.C=proc.DEC(proc.C)
			proc.PC+=1
		elif byte1 == 0x27 :
			#proc.Last="DEC D"
			proc.D=proc.DEC(proc.D)
			proc.PC+=1
		elif byte1 == 0x37 :
			#proc.Last="DEC E"
			proc.E=proc.DEC(proc.E)
			proc.PC+=1
		elif byte1 == 0x47 :
			#proc.Last="DEC H"
			proc.H=proc.DEC(proc.H)
			proc.PC+=1
		elif byte1 == 0x57 :
			#proc.Last="DEC L"
			proc.L=proc.DEC(proc.L)
			proc.PC+=1
		elif byte1 == 0x67 :
			#proc.Last="DEC [HL]"
			proc.RAM[proc.H*256+proc.L]=proc.DEC(proc.RAM[proc.H*256+proc.L])
			proc.PC+=1
		elif byte1 == 0x77 :
			#proc.Last="DEC A"
			proc.A=proc.DEC(proc.A)
			proc.PC+=1
		elif byte1 == 0xa7 :
			#proc.Last="ADDI "+hex(byte2)
			proc.ADDI(byte2)
			proc.PC+=2
		elif byte1 == 0xb7 :
			#proc.Last="SUBI "+hex(byte2)
			proc.SUBI(byte2)
			proc.PC+=2
		elif byte1 == 0xc7 :
			#proc.Last="ANDI "+hex(byte2)
			proc.ANDI(byte2)
			proc.PC+=2
		elif byte1 == 0xd7 :
			#proc.Last="ORI "+hex(byte2)
			proc.ORI(byte2)
			proc.PC+=2
		elif byte1 == 0xe7 :
			#proc.Last="XORI "+hex(byte2)
			proc.XORI(byte2)
			proc.PC+=2
		elif byte1 == 0xf7 :
			#proc.Last="CMPI "+hex(byte2)
			proc.CMPI(byte2)
			proc.PC+=2
	
	elif v==0x8:
		if byte1 == 0x08 :
			#proc.Last="CLRFLAG"
			proc.CLRFLAG()
			proc.PC+=1
		elif byte1 == 0x18 :
			#proc.Last="SETFLAG Z 1"
			proc.SETFLAG("Z",1)
			proc.PC+=1
		elif byte1 == 0x28 :
			#proc.Last="SETFLAG Z 0"
			proc.SETFLAG("Z",0)
			proc.PC+=1
		elif byte1 == 0x38 :
			#proc.Last="SETFLAG N 1"
			proc.SETFLAG("N",1)
			proc.PC+=1
		elif byte1 == 0x48 :
			#proc.Last="SETFLAG N 0"
			proc.SETFLAG("N",0)
			proc.PC+=1
		elif byte1 == 0x58 :
			#proc.Last="SETFLAG H 1"
			proc.SETFLAG("H",1)
			proc.PC+=1
		elif byte1 == 0x68 :
			#proc.Last="SETFLAG H 0"
			proc.SETFLAG("H",0)
			proc.PC+=1
		elif byte1 == 0x78 :
			#proc.Last="SETFLAG C 1"
			proc.SETFLAG("C",1)
			proc.PC+=1
		elif byte1 == 0x88 :
			#proc.Last="SETFLAG C 0"
			proc.SETFLAG("C",0)
			proc.PC+=1
		elif byte1 == 0xa8 :
			#proc.Last="INX BC"
			proc.B,proc.C=proc.INX(proc.B,proc.C)
			proc.PC+=1
		elif byte1 == 0xb8 :
			#proc.Last="INX DE"
			proc.D,proc.E=proc.INX(proc.D,proc.E)
			proc.PC+=1
		elif byte1 == 0xc8 :
			#proc.Last="INX HL"
			proc.H,proc.L=proc.INX(proc.H,proc.L)
			proc.PC+=1
	
	elif v==0x9:
		if byte1 == 0x09 :
			#proc.Last="MOV B B"
			proc.B=proc.B
			proc.PC+=1
		elif byte1 == 0x19 :
			#proc.Last="MOV B C"
			proc.B=proc.C
			proc.PC+=1
		elif byte1 == 0x29 :
			#proc.Last="MOV B D"
			proc.B=proc.D
			proc.PC+=1
		elif byte1 == 0x39 :
			#proc.Last="MOV B E"
			proc.B=proc.E
			proc.PC+=1
		elif byte1 == 0x49 :
			#proc.Last="MOV B H"
			proc.B=proc.H
			proc.PC+=1
		elif byte1 == 0x59 :
			#proc.Last="MOV B L"
			proc.B=proc.L
			proc.PC+=1
		elif byte1 == 0x69 :
			#proc.Last="MOV B [HL]"
			proc.B=proc.RAM[proc.H*256+proc.L]
			proc.PC+=1
		elif byte1 == 0x79 :
			#proc.Last="MOV B A"
			proc.B=proc.A
			proc.PC+=1
		elif byte1 == 0x89 :
			#proc.Last="MOV C B"
			proc.C=proc.B
			proc.PC+=1
		elif byte1 == 0x99 :
			#proc.Last="MOV C C"
			proc.C=proc.C
			proc.PC+=1
		elif byte1 == 0xa9 :
			#proc.Last="MOV C D"
			proc.C=proc.D
			proc.PC+=1
		elif byte1 == 0xb9 :
			#proc.Last="MOV C E"
			proc.C=proc.E
			proc.PC+=1
		elif byte1 == 0xc9 :
			#proc.Last="MOV C H"
			proc.C=proc.H
			proc.PC+=1
		elif byte1 == 0xd9 :
			#proc.Last="MOV C L"
			proc.C=proc.L
			proc.PC+=1
		elif byte1 == 0xe9 :
			#proc.Last="MOV C [HL]"
			proc.C=proc.RAM[proc.H*256+proc.L]
			proc.PC+=1
		elif byte1 == 0xf9 :
			#proc.Last="MOV C A"
			proc.C=proc.A
			proc.PC+=1
	
	elif v==0xa:
		if byte1 == 0x0a :
			#proc.Last="MOV D B"
			proc.D=proc.B
			proc.PC+=1
		elif byte1 == 0x1a :
			#proc.Last="MOV D C"
			proc.D=proc.C
			proc.PC+=1
		elif byte1 == 0x2a :
			#proc.Last="MOV D D"
			proc.D=proc.D
			proc.PC+=1
		elif byte1 == 0x3a :
			#proc.Last="MOV D E"
			proc.D=proc.E
			proc.PC+=1
		elif byte1 == 0x4a :
			#proc.Last="MOV D H"
			proc.D=proc.H
			proc.PC+=1
		elif byte1 == 0x5a :
			#proc.Last="MOV D L"
			proc.D=proc.L
			proc.PC+=1
		elif byte1 == 0x6a :
			#proc.Last="MOV D [HL]"
			proc.D=proc.RAM[proc.H*256+proc.L]
			proc.PC+=1
		elif byte1 == 0x7a :
			#proc.Last="MOV D A"
			proc.D=proc.A
			proc.PC+=1
		elif byte1 == 0x8a :
			#proc.Last="MOV E B"
			proc.E=proc.B
			proc.PC+=1
		elif byte1 == 0x9a :
			#proc.Last="MOV E C"
			proc.E=proc.C
			proc.PC+=1
		elif byte1 == 0xaa :
			#proc.Last="MOV E D"
			proc.E=proc.D
			proc.PC+=1
		elif byte1 == 0xba :
			#proc.Last="MOV E E"
			proc.E=proc.E
			proc.PC+=1
		elif byte1 == 0xca :
			#proc.Last="MOV E H"
			proc.E=proc.H
			proc.PC+=1
		elif byte1 == 0xda :
			#proc.Last="MOV E L"
			proc.E=proc.L
			proc.PC+=1
		elif byte1 == 0xea :
			#proc.Last="MOV E [HL]"
			proc.E=proc.RAM[proc.H*256+proc.L]
			proc.PC+=1
		elif byte1 == 0xfa :
			#proc.Last="MOV E A"
			proc.E=proc.A
			proc.PC+=1
	
	elif v==0xb:
		if byte1 == 0x0b :
			#proc.Last="MOV H B"
			proc.H=proc.B
			proc.PC+=1
		elif byte1 == 0x1b :
			#proc.Last="MOV H C"
			proc.H=proc.C
			proc.PC+=1
		elif byte1 == 0x2b :
			#proc.Last="MOV H D"
			proc.H=proc.D
			proc.PC+=1
		elif byte1 == 0x3b :
			#proc.Last="MOV H E"
			proc.H=proc.E
			proc.PC+=1
		elif byte1 == 0x4b :
			#proc.Last="MOV H H"
			proc.H=proc.H
			proc.PC+=1
		elif byte1 == 0x5b :
			#proc.Last="MOV H L"
			proc.H=proc.L
			proc.PC+=1
		elif byte1 == 0x6b :
			#proc.Last="MOV H [HL]"
			proc.H=proc.RAM[proc.H*256+proc.L]
			proc.PC+=1
		elif byte1 == 0x7b :
			#proc.Last="MOV H A"
			proc.H=proc.A
			proc.PC+=1
		elif byte1 == 0x8b :
			#proc.Last="MOV L B"
			proc.L=proc.B
			proc.PC+=1
		elif byte1 == 0x9b :
			#proc.Last="MOV L C"
			proc.L=proc.C
			proc.PC+=1
		elif byte1 == 0xab :
			#proc.Last="MOV L D"
			proc.L=proc.D
			proc.PC+=1
		elif byte1 == 0xbb :
			#proc.Last="MOV L E"
			proc.L=proc.E
			proc.PC+=1
		elif byte1 == 0xcb :
			#proc.Last="MOV L H"
			proc.L=proc.H
			proc.PC+=1
		elif byte1 == 0xdb :
			#proc.Last="MOV L L"
			proc.L=proc.L
			proc.PC+=1
		elif byte1 == 0xeb :
			#proc.Last="MOV L [HL]"
			proc.L=proc.RAM[proc.H*256+proc.L]
			proc.PC+=1
		elif byte1 == 0xfb :
			#proc.Last="MOV L A"
			proc.L=proc.A
			proc.PC+=1
	
	elif v==0xc:
		if byte1 == 0x0c :
			#proc.Last="MOV [HL] B"
			proc.RAM[proc.H*256+proc.L]=proc.B
			proc.PC+=1
		elif byte1 == 0x1c :
			#proc.Last="MOV [HL] C"
			proc.RAM[proc.H*256+proc.L]=proc.C
			proc.PC+=1
		elif byte1 == 0x2c :
			#proc.Last="MOV [HL] D"
			proc.RAM[proc.H*256+proc.L]=proc.D
			proc.PC+=1
		elif byte1 == 0x3c :
			#proc.Last="MOV [HL] E"
			proc.RAM[proc.H*256+proc.L]=proc.E
			proc.PC+=1
		elif byte1 == 0x4c :
			#proc.Last="MOV [HL] H"
			proc.RAM[proc.H*256+proc.L]=proc.H
			proc.PC+=1
		elif byte1 == 0x5c :
			#proc.Last="MOV [HL] L"
			proc.RAM[proc.H*256+proc.L]=proc.L
			proc.PC+=1
		elif byte1 == 0x6c :
			#proc.Last="HCF"
			proc.HCF()
		elif byte1 == 0x7c :
			#proc.Last="MOV [HL] A"
			proc.RAM[proc.H*256+proc.L]=proc.A
			proc.PC+=1
		elif byte1 == 0x8c :
			#proc.Last="MOV A B"
			proc.A=proc.B
			proc.PC+=1
		elif byte1 == 0x9c :
			#proc.Last="MOV A C"
			proc.A=proc.C
			proc.PC+=1
		elif byte1 == 0xac :
			#proc.Last="MOV A D"
			proc.A=proc.D
			proc.PC+=1
		elif byte1 == 0xbc :
			#proc.Last="MOV A E"
			proc.A=proc.E
			proc.PC+=1
		elif byte1 == 0xcc :
			#proc.Last="MOV A H"
			proc.A=proc.H
			proc.PC+=1
		elif byte1 == 0xdc :
			#proc.Last="MOV A L"
			proc.A=proc.L
			proc.PC+=1
		elif byte1 == 0xec :
			#proc.Last="MOV A [HL]"
			proc.A=proc.RAM[proc.H*256+proc.L]
			proc.PC+=1
		elif byte1 == 0xfc :
			#proc.Last="MOV A A"
			proc.A=proc.A
			proc.PC+=1
	
	elif v==0xd:
		if byte1 == 0x0d :
			#proc.Last="CMPS B"
			proc.CMPS(proc.B)
			proc.PC+=1
		elif byte1 == 0x1d :
			#proc.Last="CMPS C"
			proc.CMPS(proc.C)
			proc.PC+=1
		elif byte1 == 0x2d :
			#proc.Last="CMPS D"
			proc.CMPS(proc.D)
			proc.PC+=1
		elif byte1 == 0x3d :
			#proc.Last="CMPS E"
			proc.CMPS(proc.E)
			proc.PC+=1
		elif byte1 == 0x4d :
			#proc.Last="CMPS H"
			proc.CMPS(proc.H)
			proc.PC+=1
		elif byte1 == 0x5d :
			#proc.Last="CMPS L"
			proc.CMPS(proc.L)
			proc.PC+=1
		elif byte1 == 0x6d :
			#proc.Last="CMPS [HL]"
			proc.CMPS(proc.RAM[proc.H*256+proc.L])
			proc.PC+=1
		elif byte1 == 0x7d :
			#proc.Last="CMPS A"
			proc.CMPS(proc.A)
			proc.PC+=1
		elif byte1 == 0xed :
			#proc.Last="MOV HL BC"
			proc.H,proc.L=proc.B,proc.C
			proc.PC+=1
		elif byte1 == 0xfd :
			#proc.Last="MOV HL DE"
			proc.H,proc.L=proc.D,proc.E
			proc.PC+=1
	
	elif v==0xe:
		if byte1 == 0x0e :
			#proc.Last="RET"
			# proc.RET()
			proc.SP=proc.SP+2
			a=proc.RAM[proc.SP+1]
			b=proc.RAM[proc.SP]
			proc.PC=a*256+b
		elif byte1 == 0x1e :
			#proc.Last="CALL "+hex(byte3)+" "+hex(byte2)
			proc.CALL(byte3,byte2)
		elif byte1 == 0xee :
			#proc.Last="JMPC "+hex(byte3)+" "+hex(byte2)
			proc.JMPNearC("C",1,byte2)
		elif byte1 == 0xfe :
			#proc.Last="JMPNC "+hex(byte3)+" "+hex(byte2)
			proc.JMPNearC("C",0,byte2)
	
	elif v==0xf:
		if byte1 == 0x0f :
			#proc.Last="JMP "+hex(byte3)+" "+hex(byte2)
			proc.JMP(byte3,byte2)
		elif byte1 == 0x1f :
			#proc.Last="JMPZ "+hex(byte3)+" "+hex(byte2)
			proc.JMPC("Z",1,byte3,byte2)
		elif byte1 == 0x2f :
			#proc.Last="JMPNZ "+hex(byte3)+" "+hex(byte2)
			proc.JMPC("Z",0,byte3,byte2)
		elif byte1 == 0x3f :
			#proc.Last="JMPN "+hex(byte3)+" "+hex(byte2)
			proc.JMPC("N",1,byte3,byte2)
		elif byte1 == 0x4f :
			#proc.Last="JMPNN "+hex(byte3)+" "+hex(byte2)
			proc.JMPC("N",0,byte3,byte2)
		elif byte1 == 0x5f :
			#proc.Last="JMPH "+hex(byte3)+" "+hex(byte2)
			proc.JMPC("H",1,byte3,byte2)
		elif byte1 == 0x6f :
			#proc.Last="JMPNH "+hex(byte3)+" "+hex(byte2)
			proc.JMPC("H",0,byte3,byte2)
		elif byte1 == 0x7f :
			#proc.Last="JMPC "+hex(byte3)+" "+hex(byte2)
			proc.JMPC("C",1,byte3,byte2)
		elif byte1 == 0x8f :
			#proc.Last="JMPNC "+hex(byte3)+" "+hex(byte2)
			proc.JMPC("C",0,byte3,byte2)
		elif byte1 == 0x9f :
			#proc.Last="JMP "+hex(byte2)
			proc.JMPNear(byte2)
		elif byte1 == 0xaf :
			#proc.Last="JMPZ "+hex(byte2)
			proc.JMPNearC("Z",1,byte2)
		elif byte1 == 0xbf :
			#proc.Last="JMPNZ "+hex(byte2)
			proc.JMPNearC("Z",0,byte2)
		elif byte1 == 0xcf :
			#proc.Last="JMPN "+hex(byte2)
			proc.JMPNearC("N",1,byte2)
		elif byte1 == 0xdf :
			#proc.Last="JMPNN "+hex(byte2)
			proc.JMPNearC("N",0,byte2)
		elif byte1 == 0xef :
			#proc.Last="JMPH "+hex(byte2)
			proc.JMPNearC("H",1,byte2)
		elif byte1 == 0xff :
			#proc.Last="JMPNH "+hex(byte2)
			proc.JMPNearC("H",0,byte2)

	elif byte1 in self.invalidInstr:
		proc.DisplayState()
		proc.DisplayStack(10)
		print("\n")
		print("invalid instruction",hex(byte1))
		raise ValueError("invalid instruction encountered")

def saveState(fileName,proc,screen):
	g=open(fileName,"w")
	g.write(hex(proc.A)+",;")
	g.write(hex(proc.B)+",;")
	g.write(hex(proc.C)+",;")
	g.write(hex(proc.D)+",;")
	g.write(hex(proc.E)+",;")
	g.write(hex(proc.H)+",;")
	g.write(hex(proc.L)+",;")
	g.write(hex(proc.PC)+",;")
	g.write(hex(proc.SP)+",;")
	g.write(str(proc.F)+",;")
	g.write(str(proc.RAM)+",;")
	g.write(str(screen)+",;")
	g.close()

def loadState(fileName,proc,screen):
	g=open(fileName,"r")
	t=g.readline()
	t=t.split(",;")
	# print(t)
	proc.A=int(t[0],0)
	proc.B=int(t[1],0)
	proc.C=int(t[2],0)
	proc.D=int(t[3],0)
	proc.E=int(t[4],0)
	proc.H=int(t[5],0)
	proc.L=int(t[6],0)
	proc.PC=int(t[7],0)
	proc.SP=int(t[8],0)
	proc.F=eval(t[9])
	proc.RAM=eval(t[10])
	screen=np.zeros((128,128))

	# screen=eval(t[11])
	plt.imshow(screen)
	plt.show()
	plt.pause(0.0001)

def BOOT(rom,bootrom,proc):
	for i in range(len(bootrom)):
		proc.RAM[i]=bootrom[i]
	for j in range(len(rom)):
		proc.RAM[j+0x597]=rom[j]

def runproc(proc,screen,logging,logfile):
	if logging:
		log=open(logfile,"w")
	while True:
		# time.sleep(1)
		# loadState("initial.txt",proc)
		# proc.DisplayState()
		try:
			byte1=proc.RAM[proc.PC]
			byte2=proc.RAM[proc.PC+1]
			byte3=proc.RAM[proc.PC+2]
			# c=input()
			# if c=="c":
			# if logging:
				# log.write(#proc.Last+"\n")
			ParseInst(byte1,byte2,byte3,proc,screen)
		except Exception:
			traceback.print_exc()
			while True:
				proc.DisplayState()
				proc.DisplayStack(40)
				t=input("WHAT TO DO SIR\n")
				if t[0:2]=="SP":
					addr=int(t[2:],0)
					proc.SP=addr
				elif t[0:2]=="PC":
					addr=int(t[2:],0)
					proc.PC=addr
				elif t[0]=="s":
					saveState(t[1:],proc,screen)
				elif t[0]=="l":
					loadState(t[1:],proc,screen)
				elif t=="b":
					break
				else:
					eval(t)

def main():	
	# f=open('chip9rom','rb')
	# g=open('bootrom','rb')
	f=open('CHIP9_rom','rb')
	g=open('CHIP9_bootrom','rb')
	romList=f.readlines()
	bootromList=g.readlines()
	rom=b''
	bootrom=b''
	for i in bootromList:
		bootrom+=i
	for i in romList:
		rom+=i
	
	proc=Processor()
	BOOT(rom,bootrom,proc)
	count=0
	screen=np.zeros((128,128))
	plt.ion()
	plt.imshow(screen)
	plt.show()
	plt.pause(0.0001)
	# loadState("start",proc,screen)
	proc.DisplayState()
	runproc(proc,screen,True,"log.txt")

  
if __name__== "__main__":
  main()
