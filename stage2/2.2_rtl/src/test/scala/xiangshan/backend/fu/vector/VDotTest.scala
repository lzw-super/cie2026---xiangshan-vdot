package xiangshan.backend.fu.vector

import chisel3._
import chisel3.util._
import chiseltest._
import chiseltest.simulator.VerilatorCFlags
import org.scalatest.flatspec.AnyFlatSpec
import org.chipsalliance.cde.config.Parameters
import top.KunminghuV2Config
import xiangshan._
import xiangshan.backend.fu._
import xiangshan.backend.fu.wrapper.VDot
import xiangshan.backend.fu.vector.Bundles.VConfig

/** Reproduces ExeUnit's shared metadata/redirect pipeline, with WB always ready. */
class VDotHarness(implicit p: Parameters) extends Module {
  val cfg = FuConfig.VdotCfg
  val io = IO(new Bundle {
    val valid = Input(Bool())
    // Keep test boundary <=64 bits for chiseltest 6 / Verilator 5.052 compatibility.
    val a = Input(Vec(2, UInt(64.W))); val b = Input(Vec(2, UInt(64.W)))
    val tag = Input(UInt(7.W)); val dest = Input(UInt(7.W))
    val vl = Input(UInt(8.W)); val sew = Input(UInt(3.W))
    val lmul = Input(UInt(3.W)); val start = Input(UInt(8.W))
    val vm = Input(Bool()); val v0 = Input(Bool())
    val flush = Input(Bool()); val flushTag = Input(UInt(7.W))
    val validOut = Output(Bool()); val result = Output(Vec(2, UInt(64.W)))
    val tagOut = Output(UInt(7.W)); val destOut = Output(UInt(7.W))
    val illegal = Output(Bool()); val v0Out = Output(Bool())
  })
  val fu = Module(new VDot(cfg))
  fu.io.in.bits := 0.U.asTypeOf(fu.io.in.bits)
  fu.io.flush.bits := 0.U.asTypeOf(fu.io.flush.bits)
  fu.io.flush.valid := io.flush
  fu.io.flush.bits.robIdx.value := io.flushTag
  fu.io.flush.bits.level := 0.U // flush younger instructions, preserve redirect itself
  fu.io.in.valid := io.valid
  fu.io.out.ready := true.B
  val ctrl = WireDefault(0.U.asTypeOf(new FuncUnitCtrlInput(cfg)))
  ctrl.robIdx.value := io.tag
  ctrl.pdest := io.dest
  ctrl.vecWen.get := !io.v0
  ctrl.v0Wen.get := io.v0
  ctrl.vpu.get.vm := io.vm
  ctrl.vpu.get.vsew := io.sew
  ctrl.vpu.get.vlmul := io.lmul
  ctrl.vpu.get.vstart := io.start
  val data = WireDefault(0.U.asTypeOf(new FuncUnitDataInput(cfg)))
  data.src(0) := io.a.asUInt
  data.src(1) := io.b.asUInt
  data.src(2) := Fill(128, 1.U(1.W)) // must never enter result
  val vconfig = WireDefault(0.U.asTypeOf(new VConfig))
  vconfig.vl := io.vl
  data.src(cfg.vconfigIdx) := vconfig.asUInt
  fu.io.in.bits.ctrl := ctrl
  fu.io.in.bits.data := data
  val ctrls = ctrl +: Seq.fill(4)(Reg(chiselTypeOf(ctrl)))
  val datas = data +: Seq.fill(4)(Reg(chiselTypeOf(data)))
  val valids = io.valid +: Seq.fill(4)(RegInit(false.B))
  for (i <- 1 to 4) {
    ctrls(i) := ctrls(i-1)
    datas(i) := datas(i-1)
    valids(i) := valids(i-1) && !ctrls(i-1).robIdx.needFlush(fu.io.flush)
  }
  fu.io.in.bits.ctrlPipe.get := VecInit(ctrls)
  fu.io.in.bits.dataPipe.get := VecInit(datas)
  fu.io.in.bits.validPipe.get := VecInit(valids)
  io.validOut := fu.io.out.valid
  io.result := fu.io.out.bits.res.data.asTypeOf(io.result)
  io.tagOut := fu.io.out.bits.ctrl.robIdx.value
  io.destOut := fu.io.out.bits.ctrl.pdest
  io.illegal := fu.io.out.bits.ctrl.exceptionVec.get(ExceptionNO.illegalInstr)
  io.v0Out := fu.io.out.bits.ctrl.v0Wen.get
}

class VDotTest extends AnyFlatSpec with ChiselScalatestTester {
  private val base = new KunminghuV2Config
  implicit val p: Parameters = base.alterPartial { case XSCoreParamsKey => base(XSTileKey).head }
  private def pack(xs: Seq[Int]): BigInt = xs.zipWithIndex.map { case (x,i) => BigInt(x & 255) << (8*i) }.sum
  private def dot(a: Seq[Int], b: Seq[Int]): BigInt = BigInt(a.take(8).zip(b).map { case (x,y) => x*y }.sum) & BigInt("ffffffff",16)

  behavior of "VDot four-stage pipeline"
  it should "match signed golden results, tags, bubbles, v0 and redirect kills" in {
    test(new VDotHarness).withAnnotations(Seq(VerilatorBackendAnnotation, WriteVcdAnnotation,
      // chiseltest 6 uses WData; Verilator 5.052 renamed wide words to EData.
      // IData remains the same uint32_t on both old and new Verilator releases.
      VerilatorCFlags(Seq("-DWData=IData")))) { d =>
      val random = new scala.util.Random(20261027L)
      case class Item(result: BigInt, tag: Int, dest: Int, illegal: Boolean, v0: Boolean)
      var q = List.fill[Option[Item]](4)(None)
      var checked = 0
      val killedAtStage = Array.fill(4)(0)
      def tick(a: Seq[Int], b: Seq[Int], valid: Boolean, tag: Int,
               flush: Boolean = false, cut: Int = 0, vl: Int = 8,
               sew: Int = 0, lmul: Int = 0, start: Int = 0, vm: Boolean = true): Unit = {
        val dest = (tag * 3 + 1) % 128
        val v0 = tag % 7 == 0
        for (i <- 0 until 2) {
          d.io.a(i).poke(pack(a.slice(i*8,i*8+8)).U)
          d.io.b(i).poke(pack(b.slice(i*8,i*8+8)).U)
        }
        d.io.valid.poke(valid.B); d.io.tag.poke(tag.U); d.io.dest.poke(dest.U)
        d.io.flush.poke(flush.B); d.io.flushTag.poke(cut.U)
        d.io.vl.poke(vl.U); d.io.sew.poke(sew.U); d.io.lmul.poke(lmul.U)
        d.io.start.poke(start.U); d.io.vm.poke(vm.B); d.io.v0.poke(v0.B)
        for (i <- q.indices) {
          if (flush && q(i).exists(_.tag > cut)) killedAtStage(i) += 1
        }
        q = q.map(_.filter(x => !flush || x.tag <= cut))
        d.io.validOut.expect(q.head.nonEmpty.B)
        q.head.foreach { x =>
          d.io.result(0).expect(x.result.U); d.io.result(1).expect(0.U); d.io.tagOut.expect(x.tag.U)
          d.io.destOut.expect(x.dest.U); d.io.illegal.expect(x.illegal.B)
          d.io.v0Out.expect(x.v0.B); checked += 1
        }
        val item = if(valid && (!flush || tag <= cut)) Some(Item(dot(a,b),tag,dest,
          vl != 8 || sew != 0 || lmul != 0 || start != 0 || !vm, v0)) else None
        d.clock.step()
        q = q.tail :+ item
      }
      val zero = Seq.fill(16)(0)
      for ((a,b) <- Seq((127,127),(-128,-128),(-128,127),(-1,1),(0,127))) {
        tick(Seq.fill(16)(a), Seq.fill(16)(b), true, 1)
      }
      for (i <- 0 until 1600) {
        val a = Seq.fill(16)(random.nextInt(256)-128)
        val b = Seq.fill(16)(random.nextInt(256)-128)
        // First 128 cycles are uninterrupted, then bubbles and selective redirects.
        tick(a,b,i < 128 || random.nextInt(4)!=0, 10 + i%64,
          flush = i>=128 && i%19==0, cut = 40)
      }
      tick(zero,zero,true,2,vl=7)
      tick(zero,zero,true,3,sew=1)
      tick(zero,zero,true,4,lmul=1)
      tick(zero,zero,true,5,start=1)
      tick(zero,zero,true,6,vm=false)
      for (_ <- 0 until 5) tick(zero,zero,false,0)
      assert(checked > 1000)
      assert(killedAtStage.forall(_ > 0))
      println(s"VDot checked=$checked; killed output-to-input stages=${killedAtStage.mkString(",")}")
      // Reset cancels in-flight valid state; arithmetic registers need not reset.
      tick(zero,zero,true,7)
      d.reset.poke(true.B); d.clock.step(); d.reset.poke(false.B)
      q = List.fill(4)(None)
      for (_ <- 0 until 5) tick(zero,zero,false,0)
    }
  }
}
