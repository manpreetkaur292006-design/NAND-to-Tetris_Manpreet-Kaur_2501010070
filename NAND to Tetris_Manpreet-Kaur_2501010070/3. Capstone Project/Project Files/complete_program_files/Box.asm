// Box.asm  (K = 70)
// Black box while a key is pressed: rows 70-89, 3 words (48 pixels) wide

(LOOP)
    @KBD
    D=M
    @BLACK
    D;JNE
    @color
    M=0
    @DRAW
    0;JMP

(BLACK)
    @color
    M=-1

(DRAW)
    @18624
    D=A
    @addr
    M=D
    @20
    D=A
    @row
    M=D

(ROWLOOP)
    @color
    D=M
    @addr
    A=M
    M=D
    A=A+1
    M=D
    A=A+1
    M=D

    @32
    D=A
    @addr
    M=D+M

    @row
    M=M-1
    D=M
    @ROWLOOP
    D;JGT

    @LOOP
    0;JMP