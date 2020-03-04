// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// while True
(LOOP)
// pixeladdress=16384
@SCREEN
D=A
@pixeladdress
M=D
// while True
(WHILEBLACK)
// if no key pressed break
@24576
D=M
@ENDWHILEBLACK
D;JEQ
// blacken pixel at pixeladdress
@pixeladdress
A=M
M=-1
// pixeladdress++
@pixeladdress
M=M+1
D=M
// if pixeladdress < 24576 goto start of WHILEBLACK
@24576
D=A-D
@WHILEBLACK
D;JGE
// goto main loop
@LOOP
0;JMP
(ENDWHILEBLACK)
// pixeladdress=16384
@SCREEN
D=A
@pixeladdress
M=D
// while True
(WHILEWHITE)
// if some key is pressed break
@24576
D=M
@LOOP
D;JNE
// whiten pixel at pixeladdress
@pixeladdress
A=M
M=0
// pixeladdress++
@pixeladdress
M=M+1
D=M
// if pixeladdress < 24576 goto start of WHILEBLACK
@24576
D=A-D
@WHILEWHITE
D;JGE
// goto main loop
@LOOP
0;JMP
