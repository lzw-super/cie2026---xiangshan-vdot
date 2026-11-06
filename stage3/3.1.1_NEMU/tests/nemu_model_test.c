// Exercise the actual NEMU shared-library instruction decoder and execution model.
#include <isa-def.h>
#include <dlfcn.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(c) do { if (!(c)) { fprintf(stderr,"FAIL line=%d case=%d\n",__LINE__,test_id); exit(1); } } while(0)
static uint32_t rng = 20261027;
static uint32_t random32(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
int main(int argc, char **argv) {
  int test_id = 0;
  CHECK(argc == 2);
  void *lib = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
  if (!lib) { fprintf(stderr,"%s\n",dlerror()); return 1; }
  void (*init)(void) = dlsym(lib,"difftest_init");
  void (*ramsize)(size_t) = dlsym(lib,"difftest_set_ramsize");
  void (*regcpy)(void *, bool) = dlsym(lib,"difftest_regcpy");
  void (*memcpy_ref)(uint64_t, void *, size_t, bool) = dlsym(lib,"difftest_memcpy");
  void (*exec)(uint64_t) = dlsym(lib,"difftest_exec");
  const unsigned *size = dlsym(lib,"DIFFTEST_REG_SIZE");
  CHECK(init && ramsize && regcpy && memcpy_ref && exec && size);
  CHECK(*size == offsetof(riscv64_CPU_state,difftest_state_end));
  ramsize(128ul<<20); init();
  riscv64_CPU_state initial={0}, state={0};
  regcpy(&initial,false);
  for(test_id=0;test_id<1100;test_id++) {
    state=initial;
    state.mode=3; state.mstatus=0x200; state.pc=0x80000000+4*test_id;
    state.mtvec=0x80020000; state.vl=8; state.vtype=0; state.vstart=0;
    for(int reg=0;reg<32;reg++) for(int j=0;j<16;j++) state.vr[reg]._8[j]=random32();
    unsigned vd=random32()%32, a=random32()%32, b=random32()%32;
    // Include the exact minimum/maximum input extrema and alias patterns.
    if(test_id<4) {
      vd=3; a=1; b=2;
      memset(&state.vr[a], test_id==0?127:128,16);
      memset(&state.vr[b], test_id==1?128:test_id==3?0:127,16);
    }
    int64_t sum=0;
    for(int i=0;i<8;i++) {
      int aa=state.vr[a]._8[i],bb=state.vr[b]._8[i];
      sum+=(aa>=128?aa-256:aa)*(bb>=128?bb-256:bb);
    }
    uint8_t before[32][16]; memcpy(before,state.vr,sizeof(before));
    uint32_t instruction=0xfe000057u | (b<<20) | (a<<15) | (vd<<7);
    uint64_t pc = state.pc;
    memcpy_ref(pc,&instruction,4,true); regcpy(&state,true); exec(1); regcpy(&state,false);
    CHECK(state.pc==pc+4);
    CHECK(state.vr[vd]._32[0]==(uint32_t)sum);
    for(int i=4;i<16;i++) CHECK(state.vr[vd]._8[i]==0);
    for(int reg=0;reg<32;reg++) if(reg!=vd) CHECK(memcmp(before[reg],&state.vr[reg],16)==0);
    CHECK(state.vstart==0 && state.vl==8 && state.vtype==0);
    CHECK((state.mstatus & 0x600)==0x600);
  }
  uint32_t handler = 0x00000013; // retire one NOP after taking the fault
  memcpy_ref(0x80020000,&handler,4,true);
  for(test_id=0;test_id<7;test_id++) {
    state=initial;state.mode=3;state.mstatus=0x600;state.pc=0x80010000+4*test_id;
    state.mtvec=0x80020000;state.vl=8;state.vtype=0;state.vstart=0;
    if(test_id==0)state.vl=0;
    if(test_id==1)state.vl=7;
    if(test_id==2)state.vtype=8; // e16
    if(test_id==3)state.vtype=1; // m2
    if(test_id==4)state.vstart=1;
    if(test_id==5)state.mstatus=0; // VS off
    uint32_t instruction=test_id==6?0xfc2081d7:0xfe2081d7;
    memset(&state.vr[3],0xa5,16);
    uint64_t pc = state.pc;
    memcpy_ref(pc,&instruction,4,true);regcpy(&state,true);exec(1);regcpy(&state,false);
    if(state.mcause!=2 || state.mepc!=pc) fprintf(stderr,"exception case=%d cause=%lx mepc=%lx pc=%lx expected=%lx\n",test_id,state.mcause,state.mepc,state.pc,pc);
    CHECK(state.mcause==2 && state.mepc==pc);
    CHECK(state.mtval==(test_id<=1?0:instruction));
    for(int i=0;i<16;i++)CHECK(state.vr[3]._8[i]==0xa5);
  }
  puts("PASS: actual NEMU model, 1100 valid cases and 7 illegal configurations; all 128 result bits and non-destination registers checked");
  return 0;
}
