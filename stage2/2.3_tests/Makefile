CROSS ?= riscv64-linux-gnu-
CASES := 00_smoke 01_directed
.PHONY: all verify clean
all: $(CASES:%=build/%.bin)
build:
	mkdir -p $@
# Test sources are submitted; all generated files go to build/.
define SUITE
build/$(1).elf: suites/$(1)/source/$(1).S suites/$(1)/source/common.S suites/$(1)/source/link.ld | build
	$$(CROSS)gcc -Isuites/$(1)/source -march=rv64gcv -mabi=lp64d -nostdlib -nostartfiles -static -Wl,--build-id=none,--no-relax -T suites/$(1)/source/link.ld suites/$(1)/source/$(1).S -o $$@
build/$(1).bin: build/$(1).elf
	$$(CROSS)objcopy -O binary $$< $$@
endef
$(foreach suite,$(CASES),$(eval $(call SUITE,$(suite))))
verify: all
	sha256sum -c images.sha256
clean:
	rm -rf build
