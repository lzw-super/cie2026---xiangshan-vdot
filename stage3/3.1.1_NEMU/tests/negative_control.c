// Deliberately corrupt one reference vector high bit after vdot, ONLY for detector testing.
// Never use this library as the passing reference.
#include <isa-def.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#ifndef REAL_REF
#error REAL_REF required
#endif
#ifndef TARGET_PC
#error TARGET_PC required
#endif
void difftest_regcpy(void *dut, bool direction) {
  static void (*real_copy)(void *,bool);
  if(!real_copy) {
    void *h=dlopen(REAL_REF,RTLD_NOW|RTLD_LOCAL);
    if(!h) {fprintf(stderr,"%s\n",dlerror());abort();}
    real_copy=dlsym(h,"difftest_regcpy");
    if(!real_copy || real_copy==difftest_regcpy) abort();
  }
  real_copy(dut,direction);
  riscv64_CPU_state *state=dut;
  if(!direction && state->pc>=TARGET_PC && state->pc<0x80001000 && state->vr[3]._64[0]==36) {
    state->vr[3]._64[1]^=1;
    fprintf(stderr,"STAGE3_NEGATIVE_CONTROL: flipped vd[64] after vdot\n");
  }
}
