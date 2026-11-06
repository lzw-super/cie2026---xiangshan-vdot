#include "common.S"
.globl test_body
test_body:
vsetivli t0, 16, e8, m1, tu, mu
LOAD v3, data_00_smoke_poison1
LOAD v1, data_00_smoke_a1
LOAD v2, data_00_smoke_b1
vsetivli t0, 8, e8, m1, tu, mu
.globl target_1
target_1:
VDOT 3, 1, 2
CHECK v3, data_00_smoke_expected1, 1
j pass
.section .data
.balign 16
.balign 16
data_00_smoke_a1:
 .byte 1,2,3,4,5,6,7,8,78,25,66,97,96,209,51,116
.balign 16
data_00_smoke_b1:
 .byte 1,1,1,1,1,1,1,1,13,14,252,215,215,20,40,221
.balign 16
data_00_smoke_poison1:
 .byte 165,165,165,165,165,165,165,165,165,165,165,165,165,165,165,165
.balign 16
data_00_smoke_expected1:
 .byte 36,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
