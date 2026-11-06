#include "common.S"
.globl test_body
test_body:
vsetivli t0, 16, e8, m1, ta, ma
LOAD v3, data_01_directed_poison1
LOAD v1, data_01_directed_a1
LOAD v2, data_01_directed_b1
vsetivli t0, 8, e8, m1, ta, ma
.globl target_1
target_1:
VDOT 3, 1, 2
CHECK v3, data_01_directed_expected1, 1
vsetivli t0, 16, e8, m1, tu, mu
LOAD v3, data_01_directed_poison2
LOAD v1, data_01_directed_a2
LOAD v2, data_01_directed_b2
vsetivli t0, 8, e8, m1, tu, mu
.globl target_2
target_2:
VDOT 3, 1, 2
CHECK v3, data_01_directed_expected2, 2
vsetivli t0, 16, e8, m1, ta, ma
LOAD v3, data_01_directed_poison3
LOAD v1, data_01_directed_a3
LOAD v2, data_01_directed_b3
vsetivli t0, 8, e8, m1, ta, ma
.globl target_3
target_3:
VDOT 3, 1, 2
CHECK v3, data_01_directed_expected3, 3
vsetivli t0, 16, e8, m1, tu, mu
LOAD v3, data_01_directed_poison4
LOAD v1, data_01_directed_a4
LOAD v2, data_01_directed_b4
vsetivli t0, 8, e8, m1, tu, mu
.globl target_4
target_4:
VDOT 3, 1, 2
CHECK v3, data_01_directed_expected4, 4
vsetivli t0, 16, e8, m1, ta, ma
LOAD v3, data_01_directed_poison5
LOAD v1, data_01_directed_a5
LOAD v2, data_01_directed_b5
vsetivli t0, 8, e8, m1, ta, ma
.globl target_5
target_5:
VDOT 3, 1, 2
CHECK v3, data_01_directed_expected5, 5
vsetivli t0, 16, e8, m1, tu, mu
LOAD v3, data_01_directed_poison6
LOAD v1, data_01_directed_a6
LOAD v2, data_01_directed_b6
vsetivli t0, 8, e8, m1, tu, mu
.globl target_6
target_6:
VDOT 3, 1, 2
CHECK v3, data_01_directed_expected6, 6
vsetivli t0, 16, e8, m1, ta, ma
LOAD v3, data_01_directed_poison7
LOAD v1, data_01_directed_a7
LOAD v2, data_01_directed_b7
vsetivli t0, 8, e8, m1, ta, ma
.globl target_7
target_7:
VDOT 3, 1, 2
CHECK v3, data_01_directed_expected7, 7
vsetivli t0, 16, e8, m1, tu, mu
LOAD v3, data_01_directed_poison20
LOAD v1, data_01_directed_a20
LOAD v2, data_01_directed_b20
vsetivli t0, 8, e8, m1, tu, mu
.globl target_20
target_20:
VDOT 3, 1, 2
CHECK v3, data_01_directed_expected20, 20
vsetivli t0, 16, e8, m1, tu, mu
LOAD v3, data_01_directed_poison21
LOAD v1, data_01_directed_a21
LOAD v2, data_01_directed_b21
vsetivli t0, 8, e8, m1, tu, mu
.globl target_21
target_21:
VDOT 3, 1, 2
CHECK v3, data_01_directed_expected21, 21
vsetivli t0, 16, e8, m1, tu, mu
LOAD v3, data_01_directed_poison22
LOAD v1, data_01_directed_a22
LOAD v2, data_01_directed_b22
vsetivli t0, 8, e8, m1, tu, mu
.globl target_22
target_22:
VDOT 3, 1, 2
CHECK v3, data_01_directed_expected22, 22
j pass
.section .data
.balign 16
.balign 16
data_01_directed_a1:
 .byte 0,0,0,0,0,0,0,0,119,253,106,130,196,88,102,248
.balign 16
data_01_directed_b1:
 .byte 127,127,127,127,127,127,127,127,167,208,66,132,188,163,44,5
.balign 16
data_01_directed_poison1:
 .byte 165,165,165,165,165,165,165,165,165,165,165,165,165,165,165,165
.balign 16
data_01_directed_expected1:
 .byte 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
.balign 16
data_01_directed_a2:
 .byte 1,1,1,1,1,1,1,1,60,109,136,156,96,138,42,155
.balign 16
data_01_directed_b2:
 .byte 255,255,255,255,255,255,255,255,76,199,165,187,49,196,196,167
.balign 16
data_01_directed_poison2:
 .byte 165,165,165,165,165,165,165,165,165,165,165,165,165,165,165,165
.balign 16
data_01_directed_expected2:
 .byte 248,255,255,255,0,0,0,0,0,0,0,0,0,0,0,0
.balign 16
data_01_directed_a3:
 .byte 127,127,127,127,127,127,127,127,181,222,147,73,19,124,192,172
.balign 16
data_01_directed_b3:
 .byte 127,127,127,127,127,127,127,127,153,100,30,31,113,12,242,67
.balign 16
data_01_directed_poison3:
 .byte 165,165,165,165,165,165,165,165,165,165,165,165,165,165,165,165
.balign 16
data_01_directed_expected3:
 .byte 8,248,1,0,0,0,0,0,0,0,0,0,0,0,0,0
.balign 16
data_01_directed_a4:
 .byte 128,128,128,128,128,128,128,128,65,124,152,96,136,115,239,43
.balign 16
data_01_directed_b4:
 .byte 128,128,128,128,128,128,128,128,164,175,196,206,206,175,59,205
.balign 16
data_01_directed_poison4:
 .byte 165,165,165,165,165,165,165,165,165,165,165,165,165,165,165,165
.balign 16
data_01_directed_expected4:
 .byte 0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0
.balign 16
data_01_directed_a5:
 .byte 128,128,128,128,128,128,128,128,178,144,251,3,38,59,114,239
.balign 16
data_01_directed_b5:
 .byte 127,127,127,127,127,127,127,127,183,242,17,85,150,30,172,69
.balign 16
data_01_directed_poison5:
 .byte 165,165,165,165,165,165,165,165,165,165,165,165,165,165,165,165
.balign 16
data_01_directed_expected5:
 .byte 0,4,254,255,0,0,0,0,0,0,0,0,0,0,0,0
.balign 16
data_01_directed_a6:
 .byte 1,254,3,252,5,250,7,248,112,37,122,118,106,232,148,69
.balign 16
data_01_directed_b6:
 .byte 1,1,1,1,1,1,1,1,192,183,97,17,128,66,170,215
.balign 16
data_01_directed_poison6:
 .byte 165,165,165,165,165,165,165,165,165,165,165,165,165,165,165,165
.balign 16
data_01_directed_expected6:
 .byte 252,255,255,255,0,0,0,0,0,0,0,0,0,0,0,0
.balign 16
data_01_directed_a7:
 .byte 128,127,0,1,255,64,192,2,82,116,5,106,167,189,43,90
.balign 16
data_01_directed_b7:
 .byte 127,128,1,255,1,192,64,3,211,243,0,77,56,182,203,52
.balign 16
data_01_directed_poison7:
 .byte 165,165,165,165,165,165,165,165,165,165,165,165,165,165,165,165
.balign 16
data_01_directed_expected7:
 .byte 4,97,255,255,0,0,0,0,0,0,0,0,0,0,0,0
.balign 16
data_01_directed_a20:
 .byte 0,1,2,3,4,5,6,7,0,0,0,0,0,0,0,0
.balign 16
data_01_directed_b20:
 .byte 2,2,2,2,2,2,2,2,0,0,0,0,0,0,0,0
.balign 16
data_01_directed_poison20:
 .byte 165,165,165,165,165,165,165,165,165,165,165,165,165,165,165,165
.balign 16
data_01_directed_expected20:
 .byte 56,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
.balign 16
data_01_directed_a21:
 .byte 0,1,2,3,4,5,6,7,255,255,255,255,255,255,255,255
.balign 16
data_01_directed_b21:
 .byte 2,2,2,2,2,2,2,2,255,255,255,255,255,255,255,255
.balign 16
data_01_directed_poison21:
 .byte 165,165,165,165,165,165,165,165,165,165,165,165,165,165,165,165
.balign 16
data_01_directed_expected21:
 .byte 56,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
.balign 16
data_01_directed_a22:
 .byte 0,1,2,3,4,5,6,7,128,128,128,128,128,128,128,128
.balign 16
data_01_directed_b22:
 .byte 2,2,2,2,2,2,2,2,128,128,128,128,128,128,128,128
.balign 16
data_01_directed_poison22:
 .byte 165,165,165,165,165,165,165,165,165,165,165,165,165,165,165,165
.balign 16
data_01_directed_expected22:
 .byte 56,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
