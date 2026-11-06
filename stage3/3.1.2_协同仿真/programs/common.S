.option norvc
.option norelax
.macro VDOT vd, vs1, vs2
 .word (0xfe000057 | ((\vs2) << 20) | ((\vs1) << 15) | ((\vd) << 7))
.endm
.macro LOAD reg, label
 la t0, \label
 vle8.v \reg, (t0)
.endm
# CHECK changes VL to 16; restore VL=8 before another vdot.
# On failure: a1=case ID, a2=byte index, a3=actual, a4=expected.
.macro CHECK reg, label, id
 li a1, \id
 vsetivli t0, 16, e8, m1, tu, mu
 la t0, output
 vse8.v \reg, (t0)
 fence rw, rw
 la t1, \label
 li a2, 0
.Lcheck\@:
 lbu a3, 0(t0)
 lbu a4, 0(t1)
 bne a3, a4, mismatch
 addi t0, t0, 1
 addi t1, t1, 1
 addi a2, a2, 1
 li t2, 16
 bltu a2, t2, .Lcheck\@
.endm
.section .text.entry,"ax"
.globl _start
_start:
 la t0, exception
 csrw mtvec, t0
 li t0, 0x600
 csrs mstatus, t0
 csrw vstart, zero
 csrw vcsr, zero
 csrr t0, vlenb
 li t1, 16
 bne t0, t1, wrong_config
 li s11, 0
 j test_body
mismatch:
 li a0, 1
 j finish
wrong_config:
 li a0, 2
 j finish
exception:
 csrr a1, mcause
 csrr a2, mepc
 csrr a3, mtval
 # Only the negative suite sets s11 to an exact expected fault PC.
 bne a2, s11, unexpected_exception
 li t0, 2
 bne a1, t0, unexpected_exception
 li s11, 0
 addi a2, a2, 4
 csrw mepc, a2
 csrw vstart, zero
 addi s10, s10, 1
 mret
unexpected_exception:
 li a0, 3
 j finish
pass:
 li a0, 0
finish:
 .word 0x0005006b
 j finish
.section .data
.balign 16
output: .fill 16, 1, 0xa5
.section .text
