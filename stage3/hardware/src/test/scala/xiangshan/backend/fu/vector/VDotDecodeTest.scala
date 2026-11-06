package xiangshan.backend.fu.vector

import chisel3._
import chiseltest._
import chiseltest.simulator.VerilatorCFlags
import org.scalatest.flatspec.AnyFlatSpec
import org.chipsalliance.cde.config.Parameters
import top.KunminghuV2Config
import xiangshan._
import xiangshan.backend.decode.DecodeUnit
import xiangshan.backend.fu.FuType

class VDotDecodeHarness(implicit p: Parameters) extends Module {
  val io = IO(new Bundle {
    val inst = Input(UInt(32.W))
    val sew = Input(UInt(3.W)); val lmul = Input(UInt(3.W))
    val start = Input(UInt(8.W)); val vsOff = Input(Bool())
    val vdot = Output(Bool()); val vadd = Output(Bool())
    val illegal = Output(Bool()); val vecWen = Output(Bool())
    val rfWen = Output(Bool()); val oldVdSource = Output(Bool())
    val maskSource = Output(Bool()); val uops = Output(UInt(8.W))
  })
  val dec = Module(new DecodeUnit)
  dec.io.enq.ctrlFlow := 0.U.asTypeOf(dec.io.enq.ctrlFlow)
  dec.io.enq.ctrlFlow.instr := io.inst
  dec.io.enq.vtype := 0.U.asTypeOf(dec.io.enq.vtype)
  dec.io.enq.vtype.vsew := io.sew
  dec.io.enq.vtype.vlmul := io.lmul
  dec.io.enq.vstart := io.start
  dec.io.csrCtrl := 0.U.asTypeOf(dec.io.csrCtrl)
  dec.io.fromCSR := 0.U.asTypeOf(dec.io.fromCSR)
  dec.io.fromCSR.illegalInst.vsIsOff := io.vsOff
  val out = dec.io.deq.decodedInst
  io.vdot := FuType.FuTypeOrR(out.fuType, FuType.vdot)
  io.vadd := FuType.FuTypeOrR(out.fuType, FuType.vialuF)
  io.illegal := out.exceptionVec(ExceptionNO.illegalInstr)
  io.vecWen := out.vecWen
  io.rfWen := out.rfWen
  io.oldVdSource := !SrcType.isNotReg(out.srcType(2))
  io.maskSource := !SrcType.isNotReg(out.srcType(3))
  io.uops := out.numUops
}

class VDotDecodeTest extends AnyFlatSpec with ChiselScalatestTester {
  private val base = new KunminghuV2Config
  implicit val p: Parameters = base.alterPartial { case XSCoreParamsKey => base(XSTileKey).head }
  behavior of "VDot DecodeUnit"
  it should "decode project encoding uniquely and reject unsupported modes" in {
    test(new VDotDecodeHarness).withAnnotations(Seq(VerilatorBackendAnnotation,
      VerilatorCFlags(Seq("-DWData=IData")))) { d =>
      d.io.sew.poke(0.U); d.io.lmul.poke(0.U); d.io.start.poke(0.U); d.io.vsOff.poke(false.B)
      for (vd <- 0 until 32; vs1 <- Seq(0,1,31); vs2 <- Seq(0,2,31)) {
        d.io.inst.poke((BigInt("fe000057",16) | BigInt(vd<<7 | vs1<<15 | vs2<<20)).U)
        d.io.vdot.expect(true.B); d.io.illegal.expect(false.B)
        d.io.vecWen.expect(true.B); d.io.rfWen.expect(false.B)
        d.io.oldVdSource.expect(false.B); d.io.maskSource.expect(false.B)
        d.io.uops.expect(1.U)
      }
      d.io.inst.poke("hfc2081d7".U) // vm=0 must not match
      d.io.vdot.expect(false.B); d.io.illegal.expect(true.B)
      d.io.inst.poke("hfe2081d7".U)
      d.io.sew.poke(1.U); d.io.illegal.expect(true.B); d.io.sew.poke(0.U)
      d.io.lmul.poke(1.U); d.io.illegal.expect(true.B); d.io.lmul.poke(0.U)
      d.io.start.poke(1.U); d.io.illegal.expect(true.B); d.io.start.poke(0.U)
      d.io.vsOff.poke(true.B); d.io.illegal.expect(true.B); d.io.vsOff.poke(false.B)
      d.io.inst.poke("h022081d7".U) // vadd.vv v3,v1,v2
      d.io.vdot.expect(false.B); d.io.vadd.expect(true.B); d.io.illegal.expect(false.B)
    }
  }
}
