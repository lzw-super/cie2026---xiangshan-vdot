OUTPUT_ARCH(riscv)
ENTRY(_start)
SECTIONS {
 . = 0x80000000;
 .text : { *(.text.entry) *(.text*) }
 . = ALIGN(16);
 .data : { *(.data*) }
}
