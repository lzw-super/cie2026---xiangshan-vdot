package xiangshan.backend.fu.wrapper

import chisel3._
import org.chipsalliance.cde.config.Parameters
import xiangshan.ExceptionNO.illegalInstr
import xiangshan.backend.fu.FuConfig
import xiangshan.backend.fu.vector.{VDotDataModule, VecPipedFuncUnit}

/** Uses ExeUnit's shared, redirect-filtered metadata pipeline and WB reservation. */
class VDot(cfg: FuConfig)(implicit p: Parameters) extends VecPipedFuncUnit(cfg) {
  require(VLEN == 128 && cfg.destDataBits == 128 && latency == 4 && latdiff == 0)
  val dot = Module(new VDotDataModule)
  dot.io.vs1 := vs1
  dot.io.vs2 := vs2
  for (i <- 0 until 4) { dot.io.enable(i) := regEnable(i + 1) }
  io.out.bits.res.data := dot.io.result
  // A redirect arriving at the output cycle must also suppress this result.
  io.out.valid := validVec.last && !outCtrl.robIdx.needFlush(io.flush)
  io.out.bits.ctrl.exceptionVec.get(illegalInstr) := outVstart =/= 0.U ||
    outVecCtrl.vill || outVecCtrl.vsew =/= 0.U || outVlmul =/= 0.U ||
    !outVm || outVl =/= 8.U
}
