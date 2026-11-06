CROSS ?= riscv64-linux-gnu-
CASES := 00_vl4_ta
.PHONY: all clean
all: $(CASES:%=build/%.bin) $(CASES:%=build/%.dis)
build:
	mkdir -p $@
build/%.elf: %.S link.ld | build
	$(CROSS)gcc -march=rv64gcv -mabi=lp64d -nostdlib -nostartfiles -static -Wl,--build-id=none,--no-relax -T link.ld $< -o $@
build/%.bin: build/%.elf
	$(CROSS)objcopy -O binary $< $@
build/%.dis: build/%.elf
	$(CROSS)objdump -d -M no-aliases,numeric $< > $@
	$(CROSS)nm -n $< > build/$*.symbols
.SECONDARY:
clean:
	rm -rf build
