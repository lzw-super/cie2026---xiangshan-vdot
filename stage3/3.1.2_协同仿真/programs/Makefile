CROSS ?= riscv64-linux-gnu-
CASES := 00_smoke 01_directed 02_random 03_alias_v0 04_pipeline 05_redirect 06_illegal 07_vadd
.PHONY: all clean generate
all: $(CASES:%=build/%.bin) $(CASES:%=build/%.dis)
build:
	mkdir -p $@
$(CASES:%=build/%.S) $(CASES:%=build/%.json) &: generate.py | build
	python3 generate.py
build/%.elf: build/%.S common.S link.ld
	$(CROSS)gcc -I. -march=rv64gcv -mabi=lp64d -nostdlib -nostartfiles -static -Wl,--build-id=none,--no-relax -T link.ld $< -o $@
build/%.bin: build/%.elf
	$(CROSS)objcopy -O binary $< $@
build/%.dis: build/%.elf
	$(CROSS)objdump -d -M no-aliases,numeric $< > $@
	$(CROSS)nm -n $< > build/$*.symbols
generate: $(CASES:%=build/%.S) $(CASES:%=build/%.json)
.SECONDARY:
clean:
	rm -rf build
