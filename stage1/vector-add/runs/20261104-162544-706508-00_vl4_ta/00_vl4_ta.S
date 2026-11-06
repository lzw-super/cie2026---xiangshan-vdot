/* Focus: one unmasked vadd.vv; VLEN=128, SEW=8, LMUL=1, VL=4.
 * Loads/stores only prepare inputs and check the four active bytes.
 * Tail bytes are deliberately not checked. */
.option norvc
.option norelax
.section .text.entry,"ax"
.globl _start, target_vadd
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
  vsetivli t0, 4, e8, m1, ta, ma
  li t1, 4
  bne t0, t1, wrong_config
  la t0, input_a
  vle8.v v1, (t0)
  la t0, input_b
  vle8.v v2, (t0)
.balign 4
target_vadd:
  vadd.vv v3, v1, v2
  la t0, output
  vse8.v v3, (t0)
  fence rw, rw
  la t0, output
  la t1, expected
  li t2, 4
check:
  lbu t3, 0(t0)
  lbu t4, 0(t1)
  bne t3, t4, mismatch
  addi t0, t0, 1
  addi t1, t1, 1
  addi t2, t2, -1
  bnez t2, check
  li a0, 0
  j finish
mismatch:
  li a0, 1
  j finish
wrong_config:
  li a0, 2
  j finish
.balign 4
exception:
  csrr a1, mcause
  csrr a2, mepc
  csrr a3, mtval
  li a0, 3
finish:
  .word 0x0005006b
  j finish
.section .data
.balign 16
input_a: .byte 1,2,3,4
input_b: .byte 10,20,30,40
output: .fill 4,1,0
expected: .byte 11,22,33,44
