// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
AM=M-1
D=M
A=A-1
D=M-D
@CMP$TRUE.0
D;JEQ
@SP
A=M-1
M=0
@CMP$END.0
0;JMP
(CMP$TRUE.0)
@SP
A=M-1
M=-1
(CMP$END.0)
// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 16
@16
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
AM=M-1
D=M
A=A-1
D=M-D
@CMP$TRUE.1
D;JEQ
@SP
A=M-1
M=0
@CMP$END.1
0;JMP
(CMP$TRUE.1)
@SP
A=M-1
M=-1
(CMP$END.1)
// push constant 16
@16
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 17
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq
@SP
AM=M-1
D=M
A=A-1
D=M-D
@CMP$TRUE.2
D;JEQ
@SP
A=M-1
M=0
@CMP$END.2
0;JMP
(CMP$TRUE.2)
@SP
A=M-1
M=-1
(CMP$END.2)
// push constant 892
@892
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@SP
AM=M-1
D=M
A=A-1
D=M-D
@CMP$TRUE.3
D;JLT
@SP
A=M-1
M=0
@CMP$END.3
0;JMP
(CMP$TRUE.3)
@SP
A=M-1
M=-1
(CMP$END.3)
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 892
@892
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@SP
AM=M-1
D=M
A=A-1
D=M-D
@CMP$TRUE.4
D;JLT
@SP
A=M-1
M=0
@CMP$END.4
0;JMP
(CMP$TRUE.4)
@SP
A=M-1
M=-1
(CMP$END.4)
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 891
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt
@SP
AM=M-1
D=M
A=A-1
D=M-D
@CMP$TRUE.5
D;JLT
@SP
A=M-1
M=0
@CMP$END.5
0;JMP
(CMP$TRUE.5)
@SP
A=M-1
M=-1
(CMP$END.5)
// push constant 32767
@32767
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@SP
AM=M-1
D=M
A=A-1
D=M-D
@CMP$TRUE.6
D;JGT
@SP
A=M-1
M=0
@CMP$END.6
0;JMP
(CMP$TRUE.6)
@SP
A=M-1
M=-1
(CMP$END.6)
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 32767
@32767
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@SP
AM=M-1
D=M
A=A-1
D=M-D
@CMP$TRUE.7
D;JGT
@SP
A=M-1
M=0
@CMP$END.7
0;JMP
(CMP$TRUE.7)
@SP
A=M-1
M=-1
(CMP$END.7)
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 32766
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt
@SP
AM=M-1
D=M
A=A-1
D=M-D
@CMP$TRUE.8
D;JGT
@SP
A=M-1
M=0
@CMP$END.8
0;JMP
(CMP$TRUE.8)
@SP
A=M-1
M=-1
(CMP$END.8)
// push constant 57
@57
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 31
@31
D=A
@SP
A=M
M=D
@SP
M=M+1
// push constant 53
@53
D=A
@SP
A=M
M=D
@SP
M=M+1
// add
@SP
AM=M-1
D=M
A=A-1
M=D+M
// push constant 112
@112
D=A
@SP
A=M
M=D
@SP
M=M+1
// sub
@SP
AM=M-1
D=M
A=A-1
M=M-D
// neg
@SP
A=M-1
M=-M
// and
@SP
AM=M-1
D=M
A=A-1
M=D&M
// push constant 82
@82
D=A
@SP
A=M
M=D
@SP
M=M+1
// or
@SP
AM=M-1
D=M
A=A-1
M=D|M
// not
@SP
A=M-1
M=!M
