CROSS ?= riscv64-linux-gnu-
CASES := rvv_equivalence bench_vdot_1 bench_rvv_1 bench_vdot_32 bench_rvv_32 bench_vdot_128 bench_rvv_128
.PHONY: all clean generate
all: $(CASES:%=build/%.bin) $(CASES:%=build/%.dis)
build:
	mkdir -p $@
$(CASES:%=build/%.S) $(CASES:%=build/%.json) &: generate.py program.py fixtures.json | build
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
