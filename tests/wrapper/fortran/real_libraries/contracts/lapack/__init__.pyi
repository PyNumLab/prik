from x2py.contracts import Addr, Arg, Bool, Complex128, Complex64, Flat, Float32, Float64, Int32, Return, Returns, String, bind, external, native_call
from . import LA_CONSTANTS
from . import LA_XISNAN

@bind("CBBCSD")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Arg(23), Arg(24), Arg(25), Arg(26), Addr(Arg(27)), Addr(Arg(28))])
def cbbcsd(
    JOBU1: String[1],
    JOBU2: String[1],
    JOBV1T: String[1],
    JOBV2T: String[1],
    TRANS: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    THETA: Float32[Flat],
    PHI: Float32[Flat],
    U1: Complex64[LDU1, Flat],
    LDU1: Int32,
    U2: Complex64[LDU2, Flat],
    LDU2: Int32,
    V1T: Complex64[LDV1T, Flat],
    LDV1T: Int32,
    V2T: Complex64[LDV2T, Flat],
    LDV2T: Int32,
    B11D: Float32[Flat],
    B11E: Float32[Flat],
    B12D: Float32[Flat],
    B12E: Float32[Flat],
    B21D: Float32[Flat],
    B21E: Float32[Flat],
    B22D: Float32[Flat],
    B22E: Float32[Flat],
    RWORK: Float32[Flat],
    LRWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CBDSQR")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14))])
def cbdsqr(
    UPLO: String[1],
    N: Int32,
    NCVT: Int32,
    NRU: Int32,
    NCC: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    VT: Complex64[LDVT, Flat],
    LDVT: Int32,
    U: Complex64[LDU, Flat],
    LDU: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGBBRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Addr(Arg(18))])
def cgbbrd(
    VECT: String[1],
    M: Int32,
    N: Int32,
    NCC: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    PT: Complex64[LDPT, Flat],
    LDPT: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGBCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def cgbcon(
    NORM: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGBEQU")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11))])
def cgbequ(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    R: Float32[Flat],
    C: Float32[Flat],
    ROWCND: Float32,
    COLCND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("CGBEQUB")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11))])
def cgbequb(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    R: Float32[Flat],
    C: Float32[Flat],
    ROWCND: Float32,
    COLCND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("CGBRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Addr(Arg(18))])
def cgbrfs(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex64[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGBRFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22)), Arg(23), Arg(24), Arg(25), Addr(Arg(26))])
def cgbrfsx(
    TRANS: String[1],
    EQUED: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex64[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    R: Float32[Flat],
    C: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGBSV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def cgbsv(
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CGBSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def cgbsvx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex64[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float32[Flat],
    C: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGBSVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Addr(Arg(24)), Arg(25), Arg(26), Arg(27), Addr(Arg(28))])
def cgbsvxx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex64[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float32[Flat],
    C: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    RPVGRW: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGBTF2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def cgbtf2(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGBTRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def cgbtrf(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGBTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def cgbtrs(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CGEBAK")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def cgebak(
    JOB: String[1],
    SIDE: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    SCALE: Float32[Flat],
    M: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    INFO: Int32
) -> None: ...

@bind("CGEBAL")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def cgebal(
    JOB: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    ILO: Int32,
    IHI: Int32,
    SCALE: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEBD2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9))])
def cgebd2(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    TAUQ: Complex64[Flat],
    TAUP: Complex64[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEBRD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def cgebrd(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    TAUQ: Complex64[Flat],
    TAUP: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGECON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def cgecon(
    NORM: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEDMD")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Return('K', 0), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Arg(21), Addr(Arg(22)), Arg(23), Addr(Arg(24)), Arg(25), Addr(Arg(26)), Arg(27), Addr(Arg(28)), Return('INFO', 1)])
def cgedmd(
    JOBS: String[1],
    JOBZ: String[1],
    JOBR: String[1],
    JOBF: String[1],
    WHTSVD: Int32,
    M: Int32,
    N: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    Y: Complex64[LDY, Flat],
    LDY: Int32,
    NRNK: Int32,
    TOL: Float32,
    EIGS: Complex64[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    RES: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    W: Complex64[LDW, Flat],
    LDW: Int32,
    S: Complex64[LDS, Flat],
    LDS: Int32,
    ZWORK: Complex64[Flat],
    LZWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32
) -> tuple[Int32, Int32]: ...

@bind("CGEDMDQ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Return('K', 0), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22)), Arg(23), Addr(Arg(24)), Arg(25), Addr(Arg(26)), Arg(27), Addr(Arg(28)), Arg(29), Addr(Arg(30)), Arg(31), Addr(Arg(32)), Return('INFO', 1)])
def cgedmdq(
    JOBS: String[1],
    JOBZ: String[1],
    JOBR: String[1],
    JOBQ: String[1],
    JOBT: String[1],
    JOBF: String[1],
    WHTSVD: Int32,
    M: Int32,
    N: Int32,
    F: Complex64[LDF, Flat],
    LDF: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    Y: Complex64[LDY, Flat],
    LDY: Int32,
    NRNK: Int32,
    TOL: Float32,
    EIGS: Complex64[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    RES: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    S: Complex64[LDS, Flat],
    LDS: Int32,
    ZWORK: Complex64[Flat],
    LZWORK: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32
) -> tuple[Int32, Int32]: ...

@bind("CGEEQU")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def cgeequ(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    R: Float32[Flat],
    C: Float32[Flat],
    ROWCND: Float32,
    COLCND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("CGEEQUB")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def cgeequb(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    R: Float32[Flat],
    C: Float32[Flat],
    ROWCND: Float32,
    COLCND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("CGEES")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14))])
def cgees(
    JOBVS: String[1],
    SORT: String[1],
    SELECT: Bool,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    SDIM: Int32,
    W: Complex64[Flat],
    VS: Complex64[LDVS, Flat],
    LDVS: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEESX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17))])
def cgeesx(
    JOBVS: String[1],
    SORT: String[1],
    SELECT: Bool,
    SENSE: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    SDIM: Int32,
    W: Complex64[Flat],
    VS: Complex64[LDVS, Flat],
    LDVS: Int32,
    RCONDE: Float32,
    RCONDV: Float32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def cgeev(
    JOBVL: String[1],
    JOBVR: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    W: Complex64[Flat],
    VL: Complex64[LDVL, Flat],
    LDVL: Int32,
    VR: Complex64[LDVR, Flat],
    LDVR: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21))])
def cgeevx(
    BALANC: String[1],
    JOBVL: String[1],
    JOBVR: String[1],
    SENSE: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    W: Complex64[Flat],
    VL: Complex64[LDVL, Flat],
    LDVL: Int32,
    VR: Complex64[LDVR, Flat],
    LDVR: Int32,
    ILO: Int32,
    IHI: Int32,
    SCALE: Float32[Flat],
    ABNRM: Float32,
    RCONDE: Float32[Flat],
    RCONDV: Float32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEHD2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def cgehd2(
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEHRD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def cgehrd(
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGEJSV")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20))])
def cgejsv(
    JOBA: String[1],
    JOBU: String[1],
    JOBV: String[1],
    JOBR: String[1],
    JOBT: String[1],
    JOBP: String[1],
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    SVA: Float32[N],
    U: Complex64[LDU, Flat],
    LDU: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    CWORK: Complex64[LWORK],
    LWORK: Int32,
    RWORK: Float32[LRWORK],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGELQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def cgelq(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[Flat],
    TSIZE: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGELQ2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def cgelq2(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CGELQF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def cgelqf(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGELQT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def cgelqt(
    M: Int32,
    N: Int32,
    MB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CGELQT3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def cgelqt3(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("CGELS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def cgels(
    TRANS: String[1],
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGELSD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14))])
def cgelsd(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    S: Float32[Flat],
    RCOND: Float32,
    RANK: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGELSS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def cgelss(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    S: Float32[Flat],
    RCOND: Float32,
    RANK: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGELST")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def cgelst(
    TRANS: String[1],
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGELSY")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def cgelsy(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    JPVT: Int32[Flat],
    RCOND: Float32,
    RANK: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEMLQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def cgemlq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[Flat],
    TSIZE: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGEMLQT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def cgemlqt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    MB: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEMQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def cgemqr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[Flat],
    TSIZE: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGEMQRT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def cgemqrt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    NB: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEQL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def cgeql2(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEQLF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def cgeqlf(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGEQP3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def cgeqp3(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    JPVT: Int32[Flat],
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEQP3RK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17))])
def cgeqp3rk(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    KMAX: Int32,
    ABSTOL: Float32,
    RELTOL: Float32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    K: Int32,
    MAXC2NRMK: Float32,
    RELMAXC2NRMK: Float32,
    JPIV: Int32[Flat],
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def cgeqr(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[Flat],
    TSIZE: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGEQR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def cgeqr2(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEQR2P")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def cgeqr2p(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEQRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def cgeqrf(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGEQRFP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def cgeqrfp(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGEQRT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def cgeqrt(
    M: Int32,
    N: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CGEQRT2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def cgeqrt2(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("CGEQRT3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def cgeqrt3(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("CGERFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def cgerfs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGERFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def cgerfsx(
    TRANS: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    R: Float32[Flat],
    C: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGERQ2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def cgerq2(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CGERQF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def cgerqf(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGESC2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def cgesc2(
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    RHS: Complex64[Flat],
    IPIV: Int32[Flat],
    JPIV: Int32[Flat],
    SCALE: Float32
) -> None: ...

@bind("CGESDD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14))])
def cgesdd(
    JOBZ: String[1],
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    U: Complex64[LDU, Flat],
    LDU: Int32,
    VT: Complex64[LDVT, Flat],
    LDVT: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGESV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def cgesv(
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CGESVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14))])
def cgesvd(
    JOBU: String[1],
    JOBVT: String[1],
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    U: Complex64[LDU, Flat],
    LDU: Int32,
    VT: Complex64[LDVT, Flat],
    LDVT: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGESVDQ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Addr(Arg(21))])
def cgesvdq(
    JOBA: String[1],
    JOBP: String[1],
    JOBR: String[1],
    JOBU: String[1],
    JOBV: String[1],
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    U: Complex64[LDU, Flat],
    LDU: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    NUMRANK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    CWORK: Complex64[Flat],
    LCWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGESVDX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Addr(Arg(21))])
def cgesvdx(
    JOBU: String[1],
    JOBVT: String[1],
    RANGE: String[1],
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    NS: Int32,
    S: Float32[Flat],
    U: Complex64[LDU, Flat],
    LDU: Int32,
    VT: Complex64[LDVT, Flat],
    LDVT: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGESVJ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def cgesvj(
    JOBA: String[1],
    JOBU: String[1],
    JOBV: String[1],
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    SVA: Float32[N],
    MV: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    CWORK: Complex64[LWORK],
    LWORK: Int32,
    RWORK: Float32[LRWORK],
    LRWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGESVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def cgesvx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float32[Flat],
    C: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGESVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22)), Arg(23), Arg(24), Arg(25), Addr(Arg(26))])
def cgesvxx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float32[Flat],
    C: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    RPVGRW: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGETC2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def cgetc2(
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    JPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGETF2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def cgetf2(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGETRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def cgetrf(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGETRF2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def cgetrf2(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGETRI")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def cgetri(
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGETRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def cgetrs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CGETSLS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def cgetsls(
    TRANS: String[1],
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGETSQRHRT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def cgetsqrhrt(
    M: Int32,
    N: Int32,
    MB1: Int32,
    NB1: Int32,
    NB2: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGGBAK")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def cggbak(
    JOB: String[1],
    SIDE: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    LSCALE: Float32[Flat],
    RSCALE: Float32[Flat],
    M: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    INFO: Int32
) -> None: ...

@bind("CGGBAL")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11))])
def cggbal(
    JOB: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    ILO: Int32,
    IHI: Int32,
    LSCALE: Float32[Flat],
    RSCALE: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGGES")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20))])
def cgges(
    JOBVSL: String[1],
    JOBVSR: String[1],
    SORT: String[1],
    SELCTG: Bool,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    SDIM: Int32,
    ALPHA: Complex64[Flat],
    BETA: Complex64[Flat],
    VSL: Complex64[LDVSL, Flat],
    LDVSL: Int32,
    VSR: Complex64[LDVSR, Flat],
    LDVSR: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("CGGES3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20))])
def cgges3(
    JOBVSL: String[1],
    JOBVSR: String[1],
    SORT: String[1],
    SELCTG: Bool,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    SDIM: Int32,
    ALPHA: Complex64[Flat],
    BETA: Complex64[Flat],
    VSL: Complex64[LDVSL, Flat],
    LDVSL: Int32,
    VSR: Complex64[LDVSR, Flat],
    LDVSR: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("CGGESX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25))])
def cggesx(
    JOBVSL: String[1],
    JOBVSR: String[1],
    SORT: String[1],
    SELCTG: Bool,
    SENSE: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    SDIM: Int32,
    ALPHA: Complex64[Flat],
    BETA: Complex64[Flat],
    VSL: Complex64[LDVSL, Flat],
    LDVSL: Int32,
    VSR: Complex64[LDVSR, Flat],
    LDVSR: Int32,
    RCONDE: Float32[2],
    RCONDV: Float32[2],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    LIWORK: Int32,
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("CGGEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def cggev(
    JOBVL: String[1],
    JOBVR: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    ALPHA: Complex64[Flat],
    BETA: Complex64[Flat],
    VL: Complex64[LDVL, Flat],
    LDVL: Int32,
    VR: Complex64[LDVR, Flat],
    LDVR: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGGEV3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def cggev3(
    JOBVL: String[1],
    JOBVR: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    ALPHA: Complex64[Flat],
    BETA: Complex64[Flat],
    VL: Complex64[LDVL, Flat],
    LDVL: Int32,
    VR: Complex64[LDVR, Flat],
    LDVR: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGGEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24)), Arg(25), Arg(26), Arg(27), Addr(Arg(28))])
def cggevx(
    BALANC: String[1],
    JOBVL: String[1],
    JOBVR: String[1],
    SENSE: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    ALPHA: Complex64[Flat],
    BETA: Complex64[Flat],
    VL: Complex64[LDVL, Flat],
    LDVL: Int32,
    VR: Complex64[LDVR, Flat],
    LDVR: Int32,
    ILO: Int32,
    IHI: Int32,
    LSCALE: Float32[Flat],
    RSCALE: Float32[Flat],
    ABNRM: Float32,
    BBNRM: Float32,
    RCONDE: Float32[Flat],
    RCONDV: Float32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("CGGGLM")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def cggglm(
    N: Int32,
    M: Int32,
    P: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    D: Complex64[Flat],
    X: Complex64[Flat],
    Y: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGGHD3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def cgghd3(
    COMPQ: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGGHRD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def cgghrd(
    COMPQ: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    INFO: Int32
) -> None: ...

@bind("CGGLSE")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def cgglse(
    M: Int32,
    N: Int32,
    P: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    C: Complex64[Flat],
    D: Complex64[Flat],
    X: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGGQRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def cggqrf(
    N: Int32,
    M: Int32,
    P: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAUA: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    TAUB: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGGRQF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def cggrqf(
    M: Int32,
    P: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAUA: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    TAUB: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGGSVD3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Addr(Arg(24))])
def cggsvd3(
    JOBU: String[1],
    JOBV: String[1],
    JOBQ: String[1],
    M: Int32,
    N: Int32,
    P: Int32,
    K: Int32,
    L: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    ALPHA: Float32[Flat],
    BETA: Float32[Flat],
    U: Complex64[LDU, Flat],
    LDU: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGGSVP3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Arg(23), Addr(Arg(24)), Addr(Arg(25))])
def cggsvp3(
    JOBU: String[1],
    JOBV: String[1],
    JOBQ: String[1],
    M: Int32,
    P: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    TOLA: Float32,
    TOLB: Float32,
    K: Int32,
    L: Int32,
    U: Complex64[LDU, Flat],
    LDU: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    IWORK: Int32[Flat],
    RWORK: Float32[Flat],
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGSVJ0")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def cgsvj0(
    JOBV: String[1],
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    D: Complex64[N],
    SVA: Float32[N],
    MV: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    EPS: Float32,
    SFMIN: Float32,
    TOL: Float32,
    NSWEEP: Int32,
    WORK: Complex64[LWORK],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGSVJ1")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Addr(Arg(17))])
def cgsvj1(
    JOBV: String[1],
    M: Int32,
    N: Int32,
    N1: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    D: Complex64[N],
    SVA: Float32[N],
    MV: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    EPS: Float32,
    SFMIN: Float32,
    TOL: Float32,
    NSWEEP: Int32,
    WORK: Complex64[LWORK],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CGTCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def cgtcon(
    NORM: String[1],
    N: Int32,
    DL: Complex64[Flat],
    D: Complex64[Flat],
    DU: Complex64[Flat],
    DU2: Complex64[Flat],
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CGTRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def cgtrfs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    DL: Complex64[Flat],
    D: Complex64[Flat],
    DU: Complex64[Flat],
    DLF: Complex64[Flat],
    DF: Complex64[Flat],
    DUF: Complex64[Flat],
    DU2: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGTSV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def cgtsv(
    N: Int32,
    NRHS: Int32,
    DL: Complex64[Flat],
    D: Complex64[Flat],
    DU: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CGTSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def cgtsvx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    DL: Complex64[Flat],
    D: Complex64[Flat],
    DU: Complex64[Flat],
    DLF: Complex64[Flat],
    DF: Complex64[Flat],
    DUF: Complex64[Flat],
    DU2: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGTTRF")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def cgttrf(
    N: Int32,
    DL: Complex64[Flat],
    D: Complex64[Flat],
    DU: Complex64[Flat],
    DU2: Complex64[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CGTTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def cgttrs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    DL: Complex64[Flat],
    D: Complex64[Flat],
    DU: Complex64[Flat],
    DU2: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CGTTS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9))])
def cgtts2(
    ITRANS: Int32,
    N: Int32,
    NRHS: Int32,
    DL: Complex64[Flat],
    D: Complex64[Flat],
    DU: Complex64[Flat],
    DU2: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("CHB2ST_KERNELS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14)])
def chb2st_kernels(
    UPLO: String[1],
    WANTZ: Bool,
    TTYPE: Int32,
    ST: Int32,
    ED: Int32,
    SWEEP: Int32,
    N: Int32,
    NB: Int32,
    IB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    V: Complex64[Flat],
    TAU: Complex64[Flat],
    LDVT: Int32,
    WORK: Complex64[Flat]
) -> None: ...

@bind("CHBEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def chbev(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHBEV_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def chbev_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHBEVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def chbevd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHBEVD_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def chbevd_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHBEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Arg(20), Arg(21), Addr(Arg(22))])
def chbevx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHBEVX_2STAGE")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def chbevx_2stage(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHBGST")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13))])
def chbgst(
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    BB: Complex64[LDBB, Flat],
    LDBB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHBGV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14))])
def chbgv(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    BB: Complex64[LDBB, Flat],
    LDBB: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHBGVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18))])
def chbgvd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    BB: Complex64[LDBB, Flat],
    LDBB: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHBGVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Arg(24), Addr(Arg(25))])
def chbgvx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    BB: Complex64[LDBB, Flat],
    LDBB: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHBTRD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def chbtrd(
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CHECON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def checon(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CHECON_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def checon_3(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CHECON_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def checon_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CHEEQUB")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def cheequb(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CHEEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def cheev(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    W: Float32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHEEV_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def cheev_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    W: Float32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHEEVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def cheevd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    W: Float32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHEEVD_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def cheevd_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    W: Float32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHEEVR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Addr(Arg(22))])
def cheevr(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHEEVR_2STAGE")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Addr(Arg(22))])
def cheevr_2stage(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHEEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Addr(Arg(20))])
def cheevx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHEEVX_2STAGE")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Addr(Arg(20))])
def cheevx_2stage(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHEGS2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def chegs2(
    ITYPE: Int32,
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CHEGST")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def chegst(
    ITYPE: Int32,
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CHEGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def chegv(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    W: Float32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHEGV_2STAGE")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def chegv_2stage(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    W: Float32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHEGVD")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def chegvd(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    W: Float32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHEGVX")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def chegvx(
    ITYPE: Int32,
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHERFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def cherfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHERFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def cherfsx(
    UPLO: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    S: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHESV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def chesv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHESV_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def chesv_aa(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHESV_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def chesv_aa_2stage(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TB: Complex64[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHESV_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def chesv_rk(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHESV_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def chesv_rook(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHESVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def chesvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHESVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Arg(24), Addr(Arg(25))])
def chesvxx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    S: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    RPVGRW: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHESWAPR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def cheswapr(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, N],
    LDA: Int32,
    I1: Int32,
    I2: Int32
) -> None: ...

@bind("CHETD2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7))])
def chetd2(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    TAU: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CHETF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def chetf2(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHETF2_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def chetf2_rk(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHETF2_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def chetf2_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHETRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def chetrd(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRD_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def chetrd_2stage(
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    TAU: Complex64[Flat],
    HOUS2: Complex64[Flat],
    LHOUS2: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRD_HB2ST")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def chetrd_hb2st(
    STAGE1: String[1],
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    HOUS: Complex64[Flat],
    LHOUS: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRD_HE2HB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def chetrd_he2hb(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def chetrf(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRF_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def chetrf_aa(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRF_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def chetrf_aa_2stage(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TB: Complex64[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRF_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def chetrf_rk(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRF_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def chetrf_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def chetri(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CHETRI2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def chetri2(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRI2X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def chetri2x(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[N + NB + 1, Flat],
    NB: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRI_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def chetri_3(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRI_3X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def chetri_3x(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    WORK: Complex64[N + NB + 1, Flat],
    NB: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRI_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def chetri_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CHETRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def chetrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRS2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def chetrs2(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CHETRS_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def chetrs_3(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRS_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def chetrs_aa(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRS_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def chetrs_aa_2stage(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TB: Complex64[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CHETRS_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def chetrs_rook(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CHFRK")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9)])
def chfrk(
    TRANSR: String[1],
    UPLO: String[1],
    TRANS: String[1],
    N: Int32,
    K: Int32,
    ALPHA: Float32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    BETA: Float32,
    C: Complex64[Flat]
) -> None: ...

@bind("CHGEQZ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def chgeqz(
    JOB: String[1],
    COMPQ: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Complex64[LDH, Flat],
    LDH: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    ALPHA: Complex64[Flat],
    BETA: Complex64[Flat],
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHLA_TRANSTYPE")
@external
@native_call([Addr(Arg(0))])
def chla_transtype(
    TRANS: Int32
) -> String[1]: ...

@bind("CHPCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def chpcon(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CHPEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def chpev(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHPEVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def chpevd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHPEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Addr(Arg(18))])
def chpevx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHPGST")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def chpgst(
    ITYPE: Int32,
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    BP: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CHPGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def chpgv(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    BP: Complex64[Flat],
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHPGVD")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def chpgvd(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    BP: Complex64[Flat],
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CHPGVX")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20))])
def chpgvx(
    ITYPE: Int32,
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    BP: Complex64[Flat],
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHPRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14))])
def chprfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    AFP: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHPSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def chpsv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CHPSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def chpsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    AFP: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHPTRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def chptrd(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    D: Float32[Flat],
    E: Float32[Flat],
    TAU: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CHPTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def chptrf(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHPTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5))])
def chptri(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CHPTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def chptrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CHSEIN")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Addr(Arg(18))])
def chsein(
    SIDE: String[1],
    EIGSRC: String[1],
    INITV: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    H: Complex64[LDH, Flat],
    LDH: Int32,
    W: Complex64[Flat],
    VL: Complex64[LDVL, Flat],
    LDVL: Int32,
    VR: Complex64[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    IFAILL: Int32[Flat],
    IFAILR: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CHSEQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def chseqr(
    JOB: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Complex64[LDH, Flat],
    LDH: Int32,
    W: Complex64[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CLA_GBAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def cla_gbamv(
    TRANS: Int32,
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    ALPHA: Float32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    X: Complex64[Flat],
    INCX: Int32,
    BETA: Float32,
    Y: Float32[Flat],
    INCY: Int32
) -> None: ...

@bind("CLA_GBRCOND_C")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13)])
def cla_gbrcond_c(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex64[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    C: Float32[Flat],
    CAPPLY: Bool,
    INFO: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat]
) -> Float32: ...

@bind("CLA_GBRCOND_X")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Arg(12)])
def cla_gbrcond_x(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex64[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    X: Complex64[Flat],
    INFO: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat]
) -> Float32: ...

@bind("CLA_GBRFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Arg(22), Arg(23), Arg(24), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28)), Addr(Arg(29)), Addr(Arg(30))])
def cla_gbrfsx_extended(
    PREC_TYPE: Int32,
    TRANS_TYPE: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex64[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    Y: Complex64[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float32[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    RES: Complex64[Flat],
    AYB: Float32[Flat],
    DY: Complex64[Flat],
    Y_TAIL: Complex64[Flat],
    RCOND: Float32,
    ITHRESH: Int32,
    RTHRESH: Float32,
    DZ_UB: Float32,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("CLA_GBRPVGRW")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def cla_gbrpvgrw(
    N: Int32,
    KL: Int32,
    KU: Int32,
    NCOLS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex64[LDAFB, Flat],
    LDAFB: Int32
) -> Float32: ...

@bind("CLA_GEAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def cla_geamv(
    TRANS: Int32,
    M: Int32,
    N: Int32,
    ALPHA: Float32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    X: Complex64[Flat],
    INCX: Int32,
    BETA: Float32,
    Y: Float32[Flat],
    INCY: Int32
) -> None: ...

@bind("CLA_GERCOND_C")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11)])
def cla_gercond_c(
    TRANS: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    C: Float32[Flat],
    CAPPLY: Bool,
    INFO: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat]
) -> Float32: ...

@bind("CLA_GERCOND_X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10)])
def cla_gercond_x(
    TRANS: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    X: Complex64[Flat],
    INFO: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat]
) -> Float32: ...

@bind("CLA_GERFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28))])
def cla_gerfsx_extended(
    PREC_TYPE: Int32,
    TRANS_TYPE: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    Y: Complex64[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float32[Flat],
    N_NORMS: Int32,
    ERRS_N: Float32[NRHS, Flat],
    ERRS_C: Float32[NRHS, Flat],
    RES: Complex64[Flat],
    AYB: Float32[Flat],
    DY: Complex64[Flat],
    Y_TAIL: Complex64[Flat],
    RCOND: Float32,
    ITHRESH: Int32,
    RTHRESH: Float32,
    DZ_UB: Float32,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("CLA_GERPVGRW")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def cla_gerpvgrw(
    N: Int32,
    NCOLS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32
) -> Float32: ...

@bind("CLA_HEAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def cla_heamv(
    UPLO: Int32,
    N: Int32,
    ALPHA: Float32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    X: Complex64[Flat],
    INCX: Int32,
    BETA: Float32,
    Y: Float32[Flat],
    INCY: Int32
) -> None: ...

@bind("CLA_HERCOND_C")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11)])
def cla_hercond_c(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    C: Float32[Flat],
    CAPPLY: Bool,
    INFO: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat]
) -> Float32: ...

@bind("CLA_HERCOND_X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10)])
def cla_hercond_x(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    X: Complex64[Flat],
    INFO: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat]
) -> Float32: ...

@bind("CLA_HERFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28))])
def cla_herfsx_extended(
    PREC_TYPE: Int32,
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    Y: Complex64[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float32[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    RES: Complex64[Flat],
    AYB: Float32[Flat],
    DY: Complex64[Flat],
    Y_TAIL: Complex64[Flat],
    RCOND: Float32,
    ITHRESH: Int32,
    RTHRESH: Float32,
    DZ_UB: Float32,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("CLA_HERPVGRW")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8)])
def cla_herpvgrw(
    UPLO: String[1],
    N: Int32,
    INFO: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLA_LIN_BERR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5)])
def cla_lin_berr(
    N: Int32,
    NZ: Int32,
    NRHS: Int32,
    RES: Complex64[N, NRHS],
    AYB: Float32[N, NRHS],
    BERR: Float32[NRHS]
) -> None: ...

@bind("CLA_PORCOND_C")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10)])
def cla_porcond_c(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    C: Float32[Flat],
    CAPPLY: Bool,
    INFO: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat]
) -> Float32: ...

@bind("CLA_PORCOND_X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9)])
def cla_porcond_x(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    X: Complex64[Flat],
    INFO: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat]
) -> Float32: ...

@bind("CLA_PORFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Addr(Arg(22)), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27))])
def cla_porfsx_extended(
    PREC_TYPE: Int32,
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    COLEQU: Bool,
    C: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    Y: Complex64[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float32[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    RES: Complex64[Flat],
    AYB: Float32[Flat],
    DY: Complex64[Flat],
    Y_TAIL: Complex64[Flat],
    RCOND: Float32,
    ITHRESH: Int32,
    RTHRESH: Float32,
    DZ_UB: Float32,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("CLA_PORPVGRW")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def cla_porpvgrw(
    UPLO: String[1],
    NCOLS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLA_SYAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def cla_syamv(
    UPLO: Int32,
    N: Int32,
    ALPHA: Float32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    X: Complex64[Flat],
    INCX: Int32,
    BETA: Float32,
    Y: Float32[Flat],
    INCY: Int32
) -> None: ...

@bind("CLA_SYRCOND_C")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11)])
def cla_syrcond_c(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    C: Float32[Flat],
    CAPPLY: Bool,
    INFO: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat]
) -> Float32: ...

@bind("CLA_SYRCOND_X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10)])
def cla_syrcond_x(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    X: Complex64[Flat],
    INFO: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat]
) -> Float32: ...

@bind("CLA_SYRFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28))])
def cla_syrfsx_extended(
    PREC_TYPE: Int32,
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    Y: Complex64[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float32[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    RES: Complex64[Flat],
    AYB: Float32[Flat],
    DY: Complex64[Flat],
    Y_TAIL: Complex64[Flat],
    RCOND: Float32,
    ITHRESH: Int32,
    RTHRESH: Float32,
    DZ_UB: Float32,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("CLA_SYRPVGRW")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8)])
def cla_syrpvgrw(
    UPLO: String[1],
    N: Int32,
    INFO: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLA_WWADDW")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def cla_wwaddw(
    N: Int32,
    X: Complex64[Flat],
    Y: Complex64[Flat],
    W: Complex64[Flat]
) -> None: ...

@bind("CLABRD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def clabrd(
    M: Int32,
    N: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    TAUQ: Complex64[Flat],
    TAUP: Complex64[Flat],
    X: Complex64[LDX, Flat],
    LDX: Int32,
    Y: Complex64[LDY, Flat],
    LDY: Int32
) -> None: ...

@bind("CLACGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2))])
def clacgv(
    N: Int32,
    X: Complex64[Flat],
    INCX: Int32
) -> None: ...

@bind("CLACN2")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5)])
def clacn2(
    N: Int32,
    V: Complex64[Flat],
    X: Complex64[Flat],
    EST: Float32,
    KASE: Int32,
    ISAVE: Int32[3]
) -> None: ...

@bind("CLACON")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def clacon(
    N: Int32,
    V: Complex64[N],
    X: Complex64[N],
    EST: Float32,
    KASE: Int32
) -> None: ...

@bind("CLACP2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def clacp2(
    UPLO: String[1],
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("CLACPY")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def clacpy(
    UPLO: String[1],
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("CLACRM")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def clacrm(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    RWORK: Float32[Flat]
) -> None: ...

@bind("CLACRT")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def clacrt(
    N: Int32,
    CX: Complex64[Flat],
    INCX: Int32,
    CY: Complex64[Flat],
    INCY: Int32,
    C: Complex64,
    S: Complex64
) -> None: ...

@bind("CLADIV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def cladiv(
    X: Complex64,
    Y: Complex64
) -> Complex64: ...

@bind("CLAED0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def claed0(
    QSIZ: Int32,
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    QSTORE: Complex64[LDQS, Flat],
    LDQS: Int32,
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CLAED7")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def claed7(
    N: Int32,
    CUTPNT: Int32,
    QSIZ: Int32,
    TLVLS: Int32,
    CURLVL: Int32,
    CURPBM: Int32,
    D: Float32[Flat],
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    RHO: Float32,
    INDXQ: Int32[Flat],
    QSTORE: Float32[Flat],
    QPTR: Int32[Flat],
    PRMPTR: Int32[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32[Flat],
    GIVCOL: Int32[2, Flat],
    GIVNUM: Float32[2, Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CLAED8")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20))])
def claed8(
    K: Int32,
    N: Int32,
    QSIZ: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    D: Float32[Flat],
    RHO: Float32,
    CUTPNT: Int32,
    Z: Float32[Flat],
    DLAMBDA: Float32[Flat],
    Q2: Complex64[LDQ2, Flat],
    LDQ2: Int32,
    W: Float32[Flat],
    INDXP: Int32[Flat],
    INDX: Int32[Flat],
    INDXQ: Int32[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32,
    GIVCOL: Int32[2, Flat],
    GIVNUM: Float32[2, Flat],
    INFO: Int32
) -> None: ...

@bind("CLAEIN")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12))])
def claein(
    RIGHTV: Bool,
    NOINIT: Bool,
    N: Int32,
    H: Complex64[LDH, Flat],
    LDH: Int32,
    W: Complex64,
    V: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    RWORK: Float32[Flat],
    EPS3: Float32,
    SMLNUM: Float32,
    INFO: Int32
) -> None: ...

@bind("CLAESY")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7))])
def claesy(
    A: Complex64,
    B: Complex64,
    C: Complex64,
    RT1: Complex64,
    RT2: Complex64,
    EVSCAL: Complex64,
    CS1: Complex64,
    SN1: Complex64
) -> None: ...

@bind("CLAEV2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def claev2(
    A: Complex64,
    B: Complex64,
    C: Complex64,
    RT1: Float32,
    RT2: Float32,
    CS1: Float32,
    SN1: Complex64
) -> None: ...

@bind("CLAG2Z")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def clag2z(
    M: Int32,
    N: Int32,
    SA: Complex64[LDSA, Flat],
    LDSA: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("CLAGS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12))])
def clags2(
    UPPER: Bool,
    A1: Float32,
    A2: Complex64,
    A3: Float32,
    B1: Float32,
    B2: Complex64,
    B3: Float32,
    CSU: Float32,
    SNU: Complex64,
    CSV: Float32,
    SNV: Complex64,
    CSQ: Float32,
    SNQ: Complex64
) -> None: ...

@bind("CLAGTM")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def clagtm(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    ALPHA: Float32,
    DL: Complex64[Flat],
    D: Complex64[Flat],
    DU: Complex64[Flat],
    X: Complex64[LDX, Flat],
    LDX: Int32,
    BETA: Float32,
    B: Complex64[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("CLAHEF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def clahef(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    W: Complex64[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("CLAHEF_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9)])
def clahef_aa(
    UPLO: String[1],
    J1: Int32,
    M: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    H: Complex64[LDH, Flat],
    LDH: Int32,
    WORK: Complex64[Flat]
) -> None: ...

@bind("CLAHEF_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def clahef_rk(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    W: Complex64[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("CLAHEF_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def clahef_rook(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    W: Complex64[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("CLAHQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def clahqr(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Complex64[LDH, Flat],
    LDH: Int32,
    W: Complex64[Flat],
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    INFO: Int32
) -> None: ...

@bind("CLAHR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def clahr2(
    N: Int32,
    K: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[NB],
    T: Complex64[LDT, NB],
    LDT: Int32,
    Y: Complex64[LDY, NB],
    LDY: Int32
) -> None: ...

@bind("CLAIC1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8))])
def claic1(
    JOB: Int32,
    J: Int32,
    X: Complex64[J],
    SEST: Float32,
    W: Complex64[J],
    GAMMA: Complex64,
    SESTPR: Float32,
    S: Complex64,
    C: Complex64
) -> None: ...

@bind("CLALS0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19)), Addr(Arg(20)), Addr(Arg(21)), Arg(22), Addr(Arg(23))])
def clals0(
    ICOMPQ: Int32,
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    NRHS: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    BX: Complex64[LDBX, Flat],
    LDBX: Int32,
    PERM: Int32[Flat],
    GIVPTR: Int32,
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    GIVNUM: Float32[LDGNUM, Flat],
    LDGNUM: Int32,
    POLES: Float32[LDGNUM, Flat],
    DIFL: Float32[Flat],
    DIFR: Float32[LDGNUM, Flat],
    Z: Float32[Flat],
    K: Int32,
    C: Float32,
    S: Float32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CLALSA")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Arg(22), Arg(23), Arg(24), Addr(Arg(25))])
def clalsa(
    ICOMPQ: Int32,
    SMLSIZ: Int32,
    N: Int32,
    NRHS: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    BX: Complex64[LDBX, Flat],
    LDBX: Int32,
    U: Float32[LDU, Flat],
    LDU: Int32,
    VT: Float32[LDU, Flat],
    K: Int32[Flat],
    DIFL: Float32[LDU, Flat],
    DIFR: Float32[LDU, Flat],
    Z: Float32[LDU, Flat],
    POLES: Float32[LDU, Flat],
    GIVPTR: Int32[Flat],
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    PERM: Int32[LDGCOL, Flat],
    GIVNUM: Float32[LDU, Flat],
    C: Float32[Flat],
    S: Float32[Flat],
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CLALSD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def clalsd(
    UPLO: String[1],
    SMLSIZ: Int32,
    N: Int32,
    NRHS: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    RCOND: Float32,
    RANK: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CLAMSWLQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def clamswlq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    MB: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CLAMTSQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def clamtsqr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    MB: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CLANGB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def clangb(
    NORM: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLANGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def clange(
    NORM: String[1],
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLANGT")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4)])
def clangt(
    NORM: String[1],
    N: Int32,
    DL: Complex64[Flat],
    D: Complex64[Flat],
    DU: Complex64[Flat]
) -> Float32: ...

@bind("CLANHB")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def clanhb(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    K: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLANHE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def clanhe(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLANHF")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5)])
def clanhf(
    NORM: String[1],
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[Flat],
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLANHP")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4)])
def clanhp(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLANHS")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4)])
def clanhs(
    NORM: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLANHT")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3)])
def clanht(
    NORM: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Complex64[Flat]
) -> Float32: ...

@bind("CLANSB")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def clansb(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    K: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLANSP")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4)])
def clansp(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLANSY")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def clansy(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLANTB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def clantb(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    K: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLANTP")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5)])
def clantp(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    AP: Complex64[Flat],
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLANTR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def clantr(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("CLAPLL")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def clapll(
    N: Int32,
    X: Complex64[Flat],
    INCX: Int32,
    Y: Complex64[Flat],
    INCY: Int32,
    SSMIN: Float32
) -> None: ...

@bind("CLAPMR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def clapmr(
    FORWRD: Bool,
    M: Int32,
    N: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    K: Int32[Flat]
) -> None: ...

@bind("CLAPMT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def clapmt(
    FORWRD: Bool,
    M: Int32,
    N: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    K: Int32[Flat]
) -> None: ...

@bind("CLAQGB")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11)])
def claqgb(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    R: Float32[Flat],
    C: Float32[Flat],
    ROWCND: Float32,
    COLCND: Float32,
    AMAX: Float32,
    EQUED: String[1]
) -> None: ...

@bind("CLAQGE")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9)])
def claqge(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    R: Float32[Flat],
    C: Float32[Flat],
    ROWCND: Float32,
    COLCND: Float32,
    AMAX: Float32,
    EQUED: String[1]
) -> None: ...

@bind("CLAQHB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8)])
def claqhb(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    EQUED: String[1]
) -> None: ...

@bind("CLAQHE")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7)])
def claqhe(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    EQUED: String[1]
) -> None: ...

@bind("CLAQHP")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6)])
def claqhp(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    EQUED: String[1]
) -> None: ...

@bind("CLAQP2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9)])
def claqp2(
    M: Int32,
    N: Int32,
    OFFSET: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    JPVT: Int32[Flat],
    TAU: Complex64[Flat],
    VN1: Float32[Flat],
    VN2: Float32[Flat],
    WORK: Complex64[Flat]
) -> None: ...

@bind("CLAQP2RK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def claqp2rk(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    IOFFSET: Int32,
    KMAX: Int32,
    ABSTOL: Float32,
    RELTOL: Float32,
    KP1: Int32,
    MAXC2NRM: Float32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    K: Int32,
    MAXC2NRMK: Float32,
    RELMAXC2NRMK: Float32,
    JPIV: Int32[Flat],
    TAU: Complex64[Flat],
    VN1: Float32[Flat],
    VN2: Float32[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CLAQP3RK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23))])
def claqp3rk(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    IOFFSET: Int32,
    NB: Int32,
    ABSTOL: Float32,
    RELTOL: Float32,
    KP1: Int32,
    MAXC2NRM: Float32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    DONE: Bool,
    KB: Int32,
    MAXC2NRMK: Float32,
    RELMAXC2NRMK: Float32,
    JPIV: Int32[Flat],
    TAU: Complex64[Flat],
    VN1: Float32[Flat],
    VN2: Float32[Flat],
    AUXV: Complex64[Flat],
    F: Complex64[LDF, Flat],
    LDF: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CLAQPS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def claqps(
    M: Int32,
    N: Int32,
    OFFSET: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    JPVT: Int32[Flat],
    TAU: Complex64[Flat],
    VN1: Float32[Flat],
    VN2: Float32[Flat],
    AUXV: Complex64[Flat],
    F: Complex64[LDF, Flat],
    LDF: Int32
) -> None: ...

@bind("CLAQR0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def claqr0(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Complex64[LDH, Flat],
    LDH: Int32,
    W: Complex64[Flat],
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CLAQR1")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5)])
def claqr1(
    N: Int32,
    H: Complex64[LDH, Flat],
    LDH: Int32,
    S1: Complex64,
    S2: Complex64,
    V: Complex64[Flat]
) -> None: ...

@bind("CLAQR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Addr(Arg(20)), Arg(21), Addr(Arg(22)), Arg(23), Addr(Arg(24))])
def claqr2(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    KTOP: Int32,
    KBOT: Int32,
    NW: Int32,
    H: Complex64[LDH, Flat],
    LDH: Int32,
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    NS: Int32,
    ND: Int32,
    SH: Complex64[Flat],
    V: Complex64[LDV, Flat],
    LDV: Int32,
    NH: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    NV: Int32,
    WV: Complex64[LDWV, Flat],
    LDWV: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32
) -> None: ...

@bind("CLAQR3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Addr(Arg(20)), Arg(21), Addr(Arg(22)), Arg(23), Addr(Arg(24))])
def claqr3(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    KTOP: Int32,
    KBOT: Int32,
    NW: Int32,
    H: Complex64[LDH, Flat],
    LDH: Int32,
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    NS: Int32,
    ND: Int32,
    SH: Complex64[Flat],
    V: Complex64[LDV, Flat],
    LDV: Int32,
    NH: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    NV: Int32,
    WV: Complex64[LDWV, Flat],
    LDWV: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32
) -> None: ...

@bind("CLAQR4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def claqr4(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Complex64[LDH, Flat],
    LDH: Int32,
    W: Complex64[Flat],
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CLAQR5")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Addr(Arg(21)), Arg(22), Addr(Arg(23))])
def claqr5(
    WANTT: Bool,
    WANTZ: Bool,
    KACC22: Int32,
    N: Int32,
    KTOP: Int32,
    KBOT: Int32,
    NSHFTS: Int32,
    S: Complex64[Flat],
    H: Complex64[LDH, Flat],
    LDH: Int32,
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    U: Complex64[LDU, Flat],
    LDU: Int32,
    NV: Int32,
    WV: Complex64[LDWV, Flat],
    LDWV: Int32,
    NH: Int32,
    WH: Complex64[LDWH, Flat],
    LDWH: Int32
) -> None: ...

@bind("CLAQSB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8)])
def claqsb(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    EQUED: String[1]
) -> None: ...

@bind("CLAQSP")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6)])
def claqsp(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    EQUED: String[1]
) -> None: ...

@bind("CLAQSY")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7)])
def claqsy(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    EQUED: String[1]
) -> None: ...

@bind("CLAQZ0")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Return('INFO', 0)])
def claqz0(
    WANTS: String[1],
    WANTQ: String[1],
    WANTZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    ALPHA: Complex64[Flat],
    BETA: Complex64[Flat],
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    REC: Int32
) -> Int32: ...

@bind("CLAQZ1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def claqz1(
    ILQ: Bool,
    ILZ: Bool,
    K: Int32,
    ISTARTM: Int32,
    ISTOPM: Int32,
    IHI: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    NQ: Int32,
    QSTART: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    NZ: Int32,
    ZSTART: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32
) -> None: ...

@bind("CLAQZ2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Return('NS', 0), Return('ND', 1), Arg(15), Arg(16), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Arg(21), Addr(Arg(22)), Arg(23), Addr(Arg(24)), Return('INFO', 2)])
def claqz2(
    ILSCHUR: Bool,
    ILQ: Bool,
    ILZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    NW: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    ALPHA: Complex64[Flat],
    BETA: Complex64[Flat],
    QC: Complex64[LDQC, Flat],
    LDQC: Int32,
    ZC: Complex64[LDZC, Flat],
    LDZC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    REC: Int32
) -> tuple[Int32, Int32, Int32]: ...

@bind("CLAQZ3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Return('INFO', 0)])
def claqz3(
    ILSCHUR: Bool,
    ILQ: Bool,
    ILZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    NSHIFTS: Int32,
    NBLOCK_DESIRED: Int32,
    ALPHA: Complex64[Flat],
    BETA: Complex64[Flat],
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    QC: Complex64[LDQC, Flat],
    LDQC: Int32,
    ZC: Complex64[LDZC, Flat],
    LDZC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32
) -> Int32: ...

@bind("CLAR1V")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Addr(Arg(19)), Arg(20)])
def clar1v(
    N: Int32,
    B1: Int32,
    BN: Int32,
    LAMBDA: Float32,
    D: Float32[Flat],
    L: Float32[Flat],
    LD: Float32[Flat],
    LLD: Float32[Flat],
    PIVMIN: Float32,
    GAPTOL: Float32,
    Z: Complex64[Flat],
    WANTNC: Bool,
    NEGCNT: Int32,
    ZTZ: Float32,
    MINGMA: Float32,
    R: Int32,
    ISUPPZ: Int32[Flat],
    NRMINV: Float32,
    RESID: Float32,
    RQCORR: Float32,
    WORK: Float32[Flat]
) -> None: ...

@bind("CLAR2V")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def clar2v(
    N: Int32,
    X: Complex64[Flat],
    Y: Complex64[Flat],
    Z: Complex64[Flat],
    INCX: Int32,
    C: Float32[Flat],
    S: Complex64[Flat],
    INCC: Int32
) -> None: ...

@bind("CLARCM")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def clarcm(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    RWORK: Float32[Flat]
) -> None: ...

@bind("CLARF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def clarf(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Complex64[Flat],
    INCV: Int32,
    TAU: Complex64,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat]
) -> None: ...

@bind("CLARF1F")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def clarf1f(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Complex64[Flat],
    INCV: Int32,
    TAU: Complex64,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat]
) -> None: ...

@bind("CLARF1L")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def clarf1l(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Complex64[Flat],
    INCV: Int32,
    TAU: Complex64,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat]
) -> None: ...

@bind("CLARFB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14))])
def clarfb(
    SIDE: String[1],
    TRANS: String[1],
    DIRECT: String[1],
    STOREV: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("CLARFB_GETT")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def clarfb_gett(
    IDENT: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("CLARFG")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def clarfg(
    N: Int32,
    ALPHA: Complex64,
    X: Complex64[Flat],
    INCX: Int32,
    TAU: Complex64
) -> None: ...

@bind("CLARFGP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def clarfgp(
    N: Int32,
    ALPHA: Complex64,
    X: Complex64[Flat],
    INCX: Int32,
    TAU: Complex64
) -> None: ...

@bind("CLARFT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def clarft(
    DIRECT: String[1],
    STOREV: String[1],
    N: Int32,
    K: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    TAU: Complex64[Flat],
    T: Complex64[LDT, Flat],
    LDT: Int32
) -> None: ...

@bind("CLARFX")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def clarfx(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Complex64[Flat],
    TAU: Complex64,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat]
) -> None: ...

@bind("CLARFY")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def clarfy(
    UPLO: String[1],
    N: Int32,
    V: Complex64[Flat],
    INCV: Int32,
    TAU: Complex64,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat]
) -> None: ...

@bind("CLARGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def clargv(
    N: Int32,
    X: Complex64[Flat],
    INCX: Int32,
    Y: Complex64[Flat],
    INCY: Int32,
    C: Float32[Flat],
    INCC: Int32
) -> None: ...

@bind("CLARNV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3)])
def clarnv(
    IDIST: Int32,
    ISEED: Int32[4],
    N: Int32,
    X: Complex64[Flat]
) -> None: ...

@bind("CLARRV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def clarrv(
    N: Int32,
    VL: Float32,
    VU: Float32,
    D: Float32[Flat],
    L: Float32[Flat],
    PIVMIN: Float32,
    ISPLIT: Int32[Flat],
    M: Int32,
    DOL: Int32,
    DOU: Int32,
    MINRGP: Float32,
    RTOL1: Float32,
    RTOL2: Float32,
    W: Float32[Flat],
    WERR: Float32[Flat],
    WGAP: Float32[Flat],
    IBLOCK: Int32[Flat],
    INDEXW: Int32[Flat],
    GERS: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CLARSCL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def clarscl2(
    M: Int32,
    N: Int32,
    D: Float32[Flat],
    X: Complex64[LDX, Flat],
    LDX: Int32
) -> None: ...

@bind("CLARTG")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def clartg(
    f: Complex64,
    g: Complex64,
    c: Float32,
    s: Complex64,
    r: Complex64
) -> None: ...

@bind("CLARTV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def clartv(
    N: Int32,
    X: Complex64[Flat],
    INCX: Int32,
    Y: Complex64[Flat],
    INCY: Int32,
    C: Float32[Flat],
    S: Complex64[Flat],
    INCC: Int32
) -> None: ...

@bind("CLARZ")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9)])
def clarz(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    L: Int32,
    V: Complex64[Flat],
    INCV: Int32,
    TAU: Complex64,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat]
) -> None: ...

@bind("CLARZB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15))])
def clarzb(
    SIDE: String[1],
    TRANS: String[1],
    DIRECT: String[1],
    STOREV: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("CLARZT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def clarzt(
    DIRECT: String[1],
    STOREV: String[1],
    N: Int32,
    K: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    TAU: Complex64[Flat],
    T: Complex64[LDT, Flat],
    LDT: Int32
) -> None: ...

@bind("CLASCL")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def clascl(
    TYPE: String[1],
    KL: Int32,
    KU: Int32,
    CFROM: Float32,
    CTO: Float32,
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("CLASCL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def clascl2(
    M: Int32,
    N: Int32,
    D: Float32[Flat],
    X: Complex64[LDX, Flat],
    LDX: Int32
) -> None: ...

@bind("CLASET")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def claset(
    UPLO: String[1],
    M: Int32,
    N: Int32,
    ALPHA: Complex64,
    BETA: Complex64,
    A: Complex64[LDA, Flat],
    LDA: Int32
) -> None: ...

@bind("CLASR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8))])
def clasr(
    SIDE: String[1],
    PIVOT: String[1],
    DIRECT: String[1],
    M: Int32,
    N: Int32,
    C: Float32[Flat],
    S: Float32[Flat],
    A: Complex64[LDA, Flat],
    LDA: Int32
) -> None: ...

@bind("CLASSQ")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def classq(
    n: Int32,
    x: Complex64[Flat],
    incx: Int32,
    scale: Float32,
    sumsq: Float32
) -> None: ...

@bind("CLASWLQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def claswlq(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CLASWP")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def claswp(
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    K1: Int32,
    K2: Int32,
    IPIV: Int32[Flat],
    INCX: Int32
) -> None: ...

@bind("CLASYF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def clasyf(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    W: Complex64[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("CLASYF_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9)])
def clasyf_aa(
    UPLO: String[1],
    J1: Int32,
    M: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    H: Complex64[LDH, Flat],
    LDH: Int32,
    WORK: Complex64[Flat]
) -> None: ...

@bind("CLASYF_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def clasyf_rk(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    W: Complex64[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("CLASYF_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def clasyf_rook(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    W: Complex64[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("CLATBS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def clatbs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    X: Complex64[Flat],
    SCALE: Float32,
    CNORM: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CLATDF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8)])
def clatdf(
    IJOB: Int32,
    N: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    RHS: Complex64[Flat],
    RDSUM: Float32,
    RDSCAL: Float32,
    IPIV: Int32[Flat],
    JPIV: Int32[Flat]
) -> None: ...

@bind("CLATPS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def clatps(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    AP: Complex64[Flat],
    X: Complex64[Flat],
    SCALE: Float32,
    CNORM: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CLATRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8))])
def clatrd(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Float32[Flat],
    TAU: Complex64[Flat],
    W: Complex64[LDW, Flat],
    LDW: Int32
) -> None: ...

@bind("CLATRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def clatrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    X: Complex64[Flat],
    SCALE: Float32,
    CNORM: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CLATRS3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def clatrs3(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    SCALE: Float32[Flat],
    CNORM: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CLATRZ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6)])
def clatrz(
    M: Int32,
    N: Int32,
    L: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat]
) -> None: ...

@bind("CLATSQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def clatsqr(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CLAUNHR_COL_GETRFNP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def claunhr_col_getrfnp(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    D: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CLAUNHR_COL_GETRFNP2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def claunhr_col_getrfnp2(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    D: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CLAUU2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def clauu2(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("CLAUUM")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def clauum(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("CPBCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def cpbcon(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPBEQU")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8))])
def cpbequ(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("CPBRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def cpbrfs(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex64[LDAFB, Flat],
    LDAFB: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPBSTF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def cpbstf(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    INFO: Int32
) -> None: ...

@bind("CPBSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def cpbsv(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CPBSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20))])
def cpbsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex64[LDAFB, Flat],
    LDAFB: Int32,
    EQUED: String[1],
    S: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPBTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def cpbtf2(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    INFO: Int32
) -> None: ...

@bind("CPBTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def cpbtrf(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    INFO: Int32
) -> None: ...

@bind("CPBTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def cpbtrs(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CPFTRF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4))])
def cpftrf(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CPFTRI")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4))])
def cpftri(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CPFTRS")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def cpftrs(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CPOCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def cpocon(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPOEQU")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def cpoequ(
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("CPOEQUB")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def cpoequb(
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("CPORFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15))])
def cporfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPORFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Addr(Arg(22))])
def cporfsx(
    UPLO: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    S: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPOSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def cposv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CPOSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def cposvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    EQUED: String[1],
    S: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPOSVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def cposvxx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    EQUED: String[1],
    S: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    RPVGRW: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPOTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def cpotf2(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("CPOTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def cpotrf(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("CPOTRF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def cpotrf2(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("CPOTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def cpotri(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("CPOTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def cpotrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CPPCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def cppcon(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPPEQU")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def cppequ(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("CPPRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def cpprfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    AFP: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPPSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def cppsv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CPPSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Arg(14), Arg(15), Arg(16), Addr(Arg(17))])
def cppsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    AFP: Complex64[Flat],
    EQUED: String[1],
    S: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPPTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def cpptrf(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CPPTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def cpptri(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CPPTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def cpptrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CPSTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def cpstf2(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    PIV: Int32[N],
    RANK: Int32,
    TOL: Float32,
    WORK: Float32[2 * N],
    INFO: Int32
) -> None: ...

@bind("CPSTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def cpstrf(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    PIV: Int32[N],
    RANK: Int32,
    TOL: Float32,
    WORK: Float32[2 * N],
    INFO: Int32
) -> None: ...

@bind("CPTCON")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def cptcon(
    N: Int32,
    D: Float32[Flat],
    E: Complex64[Flat],
    ANORM: Float32,
    RCOND: Float32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPTEQR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def cpteqr(
    COMPZ: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPTRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15))])
def cptrfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    D: Float32[Flat],
    E: Complex64[Flat],
    DF: Float32[Flat],
    EF: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPTSV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def cptsv(
    N: Int32,
    NRHS: Int32,
    D: Float32[Flat],
    E: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CPTSVX")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def cptsvx(
    FACT: String[1],
    N: Int32,
    NRHS: Int32,
    D: Float32[Flat],
    E: Complex64[Flat],
    DF: Float32[Flat],
    EF: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CPTTRF")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3))])
def cpttrf(
    N: Int32,
    D: Float32[Flat],
    E: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CPTTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def cpttrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    D: Float32[Flat],
    E: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CPTTS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def cptts2(
    IUPLO: Int32,
    N: Int32,
    NRHS: Int32,
    D: Float32[Flat],
    E: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("CROT")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def crot(
    N: Int32,
    CX: Complex64[Flat],
    INCX: Int32,
    CY: Complex64[Flat],
    INCY: Int32,
    C: Float32,
    S: Complex64
) -> None: ...

@bind("CRSCL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def crscl(
    N: Int32,
    A: Complex64,
    X: Complex64[Flat],
    INCX: Int32
) -> None: ...

@bind("CSPCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def cspcon(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CSPMV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def cspmv(
    UPLO: String[1],
    N: Int32,
    ALPHA: Complex64,
    AP: Complex64[Flat],
    X: Complex64[Flat],
    INCX: Int32,
    BETA: Complex64,
    Y: Complex64[Flat],
    INCY: Int32
) -> None: ...

@bind("CSPR")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def cspr(
    UPLO: String[1],
    N: Int32,
    ALPHA: Complex64,
    X: Complex64[Flat],
    INCX: Int32,
    AP: Complex64[Flat]
) -> None: ...

@bind("CSPRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14))])
def csprfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    AFP: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSPSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def cspsv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CSPSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def cspsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    AFP: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSPTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def csptrf(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSPTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5))])
def csptri(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CSPTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def csptrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CSRSCL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def csrscl(
    N: Int32,
    SA: Float32,
    SX: Complex64[Flat],
    INCX: Int32
) -> None: ...

@bind("CSTEDC")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def cstedc(
    COMPZ: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSTEGR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Addr(Arg(19))])
def cstegr(
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSTEIN")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12))])
def cstein(
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    M: Int32,
    W: Float32[Flat],
    IBLOCK: Int32[Flat],
    ISPLIT: Int32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSTEMR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Addr(Arg(20))])
def cstemr(
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    M: Int32,
    W: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    NZC: Int32,
    ISUPPZ: Int32[Flat],
    TRYRAC: Bool,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSTEQR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def csteqr(
    COMPZ: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def csycon(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYCON_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def csycon_3(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYCON_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def csycon_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYCONV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def csyconv(
    UPLO: String[1],
    WAY: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    E: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYCONVF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def csyconvf(
    UPLO: String[1],
    WAY: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYCONVF_ROOK")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def csyconvf_rook(
    UPLO: String[1],
    WAY: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYEQUB")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def csyequb(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYMV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def csymv(
    UPLO: String[1],
    N: Int32,
    ALPHA: Complex64,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    X: Complex64[Flat],
    INCX: Int32,
    BETA: Complex64,
    Y: Complex64[Flat],
    INCY: Int32
) -> None: ...

@bind("CSYR")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def csyr(
    UPLO: String[1],
    N: Int32,
    ALPHA: Complex64,
    X: Complex64[Flat],
    INCX: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32
) -> None: ...

@bind("CSYRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def csyrfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYRFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def csyrfsx(
    UPLO: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    S: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def csysv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYSV_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def csysv_aa(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYSV_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def csysv_aa_2stage(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TB: Complex64[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYSV_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def csysv_rk(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYSV_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def csysv_rook(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def csysvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYSVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Arg(24), Addr(Arg(25))])
def csysvxx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AF: Complex64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    S: Float32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    RPVGRW: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYSWAPR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def csyswapr(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, N],
    LDA: Int32,
    I1: Int32,
    I2: Int32
) -> None: ...

@bind("CSYTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def csytf2(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYTF2_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def csytf2_rk(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYTF2_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def csytf2_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def csytrf(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYTRF_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def csytrf_aa(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYTRF_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def csytrf_aa_2stage(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TB: Complex64[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYTRF_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def csytrf_rk(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYTRF_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def csytrf_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def csytri(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYTRI2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def csytri2(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYTRI2X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def csytri2x(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[N + NB + 1, Flat],
    NB: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYTRI_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def csytri_3(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYTRI_3X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def csytri_3x(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    WORK: Complex64[N + NB + 1, Flat],
    NB: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYTRI_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def csytri_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def csytrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYTRS2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def csytrs2(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CSYTRS_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def csytrs_3(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    E: Complex64[Flat],
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYTRS_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def csytrs_aa(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYTRS_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def csytrs_aa_2stage(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TB: Complex64[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CSYTRS_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def csytrs_rook(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CTBCON")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def ctbcon(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CTBRFS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def ctbrfs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CTBTRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def ctbtrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Complex64[LDAB, Flat],
    LDAB: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CTFSM")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def ctfsm(
    TRANSR: String[1],
    SIDE: String[1],
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    M: Int32,
    N: Int32,
    ALPHA: Complex64,
    A: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("CTFTRI")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def ctftri(
    TRANSR: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CTFTTP")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def ctfttp(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    ARF: Complex64[Flat],
    AP: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CTFTTR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def ctfttr(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    ARF: Complex64[Flat],
    A: Complex64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("CTGEVC")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16))])
def ctgevc(
    SIDE: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    S: Complex64[LDS, Flat],
    LDS: Int32,
    P: Complex64[LDP, Flat],
    LDP: Int32,
    VL: Complex64[LDVL, Flat],
    LDVL: Int32,
    VR: Complex64[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CTGEX2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12))])
def ctgex2(
    WANTQ: Bool,
    WANTZ: Bool,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    J1: Int32,
    INFO: Int32
) -> None: ...

@bind("CTGEXC")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13))])
def ctgexc(
    WANTQ: Bool,
    WANTZ: Bool,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    IFST: Int32,
    ILST: Int32,
    INFO: Int32
) -> None: ...

@bind("CTGSEN")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Addr(Arg(22)), Addr(Arg(23))])
def ctgsen(
    IJOB: Int32,
    WANTQ: Bool,
    WANTZ: Bool,
    SELECT: Bool[Flat],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    ALPHA: Complex64[Flat],
    BETA: Complex64[Flat],
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    Z: Complex64[LDZ, Flat],
    LDZ: Int32,
    M: Int32,
    PL: Float32,
    PR: Float32,
    DIF: Float32[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CTGSJA")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Addr(Arg(24))])
def ctgsja(
    JOBU: String[1],
    JOBV: String[1],
    JOBQ: String[1],
    M: Int32,
    P: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    TOLA: Float32,
    TOLB: Float32,
    ALPHA: Float32[Flat],
    BETA: Float32[Flat],
    U: Complex64[LDU, Flat],
    LDU: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    WORK: Complex64[Flat],
    NCYCLE: Int32,
    INFO: Int32
) -> None: ...

@bind("CTGSNA")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def ctgsna(
    JOB: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    VL: Complex64[LDVL, Flat],
    LDVL: Int32,
    VR: Complex64[LDVR, Flat],
    LDVR: Int32,
    S: Float32[Flat],
    DIF: Float32[Flat],
    MM: Int32,
    M: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CTGSY2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Addr(Arg(18)), Addr(Arg(19))])
def ctgsy2(
    TRANS: String[1],
    IJOB: Int32,
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    D: Complex64[LDD, Flat],
    LDD: Int32,
    E: Complex64[LDE, Flat],
    LDE: Int32,
    F: Complex64[LDF, Flat],
    LDF: Int32,
    SCALE: Float32,
    RDSUM: Float32,
    RDSCAL: Float32,
    INFO: Int32
) -> None: ...

@bind("CTGSYL")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21))])
def ctgsyl(
    TRANS: String[1],
    IJOB: Int32,
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    D: Complex64[LDD, Flat],
    LDD: Int32,
    E: Complex64[LDE, Flat],
    LDE: Int32,
    F: Complex64[LDF, Flat],
    LDF: Int32,
    SCALE: Float32,
    DIF: Float32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CTPCON")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def ctpcon(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    AP: Complex64[Flat],
    RCOND: Float32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CTPLQT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def ctplqt(
    M: Int32,
    N: Int32,
    L: Int32,
    MB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CTPLQT2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def ctplqt2(
    M: Int32,
    N: Int32,
    L: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("CTPMLQT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def ctpmlqt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    MB: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CTPMQRT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def ctpmqrt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    NB: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CTPQRT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def ctpqrt(
    M: Int32,
    N: Int32,
    L: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CTPQRT2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def ctpqrt2(
    M: Int32,
    N: Int32,
    L: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("CTPRFB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def ctprfb(
    SIDE: String[1],
    TRANS: String[1],
    DIRECT: String[1],
    STOREV: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    V: Complex64[LDV, Flat],
    LDV: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    WORK: Complex64[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("CTPRFS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14))])
def ctprfs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CTPTRI")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4))])
def ctptri(
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    AP: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CTPTRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def ctptrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex64[Flat],
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CTPTTF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def ctpttf(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    ARF: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CTPTTR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def ctpttr(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    A: Complex64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("CTRCON")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def ctrcon(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    RCOND: Float32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CTREVC")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14))])
def ctrevc(
    SIDE: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    VL: Complex64[LDVL, Flat],
    LDVL: Int32,
    VR: Complex64[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CTREVC3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def ctrevc3(
    SIDE: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    VL: Complex64[LDVL, Flat],
    LDVL: Int32,
    VR: Complex64[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CTREXC")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8))])
def ctrexc(
    COMPQ: String[1],
    N: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    IFST: Int32,
    ILST: Int32,
    INFO: Int32
) -> None: ...

@bind("CTRRFS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15))])
def ctrrfs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    X: Complex64[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Complex64[Flat],
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CTRSEN")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def ctrsen(
    JOB: String[1],
    COMPQ: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    W: Complex64[Flat],
    M: Int32,
    S: Float32,
    SEP: Float32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CTRSNA")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def ctrsna(
    JOB: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    VL: Complex64[LDVL, Flat],
    LDVL: Int32,
    VR: Complex64[LDVR, Flat],
    LDVR: Int32,
    S: Float32[Flat],
    SEP: Float32[Flat],
    MM: Int32,
    M: Int32,
    WORK: Complex64[LDWORK, Flat],
    LDWORK: Int32,
    RWORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("CTRSYL")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12))])
def ctrsyl(
    TRANA: String[1],
    TRANB: String[1],
    ISGN: Int32,
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    SCALE: Float32,
    INFO: Int32
) -> None: ...

@bind("CTRSYL3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def ctrsyl3(
    TRANA: String[1],
    TRANB: String[1],
    ISGN: Int32,
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    SCALE: Float32,
    SWORK: Float32[LDSWORK, Flat],
    LDSWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CTRTI2")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def ctrti2(
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("CTRTRI")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def ctrtri(
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("CTRTRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def ctrtrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    B: Complex64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("CTRTTF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def ctrttf(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    ARF: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CTRTTP")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def ctrttp(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    AP: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CTZRZF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def ctzrzf(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNBDB")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Addr(Arg(21))])
def cunbdb(
    TRANS: String[1],
    SIGNS: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex64[LDX11, Flat],
    LDX11: Int32,
    X12: Complex64[LDX12, Flat],
    LDX12: Int32,
    X21: Complex64[LDX21, Flat],
    LDX21: Int32,
    X22: Complex64[LDX22, Flat],
    LDX22: Int32,
    THETA: Float32[Flat],
    PHI: Float32[Flat],
    TAUP1: Complex64[Flat],
    TAUP2: Complex64[Flat],
    TAUQ1: Complex64[Flat],
    TAUQ2: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNBDB1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def cunbdb1(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex64[LDX11, Flat],
    LDX11: Int32,
    X21: Complex64[LDX21, Flat],
    LDX21: Int32,
    THETA: Float32[Flat],
    PHI: Float32[Flat],
    TAUP1: Complex64[Flat],
    TAUP2: Complex64[Flat],
    TAUQ1: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNBDB2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def cunbdb2(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex64[LDX11, Flat],
    LDX11: Int32,
    X21: Complex64[LDX21, Flat],
    LDX21: Int32,
    THETA: Float32[Flat],
    PHI: Float32[Flat],
    TAUP1: Complex64[Flat],
    TAUP2: Complex64[Flat],
    TAUQ1: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNBDB3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def cunbdb3(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex64[LDX11, Flat],
    LDX11: Int32,
    X21: Complex64[LDX21, Flat],
    LDX21: Int32,
    THETA: Float32[Flat],
    PHI: Float32[Flat],
    TAUP1: Complex64[Flat],
    TAUP2: Complex64[Flat],
    TAUQ1: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNBDB4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def cunbdb4(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex64[LDX11, Flat],
    LDX11: Int32,
    X21: Complex64[LDX21, Flat],
    LDX21: Int32,
    THETA: Float32[Flat],
    PHI: Float32[Flat],
    TAUP1: Complex64[Flat],
    TAUP2: Complex64[Flat],
    TAUQ1: Complex64[Flat],
    PHANTOM: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNBDB5")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def cunbdb5(
    M1: Int32,
    M2: Int32,
    N: Int32,
    X1: Complex64[Flat],
    INCX1: Int32,
    X2: Complex64[Flat],
    INCX2: Int32,
    Q1: Complex64[LDQ1, Flat],
    LDQ1: Int32,
    Q2: Complex64[LDQ2, Flat],
    LDQ2: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNBDB6")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def cunbdb6(
    M1: Int32,
    M2: Int32,
    N: Int32,
    X1: Complex64[Flat],
    INCX1: Int32,
    X2: Complex64[Flat],
    INCX2: Int32,
    Q1: Complex64[LDQ1, Flat],
    LDQ1: Int32,
    Q2: Complex64[LDQ2, Flat],
    LDQ2: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNCSD")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25)), Arg(26), Addr(Arg(27)), Arg(28), Addr(Arg(29)), Arg(30), Addr(Arg(31))])
def cuncsd(
    JOBU1: String[1],
    JOBU2: String[1],
    JOBV1T: String[1],
    JOBV2T: String[1],
    TRANS: String[1],
    SIGNS: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex64[LDX11, Flat],
    LDX11: Int32,
    X12: Complex64[LDX12, Flat],
    LDX12: Int32,
    X21: Complex64[LDX21, Flat],
    LDX21: Int32,
    X22: Complex64[LDX22, Flat],
    LDX22: Int32,
    THETA: Float32[Flat],
    U1: Complex64[LDU1, Flat],
    LDU1: Int32,
    U2: Complex64[LDU2, Flat],
    LDU2: Int32,
    V1T: Complex64[LDV1T, Flat],
    LDV1T: Int32,
    V2T: Complex64[LDV2T, Flat],
    LDV2T: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CUNCSD2BY1")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Arg(21), Addr(Arg(22))])
def cuncsd2by1(
    JOBU1: String[1],
    JOBU2: String[1],
    JOBV1T: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex64[LDX11, Flat],
    LDX11: Int32,
    X21: Complex64[LDX21, Flat],
    LDX21: Int32,
    THETA: Float32[Flat],
    U1: Complex64[LDU1, Flat],
    LDU1: Int32,
    U2: Complex64[LDU2, Flat],
    LDU2: Int32,
    V1T: Complex64[LDV1T, Flat],
    LDV1T: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("CUNG2L")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def cung2l(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CUNG2R")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def cung2r(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CUNGBR")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def cungbr(
    VECT: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNGHR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def cunghr(
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNGL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def cungl2(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CUNGLQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def cunglq(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNGQL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def cungql(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNGQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def cungqr(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNGR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def cungr2(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CUNGRQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def cungrq(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNGTR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def cungtr(
    UPLO: String[1],
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNGTSQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def cungtsqr(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNGTSQR_ROW")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def cungtsqr_row(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNHR_COL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def cunhr_col(
    M: Int32,
    N: Int32,
    NB: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    T: Complex64[LDT, Flat],
    LDT: Int32,
    D: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CUNM22")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def cunm22(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    N1: Int32,
    N2: Int32,
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNM2L")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def cunm2l(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CUNM2R")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def cunm2r(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CUNMBR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def cunmbr(
    VECT: String[1],
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNMHR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def cunmhr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNML2")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def cunml2(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CUNMLQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def cunmlq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNMQL")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def cunmql(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNMQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def cunmqr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNMR2")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def cunmr2(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CUNMR3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def cunmr3(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CUNMRQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def cunmrq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNMRZ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def cunmrz(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUNMTR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def cunmtr(
    SIDE: String[1],
    UPLO: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32,
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("CUPGTR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def cupgtr(
    UPLO: String[1],
    N: Int32,
    AP: Complex64[Flat],
    TAU: Complex64[Flat],
    Q: Complex64[LDQ, Flat],
    LDQ: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("CUPMTR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def cupmtr(
    SIDE: String[1],
    UPLO: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    AP: Complex64[Flat],
    TAU: Complex64[Flat],
    C: Complex64[LDC, Flat],
    LDC: Int32,
    WORK: Complex64[Flat],
    INFO: Int32
) -> None: ...

@bind("DBBCSD")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Arg(23), Arg(24), Arg(25), Arg(26), Addr(Arg(27)), Addr(Arg(28))])
def dbbcsd(
    JOBU1: String[1],
    JOBU2: String[1],
    JOBV1T: String[1],
    JOBV2T: String[1],
    TRANS: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    THETA: Float64[Flat],
    PHI: Float64[Flat],
    U1: Float64[LDU1, Flat],
    LDU1: Int32,
    U2: Float64[LDU2, Flat],
    LDU2: Int32,
    V1T: Float64[LDV1T, Flat],
    LDV1T: Int32,
    V2T: Float64[LDV2T, Flat],
    LDV2T: Int32,
    B11D: Float64[Flat],
    B11E: Float64[Flat],
    B12D: Float64[Flat],
    B12E: Float64[Flat],
    B21D: Float64[Flat],
    B21E: Float64[Flat],
    B22D: Float64[Flat],
    B22E: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DBDSDC")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def dbdsdc(
    UPLO: String[1],
    COMPQ: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    U: Float64[LDU, Flat],
    LDU: Int32,
    VT: Float64[LDVT, Flat],
    LDVT: Int32,
    Q: Float64[Flat],
    IQ: Int32[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DBDSQR")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14))])
def dbdsqr(
    UPLO: String[1],
    N: Int32,
    NCVT: Int32,
    NRU: Int32,
    NCC: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    VT: Float64[LDVT, Flat],
    LDVT: Int32,
    U: Float64[LDU, Flat],
    LDU: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DBDSVDX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16))])
def dbdsvdx(
    UPLO: String[1],
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    NS: Int32,
    S: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DDISNA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def ddisna(
    JOB: String[1],
    M: Int32,
    N: Int32,
    D: Float64[Flat],
    SEP: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGBBRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def dgbbrd(
    VECT: String[1],
    M: Int32,
    N: Int32,
    NCC: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    PT: Float64[LDPT, Flat],
    LDPT: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGBCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def dgbcon(
    NORM: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGBEQU")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11))])
def dgbequ(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    R: Float64[Flat],
    C: Float64[Flat],
    ROWCND: Float64,
    COLCND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("DGBEQUB")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11))])
def dgbequb(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    R: Float64[Flat],
    C: Float64[Flat],
    ROWCND: Float64,
    COLCND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("DGBRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Addr(Arg(18))])
def dgbrfs(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    AFB: Float64[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGBRFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22)), Arg(23), Arg(24), Arg(25), Addr(Arg(26))])
def dgbrfsx(
    TRANS: String[1],
    EQUED: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    AFB: Float64[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    R: Float64[Flat],
    C: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGBSV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def dgbsv(
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DGBSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def dgbsvx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    AFB: Float64[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float64[Flat],
    C: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGBSVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Addr(Arg(24)), Arg(25), Arg(26), Arg(27), Addr(Arg(28))])
def dgbsvxx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    AFB: Float64[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float64[Flat],
    C: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    RPVGRW: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGBTF2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def dgbtf2(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGBTRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def dgbtrf(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGBTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dgbtrs(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DGEBAK")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def dgebak(
    JOB: String[1],
    SIDE: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    SCALE: Float64[Flat],
    M: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    INFO: Int32
) -> None: ...

@bind("DGEBAL")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def dgebal(
    JOB: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    ILO: Int32,
    IHI: Int32,
    SCALE: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEBD2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9))])
def dgebd2(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    TAUQ: Float64[Flat],
    TAUP: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEBRD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dgebrd(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    TAUQ: Float64[Flat],
    TAUP: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGECON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def dgecon(
    NORM: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    ANORM: Float64,
    RCOND: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEDMD")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Return('K', 0), Arg(13), Arg(14), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25)), Arg(26), Addr(Arg(27)), Return('INFO', 1)])
def dgedmd(
    JOBS: String[1],
    JOBZ: String[1],
    JOBR: String[1],
    JOBF: String[1],
    WHTSVD: Int32,
    M: Int32,
    N: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    Y: Float64[LDY, Flat],
    LDY: Int32,
    NRNK: Int32,
    TOL: Float64,
    REIG: Float64[Flat],
    IMEIG: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    RES: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    W: Float64[LDW, Flat],
    LDW: Int32,
    S: Float64[LDS, Flat],
    LDS: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32
) -> tuple[Int32, Int32]: ...

@bind("DGEDMDQ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Return('K', 0), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25)), Arg(26), Addr(Arg(27)), Arg(28), Addr(Arg(29)), Arg(30), Addr(Arg(31)), Return('INFO', 1)])
def dgedmdq(
    JOBS: String[1],
    JOBZ: String[1],
    JOBR: String[1],
    JOBQ: String[1],
    JOBT: String[1],
    JOBF: String[1],
    WHTSVD: Int32,
    M: Int32,
    N: Int32,
    F: Float64[LDF, Flat],
    LDF: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    Y: Float64[LDY, Flat],
    LDY: Int32,
    NRNK: Int32,
    TOL: Float64,
    REIG: Float64[Flat],
    IMEIG: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    RES: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    S: Float64[LDS, Flat],
    LDS: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32
) -> tuple[Int32, Int32]: ...

@bind("DGEEQU")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def dgeequ(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    R: Float64[Flat],
    C: Float64[Flat],
    ROWCND: Float64,
    COLCND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("DGEEQUB")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def dgeequb(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    R: Float64[Flat],
    C: Float64[Flat],
    ROWCND: Float64,
    COLCND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("DGEES")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14))])
def dgees(
    JOBVS: String[1],
    SORT: String[1],
    SELECT: Bool,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    SDIM: Int32,
    WR: Float64[Flat],
    WI: Float64[Flat],
    VS: Float64[LDVS, Flat],
    LDVS: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEESX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def dgeesx(
    JOBVS: String[1],
    SORT: String[1],
    SELECT: Bool,
    SENSE: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    SDIM: Int32,
    WR: Float64[Flat],
    WI: Float64[Flat],
    VS: Float64[LDVS, Flat],
    LDVS: Int32,
    RCONDE: Float64,
    RCONDV: Float64,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dgeev(
    JOBVL: String[1],
    JOBVR: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    WR: Float64[Flat],
    WI: Float64[Flat],
    VL: Float64[LDVL, Flat],
    LDVL: Int32,
    VR: Float64[LDVR, Flat],
    LDVR: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGEEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Addr(Arg(22))])
def dgeevx(
    BALANC: String[1],
    JOBVL: String[1],
    JOBVR: String[1],
    SENSE: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    WR: Float64[Flat],
    WI: Float64[Flat],
    VL: Float64[LDVL, Flat],
    LDVL: Int32,
    VR: Float64[LDVR, Flat],
    LDVR: Int32,
    ILO: Int32,
    IHI: Int32,
    SCALE: Float64[Flat],
    ABNRM: Float64,
    RCONDE: Float64[Flat],
    RCONDV: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEHD2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def dgehd2(
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEHRD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dgehrd(
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGEJSV")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18))])
def dgejsv(
    JOBA: String[1],
    JOBU: String[1],
    JOBV: String[1],
    JOBR: String[1],
    JOBT: String[1],
    JOBP: String[1],
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    SVA: Float64[N],
    U: Float64[LDU, Flat],
    LDU: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    WORK: Float64[LWORK],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGELQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dgelq(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[Flat],
    TSIZE: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGELQ2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def dgelq2(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGELQF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dgelqf(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGELQT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def dgelqt(
    M: Int32,
    N: Int32,
    MB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGELQT3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def dgelqt3(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("DGELS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dgels(
    TRANS: String[1],
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGELSD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def dgelsd(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    S: Float64[Flat],
    RCOND: Float64,
    RANK: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGELSS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dgelss(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    S: Float64[Flat],
    RCOND: Float64,
    RANK: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGELST")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dgelst(
    TRANS: String[1],
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGELSY")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dgelsy(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    JPVT: Int32[Flat],
    RCOND: Float64,
    RANK: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGEMLQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dgemlq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[Flat],
    TSIZE: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGEMLQT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def dgemlqt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    MB: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEMQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dgemqr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[Flat],
    TSIZE: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGEMQRT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def dgemqrt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    NB: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEQL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def dgeql2(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEQLF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dgeqlf(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGEQP3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dgeqp3(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    JPVT: Int32[Flat],
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGEQP3RK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def dgeqp3rk(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    KMAX: Int32,
    ABSTOL: Float64,
    RELTOL: Float64,
    A: Float64[LDA, Flat],
    LDA: Int32,
    K: Int32,
    MAXC2NRMK: Float64,
    RELMAXC2NRMK: Float64,
    JPIV: Int32[Flat],
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dgeqr(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[Flat],
    TSIZE: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGEQR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def dgeqr2(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEQR2P")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def dgeqr2p(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEQRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dgeqrf(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGEQRFP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dgeqrfp(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGEQRT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def dgeqrt(
    M: Int32,
    N: Int32,
    NB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGEQRT2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def dgeqrt2(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("DGEQRT3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def dgeqrt3(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("DGERFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def dgerfs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGERFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def dgerfsx(
    TRANS: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    R: Float64[Flat],
    C: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGERQ2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def dgerq2(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGERQF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dgerqf(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGESC2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def dgesc2(
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    RHS: Float64[Flat],
    IPIV: Int32[Flat],
    JPIV: Int32[Flat],
    SCALE: Float64
) -> None: ...

@bind("DGESDD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def dgesdd(
    JOBZ: String[1],
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    U: Float64[LDU, Flat],
    LDU: Int32,
    VT: Float64[LDVT, Flat],
    LDVT: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGESV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dgesv(
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DGESVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dgesvd(
    JOBU: String[1],
    JOBVT: String[1],
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    U: Float64[LDU, Flat],
    LDU: Int32,
    VT: Float64[LDVT, Flat],
    LDVT: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGESVDQ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Addr(Arg(21))])
def dgesvdq(
    JOBA: String[1],
    JOBP: String[1],
    JOBR: String[1],
    JOBU: String[1],
    JOBV: String[1],
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    U: Float64[LDU, Flat],
    LDU: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    NUMRANK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGESVDX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20))])
def dgesvdx(
    JOBU: String[1],
    JOBVT: String[1],
    RANGE: String[1],
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    NS: Int32,
    S: Float64[Flat],
    U: Float64[LDU, Flat],
    LDU: Int32,
    VT: Float64[LDVT, Flat],
    LDVT: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGESVJ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dgesvj(
    JOBA: String[1],
    JOBU: String[1],
    JOBV: String[1],
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    SVA: Float64[N],
    MV: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    WORK: Float64[LWORK],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGESVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def dgesvx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float64[Flat],
    C: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGESVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22)), Arg(23), Arg(24), Arg(25), Addr(Arg(26))])
def dgesvxx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float64[Flat],
    C: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    RPVGRW: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGETC2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def dgetc2(
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    JPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGETF2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def dgetf2(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGETRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def dgetrf(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGETRF2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def dgetrf2(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGETRI")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def dgetri(
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGETRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dgetrs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DGETSLS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dgetsls(
    TRANS: String[1],
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGETSQRHRT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def dgetsqrhrt(
    M: Int32,
    N: Int32,
    MB1: Int32,
    NB1: Int32,
    NB2: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGGBAK")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dggbak(
    JOB: String[1],
    SIDE: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    LSCALE: Float64[Flat],
    RSCALE: Float64[Flat],
    M: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    INFO: Int32
) -> None: ...

@bind("DGGBAL")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11))])
def dggbal(
    JOB: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    ILO: Int32,
    IHI: Int32,
    LSCALE: Float64[Flat],
    RSCALE: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DGGES")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20))])
def dgges(
    JOBVSL: String[1],
    JOBVSR: String[1],
    SORT: String[1],
    SELCTG: Bool,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    SDIM: Int32,
    ALPHAR: Float64[Flat],
    ALPHAI: Float64[Flat],
    BETA: Float64[Flat],
    VSL: Float64[LDVSL, Flat],
    LDVSL: Int32,
    VSR: Float64[LDVSR, Flat],
    LDVSR: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("DGGES3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20))])
def dgges3(
    JOBVSL: String[1],
    JOBVSR: String[1],
    SORT: String[1],
    SELCTG: Bool,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    SDIM: Int32,
    ALPHAR: Float64[Flat],
    ALPHAI: Float64[Flat],
    BETA: Float64[Flat],
    VSL: Float64[LDVSL, Flat],
    LDVSL: Int32,
    VSR: Float64[LDVSR, Flat],
    LDVSR: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("DGGESX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25))])
def dggesx(
    JOBVSL: String[1],
    JOBVSR: String[1],
    SORT: String[1],
    SELCTG: Bool,
    SENSE: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    SDIM: Int32,
    ALPHAR: Float64[Flat],
    ALPHAI: Float64[Flat],
    BETA: Float64[Flat],
    VSL: Float64[LDVSL, Flat],
    LDVSL: Int32,
    VSR: Float64[LDVSR, Flat],
    LDVSR: Int32,
    RCONDE: Float64[2],
    RCONDV: Float64[2],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("DGGEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def dggev(
    JOBVL: String[1],
    JOBVR: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    ALPHAR: Float64[Flat],
    ALPHAI: Float64[Flat],
    BETA: Float64[Flat],
    VL: Float64[LDVL, Flat],
    LDVL: Int32,
    VR: Float64[LDVR, Flat],
    LDVR: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGGEV3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def dggev3(
    JOBVL: String[1],
    JOBVR: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    ALPHAR: Float64[Flat],
    ALPHAI: Float64[Flat],
    BETA: Float64[Flat],
    VL: Float64[LDVL, Flat],
    LDVL: Int32,
    VR: Float64[LDVR, Flat],
    LDVR: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGGEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Addr(Arg(21)), Arg(22), Arg(23), Arg(24), Addr(Arg(25)), Arg(26), Arg(27), Addr(Arg(28))])
def dggevx(
    BALANC: String[1],
    JOBVL: String[1],
    JOBVR: String[1],
    SENSE: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    ALPHAR: Float64[Flat],
    ALPHAI: Float64[Flat],
    BETA: Float64[Flat],
    VL: Float64[LDVL, Flat],
    LDVL: Int32,
    VR: Float64[LDVR, Flat],
    LDVR: Int32,
    ILO: Int32,
    IHI: Int32,
    LSCALE: Float64[Flat],
    RSCALE: Float64[Flat],
    ABNRM: Float64,
    BBNRM: Float64,
    RCONDE: Float64[Flat],
    RCONDV: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("DGGGLM")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dggglm(
    N: Int32,
    M: Int32,
    P: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    D: Float64[Flat],
    X: Float64[Flat],
    Y: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGGHD3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def dgghd3(
    COMPQ: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGGHRD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dgghrd(
    COMPQ: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    INFO: Int32
) -> None: ...

@bind("DGGLSE")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dgglse(
    M: Int32,
    N: Int32,
    P: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    C: Float64[Flat],
    D: Float64[Flat],
    X: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGGQRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def dggqrf(
    N: Int32,
    M: Int32,
    P: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAUA: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    TAUB: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGGRQF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def dggrqf(
    M: Int32,
    P: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAUA: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    TAUB: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGGSVD3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23))])
def dggsvd3(
    JOBU: String[1],
    JOBV: String[1],
    JOBQ: String[1],
    M: Int32,
    N: Int32,
    P: Int32,
    K: Int32,
    L: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    ALPHA: Float64[Flat],
    BETA: Float64[Flat],
    U: Float64[LDU, Flat],
    LDU: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGGSVP3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Addr(Arg(23)), Addr(Arg(24))])
def dggsvp3(
    JOBU: String[1],
    JOBV: String[1],
    JOBQ: String[1],
    M: Int32,
    P: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    TOLA: Float64,
    TOLB: Float64,
    K: Int32,
    L: Int32,
    U: Float64[LDU, Flat],
    LDU: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    IWORK: Int32[Flat],
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGSVJ0")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def dgsvj0(
    JOBV: String[1],
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    D: Float64[N],
    SVA: Float64[N],
    MV: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    EPS: Float64,
    SFMIN: Float64,
    TOL: Float64,
    NSWEEP: Int32,
    WORK: Float64[LWORK],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGSVJ1")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Addr(Arg(17))])
def dgsvj1(
    JOBV: String[1],
    M: Int32,
    N: Int32,
    N1: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    D: Float64[N],
    SVA: Float64[N],
    MV: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    EPS: Float64,
    SFMIN: Float64,
    TOL: Float64,
    NSWEEP: Int32,
    WORK: Float64[LWORK],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DGTCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def dgtcon(
    NORM: String[1],
    N: Int32,
    DL: Float64[Flat],
    D: Float64[Flat],
    DU: Float64[Flat],
    DU2: Float64[Flat],
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGTRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def dgtrfs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    DL: Float64[Flat],
    D: Float64[Flat],
    DU: Float64[Flat],
    DLF: Float64[Flat],
    DF: Float64[Flat],
    DUF: Float64[Flat],
    DU2: Float64[Flat],
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGTSV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dgtsv(
    N: Int32,
    NRHS: Int32,
    DL: Float64[Flat],
    D: Float64[Flat],
    DU: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DGTSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def dgtsvx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    DL: Float64[Flat],
    D: Float64[Flat],
    DU: Float64[Flat],
    DLF: Float64[Flat],
    DF: Float64[Flat],
    DUF: Float64[Flat],
    DU2: Float64[Flat],
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGTTRF")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def dgttrf(
    N: Int32,
    DL: Float64[Flat],
    D: Float64[Flat],
    DU: Float64[Flat],
    DU2: Float64[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DGTTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dgttrs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    DL: Float64[Flat],
    D: Float64[Flat],
    DU: Float64[Flat],
    DU2: Float64[Flat],
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DGTTS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9))])
def dgtts2(
    ITRANS: Int32,
    N: Int32,
    NRHS: Int32,
    DL: Float64[Flat],
    D: Float64[Flat],
    DU: Float64[Flat],
    DU2: Float64[Flat],
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("DHGEQZ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Addr(Arg(19))])
def dhgeqz(
    JOB: String[1],
    COMPQ: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Float64[LDH, Flat],
    LDH: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    ALPHAR: Float64[Flat],
    ALPHAI: Float64[Flat],
    BETA: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DHSEIN")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Addr(Arg(18))])
def dhsein(
    SIDE: String[1],
    EIGSRC: String[1],
    INITV: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    H: Float64[LDH, Flat],
    LDH: Int32,
    WR: Float64[Flat],
    WI: Float64[Flat],
    VL: Float64[LDVL, Flat],
    LDVL: Int32,
    VR: Float64[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Float64[Flat],
    IFAILL: Int32[Flat],
    IFAILR: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DHSEQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dhseqr(
    JOB: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Float64[LDH, Flat],
    LDH: Int32,
    WR: Float64[Flat],
    WI: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DISNAN")
@external
@native_call([Addr(Arg(0))])
def disnan(
    DIN: Float64
) -> Bool: ...

@bind("DLA_GBAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def dla_gbamv(
    TRANS: Int32,
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    ALPHA: Float64,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    X: Float64[Flat],
    INCX: Int32,
    BETA: Float64,
    Y: Float64[Flat],
    INCY: Int32
) -> None: ...

@bind("DLA_GBRCOND")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13)])
def dla_gbrcond(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    AFB: Float64[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    CMODE: Int32,
    C: Float64[Flat],
    INFO: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat]
) -> Float64: ...

@bind("DLA_GBRFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Arg(22), Arg(23), Arg(24), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28)), Addr(Arg(29)), Addr(Arg(30))])
def dla_gbrfsx_extended(
    PREC_TYPE: Int32,
    TRANS_TYPE: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    AFB: Float64[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    Y: Float64[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float64[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    RES: Float64[Flat],
    AYB: Float64[Flat],
    DY: Float64[Flat],
    Y_TAIL: Float64[Flat],
    RCOND: Float64,
    ITHRESH: Int32,
    RTHRESH: Float64,
    DZ_UB: Float64,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("DLA_GBRPVGRW")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def dla_gbrpvgrw(
    N: Int32,
    KL: Int32,
    KU: Int32,
    NCOLS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    AFB: Float64[LDAFB, Flat],
    LDAFB: Int32
) -> Float64: ...

@bind("DLA_GEAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def dla_geamv(
    TRANS: Int32,
    M: Int32,
    N: Int32,
    ALPHA: Float64,
    A: Float64[LDA, Flat],
    LDA: Int32,
    X: Float64[Flat],
    INCX: Int32,
    BETA: Float64,
    Y: Float64[Flat],
    INCY: Int32
) -> None: ...

@bind("DLA_GERCOND")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11)])
def dla_gercond(
    TRANS: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    CMODE: Int32,
    C: Float64[Flat],
    INFO: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat]
) -> Float64: ...

@bind("DLA_GERFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28))])
def dla_gerfsx_extended(
    PREC_TYPE: Int32,
    TRANS_TYPE: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    Y: Float64[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float64[Flat],
    N_NORMS: Int32,
    ERRS_N: Float64[NRHS, Flat],
    ERRS_C: Float64[NRHS, Flat],
    RES: Float64[Flat],
    AYB: Float64[Flat],
    DY: Float64[Flat],
    Y_TAIL: Float64[Flat],
    RCOND: Float64,
    ITHRESH: Int32,
    RTHRESH: Float64,
    DZ_UB: Float64,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("DLA_GERPVGRW")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def dla_gerpvgrw(
    N: Int32,
    NCOLS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32
) -> Float64: ...

@bind("DLA_LIN_BERR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5)])
def dla_lin_berr(
    N: Int32,
    NZ: Int32,
    NRHS: Int32,
    RES: Float64[N, NRHS],
    AYB: Float64[N, NRHS],
    BERR: Float64[NRHS]
) -> None: ...

@bind("DLA_PORCOND")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10)])
def dla_porcond(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    CMODE: Int32,
    C: Float64[Flat],
    INFO: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat]
) -> Float64: ...

@bind("DLA_PORFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Addr(Arg(22)), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27))])
def dla_porfsx_extended(
    PREC_TYPE: Int32,
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    COLEQU: Bool,
    C: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    Y: Float64[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float64[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    RES: Float64[Flat],
    AYB: Float64[Flat],
    DY: Float64[Flat],
    Y_TAIL: Float64[Flat],
    RCOND: Float64,
    ITHRESH: Int32,
    RTHRESH: Float64,
    DZ_UB: Float64,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("DLA_PORPVGRW")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def dla_porpvgrw(
    UPLO: String[1],
    NCOLS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("DLA_SYAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def dla_syamv(
    UPLO: Int32,
    N: Int32,
    ALPHA: Float64,
    A: Float64[LDA, Flat],
    LDA: Int32,
    X: Float64[Flat],
    INCX: Int32,
    BETA: Float64,
    Y: Float64[Flat],
    INCY: Int32
) -> None: ...

@bind("DLA_SYRCOND")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11)])
def dla_syrcond(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    CMODE: Int32,
    C: Float64[Flat],
    INFO: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat]
) -> Float64: ...

@bind("DLA_SYRFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28))])
def dla_syrfsx_extended(
    PREC_TYPE: Int32,
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    Y: Float64[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float64[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    RES: Float64[Flat],
    AYB: Float64[Flat],
    DY: Float64[Flat],
    Y_TAIL: Float64[Flat],
    RCOND: Float64,
    ITHRESH: Int32,
    RTHRESH: Float64,
    DZ_UB: Float64,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("DLA_SYRPVGRW")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8)])
def dla_syrpvgrw(
    UPLO: String[1],
    N: Int32,
    INFO: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    WORK: Float64[Flat]
) -> Float64: ...

@bind("DLA_WWADDW")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def dla_wwaddw(
    N: Int32,
    X: Float64[Flat],
    Y: Float64[Flat],
    W: Float64[Flat]
) -> None: ...

@bind("DLABAD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def dlabad(
    SMALL: Float64,
    LARGE: Float64
) -> None: ...

@bind("DLABRD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def dlabrd(
    M: Int32,
    N: Int32,
    NB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    TAUQ: Float64[Flat],
    TAUP: Float64[Flat],
    X: Float64[LDX, Flat],
    LDX: Int32,
    Y: Float64[LDY, Flat],
    LDY: Int32
) -> None: ...

@bind("DLACN2")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6)])
def dlacn2(
    N: Int32,
    V: Float64[Flat],
    X: Float64[Flat],
    ISGN: Int32[Flat],
    EST: Float64,
    KASE: Int32,
    ISAVE: Int32[3]
) -> None: ...

@bind("DLACON")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def dlacon(
    N: Int32,
    V: Float64[Flat],
    X: Float64[Flat],
    ISGN: Int32[Flat],
    EST: Float64,
    KASE: Int32
) -> None: ...

@bind("DLACPY")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def dlacpy(
    UPLO: String[1],
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("DLADIV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def dladiv(
    A: Float64,
    B: Float64,
    C: Float64,
    D: Float64,
    P: Float64,
    Q: Float64
) -> None: ...

@bind("DLADIV1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def dladiv1(
    A: Float64,
    B: Float64,
    C: Float64,
    D: Float64,
    P: Float64,
    Q: Float64
) -> None: ...

@bind("DLADIV2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def dladiv2(
    A: Float64,
    B: Float64,
    C: Float64,
    D: Float64,
    R: Float64,
    T: Float64
) -> Float64: ...

@bind("DLAE2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def dlae2(
    A: Float64,
    B: Float64,
    C: Float64,
    RT1: Float64,
    RT2: Float64
) -> None: ...

@bind("DLAEBZ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def dlaebz(
    IJOB: Int32,
    NITMAX: Int32,
    N: Int32,
    MMAX: Int32,
    MINP: Int32,
    NBMIN: Int32,
    ABSTOL: Float64,
    RELTOL: Float64,
    PIVMIN: Float64,
    D: Float64[Flat],
    E: Float64[Flat],
    E2: Float64[Flat],
    NVAL: Int32[Flat],
    AB: Float64[MMAX, Flat],
    C: Float64[Flat],
    MOUT: Int32,
    NAB: Int32[MMAX, Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAED0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def dlaed0(
    ICOMPQ: Int32,
    QSIZ: Int32,
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    QSTORE: Float64[LDQS, Flat],
    LDQS: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAED1")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def dlaed1(
    N: Int32,
    D: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    INDXQ: Int32[Flat],
    RHO: Float64,
    CUTPNT: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAED2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def dlaed2(
    K: Int32,
    N: Int32,
    N1: Int32,
    D: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    INDXQ: Int32[Flat],
    RHO: Float64,
    Z: Float64[Flat],
    DLAMBDA: Float64[Flat],
    W: Float64[Flat],
    Q2: Float64[Flat],
    INDX: Int32[Flat],
    INDXC: Int32[Flat],
    INDXP: Int32[Flat],
    COLTYP: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAED3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def dlaed3(
    K: Int32,
    N: Int32,
    N1: Int32,
    D: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    RHO: Float64,
    DLAMBDA: Float64[Flat],
    Q2: Float64[Flat],
    INDX: Int32[Flat],
    CTOT: Int32[Flat],
    W: Float64[Flat],
    S: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAED4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7))])
def dlaed4(
    N: Int32,
    I: Int32,
    D: Float64[Flat],
    Z: Float64[Flat],
    DELTA: Float64[Flat],
    RHO: Float64,
    DLAM: Float64,
    INFO: Int32
) -> None: ...

@bind("DLAED5")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def dlaed5(
    I: Int32,
    D: Float64[2],
    Z: Float64[2],
    DELTA: Float64[2],
    RHO: Float64,
    DLAM: Float64
) -> None: ...

@bind("DLAED6")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7))])
def dlaed6(
    KNITER: Int32,
    ORGATI: Bool,
    RHO: Float64,
    D: Float64[3],
    Z: Float64[3],
    FINIT: Float64,
    TAU: Float64,
    INFO: Int32
) -> None: ...

@bind("DLAED7")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def dlaed7(
    ICOMPQ: Int32,
    N: Int32,
    QSIZ: Int32,
    TLVLS: Int32,
    CURLVL: Int32,
    CURPBM: Int32,
    D: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    INDXQ: Int32[Flat],
    RHO: Float64,
    CUTPNT: Int32,
    QSTORE: Float64[Flat],
    QPTR: Int32[Flat],
    PRMPTR: Int32[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32[Flat],
    GIVCOL: Int32[2, Flat],
    GIVNUM: Float64[2, Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAED8")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def dlaed8(
    ICOMPQ: Int32,
    K: Int32,
    N: Int32,
    QSIZ: Int32,
    D: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    INDXQ: Int32[Flat],
    RHO: Float64,
    CUTPNT: Int32,
    Z: Float64[Flat],
    DLAMBDA: Float64[Flat],
    Q2: Float64[LDQ2, Flat],
    LDQ2: Int32,
    W: Float64[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32,
    GIVCOL: Int32[2, Flat],
    GIVNUM: Float64[2, Flat],
    INDXP: Int32[Flat],
    INDX: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAED9")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dlaed9(
    K: Int32,
    KSTART: Int32,
    KSTOP: Int32,
    N: Int32,
    D: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    RHO: Float64,
    DLAMBDA: Float64[Flat],
    W: Float64[Flat],
    S: Float64[LDS, Flat],
    LDS: Int32,
    INFO: Int32
) -> None: ...

@bind("DLAEDA")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def dlaeda(
    N: Int32,
    TLVLS: Int32,
    CURLVL: Int32,
    CURPBM: Int32,
    PRMPTR: Int32[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32[Flat],
    GIVCOL: Int32[2, Flat],
    GIVNUM: Float64[2, Flat],
    Q: Float64[Flat],
    QPTR: Int32[Flat],
    Z: Float64[Flat],
    ZTEMP: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAEIN")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15))])
def dlaein(
    RIGHTV: Bool,
    NOINIT: Bool,
    N: Int32,
    H: Float64[LDH, Flat],
    LDH: Int32,
    WR: Float64,
    WI: Float64,
    VR: Float64[Flat],
    VI: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[Flat],
    EPS3: Float64,
    SMLNUM: Float64,
    BIGNUM: Float64,
    INFO: Int32
) -> None: ...

@bind("DLAEV2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def dlaev2(
    A: Float64,
    B: Float64,
    C: Float64,
    RT1: Float64,
    RT2: Float64,
    CS1: Float64,
    SN1: Float64
) -> None: ...

@bind("DLAEXC")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def dlaexc(
    WANTQ: Bool,
    N: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    J1: Int32,
    N1: Int32,
    N2: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAG2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def dlag2(
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    SAFMIN: Float64,
    SCALE1: Float64,
    SCALE2: Float64,
    WR1: Float64,
    WR2: Float64,
    WI: Float64
) -> None: ...

@bind("DLAG2S")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def dlag2s(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    SA: Float32[LDSA, Flat],
    LDSA: Int32,
    INFO: Int32
) -> None: ...

@bind("DLAGS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12))])
def dlags2(
    UPPER: Bool,
    A1: Float64,
    A2: Float64,
    A3: Float64,
    B1: Float64,
    B2: Float64,
    B3: Float64,
    CSU: Float64,
    SNU: Float64,
    CSV: Float64,
    SNV: Float64,
    CSQ: Float64,
    SNQ: Float64
) -> None: ...

@bind("DLAGTF")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def dlagtf(
    N: Int32,
    A: Float64[Flat],
    LAMBDA: Float64,
    B: Float64[Flat],
    C: Float64[Flat],
    TOL: Float64,
    D: Float64[Flat],
    IN: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAGTM")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def dlagtm(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    ALPHA: Float64,
    DL: Float64[Flat],
    D: Float64[Flat],
    DU: Float64[Flat],
    X: Float64[LDX, Flat],
    LDX: Int32,
    BETA: Float64,
    B: Float64[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("DLAGTS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def dlagts(
    JOB: Int32,
    N: Int32,
    A: Float64[Flat],
    B: Float64[Flat],
    C: Float64[Flat],
    D: Float64[Flat],
    IN: Int32[Flat],
    Y: Float64[Flat],
    TOL: Float64,
    INFO: Int32
) -> None: ...

@bind("DLAGV2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10))])
def dlagv2(
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    ALPHAR: Float64[2],
    ALPHAI: Float64[2],
    BETA: Float64[2],
    CSL: Float64,
    SNL: Float64,
    CSR: Float64,
    SNR: Float64
) -> None: ...

@bind("DLAHQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dlahqr(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Float64[LDH, Flat],
    LDH: Int32,
    WR: Float64[Flat],
    WI: Float64[Flat],
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    INFO: Int32
) -> None: ...

@bind("DLAHR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def dlahr2(
    N: Int32,
    K: Int32,
    NB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[NB],
    T: Float64[LDT, NB],
    LDT: Int32,
    Y: Float64[LDY, NB],
    LDY: Int32
) -> None: ...

@bind("DLAIC1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8))])
def dlaic1(
    JOB: Int32,
    J: Int32,
    X: Float64[J],
    SEST: Float64,
    W: Float64[J],
    GAMMA: Float64,
    SESTPR: Float64,
    S: Float64,
    C: Float64
) -> None: ...

@bind("DLAISNAN")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def dlaisnan(
    DIN1: Float64,
    DIN2: Float64
) -> Bool: ...

@bind("DLALN2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17))])
def dlaln2(
    LTRANS: Bool,
    NA: Int32,
    NW: Int32,
    SMIN: Float64,
    CA: Float64,
    A: Float64[LDA, Flat],
    LDA: Int32,
    D1: Float64,
    D2: Float64,
    B: Float64[LDB, Flat],
    LDB: Int32,
    WR: Float64,
    WI: Float64,
    X: Float64[LDX, Flat],
    LDX: Int32,
    SCALE: Float64,
    XNORM: Float64,
    INFO: Int32
) -> None: ...

@bind("DLALS0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19)), Addr(Arg(20)), Addr(Arg(21)), Arg(22), Addr(Arg(23))])
def dlals0(
    ICOMPQ: Int32,
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    NRHS: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    BX: Float64[LDBX, Flat],
    LDBX: Int32,
    PERM: Int32[Flat],
    GIVPTR: Int32,
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    GIVNUM: Float64[LDGNUM, Flat],
    LDGNUM: Int32,
    POLES: Float64[LDGNUM, Flat],
    DIFL: Float64[Flat],
    DIFR: Float64[LDGNUM, Flat],
    Z: Float64[Flat],
    K: Int32,
    C: Float64,
    S: Float64,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLALSA")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Arg(22), Arg(23), Arg(24), Addr(Arg(25))])
def dlalsa(
    ICOMPQ: Int32,
    SMLSIZ: Int32,
    N: Int32,
    NRHS: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    BX: Float64[LDBX, Flat],
    LDBX: Int32,
    U: Float64[LDU, Flat],
    LDU: Int32,
    VT: Float64[LDU, Flat],
    K: Int32[Flat],
    DIFL: Float64[LDU, Flat],
    DIFR: Float64[LDU, Flat],
    Z: Float64[LDU, Flat],
    POLES: Float64[LDU, Flat],
    GIVPTR: Int32[Flat],
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    PERM: Int32[LDGCOL, Flat],
    GIVNUM: Float64[LDU, Flat],
    C: Float64[Flat],
    S: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLALSD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12))])
def dlalsd(
    UPLO: String[1],
    SMLSIZ: Int32,
    N: Int32,
    NRHS: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    RCOND: Float64,
    RANK: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAMRG")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5)])
def dlamrg(
    N1: Int32,
    N2: Int32,
    A: Float64[Flat],
    DTRD1: Int32,
    DTRD2: Int32,
    INDEX: Int32[Flat]
) -> None: ...

@bind("DLAMSWLQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def dlamswlq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    MB: Int32,
    NB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DLAMTSQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def dlamtsqr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    MB: Int32,
    NB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DLANEG")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def dlaneg(
    N: Int32,
    D: Float64[Flat],
    LLD: Float64[Flat],
    SIGMA: Float64,
    PIVMIN: Float64,
    R: Int32
) -> Int32: ...

@bind("DLANGB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def dlangb(
    NORM: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("DLANGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def dlange(
    NORM: String[1],
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("DLANGT")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4)])
def dlangt(
    NORM: String[1],
    N: Int32,
    DL: Float64[Flat],
    D: Float64[Flat],
    DU: Float64[Flat]
) -> Float64: ...

@bind("DLANHS")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4)])
def dlanhs(
    NORM: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("DLANSB")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def dlansb(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    K: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("DLANSF")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5)])
def dlansf(
    NORM: String[1],
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[Flat],
    WORK: Float64[Flat]
) -> Float64: ...

@bind("DLANSP")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4)])
def dlansp(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    WORK: Float64[Flat]
) -> Float64: ...

@bind("DLANST")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3)])
def dlanst(
    NORM: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat]
) -> Float64: ...

@bind("DLANSY")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def dlansy(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("DLANTB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def dlantb(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    K: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("DLANTP")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5)])
def dlantp(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    AP: Float64[Flat],
    WORK: Float64[Flat]
) -> Float64: ...

@bind("DLANTR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def dlantr(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("DLANV2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def dlanv2(
    A: Float64,
    B: Float64,
    C: Float64,
    D: Float64,
    RT1R: Float64,
    RT1I: Float64,
    RT2R: Float64,
    RT2I: Float64,
    CS: Float64,
    SN: Float64
) -> None: ...

@bind("DLAORHR_COL_GETRFNP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def dlaorhr_col_getrfnp(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAORHR_COL_GETRFNP2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def dlaorhr_col_getrfnp2(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAPLL")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def dlapll(
    N: Int32,
    X: Float64[Flat],
    INCX: Int32,
    Y: Float64[Flat],
    INCY: Int32,
    SSMIN: Float64
) -> None: ...

@bind("DLAPMR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def dlapmr(
    FORWRD: Bool,
    M: Int32,
    N: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    K: Int32[Flat]
) -> None: ...

@bind("DLAPMT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def dlapmt(
    FORWRD: Bool,
    M: Int32,
    N: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    K: Int32[Flat]
) -> None: ...

@bind("DLAPY2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def dlapy2(
    X: Float64,
    Y: Float64
) -> Float64: ...

@bind("DLAPY3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2))])
def dlapy3(
    X: Float64,
    Y: Float64,
    Z: Float64
) -> Float64: ...

@bind("DLAQGB")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11)])
def dlaqgb(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    R: Float64[Flat],
    C: Float64[Flat],
    ROWCND: Float64,
    COLCND: Float64,
    AMAX: Float64,
    EQUED: String[1]
) -> None: ...

@bind("DLAQGE")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9)])
def dlaqge(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    R: Float64[Flat],
    C: Float64[Flat],
    ROWCND: Float64,
    COLCND: Float64,
    AMAX: Float64,
    EQUED: String[1]
) -> None: ...

@bind("DLAQP2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9)])
def dlaqp2(
    M: Int32,
    N: Int32,
    OFFSET: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    JPVT: Int32[Flat],
    TAU: Float64[Flat],
    VN1: Float64[Flat],
    VN2: Float64[Flat],
    WORK: Float64[Flat]
) -> None: ...

@bind("DLAQP2RK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def dlaqp2rk(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    IOFFSET: Int32,
    KMAX: Int32,
    ABSTOL: Float64,
    RELTOL: Float64,
    KP1: Int32,
    MAXC2NRM: Float64,
    A: Float64[LDA, Flat],
    LDA: Int32,
    K: Int32,
    MAXC2NRMK: Float64,
    RELMAXC2NRMK: Float64,
    JPIV: Int32[Flat],
    TAU: Float64[Flat],
    VN1: Float64[Flat],
    VN2: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAQP3RK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23))])
def dlaqp3rk(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    IOFFSET: Int32,
    NB: Int32,
    ABSTOL: Float64,
    RELTOL: Float64,
    KP1: Int32,
    MAXC2NRM: Float64,
    A: Float64[LDA, Flat],
    LDA: Int32,
    DONE: Bool,
    KB: Int32,
    MAXC2NRMK: Float64,
    RELMAXC2NRMK: Float64,
    JPIV: Int32[Flat],
    TAU: Float64[Flat],
    VN1: Float64[Flat],
    VN2: Float64[Flat],
    AUXV: Float64[Flat],
    F: Float64[LDF, Flat],
    LDF: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAQPS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def dlaqps(
    M: Int32,
    N: Int32,
    OFFSET: Int32,
    NB: Int32,
    KB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    JPVT: Int32[Flat],
    TAU: Float64[Flat],
    VN1: Float64[Flat],
    VN2: Float64[Flat],
    AUXV: Float64[Flat],
    F: Float64[LDF, Flat],
    LDF: Int32
) -> None: ...

@bind("DLAQR0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def dlaqr0(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Float64[LDH, Flat],
    LDH: Int32,
    WR: Float64[Flat],
    WI: Float64[Flat],
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DLAQR1")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7)])
def dlaqr1(
    N: Int32,
    H: Float64[LDH, Flat],
    LDH: Int32,
    SR1: Float64,
    SI1: Float64,
    SR2: Float64,
    SI2: Float64,
    V: Float64[Flat]
) -> None: ...

@bind("DLAQR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25))])
def dlaqr2(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    KTOP: Int32,
    KBOT: Int32,
    NW: Int32,
    H: Float64[LDH, Flat],
    LDH: Int32,
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    NS: Int32,
    ND: Int32,
    SR: Float64[Flat],
    SI: Float64[Flat],
    V: Float64[LDV, Flat],
    LDV: Int32,
    NH: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    NV: Int32,
    WV: Float64[LDWV, Flat],
    LDWV: Int32,
    WORK: Float64[Flat],
    LWORK: Int32
) -> None: ...

@bind("DLAQR3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25))])
def dlaqr3(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    KTOP: Int32,
    KBOT: Int32,
    NW: Int32,
    H: Float64[LDH, Flat],
    LDH: Int32,
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    NS: Int32,
    ND: Int32,
    SR: Float64[Flat],
    SI: Float64[Flat],
    V: Float64[LDV, Flat],
    LDV: Int32,
    NH: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    NV: Int32,
    WV: Float64[LDWV, Flat],
    LDWV: Int32,
    WORK: Float64[Flat],
    LWORK: Int32
) -> None: ...

@bind("DLAQR4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def dlaqr4(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Float64[LDH, Flat],
    LDH: Int32,
    WR: Float64[Flat],
    WI: Float64[Flat],
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DLAQR5")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Addr(Arg(22)), Arg(23), Addr(Arg(24))])
def dlaqr5(
    WANTT: Bool,
    WANTZ: Bool,
    KACC22: Int32,
    N: Int32,
    KTOP: Int32,
    KBOT: Int32,
    NSHFTS: Int32,
    SR: Float64[Flat],
    SI: Float64[Flat],
    H: Float64[LDH, Flat],
    LDH: Int32,
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    U: Float64[LDU, Flat],
    LDU: Int32,
    NV: Int32,
    WV: Float64[LDWV, Flat],
    LDWV: Int32,
    NH: Int32,
    WH: Float64[LDWH, Flat],
    LDWH: Int32
) -> None: ...

@bind("DLAQSB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8)])
def dlaqsb(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    EQUED: String[1]
) -> None: ...

@bind("DLAQSP")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6)])
def dlaqsp(
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    EQUED: String[1]
) -> None: ...

@bind("DLAQSY")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7)])
def dlaqsy(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    EQUED: String[1]
) -> None: ...

@bind("DLAQTR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def dlaqtr(
    LTRAN: Bool,
    LREAL: Bool,
    N: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    B: Float64[Flat],
    W: Float64,
    SCALE: Float64,
    X: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLAQZ0")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Addr(Arg(19)), Return('INFO', 0)])
def dlaqz0(
    WANTS: String[1],
    WANTQ: String[1],
    WANTZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    ALPHAR: Float64[Flat],
    ALPHAI: Float64[Flat],
    BETA: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    REC: Int32
) -> Int32: ...

@bind("DLAQZ1")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9)])
def dlaqz1(
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    SR1: Float64,
    SR2: Float64,
    SI: Float64,
    BETA1: Float64,
    BETA2: Float64,
    V: Float64[Flat]
) -> None: ...

@bind("DLAQZ2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def dlaqz2(
    ILQ: Bool,
    ILZ: Bool,
    K: Int32,
    ISTARTM: Int32,
    ISTOPM: Int32,
    IHI: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    NQ: Int32,
    QSTART: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    NZ: Int32,
    ZSTART: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32
) -> None: ...

@bind("DLAQZ3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Return('NS', 0), Return('ND', 1), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Return('INFO', 2)])
def dlaqz3(
    ILSCHUR: Bool,
    ILQ: Bool,
    ILZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    NW: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    ALPHAR: Float64[Flat],
    ALPHAI: Float64[Flat],
    BETA: Float64[Flat],
    QC: Float64[LDQC, Flat],
    LDQC: Int32,
    ZC: Float64[LDZC, Flat],
    LDZC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    REC: Int32
) -> tuple[Int32, Int32, Int32]: ...

@bind("DLAQZ4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Arg(21), Addr(Arg(22)), Arg(23), Addr(Arg(24)), Return('INFO', 0)])
def dlaqz4(
    ILSCHUR: Bool,
    ILQ: Bool,
    ILZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    NSHIFTS: Int32,
    NBLOCK_DESIRED: Int32,
    SR: Float64[Flat],
    SI: Float64[Flat],
    SS: Float64[Flat],
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    QC: Float64[LDQC, Flat],
    LDQC: Int32,
    ZC: Float64[LDZC, Flat],
    LDZC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32
) -> Int32: ...

@bind("DLAR1V")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Addr(Arg(19)), Arg(20)])
def dlar1v(
    N: Int32,
    B1: Int32,
    BN: Int32,
    LAMBDA: Float64,
    D: Float64[Flat],
    L: Float64[Flat],
    LD: Float64[Flat],
    LLD: Float64[Flat],
    PIVMIN: Float64,
    GAPTOL: Float64,
    Z: Float64[Flat],
    WANTNC: Bool,
    NEGCNT: Int32,
    ZTZ: Float64,
    MINGMA: Float64,
    R: Int32,
    ISUPPZ: Int32[Flat],
    NRMINV: Float64,
    RESID: Float64,
    RQCORR: Float64,
    WORK: Float64[Flat]
) -> None: ...

@bind("DLAR2V")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def dlar2v(
    N: Int32,
    X: Float64[Flat],
    Y: Float64[Flat],
    Z: Float64[Flat],
    INCX: Int32,
    C: Float64[Flat],
    S: Float64[Flat],
    INCC: Int32
) -> None: ...

@bind("DLARF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def dlarf(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Float64[Flat],
    INCV: Int32,
    TAU: Float64,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat]
) -> None: ...

@bind("DLARF1F")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def dlarf1f(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Float64[Flat],
    INCV: Int32,
    TAU: Float64,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat]
) -> None: ...

@bind("DLARF1L")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def dlarf1l(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Float64[Flat],
    INCV: Int32,
    TAU: Float64,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat]
) -> None: ...

@bind("DLARFB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14))])
def dlarfb(
    SIDE: String[1],
    TRANS: String[1],
    DIRECT: String[1],
    STOREV: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("DLARFB_GETT")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def dlarfb_gett(
    IDENT: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("DLARFG")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def dlarfg(
    N: Int32,
    ALPHA: Float64,
    X: Float64[Flat],
    INCX: Int32,
    TAU: Float64
) -> None: ...

@bind("DLARFGP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def dlarfgp(
    N: Int32,
    ALPHA: Float64,
    X: Float64[Flat],
    INCX: Int32,
    TAU: Float64
) -> None: ...

@bind("DLARFT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def dlarft(
    DIRECT: String[1],
    STOREV: String[1],
    N: Int32,
    K: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    TAU: Float64[Flat],
    T: Float64[LDT, Flat],
    LDT: Int32
) -> None: ...

@bind("DLARFX")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def dlarfx(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Float64[Flat],
    TAU: Float64,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat]
) -> None: ...

@bind("DLARFY")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def dlarfy(
    UPLO: String[1],
    N: Int32,
    V: Float64[Flat],
    INCV: Int32,
    TAU: Float64,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat]
) -> None: ...

@bind("DLARGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def dlargv(
    N: Int32,
    X: Float64[Flat],
    INCX: Int32,
    Y: Float64[Flat],
    INCY: Int32,
    C: Float64[Flat],
    INCC: Int32
) -> None: ...

@bind("DLARMM")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2))])
def dlarmm(
    ANORM: Float64,
    BNORM: Float64,
    CNORM: Float64
) -> Float64: ...

@bind("DLARNV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3)])
def dlarnv(
    IDIST: Int32,
    ISEED: Int32[4],
    N: Int32,
    X: Float64[Flat]
) -> None: ...

@bind("DLARRA")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def dlarra(
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    E2: Float64[Flat],
    SPLTOL: Float64,
    TNRM: Float64,
    NSPLIT: Int32,
    ISPLIT: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLARRB")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16))])
def dlarrb(
    N: Int32,
    D: Float64[Flat],
    LLD: Float64[Flat],
    IFIRST: Int32,
    ILAST: Int32,
    RTOL1: Float64,
    RTOL2: Float64,
    OFFSET: Int32,
    W: Float64[Flat],
    WGAP: Float64[Flat],
    WERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    PIVMIN: Float64,
    SPDIAM: Float64,
    TWIST: Int32,
    INFO: Int32
) -> None: ...

@bind("DLARRC")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10))])
def dlarrc(
    JOBT: String[1],
    N: Int32,
    VL: Float64,
    VU: Float64,
    D: Float64[Flat],
    E: Float64[Flat],
    PIVMIN: Float64,
    EIGCNT: Int32,
    LCNT: Int32,
    RCNT: Int32,
    INFO: Int32
) -> None: ...

@bind("DLARRD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Addr(Arg(18)), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def dlarrd(
    RANGE: String[1],
    ORDER: String[1],
    N: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    GERS: Float64[Flat],
    RELTOL: Float64,
    D: Float64[Flat],
    E: Float64[Flat],
    E2: Float64[Flat],
    PIVMIN: Float64,
    NSPLIT: Int32,
    ISPLIT: Int32[Flat],
    M: Int32,
    W: Float64[Flat],
    WERR: Float64[Flat],
    WL: Float64,
    WU: Float64,
    IBLOCK: Int32[Flat],
    INDEXW: Int32[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLARRE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Addr(Arg(24))])
def dlarre(
    RANGE: String[1],
    N: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    E2: Float64[Flat],
    RTOL1: Float64,
    RTOL2: Float64,
    SPLTOL: Float64,
    NSPLIT: Int32,
    ISPLIT: Int32[Flat],
    M: Int32,
    W: Float64[Flat],
    WERR: Float64[Flat],
    WGAP: Float64[Flat],
    IBLOCK: Int32[Flat],
    INDEXW: Int32[Flat],
    GERS: Float64[Flat],
    PIVMIN: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLARRF")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17))])
def dlarrf(
    N: Int32,
    D: Float64[Flat],
    L: Float64[Flat],
    LD: Float64[Flat],
    CLSTRT: Int32,
    CLEND: Int32,
    W: Float64[Flat],
    WGAP: Float64[Flat],
    WERR: Float64[Flat],
    SPDIAM: Float64,
    CLGAPL: Float64,
    CLGAPR: Float64,
    PIVMIN: Float64,
    SIGMA: Float64,
    DPLUS: Float64[Flat],
    LPLUS: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLARRJ")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13))])
def dlarrj(
    N: Int32,
    D: Float64[Flat],
    E2: Float64[Flat],
    IFIRST: Int32,
    ILAST: Int32,
    RTOL: Float64,
    OFFSET: Int32,
    W: Float64[Flat],
    WERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    PIVMIN: Float64,
    SPDIAM: Float64,
    INFO: Int32
) -> None: ...

@bind("DLARRK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10))])
def dlarrk(
    N: Int32,
    IW: Int32,
    GL: Float64,
    GU: Float64,
    D: Float64[Flat],
    E2: Float64[Flat],
    PIVMIN: Float64,
    RELTOL: Float64,
    W: Float64,
    WERR: Float64,
    INFO: Int32
) -> None: ...

@bind("DLARRR")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3))])
def dlarrr(
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLARRV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def dlarrv(
    N: Int32,
    VL: Float64,
    VU: Float64,
    D: Float64[Flat],
    L: Float64[Flat],
    PIVMIN: Float64,
    ISPLIT: Int32[Flat],
    M: Int32,
    DOL: Int32,
    DOU: Int32,
    MINRGP: Float64,
    RTOL1: Float64,
    RTOL2: Float64,
    W: Float64[Flat],
    WERR: Float64[Flat],
    WGAP: Float64[Flat],
    IBLOCK: Int32[Flat],
    INDEXW: Int32[Flat],
    GERS: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLARSCL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def dlarscl2(
    M: Int32,
    N: Int32,
    D: Float64[Flat],
    X: Float64[LDX, Flat],
    LDX: Int32
) -> None: ...

@bind("DLARTG")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def dlartg(
    f: Float64,
    g: Float64,
    c: Float64,
    s: Float64,
    r: Float64
) -> None: ...

@bind("DLARTGP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def dlartgp(
    F: Float64,
    G: Float64,
    CS: Float64,
    SN: Float64,
    R: Float64
) -> None: ...

@bind("DLARTGS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def dlartgs(
    X: Float64,
    Y: Float64,
    SIGMA: Float64,
    CS: Float64,
    SN: Float64
) -> None: ...

@bind("DLARTV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def dlartv(
    N: Int32,
    X: Float64[Flat],
    INCX: Int32,
    Y: Float64[Flat],
    INCY: Int32,
    C: Float64[Flat],
    S: Float64[Flat],
    INCC: Int32
) -> None: ...

@bind("DLARUV")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2)])
def dlaruv(
    ISEED: Int32[4],
    N: Int32,
    X: Float64[N]
) -> None: ...

@bind("DLARZ")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9)])
def dlarz(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    L: Int32,
    V: Float64[Flat],
    INCV: Int32,
    TAU: Float64,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat]
) -> None: ...

@bind("DLARZB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15))])
def dlarzb(
    SIDE: String[1],
    TRANS: String[1],
    DIRECT: String[1],
    STOREV: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("DLARZT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def dlarzt(
    DIRECT: String[1],
    STOREV: String[1],
    N: Int32,
    K: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    TAU: Float64[Flat],
    T: Float64[LDT, Flat],
    LDT: Int32
) -> None: ...

@bind("DLAS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def dlas2(
    F: Float64,
    G: Float64,
    H: Float64,
    SSMIN: Float64,
    SSMAX: Float64
) -> None: ...

@bind("DLASCL")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def dlascl(
    TYPE: String[1],
    KL: Int32,
    KU: Int32,
    CFROM: Float64,
    CTO: Float64,
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("DLASCL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def dlascl2(
    M: Int32,
    N: Int32,
    D: Float64[Flat],
    X: Float64[LDX, Flat],
    LDX: Int32
) -> None: ...

@bind("DLASD0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def dlasd0(
    N: Int32,
    SQRE: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    U: Float64[LDU, Flat],
    LDU: Int32,
    VT: Float64[LDVT, Flat],
    LDVT: Int32,
    SMLSIZ: Int32,
    IWORK: Int32[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLASD1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def dlasd1(
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    D: Float64[Flat],
    ALPHA: Float64,
    BETA: Float64,
    U: Float64[LDU, Flat],
    LDU: Int32,
    VT: Float64[LDVT, Flat],
    LDVT: Int32,
    IDXQ: Int32[Flat],
    IWORK: Int32[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLASD2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Addr(Arg(22))])
def dlasd2(
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    K: Int32,
    D: Float64[Flat],
    Z: Float64[Flat],
    ALPHA: Float64,
    BETA: Float64,
    U: Float64[LDU, Flat],
    LDU: Int32,
    VT: Float64[LDVT, Flat],
    LDVT: Int32,
    DSIGMA: Float64[Flat],
    U2: Float64[LDU2, Flat],
    LDU2: Int32,
    VT2: Float64[LDVT2, Flat],
    LDVT2: Int32,
    IDXP: Int32[Flat],
    IDX: Int32[Flat],
    IDXC: Int32[Flat],
    IDXQ: Int32[Flat],
    COLTYP: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLASD3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def dlasd3(
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    K: Int32,
    D: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    DSIGMA: Float64[Flat],
    U: Float64[LDU, Flat],
    LDU: Int32,
    U2: Float64[LDU2, Flat],
    LDU2: Int32,
    VT: Float64[LDVT, Flat],
    LDVT: Int32,
    VT2: Float64[LDVT2, Flat],
    LDVT2: Int32,
    IDXC: Int32[Flat],
    CTOT: Int32[Flat],
    Z: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLASD4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def dlasd4(
    N: Int32,
    I: Int32,
    D: Float64[Flat],
    Z: Float64[Flat],
    DELTA: Float64[Flat],
    RHO: Float64,
    SIGMA: Float64,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLASD5")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6)])
def dlasd5(
    I: Int32,
    D: Float64[2],
    Z: Float64[2],
    DELTA: Float64[2],
    RHO: Float64,
    DSIGMA: Float64,
    WORK: Float64[2]
) -> None: ...

@bind("DLASD6")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Addr(Arg(21)), Addr(Arg(22)), Arg(23), Arg(24), Addr(Arg(25))])
def dlasd6(
    ICOMPQ: Int32,
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    D: Float64[Flat],
    VF: Float64[Flat],
    VL: Float64[Flat],
    ALPHA: Float64,
    BETA: Float64,
    IDXQ: Int32[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32,
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    GIVNUM: Float64[LDGNUM, Flat],
    LDGNUM: Int32,
    POLES: Float64[LDGNUM, Flat],
    DIFL: Float64[Flat],
    DIFR: Float64[Flat],
    Z: Float64[Flat],
    K: Int32,
    C: Float64,
    S: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLASD7")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26))])
def dlasd7(
    ICOMPQ: Int32,
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    K: Int32,
    D: Float64[Flat],
    Z: Float64[Flat],
    ZW: Float64[Flat],
    VF: Float64[Flat],
    VFW: Float64[Flat],
    VL: Float64[Flat],
    VLW: Float64[Flat],
    ALPHA: Float64,
    BETA: Float64,
    DSIGMA: Float64[Flat],
    IDX: Int32[Flat],
    IDXP: Int32[Flat],
    IDXQ: Int32[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32,
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    GIVNUM: Float64[LDGNUM, Flat],
    LDGNUM: Int32,
    C: Float64,
    S: Float64,
    INFO: Int32
) -> None: ...

@bind("DLASD8")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def dlasd8(
    ICOMPQ: Int32,
    K: Int32,
    D: Float64[Flat],
    Z: Float64[Flat],
    VF: Float64[Flat],
    VL: Float64[Flat],
    DIFL: Float64[Flat],
    DIFR: Float64[LDDIFR, Flat],
    LDDIFR: Int32,
    DSIGMA: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLASDA")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def dlasda(
    ICOMPQ: Int32,
    SMLSIZ: Int32,
    N: Int32,
    SQRE: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    U: Float64[LDU, Flat],
    LDU: Int32,
    VT: Float64[LDU, Flat],
    K: Int32[Flat],
    DIFL: Float64[LDU, Flat],
    DIFR: Float64[LDU, Flat],
    Z: Float64[LDU, Flat],
    POLES: Float64[LDU, Flat],
    GIVPTR: Int32[Flat],
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    PERM: Int32[LDGCOL, Flat],
    GIVNUM: Float64[LDU, Flat],
    C: Float64[Flat],
    S: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DLASDQ")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15))])
def dlasdq(
    UPLO: String[1],
    SQRE: Int32,
    N: Int32,
    NCVT: Int32,
    NRU: Int32,
    NCC: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    VT: Float64[LDVT, Flat],
    LDVT: Int32,
    U: Float64[LDU, Flat],
    LDU: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLASDT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def dlasdt(
    N: Int32,
    LVL: Int32,
    ND: Int32,
    INODE: Int32[Flat],
    NDIML: Int32[Flat],
    NDIMR: Int32[Flat],
    MSUB: Int32
) -> None: ...

@bind("DLASET")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def dlaset(
    UPLO: String[1],
    M: Int32,
    N: Int32,
    ALPHA: Float64,
    BETA: Float64,
    A: Float64[LDA, Flat],
    LDA: Int32
) -> None: ...

@bind("DLASQ1")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4))])
def dlasq1(
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLASQ2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2))])
def dlasq2(
    N: Int32,
    Z: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLASQ3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Addr(Arg(18)), Addr(Arg(19))])
def dlasq3(
    I0: Int32,
    N0: Int32,
    Z: Float64[Flat],
    PP: Int32,
    DMIN: Float64,
    SIGMA: Float64,
    DESIG: Float64,
    QMAX: Float64,
    NFAIL: Int32,
    ITER: Int32,
    NDIV: Int32,
    IEEE: Bool,
    TTYPE: Int32,
    DMIN1: Float64,
    DMIN2: Float64,
    DN: Float64,
    DN1: Float64,
    DN2: Float64,
    G: Float64,
    TAU: Float64
) -> None: ...

@bind("DLASQ4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13))])
def dlasq4(
    I0: Int32,
    N0: Int32,
    Z: Float64[Flat],
    PP: Int32,
    N0IN: Int32,
    DMIN: Float64,
    DMIN1: Float64,
    DMIN2: Float64,
    DN: Float64,
    DN1: Float64,
    DN2: Float64,
    TAU: Float64,
    TTYPE: Int32,
    G: Float64
) -> None: ...

@bind("DLASQ5")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13))])
def dlasq5(
    I0: Int32,
    N0: Int32,
    Z: Float64[Flat],
    PP: Int32,
    TAU: Float64,
    SIGMA: Float64,
    DMIN: Float64,
    DMIN1: Float64,
    DMIN2: Float64,
    DN: Float64,
    DNM1: Float64,
    DNM2: Float64,
    IEEE: Bool,
    EPS: Float64
) -> None: ...

@bind("DLASQ6")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def dlasq6(
    I0: Int32,
    N0: Int32,
    Z: Float64[Flat],
    PP: Int32,
    DMIN: Float64,
    DMIN1: Float64,
    DMIN2: Float64,
    DN: Float64,
    DNM1: Float64,
    DNM2: Float64
) -> None: ...

@bind("DLASR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8))])
def dlasr(
    SIDE: String[1],
    PIVOT: String[1],
    DIRECT: String[1],
    M: Int32,
    N: Int32,
    C: Float64[Flat],
    S: Float64[Flat],
    A: Float64[LDA, Flat],
    LDA: Int32
) -> None: ...

@bind("DLASRT")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def dlasrt(
    ID: String[1],
    N: Int32,
    D: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLASSQ")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def dlassq(
    n: Int32,
    x: Float64[Flat],
    incx: Int32,
    scale: Float64,
    sumsq: Float64
) -> None: ...

@bind("DLASV2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8))])
def dlasv2(
    F: Float64,
    G: Float64,
    H: Float64,
    SSMIN: Float64,
    SSMAX: Float64,
    SNR: Float64,
    CSR: Float64,
    SNL: Float64,
    CSL: Float64
) -> None: ...

@bind("DLASWLQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dlaswlq(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DLASWP")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def dlaswp(
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    K1: Int32,
    K2: Int32,
    IPIV: Int32[Flat],
    INCX: Int32
) -> None: ...

@bind("DLASY2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15))])
def dlasy2(
    LTRANL: Bool,
    LTRANR: Bool,
    ISGN: Int32,
    N1: Int32,
    N2: Int32,
    TL: Float64[LDTL, Flat],
    LDTL: Int32,
    TR: Float64[LDTR, Flat],
    LDTR: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    SCALE: Float64,
    X: Float64[LDX, Flat],
    LDX: Int32,
    XNORM: Float64,
    INFO: Int32
) -> None: ...

@bind("DLASYF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def dlasyf(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    W: Float64[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("DLASYF_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9)])
def dlasyf_aa(
    UPLO: String[1],
    J1: Int32,
    M: Int32,
    NB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    H: Float64[LDH, Flat],
    LDH: Int32,
    WORK: Float64[Flat]
) -> None: ...

@bind("DLASYF_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dlasyf_rk(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    E: Float64[Flat],
    IPIV: Int32[Flat],
    W: Float64[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("DLASYF_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def dlasyf_rook(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    W: Float64[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("DLAT2S")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def dlat2s(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    SA: Float32[LDSA, Flat],
    LDSA: Int32,
    INFO: Int32
) -> None: ...

@bind("DLATBS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def dlatbs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    X: Float64[Flat],
    SCALE: Float64,
    CNORM: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLATDF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8)])
def dlatdf(
    IJOB: Int32,
    N: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    RHS: Float64[Flat],
    RDSUM: Float64,
    RDSCAL: Float64,
    IPIV: Int32[Flat],
    JPIV: Int32[Flat]
) -> None: ...

@bind("DLATPS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def dlatps(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    AP: Float64[Flat],
    X: Float64[Flat],
    SCALE: Float64,
    CNORM: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLATRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8))])
def dlatrd(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    E: Float64[Flat],
    TAU: Float64[Flat],
    W: Float64[LDW, Flat],
    LDW: Int32
) -> None: ...

@bind("DLATRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def dlatrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    X: Float64[Flat],
    SCALE: Float64,
    CNORM: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DLATRS3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def dlatrs3(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    SCALE: Float64[Flat],
    CNORM: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DLATRZ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6)])
def dlatrz(
    M: Int32,
    N: Int32,
    L: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat]
) -> None: ...

@bind("DLATSQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dlatsqr(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DLAUU2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def dlauu2(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("DLAUUM")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def dlauum(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("DOPGTR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def dopgtr(
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    TAU: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DOPMTR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def dopmtr(
    SIDE: String[1],
    UPLO: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    AP: Float64[Flat],
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DORBDB")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Addr(Arg(21))])
def dorbdb(
    TRANS: String[1],
    SIGNS: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float64[LDX11, Flat],
    LDX11: Int32,
    X12: Float64[LDX12, Flat],
    LDX12: Int32,
    X21: Float64[LDX21, Flat],
    LDX21: Int32,
    X22: Float64[LDX22, Flat],
    LDX22: Int32,
    THETA: Float64[Flat],
    PHI: Float64[Flat],
    TAUP1: Float64[Flat],
    TAUP2: Float64[Flat],
    TAUQ1: Float64[Flat],
    TAUQ2: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORBDB1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def dorbdb1(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float64[LDX11, Flat],
    LDX11: Int32,
    X21: Float64[LDX21, Flat],
    LDX21: Int32,
    THETA: Float64[Flat],
    PHI: Float64[Flat],
    TAUP1: Float64[Flat],
    TAUP2: Float64[Flat],
    TAUQ1: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORBDB2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def dorbdb2(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float64[LDX11, Flat],
    LDX11: Int32,
    X21: Float64[LDX21, Flat],
    LDX21: Int32,
    THETA: Float64[Flat],
    PHI: Float64[Flat],
    TAUP1: Float64[Flat],
    TAUP2: Float64[Flat],
    TAUQ1: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORBDB3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def dorbdb3(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float64[LDX11, Flat],
    LDX11: Int32,
    X21: Float64[LDX21, Flat],
    LDX21: Int32,
    THETA: Float64[Flat],
    PHI: Float64[Flat],
    TAUP1: Float64[Flat],
    TAUP2: Float64[Flat],
    TAUQ1: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORBDB4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def dorbdb4(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float64[LDX11, Flat],
    LDX11: Int32,
    X21: Float64[LDX21, Flat],
    LDX21: Int32,
    THETA: Float64[Flat],
    PHI: Float64[Flat],
    TAUP1: Float64[Flat],
    TAUP2: Float64[Flat],
    TAUQ1: Float64[Flat],
    PHANTOM: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORBDB5")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dorbdb5(
    M1: Int32,
    M2: Int32,
    N: Int32,
    X1: Float64[Flat],
    INCX1: Int32,
    X2: Float64[Flat],
    INCX2: Int32,
    Q1: Float64[LDQ1, Flat],
    LDQ1: Int32,
    Q2: Float64[LDQ2, Flat],
    LDQ2: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORBDB6")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dorbdb6(
    M1: Int32,
    M2: Int32,
    N: Int32,
    X1: Float64[Flat],
    INCX1: Int32,
    X2: Float64[Flat],
    INCX2: Int32,
    Q1: Float64[LDQ1, Flat],
    LDQ1: Int32,
    Q2: Float64[LDQ2, Flat],
    LDQ2: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORCSD")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25)), Arg(26), Addr(Arg(27)), Arg(28), Addr(Arg(29))])
def dorcsd(
    JOBU1: String[1],
    JOBU2: String[1],
    JOBV1T: String[1],
    JOBV2T: String[1],
    TRANS: String[1],
    SIGNS: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float64[LDX11, Flat],
    LDX11: Int32,
    X12: Float64[LDX12, Flat],
    LDX12: Int32,
    X21: Float64[LDX21, Flat],
    LDX21: Int32,
    X22: Float64[LDX22, Flat],
    LDX22: Int32,
    THETA: Float64[Flat],
    U1: Float64[LDU1, Flat],
    LDU1: Int32,
    U2: Float64[LDU2, Flat],
    LDU2: Int32,
    V1T: Float64[LDV1T, Flat],
    LDV1T: Int32,
    V2T: Float64[LDV2T, Flat],
    LDV2T: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DORCSD2BY1")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20))])
def dorcsd2by1(
    JOBU1: String[1],
    JOBU2: String[1],
    JOBV1T: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float64[LDX11, Flat],
    LDX11: Int32,
    X21: Float64[LDX21, Flat],
    LDX21: Int32,
    THETA: Float64[Flat],
    U1: Float64[LDU1, Flat],
    LDU1: Int32,
    U2: Float64[LDU2, Flat],
    LDU2: Int32,
    V1T: Float64[LDV1T, Flat],
    LDV1T: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DORG2L")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def dorg2l(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DORG2R")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def dorg2r(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DORGBR")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def dorgbr(
    VECT: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORGHR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dorghr(
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORGL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def dorgl2(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DORGLQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dorglq(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORGQL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dorgql(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORGQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dorgqr(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORGR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def dorgr2(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DORGRQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dorgrq(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORGTR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dorgtr(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORGTSQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dorgtsqr(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORGTSQR_ROW")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dorgtsqr_row(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORHR_COL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def dorhr_col(
    M: Int32,
    N: Int32,
    NB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    D: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DORM22")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dorm22(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    N1: Int32,
    N2: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORM2L")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def dorm2l(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DORM2R")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def dorm2r(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DORMBR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dormbr(
    VECT: String[1],
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORMHR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dormhr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORML2")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def dorml2(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DORMLQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dormlq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORMQL")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dormql(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORMQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dormqr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORMR2")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def dormr2(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DORMR3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def dormr3(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DORMRQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dormrq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORMRZ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dormrz(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DORMTR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dormtr(
    SIDE: String[1],
    UPLO: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    C: Float64[LDC, Flat],
    LDC: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DPBCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def dpbcon(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    ANORM: Float64,
    RCOND: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DPBEQU")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8))])
def dpbequ(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("DPBRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def dpbrfs(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    AFB: Float64[LDAFB, Flat],
    LDAFB: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DPBSTF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def dpbstf(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    INFO: Int32
) -> None: ...

@bind("DPBSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dpbsv(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DPBSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20))])
def dpbsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    AFB: Float64[LDAFB, Flat],
    LDAFB: Int32,
    EQUED: String[1],
    S: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DPBTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def dpbtf2(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    INFO: Int32
) -> None: ...

@bind("DPBTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def dpbtrf(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    INFO: Int32
) -> None: ...

@bind("DPBTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dpbtrs(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DPFTRF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4))])
def dpftrf(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DPFTRI")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4))])
def dpftri(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DPFTRS")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dpftrs(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DPOCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def dpocon(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    ANORM: Float64,
    RCOND: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DPOEQU")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def dpoequ(
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("DPOEQUB")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def dpoequb(
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("DPORFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15))])
def dporfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DPORFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Addr(Arg(22))])
def dporfsx(
    UPLO: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    S: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DPOSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dposv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DPOSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def dposvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    EQUED: String[1],
    S: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DPOSVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def dposvxx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    EQUED: String[1],
    S: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    RPVGRW: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DPOTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def dpotf2(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("DPOTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def dpotrf(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("DPOTRF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def dpotrf2(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("DPOTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def dpotri(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("DPOTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dpotrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DPPCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def dppcon(
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DPPEQU")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def dppequ(
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("DPPRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def dpprfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float64[Flat],
    AFP: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DPPSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def dppsv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DPPSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Arg(14), Arg(15), Arg(16), Addr(Arg(17))])
def dppsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float64[Flat],
    AFP: Float64[Flat],
    EQUED: String[1],
    S: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DPPTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def dpptrf(
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DPPTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def dpptri(
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DPPTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def dpptrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DPSTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def dpstf2(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    PIV: Int32[N],
    RANK: Int32,
    TOL: Float64,
    WORK: Float64[2 * N],
    INFO: Int32
) -> None: ...

@bind("DPSTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def dpstrf(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    PIV: Int32[N],
    RANK: Int32,
    TOL: Float64,
    WORK: Float64[2 * N],
    INFO: Int32
) -> None: ...

@bind("DPTCON")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def dptcon(
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DPTEQR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def dpteqr(
    COMPZ: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DPTRFS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def dptrfs(
    N: Int32,
    NRHS: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    DF: Float64[Flat],
    EF: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DPTSV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def dptsv(
    N: Int32,
    NRHS: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DPTSVX")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Addr(Arg(15))])
def dptsvx(
    FACT: String[1],
    N: Int32,
    NRHS: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    DF: Float64[Flat],
    EF: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DPTTRF")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3))])
def dpttrf(
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DPTTRS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def dpttrs(
    N: Int32,
    NRHS: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DPTTS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5))])
def dptts2(
    N: Int32,
    NRHS: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("DRSCL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def drscl(
    N: Int32,
    SA: Float64,
    SX: Float64[Flat],
    INCX: Int32
) -> None: ...

@bind("DSB2ST_KERNELS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14)])
def dsb2st_kernels(
    UPLO: String[1],
    WANTZ: Bool,
    TTYPE: Int32,
    ST: Int32,
    ED: Int32,
    SWEEP: Int32,
    N: Int32,
    NB: Int32,
    IB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    V: Float64[Flat],
    TAU: Float64[Flat],
    LDVT: Int32,
    WORK: Float64[Flat]
) -> None: ...

@bind("DSBEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def dsbev(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSBEV_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def dsbev_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSBEVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dsbevd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSBEVD_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dsbevd_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSBEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def dsbevx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSBEVX_2STAGE")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22))])
def dsbevx_2stage(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSBGST")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def dsbgst(
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    BB: Float64[LDBB, Flat],
    LDBB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSBGV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def dsbgv(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    BB: Float64[LDBB, Flat],
    LDBB: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSBGVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def dsbgvd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    BB: Float64[LDBB, Flat],
    LDBB: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSBGVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def dsbgvx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    BB: Float64[LDBB, Flat],
    LDBB: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSBTRD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def dsbtrd(
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSFRK")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9)])
def dsfrk(
    TRANSR: String[1],
    UPLO: String[1],
    TRANS: String[1],
    N: Int32,
    K: Int32,
    ALPHA: Float64,
    A: Float64[LDA, Flat],
    LDA: Int32,
    BETA: Float64,
    C: Float64[Flat]
) -> None: ...

@bind("DSGESV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dsgesv(
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    WORK: Float64[N, Flat],
    SWORK: Float32[Flat],
    ITER: Int32,
    INFO: Int32
) -> None: ...

@bind("DSPCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def dspcon(
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSPEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def dspev(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSPEVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def dspevd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSPEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17))])
def dspevx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSPGST")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def dspgst(
    ITYPE: Int32,
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    BP: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSPGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def dspgv(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    BP: Float64[Flat],
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSPGVD")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dspgvd(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    BP: Float64[Flat],
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSPGVX")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def dspgvx(
    ITYPE: Int32,
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    BP: Float64[Flat],
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSPOSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dsposv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    WORK: Float64[N, Flat],
    SWORK: Float32[Flat],
    ITER: Int32,
    INFO: Int32
) -> None: ...

@bind("DSPRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14))])
def dsprfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float64[Flat],
    AFP: Float64[Flat],
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSPSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dspsv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float64[Flat],
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DSPSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def dspsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float64[Flat],
    AFP: Float64[Flat],
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSPTRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def dsptrd(
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    D: Float64[Flat],
    E: Float64[Flat],
    TAU: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSPTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def dsptrf(
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSPTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5))])
def dsptri(
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    IPIV: Int32[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSPTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dsptrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float64[Flat],
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DSTEBZ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Arg(16), Addr(Arg(17))])
def dstebz(
    RANGE: String[1],
    ORDER: String[1],
    N: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    D: Float64[Flat],
    E: Float64[Flat],
    M: Int32,
    NSPLIT: Int32,
    W: Float64[Flat],
    IBLOCK: Int32[Flat],
    ISPLIT: Int32[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSTEDC")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dstedc(
    COMPZ: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSTEGR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Addr(Arg(19))])
def dstegr(
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSTEIN")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12))])
def dstein(
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    M: Int32,
    W: Float64[Flat],
    IBLOCK: Int32[Flat],
    ISPLIT: Int32[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSTEMR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Addr(Arg(20))])
def dstemr(
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    NZC: Int32,
    ISUPPZ: Int32[Flat],
    TRYRAC: Bool,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSTEQR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def dsteqr(
    COMPZ: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSTERF")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3))])
def dsterf(
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSTEV")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def dstev(
    JOBZ: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSTEVD")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dstevd(
    JOBZ: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSTEVR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Addr(Arg(19))])
def dstevr(
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSTEVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17))])
def dstevx(
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def dsycon(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYCON_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def dsycon_3(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    E: Float64[Flat],
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYCON_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def dsycon_rook(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYCONV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def dsyconv(
    UPLO: String[1],
    WAY: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    E: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYCONVF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def dsyconvf(
    UPLO: String[1],
    WAY: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    E: Float64[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYCONVF_ROOK")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def dsyconvf_rook(
    UPLO: String[1],
    WAY: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    E: Float64[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYEQUB")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def dsyequb(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dsyev(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    W: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYEV_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dsyev_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    W: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYEVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dsyevd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    W: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYEVD_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dsyevd_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    W: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYEVR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Addr(Arg(20))])
def dsyevr(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYEVR_2STAGE")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Addr(Arg(20))])
def dsyevr_2stage(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19))])
def dsyevx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYEVX_2STAGE")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19))])
def dsyevx_2stage(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYGS2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dsygs2(
    ITYPE: Int32,
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYGST")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dsygst(
    ITYPE: Int32,
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def dsygv(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    W: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYGV_2STAGE")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def dsygv_2stage(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    W: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYGVD")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dsygvd(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    W: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYGVX")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22))])
def dsygvx(
    ITYPE: Int32,
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def dsyrfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYRFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def dsyrfsx(
    UPLO: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    S: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dsysv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYSV_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dsysv_aa(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYSV_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dsysv_aa_2stage(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TB: Float64[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYSV_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def dsysv_rk(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    E: Float64[Flat],
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYSV_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dsysv_rook(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def dsysvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYSVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Arg(24), Addr(Arg(25))])
def dsysvxx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AF: Float64[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    S: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    RPVGRW: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYSWAPR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def dsyswapr(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    I1: Int32,
    I2: Int32
) -> None: ...

@bind("DSYTD2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7))])
def dsytd2(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    TAU: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def dsytf2(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYTF2_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def dsytf2_rk(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    E: Float64[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYTF2_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def dsytf2_rook(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYTRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def dsytrd(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRD_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def dsytrd_2stage(
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    TAU: Float64[Flat],
    HOUS2: Float64[Flat],
    LHOUS2: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRD_SB2ST")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def dsytrd_sb2st(
    STAGE1: String[1],
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    HOUS: Float64[Flat],
    LHOUS: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRD_SY2SB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dsytrd_sy2sb(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dsytrf(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRF_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dsytrf_aa(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRF_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dsytrf_aa_2stage(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TB: Float64[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRF_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dsytrf_rk(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    E: Float64[Flat],
    IPIV: Int32[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRF_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dsytrf_rook(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def dsytri(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYTRI2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dsytri2(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRI2X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dsytri2x(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float64[N + NB + 1, Flat],
    NB: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRI_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dsytri_3(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    E: Float64[Flat],
    IPIV: Int32[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRI_3X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dsytri_3x(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    E: Float64[Flat],
    IPIV: Int32[Flat],
    WORK: Float64[N + NB + 1, Flat],
    NB: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRI_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def dsytri_rook(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dsytrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRS2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def dsytrs2(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DSYTRS_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def dsytrs_3(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    E: Float64[Flat],
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRS_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dsytrs_aa(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRS_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def dsytrs_aa_2stage(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TB: Float64[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DSYTRS_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dsytrs_rook(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DTBCON")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def dtbcon(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    KD: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    RCOND: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DTBRFS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def dtbrfs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DTBTRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def dtbtrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Float64[LDAB, Flat],
    LDAB: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DTFSM")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def dtfsm(
    TRANSR: String[1],
    SIDE: String[1],
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    M: Int32,
    N: Int32,
    ALPHA: Float64,
    A: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("DTFTRI")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def dtftri(
    TRANSR: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DTFTTP")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def dtfttp(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    ARF: Float64[Flat],
    AP: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DTFTTR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def dtfttr(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    ARF: Float64[Flat],
    A: Float64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("DTGEVC")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15))])
def dtgevc(
    SIDE: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    S: Float64[LDS, Flat],
    LDS: Int32,
    P: Float64[LDP, Flat],
    LDP: Int32,
    VL: Float64[LDVL, Flat],
    LDVL: Int32,
    VR: Float64[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DTGEX2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def dtgex2(
    WANTQ: Bool,
    WANTZ: Bool,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    J1: Int32,
    N1: Int32,
    N2: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DTGEXC")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def dtgexc(
    WANTQ: Bool,
    WANTZ: Bool,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    IFST: Int32,
    ILST: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DTGSEN")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Addr(Arg(24))])
def dtgsen(
    IJOB: Int32,
    WANTQ: Bool,
    WANTZ: Bool,
    SELECT: Bool[Flat],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    ALPHAR: Float64[Flat],
    ALPHAI: Float64[Flat],
    BETA: Float64[Flat],
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    Z: Float64[LDZ, Flat],
    LDZ: Int32,
    M: Int32,
    PL: Float64,
    PR: Float64,
    DIF: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DTGSJA")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Addr(Arg(24))])
def dtgsja(
    JOBU: String[1],
    JOBV: String[1],
    JOBQ: String[1],
    M: Int32,
    P: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    TOLA: Float64,
    TOLB: Float64,
    ALPHA: Float64[Flat],
    BETA: Float64[Flat],
    U: Float64[LDU, Flat],
    LDU: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    WORK: Float64[Flat],
    NCYCLE: Int32,
    INFO: Int32
) -> None: ...

@bind("DTGSNA")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def dtgsna(
    JOB: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    VL: Float64[LDVL, Flat],
    LDVL: Int32,
    VR: Float64[LDVR, Flat],
    LDVR: Int32,
    S: Float64[Flat],
    DIF: Float64[Flat],
    MM: Int32,
    M: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DTGSY2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Addr(Arg(21))])
def dtgsy2(
    TRANS: String[1],
    IJOB: Int32,
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    D: Float64[LDD, Flat],
    LDD: Int32,
    E: Float64[LDE, Flat],
    LDE: Int32,
    F: Float64[LDF, Flat],
    LDF: Int32,
    SCALE: Float64,
    RDSUM: Float64,
    RDSCAL: Float64,
    IWORK: Int32[Flat],
    PQ: Int32,
    INFO: Int32
) -> None: ...

@bind("DTGSYL")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21))])
def dtgsyl(
    TRANS: String[1],
    IJOB: Int32,
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    D: Float64[LDD, Flat],
    LDD: Int32,
    E: Float64[LDE, Flat],
    LDE: Int32,
    F: Float64[LDF, Flat],
    LDF: Int32,
    SCALE: Float64,
    DIF: Float64,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DTPCON")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def dtpcon(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    AP: Float64[Flat],
    RCOND: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DTPLQT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def dtplqt(
    M: Int32,
    N: Int32,
    L: Int32,
    MB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DTPLQT2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def dtplqt2(
    M: Int32,
    N: Int32,
    L: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("DTPMLQT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def dtpmlqt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    MB: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DTPMQRT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def dtpmqrt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    NB: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DTPQRT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def dtpqrt(
    M: Int32,
    N: Int32,
    L: Int32,
    NB: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DTPQRT2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def dtpqrt2(
    M: Int32,
    N: Int32,
    L: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("DTPRFB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def dtprfb(
    SIDE: String[1],
    TRANS: String[1],
    DIRECT: String[1],
    STOREV: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    V: Float64[LDV, Flat],
    LDV: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    WORK: Float64[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("DTPRFS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14))])
def dtprfs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DTPTRI")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4))])
def dtptri(
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    AP: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DTPTRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def dtptrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float64[Flat],
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DTPTTF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def dtpttf(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    ARF: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DTPTTR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def dtpttr(
    UPLO: String[1],
    N: Int32,
    AP: Float64[Flat],
    A: Float64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("DTRCON")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def dtrcon(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    RCOND: Float64,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DTREVC")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def dtrevc(
    SIDE: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    VL: Float64[LDVL, Flat],
    LDVL: Int32,
    VR: Float64[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DTREVC3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def dtrevc3(
    SIDE: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    VL: Float64[LDVL, Flat],
    LDVL: Int32,
    VR: Float64[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DTREXC")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def dtrexc(
    COMPQ: String[1],
    N: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    IFST: Int32,
    ILST: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DTRRFS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15))])
def dtrrfs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    X: Float64[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DTRSEN")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Addr(Arg(17))])
def dtrsen(
    JOB: String[1],
    COMPQ: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    Q: Float64[LDQ, Flat],
    LDQ: Int32,
    WR: Float64[Flat],
    WI: Float64[Flat],
    M: Int32,
    S: Float64,
    SEP: Float64,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DTRSNA")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def dtrsna(
    JOB: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Float64[LDT, Flat],
    LDT: Int32,
    VL: Float64[LDVL, Flat],
    LDVL: Int32,
    VR: Float64[LDVR, Flat],
    LDVR: Int32,
    S: Float64[Flat],
    SEP: Float64[Flat],
    MM: Int32,
    M: Int32,
    WORK: Float64[LDWORK, Flat],
    LDWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("DTRSYL")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12))])
def dtrsyl(
    TRANA: String[1],
    TRANB: String[1],
    ISGN: Int32,
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    SCALE: Float64,
    INFO: Int32
) -> None: ...

@bind("DTRSYL3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def dtrsyl3(
    TRANA: String[1],
    TRANB: String[1],
    ISGN: Int32,
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    C: Float64[LDC, Flat],
    LDC: Int32,
    SCALE: Float64,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    SWORK: Float64[LDSWORK, Flat],
    LDSWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DTRTI2")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def dtrti2(
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("DTRTRI")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def dtrtri(
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("DTRTRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def dtrtrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("DTRTTF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def dtrttf(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    ARF: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DTRTTP")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def dtrttp(
    UPLO: String[1],
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    AP: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("DTZRZF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def dtzrzf(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    TAU: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("DZSUM1")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2))])
def dzsum1(
    N: Int32,
    CX: Complex128[Flat],
    INCX: Int32
) -> Float64: ...

@bind("ICMAX1")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2))])
def icmax1(
    N: Int32,
    CX: Complex64[Flat],
    INCX: Int32
) -> Int32: ...

@bind("IEEECK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2))])
def ieeeck(
    ISPEC: Int32,
    ZERO: Float32,
    ONE: Float32
) -> Int32: ...

@bind("ILACLC")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def ilaclc(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32
) -> Int32: ...

@bind("ILACLR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def ilaclr(
    M: Int32,
    N: Int32,
    A: Complex64[LDA, Flat],
    LDA: Int32
) -> Int32: ...

@bind("ILADIAG")
@external
def iladiag(
    DIAG: String[1]
) -> Int32: ...

@bind("ILADLC")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def iladlc(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32
) -> Int32: ...

@bind("ILADLR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def iladlr(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32
) -> Int32: ...

@bind("ILAENV")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def ilaenv(
    ISPEC: Int32,
    NAME: String,
    OPTS: String,
    N1: Int32,
    N2: Int32,
    N3: Int32,
    N4: Int32
) -> Int32: ...

@bind("ILAENV2STAGE")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def ilaenv2stage(
    ISPEC: Int32,
    NAME: String,
    OPTS: String,
    N1: Int32,
    N2: Int32,
    N3: Int32,
    N4: Int32
) -> Int32: ...

@bind("ILAPREC")
@external
def ilaprec(
    PREC: String[1]
) -> Int32: ...

@bind("ILASLC")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def ilaslc(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32
) -> Int32: ...

@bind("ILASLR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def ilaslr(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32
) -> Int32: ...

@bind("ILATRANS")
@external
def ilatrans(
    TRANS: String[1]
) -> Int32: ...

@bind("ILAUPLO")
@external
def ilauplo(
    UPLO: String[1]
) -> Int32: ...

@bind("ILAZLC")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def ilazlc(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32
) -> Int32: ...

@bind("ILAZLR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def ilazlr(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32
) -> Int32: ...

@bind("IPARAM2STAGE")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def iparam2stage(
    ISPEC: Int32,
    NAME: String,
    OPTS: String,
    NI: Int32,
    NBI: Int32,
    IBI: Int32,
    NXI: Int32
) -> Int32: ...

@bind("IPARMQ")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def iparmq(
    ISPEC: Int32,
    NAME: String[1][Flat],
    OPTS: String[1][Flat],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    LWORK: Int32
) -> Int32: ...

@bind("IZMAX1")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2))])
def izmax1(
    N: Int32,
    ZX: Complex128[Flat],
    INCX: Int32
) -> Int32: ...

@bind("LSAMEN")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2)])
def lsamen(
    N: Int32,
    CA: String,
    CB: String
) -> Bool: ...

@bind("SBBCSD")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Arg(23), Arg(24), Arg(25), Arg(26), Addr(Arg(27)), Addr(Arg(28))])
def sbbcsd(
    JOBU1: String[1],
    JOBU2: String[1],
    JOBV1T: String[1],
    JOBV2T: String[1],
    TRANS: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    THETA: Float32[Flat],
    PHI: Float32[Flat],
    U1: Float32[LDU1, Flat],
    LDU1: Int32,
    U2: Float32[LDU2, Flat],
    LDU2: Int32,
    V1T: Float32[LDV1T, Flat],
    LDV1T: Int32,
    V2T: Float32[LDV2T, Flat],
    LDV2T: Int32,
    B11D: Float32[Flat],
    B11E: Float32[Flat],
    B12D: Float32[Flat],
    B12E: Float32[Flat],
    B21D: Float32[Flat],
    B21E: Float32[Flat],
    B22D: Float32[Flat],
    B22E: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SBDSDC")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def sbdsdc(
    UPLO: String[1],
    COMPQ: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    U: Float32[LDU, Flat],
    LDU: Int32,
    VT: Float32[LDVT, Flat],
    LDVT: Int32,
    Q: Float32[Flat],
    IQ: Int32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SBDSQR")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14))])
def sbdsqr(
    UPLO: String[1],
    N: Int32,
    NCVT: Int32,
    NRU: Int32,
    NCC: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    VT: Float32[LDVT, Flat],
    LDVT: Int32,
    U: Float32[LDU, Flat],
    LDU: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SBDSVDX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16))])
def sbdsvdx(
    UPLO: String[1],
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    NS: Int32,
    S: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SCSUM1")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2))])
def scsum1(
    N: Int32,
    CX: Complex64[Flat],
    INCX: Int32
) -> Float32: ...

@bind("SDISNA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def sdisna(
    JOB: String[1],
    M: Int32,
    N: Int32,
    D: Float32[Flat],
    SEP: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGBBRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def sgbbrd(
    VECT: String[1],
    M: Int32,
    N: Int32,
    NCC: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    PT: Float32[LDPT, Flat],
    LDPT: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGBCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def sgbcon(
    NORM: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGBEQU")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11))])
def sgbequ(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    R: Float32[Flat],
    C: Float32[Flat],
    ROWCND: Float32,
    COLCND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("SGBEQUB")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11))])
def sgbequb(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    R: Float32[Flat],
    C: Float32[Flat],
    ROWCND: Float32,
    COLCND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("SGBRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Addr(Arg(18))])
def sgbrfs(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    AFB: Float32[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGBRFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22)), Arg(23), Arg(24), Arg(25), Addr(Arg(26))])
def sgbrfsx(
    TRANS: String[1],
    EQUED: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    AFB: Float32[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    R: Float32[Flat],
    C: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGBSV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def sgbsv(
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SGBSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def sgbsvx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    AFB: Float32[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float32[Flat],
    C: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGBSVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Addr(Arg(24)), Arg(25), Arg(26), Arg(27), Addr(Arg(28))])
def sgbsvxx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    AFB: Float32[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float32[Flat],
    C: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    RPVGRW: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGBTF2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def sgbtf2(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGBTRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def sgbtrf(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGBTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def sgbtrs(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SGEBAK")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def sgebak(
    JOB: String[1],
    SIDE: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    SCALE: Float32[Flat],
    M: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    INFO: Int32
) -> None: ...

@bind("SGEBAL")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def sgebal(
    JOB: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    ILO: Int32,
    IHI: Int32,
    SCALE: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEBD2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9))])
def sgebd2(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    TAUQ: Float32[Flat],
    TAUP: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEBRD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def sgebrd(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    TAUQ: Float32[Flat],
    TAUP: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGECON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def sgecon(
    NORM: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    ANORM: Float32,
    RCOND: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEDMD")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Return('K', 0), Arg(13), Arg(14), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25)), Arg(26), Addr(Arg(27)), Return('INFO', 1)])
def sgedmd(
    JOBS: String[1],
    JOBZ: String[1],
    JOBR: String[1],
    JOBF: String[1],
    WHTSVD: Int32,
    M: Int32,
    N: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    Y: Float32[LDY, Flat],
    LDY: Int32,
    NRNK: Int32,
    TOL: Float32,
    REIG: Float32[Flat],
    IMEIG: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    RES: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    W: Float32[LDW, Flat],
    LDW: Int32,
    S: Float32[LDS, Flat],
    LDS: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32
) -> tuple[Int32, Int32]: ...

@bind("SGEDMDQ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Return('K', 0), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25)), Arg(26), Addr(Arg(27)), Arg(28), Addr(Arg(29)), Arg(30), Addr(Arg(31)), Return('INFO', 1)])
def sgedmdq(
    JOBS: String[1],
    JOBZ: String[1],
    JOBR: String[1],
    JOBQ: String[1],
    JOBT: String[1],
    JOBF: String[1],
    WHTSVD: Int32,
    M: Int32,
    N: Int32,
    F: Float32[LDF, Flat],
    LDF: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    Y: Float32[LDY, Flat],
    LDY: Int32,
    NRNK: Int32,
    TOL: Float32,
    REIG: Float32[Flat],
    IMEIG: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    RES: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    S: Float32[LDS, Flat],
    LDS: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32
) -> tuple[Int32, Int32]: ...

@bind("SGEEQU")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def sgeequ(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    R: Float32[Flat],
    C: Float32[Flat],
    ROWCND: Float32,
    COLCND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("SGEEQUB")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def sgeequb(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    R: Float32[Flat],
    C: Float32[Flat],
    ROWCND: Float32,
    COLCND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("SGEES")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14))])
def sgees(
    JOBVS: String[1],
    SORT: String[1],
    SELECT: Bool,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    SDIM: Int32,
    WR: Float32[Flat],
    WI: Float32[Flat],
    VS: Float32[LDVS, Flat],
    LDVS: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEESX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def sgeesx(
    JOBVS: String[1],
    SORT: String[1],
    SELECT: Bool,
    SENSE: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    SDIM: Int32,
    WR: Float32[Flat],
    WI: Float32[Flat],
    VS: Float32[LDVS, Flat],
    LDVS: Int32,
    RCONDE: Float32,
    RCONDV: Float32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def sgeev(
    JOBVL: String[1],
    JOBVR: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    WR: Float32[Flat],
    WI: Float32[Flat],
    VL: Float32[LDVL, Flat],
    LDVL: Int32,
    VR: Float32[LDVR, Flat],
    LDVR: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGEEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Addr(Arg(22))])
def sgeevx(
    BALANC: String[1],
    JOBVL: String[1],
    JOBVR: String[1],
    SENSE: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    WR: Float32[Flat],
    WI: Float32[Flat],
    VL: Float32[LDVL, Flat],
    LDVL: Int32,
    VR: Float32[LDVR, Flat],
    LDVR: Int32,
    ILO: Int32,
    IHI: Int32,
    SCALE: Float32[Flat],
    ABNRM: Float32,
    RCONDE: Float32[Flat],
    RCONDV: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEHD2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def sgehd2(
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEHRD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def sgehrd(
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGEJSV")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18))])
def sgejsv(
    JOBA: String[1],
    JOBU: String[1],
    JOBV: String[1],
    JOBR: String[1],
    JOBT: String[1],
    JOBP: String[1],
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    SVA: Float32[N],
    U: Float32[LDU, Flat],
    LDU: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    WORK: Float32[LWORK],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGELQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def sgelq(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[Flat],
    TSIZE: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGELQ2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def sgelq2(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGELQF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def sgelqf(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGELQT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def sgelqt(
    M: Int32,
    N: Int32,
    MB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGELQT3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def sgelqt3(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("SGELS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def sgels(
    TRANS: String[1],
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGELSD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def sgelsd(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    S: Float32[Flat],
    RCOND: Float32,
    RANK: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGELSS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def sgelss(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    S: Float32[Flat],
    RCOND: Float32,
    RANK: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGELST")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def sgelst(
    TRANS: String[1],
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGELSY")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def sgelsy(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    JPVT: Int32[Flat],
    RCOND: Float32,
    RANK: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGEMLQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def sgemlq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[Flat],
    TSIZE: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGEMLQT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def sgemlqt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    MB: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEMQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def sgemqr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[Flat],
    TSIZE: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGEMQRT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def sgemqrt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    NB: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEQL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def sgeql2(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEQLF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def sgeqlf(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGEQP3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def sgeqp3(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    JPVT: Int32[Flat],
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGEQP3RK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def sgeqp3rk(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    KMAX: Int32,
    ABSTOL: Float32,
    RELTOL: Float32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    K: Int32,
    MAXC2NRMK: Float32,
    RELMAXC2NRMK: Float32,
    JPIV: Int32[Flat],
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def sgeqr(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[Flat],
    TSIZE: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGEQR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def sgeqr2(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEQR2P")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def sgeqr2p(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEQRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def sgeqrf(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGEQRFP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def sgeqrfp(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGEQRT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def sgeqrt(
    M: Int32,
    N: Int32,
    NB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGEQRT2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def sgeqrt2(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("SGEQRT3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def sgeqrt3(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("SGERFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def sgerfs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGERFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def sgerfsx(
    TRANS: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    R: Float32[Flat],
    C: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGERQ2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def sgerq2(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGERQF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def sgerqf(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGESC2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def sgesc2(
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    RHS: Float32[Flat],
    IPIV: Int32[Flat],
    JPIV: Int32[Flat],
    SCALE: Float32
) -> None: ...

@bind("SGESDD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def sgesdd(
    JOBZ: String[1],
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    U: Float32[LDU, Flat],
    LDU: Int32,
    VT: Float32[LDVT, Flat],
    LDVT: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGESV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def sgesv(
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SGESVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def sgesvd(
    JOBU: String[1],
    JOBVT: String[1],
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    U: Float32[LDU, Flat],
    LDU: Int32,
    VT: Float32[LDVT, Flat],
    LDVT: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGESVDQ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Addr(Arg(21))])
def sgesvdq(
    JOBA: String[1],
    JOBP: String[1],
    JOBR: String[1],
    JOBU: String[1],
    JOBV: String[1],
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    U: Float32[LDU, Flat],
    LDU: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    NUMRANK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    RWORK: Float32[Flat],
    LRWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGESVDX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20))])
def sgesvdx(
    JOBU: String[1],
    JOBVT: String[1],
    RANGE: String[1],
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    NS: Int32,
    S: Float32[Flat],
    U: Float32[LDU, Flat],
    LDU: Int32,
    VT: Float32[LDVT, Flat],
    LDVT: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGESVJ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def sgesvj(
    JOBA: String[1],
    JOBU: String[1],
    JOBV: String[1],
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    SVA: Float32[N],
    MV: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    WORK: Float32[LWORK],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGESVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def sgesvx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float32[Flat],
    C: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGESVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22)), Arg(23), Arg(24), Arg(25), Addr(Arg(26))])
def sgesvxx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float32[Flat],
    C: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    RPVGRW: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGETC2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def sgetc2(
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    JPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGETF2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def sgetf2(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGETRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def sgetrf(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGETRF2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def sgetrf2(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGETRI")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def sgetri(
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGETRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def sgetrs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SGETSLS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def sgetsls(
    TRANS: String[1],
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGETSQRHRT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def sgetsqrhrt(
    M: Int32,
    N: Int32,
    MB1: Int32,
    NB1: Int32,
    NB2: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGGBAK")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def sggbak(
    JOB: String[1],
    SIDE: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    LSCALE: Float32[Flat],
    RSCALE: Float32[Flat],
    M: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    INFO: Int32
) -> None: ...

@bind("SGGBAL")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11))])
def sggbal(
    JOB: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    ILO: Int32,
    IHI: Int32,
    LSCALE: Float32[Flat],
    RSCALE: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGGES")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20))])
def sgges(
    JOBVSL: String[1],
    JOBVSR: String[1],
    SORT: String[1],
    SELCTG: Bool,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    SDIM: Int32,
    ALPHAR: Float32[Flat],
    ALPHAI: Float32[Flat],
    BETA: Float32[Flat],
    VSL: Float32[LDVSL, Flat],
    LDVSL: Int32,
    VSR: Float32[LDVSR, Flat],
    LDVSR: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("SGGES3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20))])
def sgges3(
    JOBVSL: String[1],
    JOBVSR: String[1],
    SORT: String[1],
    SELCTG: Bool,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    SDIM: Int32,
    ALPHAR: Float32[Flat],
    ALPHAI: Float32[Flat],
    BETA: Float32[Flat],
    VSL: Float32[LDVSL, Flat],
    LDVSL: Int32,
    VSR: Float32[LDVSR, Flat],
    LDVSR: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("SGGESX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25))])
def sggesx(
    JOBVSL: String[1],
    JOBVSR: String[1],
    SORT: String[1],
    SELCTG: Bool,
    SENSE: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    SDIM: Int32,
    ALPHAR: Float32[Flat],
    ALPHAI: Float32[Flat],
    BETA: Float32[Flat],
    VSL: Float32[LDVSL, Flat],
    LDVSL: Int32,
    VSR: Float32[LDVSR, Flat],
    LDVSR: Int32,
    RCONDE: Float32[2],
    RCONDV: Float32[2],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("SGGEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def sggev(
    JOBVL: String[1],
    JOBVR: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    ALPHAR: Float32[Flat],
    ALPHAI: Float32[Flat],
    BETA: Float32[Flat],
    VL: Float32[LDVL, Flat],
    LDVL: Int32,
    VR: Float32[LDVR, Flat],
    LDVR: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGGEV3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def sggev3(
    JOBVL: String[1],
    JOBVR: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    ALPHAR: Float32[Flat],
    ALPHAI: Float32[Flat],
    BETA: Float32[Flat],
    VL: Float32[LDVL, Flat],
    LDVL: Int32,
    VR: Float32[LDVR, Flat],
    LDVR: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGGEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Addr(Arg(21)), Arg(22), Arg(23), Arg(24), Addr(Arg(25)), Arg(26), Arg(27), Addr(Arg(28))])
def sggevx(
    BALANC: String[1],
    JOBVL: String[1],
    JOBVR: String[1],
    SENSE: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    ALPHAR: Float32[Flat],
    ALPHAI: Float32[Flat],
    BETA: Float32[Flat],
    VL: Float32[LDVL, Flat],
    LDVL: Int32,
    VR: Float32[LDVR, Flat],
    LDVR: Int32,
    ILO: Int32,
    IHI: Int32,
    LSCALE: Float32[Flat],
    RSCALE: Float32[Flat],
    ABNRM: Float32,
    BBNRM: Float32,
    RCONDE: Float32[Flat],
    RCONDV: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("SGGGLM")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def sggglm(
    N: Int32,
    M: Int32,
    P: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    D: Float32[Flat],
    X: Float32[Flat],
    Y: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGGHD3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def sgghd3(
    COMPQ: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGGHRD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def sgghrd(
    COMPQ: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    INFO: Int32
) -> None: ...

@bind("SGGLSE")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def sgglse(
    M: Int32,
    N: Int32,
    P: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    C: Float32[Flat],
    D: Float32[Flat],
    X: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGGQRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def sggqrf(
    N: Int32,
    M: Int32,
    P: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAUA: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    TAUB: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGGRQF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def sggrqf(
    M: Int32,
    P: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAUA: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    TAUB: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGGSVD3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23))])
def sggsvd3(
    JOBU: String[1],
    JOBV: String[1],
    JOBQ: String[1],
    M: Int32,
    N: Int32,
    P: Int32,
    K: Int32,
    L: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    ALPHA: Float32[Flat],
    BETA: Float32[Flat],
    U: Float32[LDU, Flat],
    LDU: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGGSVP3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Addr(Arg(23)), Addr(Arg(24))])
def sggsvp3(
    JOBU: String[1],
    JOBV: String[1],
    JOBQ: String[1],
    M: Int32,
    P: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    TOLA: Float32,
    TOLB: Float32,
    K: Int32,
    L: Int32,
    U: Float32[LDU, Flat],
    LDU: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    IWORK: Int32[Flat],
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGSVJ0")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def sgsvj0(
    JOBV: String[1],
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    D: Float32[N],
    SVA: Float32[N],
    MV: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    EPS: Float32,
    SFMIN: Float32,
    TOL: Float32,
    NSWEEP: Int32,
    WORK: Float32[LWORK],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGSVJ1")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Addr(Arg(17))])
def sgsvj1(
    JOBV: String[1],
    M: Int32,
    N: Int32,
    N1: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    D: Float32[N],
    SVA: Float32[N],
    MV: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    EPS: Float32,
    SFMIN: Float32,
    TOL: Float32,
    NSWEEP: Int32,
    WORK: Float32[LWORK],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SGTCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def sgtcon(
    NORM: String[1],
    N: Int32,
    DL: Float32[Flat],
    D: Float32[Flat],
    DU: Float32[Flat],
    DU2: Float32[Flat],
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGTRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def sgtrfs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    DL: Float32[Flat],
    D: Float32[Flat],
    DU: Float32[Flat],
    DLF: Float32[Flat],
    DF: Float32[Flat],
    DUF: Float32[Flat],
    DU2: Float32[Flat],
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGTSV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def sgtsv(
    N: Int32,
    NRHS: Int32,
    DL: Float32[Flat],
    D: Float32[Flat],
    DU: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SGTSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def sgtsvx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    DL: Float32[Flat],
    D: Float32[Flat],
    DU: Float32[Flat],
    DLF: Float32[Flat],
    DF: Float32[Flat],
    DUF: Float32[Flat],
    DU2: Float32[Flat],
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGTTRF")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def sgttrf(
    N: Int32,
    DL: Float32[Flat],
    D: Float32[Flat],
    DU: Float32[Flat],
    DU2: Float32[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SGTTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def sgttrs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    DL: Float32[Flat],
    D: Float32[Flat],
    DU: Float32[Flat],
    DU2: Float32[Flat],
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SGTTS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9))])
def sgtts2(
    ITRANS: Int32,
    N: Int32,
    NRHS: Int32,
    DL: Float32[Flat],
    D: Float32[Flat],
    DU: Float32[Flat],
    DU2: Float32[Flat],
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("SHGEQZ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Addr(Arg(19))])
def shgeqz(
    JOB: String[1],
    COMPQ: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Float32[LDH, Flat],
    LDH: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    ALPHAR: Float32[Flat],
    ALPHAI: Float32[Flat],
    BETA: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SHSEIN")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Addr(Arg(18))])
def shsein(
    SIDE: String[1],
    EIGSRC: String[1],
    INITV: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    H: Float32[LDH, Flat],
    LDH: Int32,
    WR: Float32[Flat],
    WI: Float32[Flat],
    VL: Float32[LDVL, Flat],
    LDVL: Int32,
    VR: Float32[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Float32[Flat],
    IFAILL: Int32[Flat],
    IFAILR: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SHSEQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def shseqr(
    JOB: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Float32[LDH, Flat],
    LDH: Int32,
    WR: Float32[Flat],
    WI: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SISNAN")
@external
@native_call([Addr(Arg(0))])
def sisnan(
    SIN: Float32
) -> Bool: ...

@bind("SLA_GBAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def sla_gbamv(
    TRANS: Int32,
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    ALPHA: Float32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    X: Float32[Flat],
    INCX: Int32,
    BETA: Float32,
    Y: Float32[Flat],
    INCY: Int32
) -> None: ...

@bind("SLA_GBRCOND")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13)])
def sla_gbrcond(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    AFB: Float32[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    CMODE: Int32,
    C: Float32[Flat],
    INFO: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat]
) -> Float32: ...

@bind("SLA_GBRFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Arg(22), Arg(23), Arg(24), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28)), Addr(Arg(29)), Addr(Arg(30))])
def sla_gbrfsx_extended(
    PREC_TYPE: Int32,
    TRANS_TYPE: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    AFB: Float32[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    Y: Float32[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float32[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    RES: Float32[Flat],
    AYB: Float32[Flat],
    DY: Float32[Flat],
    Y_TAIL: Float32[Flat],
    RCOND: Float32,
    ITHRESH: Int32,
    RTHRESH: Float32,
    DZ_UB: Float32,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("SLA_GBRPVGRW")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def sla_gbrpvgrw(
    N: Int32,
    KL: Int32,
    KU: Int32,
    NCOLS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    AFB: Float32[LDAFB, Flat],
    LDAFB: Int32
) -> Float32: ...

@bind("SLA_GEAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def sla_geamv(
    TRANS: Int32,
    M: Int32,
    N: Int32,
    ALPHA: Float32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    X: Float32[Flat],
    INCX: Int32,
    BETA: Float32,
    Y: Float32[Flat],
    INCY: Int32
) -> None: ...

@bind("SLA_GERCOND")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11)])
def sla_gercond(
    TRANS: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    CMODE: Int32,
    C: Float32[Flat],
    INFO: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat]
) -> Float32: ...

@bind("SLA_GERFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28))])
def sla_gerfsx_extended(
    PREC_TYPE: Int32,
    TRANS_TYPE: Int32,
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    Y: Float32[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float32[Flat],
    N_NORMS: Int32,
    ERRS_N: Float32[NRHS, Flat],
    ERRS_C: Float32[NRHS, Flat],
    RES: Float32[Flat],
    AYB: Float32[Flat],
    DY: Float32[Flat],
    Y_TAIL: Float32[Flat],
    RCOND: Float32,
    ITHRESH: Int32,
    RTHRESH: Float32,
    DZ_UB: Float32,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("SLA_GERPVGRW")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def sla_gerpvgrw(
    N: Int32,
    NCOLS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32
) -> Float32: ...

@bind("SLA_LIN_BERR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5)])
def sla_lin_berr(
    N: Int32,
    NZ: Int32,
    NRHS: Int32,
    RES: Float32[N, NRHS],
    AYB: Float32[N, NRHS],
    BERR: Float32[NRHS]
) -> None: ...

@bind("SLA_PORCOND")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10)])
def sla_porcond(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    CMODE: Int32,
    C: Float32[Flat],
    INFO: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat]
) -> Float32: ...

@bind("SLA_PORFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Addr(Arg(22)), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27))])
def sla_porfsx_extended(
    PREC_TYPE: Int32,
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    COLEQU: Bool,
    C: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    Y: Float32[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float32[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    RES: Float32[Flat],
    AYB: Float32[Flat],
    DY: Float32[Flat],
    Y_TAIL: Float32[Flat],
    RCOND: Float32,
    ITHRESH: Int32,
    RTHRESH: Float32,
    DZ_UB: Float32,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("SLA_PORPVGRW")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def sla_porpvgrw(
    UPLO: String[1],
    NCOLS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("SLA_SYAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def sla_syamv(
    UPLO: Int32,
    N: Int32,
    ALPHA: Float32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    X: Float32[Flat],
    INCX: Int32,
    BETA: Float32,
    Y: Float32[Flat],
    INCY: Int32
) -> None: ...

@bind("SLA_SYRCOND")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11)])
def sla_syrcond(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    CMODE: Int32,
    C: Float32[Flat],
    INFO: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat]
) -> Float32: ...

@bind("SLA_SYRFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28))])
def sla_syrfsx_extended(
    PREC_TYPE: Int32,
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    Y: Float32[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float32[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    RES: Float32[Flat],
    AYB: Float32[Flat],
    DY: Float32[Flat],
    Y_TAIL: Float32[Flat],
    RCOND: Float32,
    ITHRESH: Int32,
    RTHRESH: Float32,
    DZ_UB: Float32,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("SLA_SYRPVGRW")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8)])
def sla_syrpvgrw(
    UPLO: String[1],
    N: Int32,
    INFO: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    WORK: Float32[Flat]
) -> Float32: ...

@bind("SLA_WWADDW")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def sla_wwaddw(
    N: Int32,
    X: Float32[Flat],
    Y: Float32[Flat],
    W: Float32[Flat]
) -> None: ...

@bind("SLABAD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def slabad(
    SMALL: Float32,
    LARGE: Float32
) -> None: ...

@bind("SLABRD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def slabrd(
    M: Int32,
    N: Int32,
    NB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    TAUQ: Float32[Flat],
    TAUP: Float32[Flat],
    X: Float32[LDX, Flat],
    LDX: Int32,
    Y: Float32[LDY, Flat],
    LDY: Int32
) -> None: ...

@bind("SLACN2")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6)])
def slacn2(
    N: Int32,
    V: Float32[Flat],
    X: Float32[Flat],
    ISGN: Int32[Flat],
    EST: Float32,
    KASE: Int32,
    ISAVE: Int32[3]
) -> None: ...

@bind("SLACON")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def slacon(
    N: Int32,
    V: Float32[Flat],
    X: Float32[Flat],
    ISGN: Int32[Flat],
    EST: Float32,
    KASE: Int32
) -> None: ...

@bind("SLACPY")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def slacpy(
    UPLO: String[1],
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("SLADIV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def sladiv(
    A: Float32,
    B: Float32,
    C: Float32,
    D: Float32,
    P: Float32,
    Q: Float32
) -> None: ...

@bind("SLADIV1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def sladiv1(
    A: Float32,
    B: Float32,
    C: Float32,
    D: Float32,
    P: Float32,
    Q: Float32
) -> None: ...

@bind("SLADIV2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def sladiv2(
    A: Float32,
    B: Float32,
    C: Float32,
    D: Float32,
    R: Float32,
    T: Float32
) -> Float32: ...

@bind("SLAE2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def slae2(
    A: Float32,
    B: Float32,
    C: Float32,
    RT1: Float32,
    RT2: Float32
) -> None: ...

@bind("SLAEBZ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def slaebz(
    IJOB: Int32,
    NITMAX: Int32,
    N: Int32,
    MMAX: Int32,
    MINP: Int32,
    NBMIN: Int32,
    ABSTOL: Float32,
    RELTOL: Float32,
    PIVMIN: Float32,
    D: Float32[Flat],
    E: Float32[Flat],
    E2: Float32[Flat],
    NVAL: Int32[Flat],
    AB: Float32[MMAX, Flat],
    C: Float32[Flat],
    MOUT: Int32,
    NAB: Int32[MMAX, Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAED0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def slaed0(
    ICOMPQ: Int32,
    QSIZ: Int32,
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    QSTORE: Float32[LDQS, Flat],
    LDQS: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAED1")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def slaed1(
    N: Int32,
    D: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    INDXQ: Int32[Flat],
    RHO: Float32,
    CUTPNT: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAED2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def slaed2(
    K: Int32,
    N: Int32,
    N1: Int32,
    D: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    INDXQ: Int32[Flat],
    RHO: Float32,
    Z: Float32[Flat],
    DLAMBDA: Float32[Flat],
    W: Float32[Flat],
    Q2: Float32[Flat],
    INDX: Int32[Flat],
    INDXC: Int32[Flat],
    INDXP: Int32[Flat],
    COLTYP: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAED3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def slaed3(
    K: Int32,
    N: Int32,
    N1: Int32,
    D: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    RHO: Float32,
    DLAMBDA: Float32[Flat],
    Q2: Float32[Flat],
    INDX: Int32[Flat],
    CTOT: Int32[Flat],
    W: Float32[Flat],
    S: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAED4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7))])
def slaed4(
    N: Int32,
    I: Int32,
    D: Float32[Flat],
    Z: Float32[Flat],
    DELTA: Float32[Flat],
    RHO: Float32,
    DLAM: Float32,
    INFO: Int32
) -> None: ...

@bind("SLAED5")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def slaed5(
    I: Int32,
    D: Float32[2],
    Z: Float32[2],
    DELTA: Float32[2],
    RHO: Float32,
    DLAM: Float32
) -> None: ...

@bind("SLAED6")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7))])
def slaed6(
    KNITER: Int32,
    ORGATI: Bool,
    RHO: Float32,
    D: Float32[3],
    Z: Float32[3],
    FINIT: Float32,
    TAU: Float32,
    INFO: Int32
) -> None: ...

@bind("SLAED7")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def slaed7(
    ICOMPQ: Int32,
    N: Int32,
    QSIZ: Int32,
    TLVLS: Int32,
    CURLVL: Int32,
    CURPBM: Int32,
    D: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    INDXQ: Int32[Flat],
    RHO: Float32,
    CUTPNT: Int32,
    QSTORE: Float32[Flat],
    QPTR: Int32[Flat],
    PRMPTR: Int32[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32[Flat],
    GIVCOL: Int32[2, Flat],
    GIVNUM: Float32[2, Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAED8")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def slaed8(
    ICOMPQ: Int32,
    K: Int32,
    N: Int32,
    QSIZ: Int32,
    D: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    INDXQ: Int32[Flat],
    RHO: Float32,
    CUTPNT: Int32,
    Z: Float32[Flat],
    DLAMBDA: Float32[Flat],
    Q2: Float32[LDQ2, Flat],
    LDQ2: Int32,
    W: Float32[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32,
    GIVCOL: Int32[2, Flat],
    GIVNUM: Float32[2, Flat],
    INDXP: Int32[Flat],
    INDX: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAED9")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def slaed9(
    K: Int32,
    KSTART: Int32,
    KSTOP: Int32,
    N: Int32,
    D: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    RHO: Float32,
    DLAMBDA: Float32[Flat],
    W: Float32[Flat],
    S: Float32[LDS, Flat],
    LDS: Int32,
    INFO: Int32
) -> None: ...

@bind("SLAEDA")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def slaeda(
    N: Int32,
    TLVLS: Int32,
    CURLVL: Int32,
    CURPBM: Int32,
    PRMPTR: Int32[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32[Flat],
    GIVCOL: Int32[2, Flat],
    GIVNUM: Float32[2, Flat],
    Q: Float32[Flat],
    QPTR: Int32[Flat],
    Z: Float32[Flat],
    ZTEMP: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAEIN")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15))])
def slaein(
    RIGHTV: Bool,
    NOINIT: Bool,
    N: Int32,
    H: Float32[LDH, Flat],
    LDH: Int32,
    WR: Float32,
    WI: Float32,
    VR: Float32[Flat],
    VI: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[Flat],
    EPS3: Float32,
    SMLNUM: Float32,
    BIGNUM: Float32,
    INFO: Int32
) -> None: ...

@bind("SLAEV2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def slaev2(
    A: Float32,
    B: Float32,
    C: Float32,
    RT1: Float32,
    RT2: Float32,
    CS1: Float32,
    SN1: Float32
) -> None: ...

@bind("SLAEXC")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def slaexc(
    WANTQ: Bool,
    N: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    J1: Int32,
    N1: Int32,
    N2: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAG2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def slag2(
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    SAFMIN: Float32,
    SCALE1: Float32,
    SCALE2: Float32,
    WR1: Float32,
    WR2: Float32,
    WI: Float32
) -> None: ...

@bind("SLAG2D")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def slag2d(
    M: Int32,
    N: Int32,
    SA: Float32[LDSA, Flat],
    LDSA: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("SLAGS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12))])
def slags2(
    UPPER: Bool,
    A1: Float32,
    A2: Float32,
    A3: Float32,
    B1: Float32,
    B2: Float32,
    B3: Float32,
    CSU: Float32,
    SNU: Float32,
    CSV: Float32,
    SNV: Float32,
    CSQ: Float32,
    SNQ: Float32
) -> None: ...

@bind("SLAGTF")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def slagtf(
    N: Int32,
    A: Float32[Flat],
    LAMBDA: Float32,
    B: Float32[Flat],
    C: Float32[Flat],
    TOL: Float32,
    D: Float32[Flat],
    IN: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAGTM")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def slagtm(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    ALPHA: Float32,
    DL: Float32[Flat],
    D: Float32[Flat],
    DU: Float32[Flat],
    X: Float32[LDX, Flat],
    LDX: Int32,
    BETA: Float32,
    B: Float32[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("SLAGTS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def slagts(
    JOB: Int32,
    N: Int32,
    A: Float32[Flat],
    B: Float32[Flat],
    C: Float32[Flat],
    D: Float32[Flat],
    IN: Int32[Flat],
    Y: Float32[Flat],
    TOL: Float32,
    INFO: Int32
) -> None: ...

@bind("SLAGV2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10))])
def slagv2(
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    ALPHAR: Float32[2],
    ALPHAI: Float32[2],
    BETA: Float32[2],
    CSL: Float32,
    SNL: Float32,
    CSR: Float32,
    SNR: Float32
) -> None: ...

@bind("SLAHQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def slahqr(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Float32[LDH, Flat],
    LDH: Int32,
    WR: Float32[Flat],
    WI: Float32[Flat],
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    INFO: Int32
) -> None: ...

@bind("SLAHR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def slahr2(
    N: Int32,
    K: Int32,
    NB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[NB],
    T: Float32[LDT, NB],
    LDT: Int32,
    Y: Float32[LDY, NB],
    LDY: Int32
) -> None: ...

@bind("SLAIC1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8))])
def slaic1(
    JOB: Int32,
    J: Int32,
    X: Float32[J],
    SEST: Float32,
    W: Float32[J],
    GAMMA: Float32,
    SESTPR: Float32,
    S: Float32,
    C: Float32
) -> None: ...

@bind("SLAISNAN")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def slaisnan(
    SIN1: Float32,
    SIN2: Float32
) -> Bool: ...

@bind("SLALN2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17))])
def slaln2(
    LTRANS: Bool,
    NA: Int32,
    NW: Int32,
    SMIN: Float32,
    CA: Float32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    D1: Float32,
    D2: Float32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    WR: Float32,
    WI: Float32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    SCALE: Float32,
    XNORM: Float32,
    INFO: Int32
) -> None: ...

@bind("SLALS0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19)), Addr(Arg(20)), Addr(Arg(21)), Arg(22), Addr(Arg(23))])
def slals0(
    ICOMPQ: Int32,
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    NRHS: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    BX: Float32[LDBX, Flat],
    LDBX: Int32,
    PERM: Int32[Flat],
    GIVPTR: Int32,
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    GIVNUM: Float32[LDGNUM, Flat],
    LDGNUM: Int32,
    POLES: Float32[LDGNUM, Flat],
    DIFL: Float32[Flat],
    DIFR: Float32[LDGNUM, Flat],
    Z: Float32[Flat],
    K: Int32,
    C: Float32,
    S: Float32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLALSA")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Arg(22), Arg(23), Arg(24), Addr(Arg(25))])
def slalsa(
    ICOMPQ: Int32,
    SMLSIZ: Int32,
    N: Int32,
    NRHS: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    BX: Float32[LDBX, Flat],
    LDBX: Int32,
    U: Float32[LDU, Flat],
    LDU: Int32,
    VT: Float32[LDU, Flat],
    K: Int32[Flat],
    DIFL: Float32[LDU, Flat],
    DIFR: Float32[LDU, Flat],
    Z: Float32[LDU, Flat],
    POLES: Float32[LDU, Flat],
    GIVPTR: Int32[Flat],
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    PERM: Int32[LDGCOL, Flat],
    GIVNUM: Float32[LDU, Flat],
    C: Float32[Flat],
    S: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLALSD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12))])
def slalsd(
    UPLO: String[1],
    SMLSIZ: Int32,
    N: Int32,
    NRHS: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    RCOND: Float32,
    RANK: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAMRG")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5)])
def slamrg(
    N1: Int32,
    N2: Int32,
    A: Float32[Flat],
    STRD1: Int32,
    STRD2: Int32,
    INDEX: Int32[Flat]
) -> None: ...

@bind("SLAMSWLQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def slamswlq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    MB: Int32,
    NB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SLAMTSQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def slamtsqr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    MB: Int32,
    NB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SLANEG")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def slaneg(
    N: Int32,
    D: Float32[Flat],
    LLD: Float32[Flat],
    SIGMA: Float32,
    PIVMIN: Float32,
    R: Int32
) -> Int32: ...

@bind("SLANGB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def slangb(
    NORM: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("SLANGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def slange(
    NORM: String[1],
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("SLANGT")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4)])
def slangt(
    NORM: String[1],
    N: Int32,
    DL: Float32[Flat],
    D: Float32[Flat],
    DU: Float32[Flat]
) -> Float32: ...

@bind("SLANHS")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4)])
def slanhs(
    NORM: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("SLANSB")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def slansb(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    K: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("SLANSF")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5)])
def slansf(
    NORM: String[1],
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[Flat],
    WORK: Float32[Flat]
) -> Float32: ...

@bind("SLANSP")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4)])
def slansp(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    WORK: Float32[Flat]
) -> Float32: ...

@bind("SLANST")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3)])
def slanst(
    NORM: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat]
) -> Float32: ...

@bind("SLANSY")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def slansy(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("SLANTB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def slantb(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    K: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("SLANTP")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5)])
def slantp(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    AP: Float32[Flat],
    WORK: Float32[Flat]
) -> Float32: ...

@bind("SLANTR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def slantr(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    WORK: Float32[Flat]
) -> Float32: ...

@bind("SLANV2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def slanv2(
    A: Float32,
    B: Float32,
    C: Float32,
    D: Float32,
    RT1R: Float32,
    RT1I: Float32,
    RT2R: Float32,
    RT2I: Float32,
    CS: Float32,
    SN: Float32
) -> None: ...

@bind("SLAORHR_COL_GETRFNP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def slaorhr_col_getrfnp(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAORHR_COL_GETRFNP2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def slaorhr_col_getrfnp2(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAPLL")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def slapll(
    N: Int32,
    X: Float32[Flat],
    INCX: Int32,
    Y: Float32[Flat],
    INCY: Int32,
    SSMIN: Float32
) -> None: ...

@bind("SLAPMR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def slapmr(
    FORWRD: Bool,
    M: Int32,
    N: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    K: Int32[Flat]
) -> None: ...

@bind("SLAPMT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def slapmt(
    FORWRD: Bool,
    M: Int32,
    N: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    K: Int32[Flat]
) -> None: ...

@bind("SLAPY2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def slapy2(
    X: Float32,
    Y: Float32
) -> Float32: ...

@bind("SLAPY3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2))])
def slapy3(
    X: Float32,
    Y: Float32,
    Z: Float32
) -> Float32: ...

@bind("SLAQGB")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11)])
def slaqgb(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    R: Float32[Flat],
    C: Float32[Flat],
    ROWCND: Float32,
    COLCND: Float32,
    AMAX: Float32,
    EQUED: String[1]
) -> None: ...

@bind("SLAQGE")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9)])
def slaqge(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    R: Float32[Flat],
    C: Float32[Flat],
    ROWCND: Float32,
    COLCND: Float32,
    AMAX: Float32,
    EQUED: String[1]
) -> None: ...

@bind("SLAQP2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9)])
def slaqp2(
    M: Int32,
    N: Int32,
    OFFSET: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    JPVT: Int32[Flat],
    TAU: Float32[Flat],
    VN1: Float32[Flat],
    VN2: Float32[Flat],
    WORK: Float32[Flat]
) -> None: ...

@bind("SLAQP2RK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def slaqp2rk(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    IOFFSET: Int32,
    KMAX: Int32,
    ABSTOL: Float32,
    RELTOL: Float32,
    KP1: Int32,
    MAXC2NRM: Float32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    K: Int32,
    MAXC2NRMK: Float32,
    RELMAXC2NRMK: Float32,
    JPIV: Int32[Flat],
    TAU: Float32[Flat],
    VN1: Float32[Flat],
    VN2: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAQP3RK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23))])
def slaqp3rk(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    IOFFSET: Int32,
    NB: Int32,
    ABSTOL: Float32,
    RELTOL: Float32,
    KP1: Int32,
    MAXC2NRM: Float32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    DONE: Bool,
    KB: Int32,
    MAXC2NRMK: Float32,
    RELMAXC2NRMK: Float32,
    JPIV: Int32[Flat],
    TAU: Float32[Flat],
    VN1: Float32[Flat],
    VN2: Float32[Flat],
    AUXV: Float32[Flat],
    F: Float32[LDF, Flat],
    LDF: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAQPS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def slaqps(
    M: Int32,
    N: Int32,
    OFFSET: Int32,
    NB: Int32,
    KB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    JPVT: Int32[Flat],
    TAU: Float32[Flat],
    VN1: Float32[Flat],
    VN2: Float32[Flat],
    AUXV: Float32[Flat],
    F: Float32[LDF, Flat],
    LDF: Int32
) -> None: ...

@bind("SLAQR0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def slaqr0(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Float32[LDH, Flat],
    LDH: Int32,
    WR: Float32[Flat],
    WI: Float32[Flat],
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SLAQR1")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7)])
def slaqr1(
    N: Int32,
    H: Float32[LDH, Flat],
    LDH: Int32,
    SR1: Float32,
    SI1: Float32,
    SR2: Float32,
    SI2: Float32,
    V: Float32[Flat]
) -> None: ...

@bind("SLAQR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25))])
def slaqr2(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    KTOP: Int32,
    KBOT: Int32,
    NW: Int32,
    H: Float32[LDH, Flat],
    LDH: Int32,
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    NS: Int32,
    ND: Int32,
    SR: Float32[Flat],
    SI: Float32[Flat],
    V: Float32[LDV, Flat],
    LDV: Int32,
    NH: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    NV: Int32,
    WV: Float32[LDWV, Flat],
    LDWV: Int32,
    WORK: Float32[Flat],
    LWORK: Int32
) -> None: ...

@bind("SLAQR3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25))])
def slaqr3(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    KTOP: Int32,
    KBOT: Int32,
    NW: Int32,
    H: Float32[LDH, Flat],
    LDH: Int32,
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    NS: Int32,
    ND: Int32,
    SR: Float32[Flat],
    SI: Float32[Flat],
    V: Float32[LDV, Flat],
    LDV: Int32,
    NH: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    NV: Int32,
    WV: Float32[LDWV, Flat],
    LDWV: Int32,
    WORK: Float32[Flat],
    LWORK: Int32
) -> None: ...

@bind("SLAQR4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def slaqr4(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Float32[LDH, Flat],
    LDH: Int32,
    WR: Float32[Flat],
    WI: Float32[Flat],
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SLAQR5")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Addr(Arg(22)), Arg(23), Addr(Arg(24))])
def slaqr5(
    WANTT: Bool,
    WANTZ: Bool,
    KACC22: Int32,
    N: Int32,
    KTOP: Int32,
    KBOT: Int32,
    NSHFTS: Int32,
    SR: Float32[Flat],
    SI: Float32[Flat],
    H: Float32[LDH, Flat],
    LDH: Int32,
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    U: Float32[LDU, Flat],
    LDU: Int32,
    NV: Int32,
    WV: Float32[LDWV, Flat],
    LDWV: Int32,
    NH: Int32,
    WH: Float32[LDWH, Flat],
    LDWH: Int32
) -> None: ...

@bind("SLAQSB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8)])
def slaqsb(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    EQUED: String[1]
) -> None: ...

@bind("SLAQSP")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6)])
def slaqsp(
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    EQUED: String[1]
) -> None: ...

@bind("SLAQSY")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7)])
def slaqsy(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    EQUED: String[1]
) -> None: ...

@bind("SLAQTR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def slaqtr(
    LTRAN: Bool,
    LREAL: Bool,
    N: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    B: Float32[Flat],
    W: Float32,
    SCALE: Float32,
    X: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLAQZ0")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Addr(Arg(19)), Return('INFO', 0)])
def slaqz0(
    WANTS: String[1],
    WANTQ: String[1],
    WANTZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    ALPHAR: Float32[Flat],
    ALPHAI: Float32[Flat],
    BETA: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    REC: Int32
) -> Int32: ...

@bind("SLAQZ1")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9)])
def slaqz1(
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    SR1: Float32,
    SR2: Float32,
    SI: Float32,
    BETA1: Float32,
    BETA2: Float32,
    V: Float32[Flat]
) -> None: ...

@bind("SLAQZ2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def slaqz2(
    ILQ: Bool,
    ILZ: Bool,
    K: Int32,
    ISTARTM: Int32,
    ISTOPM: Int32,
    IHI: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    NQ: Int32,
    QSTART: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    NZ: Int32,
    ZSTART: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32
) -> None: ...

@bind("SLAQZ3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Return('NS', 0), Return('ND', 1), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Return('INFO', 2)])
def slaqz3(
    ILSCHUR: Bool,
    ILQ: Bool,
    ILZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    NW: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    ALPHAR: Float32[Flat],
    ALPHAI: Float32[Flat],
    BETA: Float32[Flat],
    QC: Float32[LDQC, Flat],
    LDQC: Int32,
    ZC: Float32[LDZC, Flat],
    LDZC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    REC: Int32
) -> tuple[Int32, Int32, Int32]: ...

@bind("SLAQZ4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Arg(21), Addr(Arg(22)), Arg(23), Addr(Arg(24)), Return('INFO', 0)])
def slaqz4(
    ILSCHUR: Bool,
    ILQ: Bool,
    ILZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    NSHIFTS: Int32,
    NBLOCK_DESIRED: Int32,
    SR: Float32[Flat],
    SI: Float32[Flat],
    SS: Float32[Flat],
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    QC: Float32[LDQC, Flat],
    LDQC: Int32,
    ZC: Float32[LDZC, Flat],
    LDZC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32
) -> Int32: ...

@bind("SLAR1V")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Addr(Arg(19)), Arg(20)])
def slar1v(
    N: Int32,
    B1: Int32,
    BN: Int32,
    LAMBDA: Float32,
    D: Float32[Flat],
    L: Float32[Flat],
    LD: Float32[Flat],
    LLD: Float32[Flat],
    PIVMIN: Float32,
    GAPTOL: Float32,
    Z: Float32[Flat],
    WANTNC: Bool,
    NEGCNT: Int32,
    ZTZ: Float32,
    MINGMA: Float32,
    R: Int32,
    ISUPPZ: Int32[Flat],
    NRMINV: Float32,
    RESID: Float32,
    RQCORR: Float32,
    WORK: Float32[Flat]
) -> None: ...

@bind("SLAR2V")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def slar2v(
    N: Int32,
    X: Float32[Flat],
    Y: Float32[Flat],
    Z: Float32[Flat],
    INCX: Int32,
    C: Float32[Flat],
    S: Float32[Flat],
    INCC: Int32
) -> None: ...

@bind("SLARF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def slarf(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Float32[Flat],
    INCV: Int32,
    TAU: Float32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat]
) -> None: ...

@bind("SLARF1F")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def slarf1f(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Float32[Flat],
    INCV: Int32,
    TAU: Float32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat]
) -> None: ...

@bind("SLARF1L")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def slarf1l(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Float32[Flat],
    INCV: Int32,
    TAU: Float32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat]
) -> None: ...

@bind("SLARFB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14))])
def slarfb(
    SIDE: String[1],
    TRANS: String[1],
    DIRECT: String[1],
    STOREV: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("SLARFB_GETT")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def slarfb_gett(
    IDENT: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("SLARFG")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def slarfg(
    N: Int32,
    ALPHA: Float32,
    X: Float32[Flat],
    INCX: Int32,
    TAU: Float32
) -> None: ...

@bind("SLARFGP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def slarfgp(
    N: Int32,
    ALPHA: Float32,
    X: Float32[Flat],
    INCX: Int32,
    TAU: Float32
) -> None: ...

@bind("SLARFT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def slarft(
    DIRECT: String[1],
    STOREV: String[1],
    N: Int32,
    K: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    TAU: Float32[Flat],
    T: Float32[LDT, Flat],
    LDT: Int32
) -> None: ...

@bind("SLARFX")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def slarfx(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Float32[Flat],
    TAU: Float32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat]
) -> None: ...

@bind("SLARFY")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def slarfy(
    UPLO: String[1],
    N: Int32,
    V: Float32[Flat],
    INCV: Int32,
    TAU: Float32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat]
) -> None: ...

@bind("SLARGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def slargv(
    N: Int32,
    X: Float32[Flat],
    INCX: Int32,
    Y: Float32[Flat],
    INCY: Int32,
    C: Float32[Flat],
    INCC: Int32
) -> None: ...

@bind("SLARMM")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2))])
def slarmm(
    ANORM: Float32,
    BNORM: Float32,
    CNORM: Float32
) -> Float32: ...

@bind("SLARNV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3)])
def slarnv(
    IDIST: Int32,
    ISEED: Int32[4],
    N: Int32,
    X: Float32[Flat]
) -> None: ...

@bind("SLARRA")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def slarra(
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    E2: Float32[Flat],
    SPLTOL: Float32,
    TNRM: Float32,
    NSPLIT: Int32,
    ISPLIT: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLARRB")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16))])
def slarrb(
    N: Int32,
    D: Float32[Flat],
    LLD: Float32[Flat],
    IFIRST: Int32,
    ILAST: Int32,
    RTOL1: Float32,
    RTOL2: Float32,
    OFFSET: Int32,
    W: Float32[Flat],
    WGAP: Float32[Flat],
    WERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    PIVMIN: Float32,
    SPDIAM: Float32,
    TWIST: Int32,
    INFO: Int32
) -> None: ...

@bind("SLARRC")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10))])
def slarrc(
    JOBT: String[1],
    N: Int32,
    VL: Float32,
    VU: Float32,
    D: Float32[Flat],
    E: Float32[Flat],
    PIVMIN: Float32,
    EIGCNT: Int32,
    LCNT: Int32,
    RCNT: Int32,
    INFO: Int32
) -> None: ...

@bind("SLARRD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Addr(Arg(18)), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def slarrd(
    RANGE: String[1],
    ORDER: String[1],
    N: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    GERS: Float32[Flat],
    RELTOL: Float32,
    D: Float32[Flat],
    E: Float32[Flat],
    E2: Float32[Flat],
    PIVMIN: Float32,
    NSPLIT: Int32,
    ISPLIT: Int32[Flat],
    M: Int32,
    W: Float32[Flat],
    WERR: Float32[Flat],
    WL: Float32,
    WU: Float32,
    IBLOCK: Int32[Flat],
    INDEXW: Int32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLARRE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Addr(Arg(24))])
def slarre(
    RANGE: String[1],
    N: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    E2: Float32[Flat],
    RTOL1: Float32,
    RTOL2: Float32,
    SPLTOL: Float32,
    NSPLIT: Int32,
    ISPLIT: Int32[Flat],
    M: Int32,
    W: Float32[Flat],
    WERR: Float32[Flat],
    WGAP: Float32[Flat],
    IBLOCK: Int32[Flat],
    INDEXW: Int32[Flat],
    GERS: Float32[Flat],
    PIVMIN: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLARRF")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17))])
def slarrf(
    N: Int32,
    D: Float32[Flat],
    L: Float32[Flat],
    LD: Float32[Flat],
    CLSTRT: Int32,
    CLEND: Int32,
    W: Float32[Flat],
    WGAP: Float32[Flat],
    WERR: Float32[Flat],
    SPDIAM: Float32,
    CLGAPL: Float32,
    CLGAPR: Float32,
    PIVMIN: Float32,
    SIGMA: Float32,
    DPLUS: Float32[Flat],
    LPLUS: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLARRJ")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13))])
def slarrj(
    N: Int32,
    D: Float32[Flat],
    E2: Float32[Flat],
    IFIRST: Int32,
    ILAST: Int32,
    RTOL: Float32,
    OFFSET: Int32,
    W: Float32[Flat],
    WERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    PIVMIN: Float32,
    SPDIAM: Float32,
    INFO: Int32
) -> None: ...

@bind("SLARRK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10))])
def slarrk(
    N: Int32,
    IW: Int32,
    GL: Float32,
    GU: Float32,
    D: Float32[Flat],
    E2: Float32[Flat],
    PIVMIN: Float32,
    RELTOL: Float32,
    W: Float32,
    WERR: Float32,
    INFO: Int32
) -> None: ...

@bind("SLARRR")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3))])
def slarrr(
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLARRV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def slarrv(
    N: Int32,
    VL: Float32,
    VU: Float32,
    D: Float32[Flat],
    L: Float32[Flat],
    PIVMIN: Float32,
    ISPLIT: Int32[Flat],
    M: Int32,
    DOL: Int32,
    DOU: Int32,
    MINRGP: Float32,
    RTOL1: Float32,
    RTOL2: Float32,
    W: Float32[Flat],
    WERR: Float32[Flat],
    WGAP: Float32[Flat],
    IBLOCK: Int32[Flat],
    INDEXW: Int32[Flat],
    GERS: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLARSCL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def slarscl2(
    M: Int32,
    N: Int32,
    D: Float32[Flat],
    X: Float32[LDX, Flat],
    LDX: Int32
) -> None: ...

@bind("SLARTG")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def slartg(
    f: Float32,
    g: Float32,
    c: Float32,
    s: Float32,
    r: Float32
) -> None: ...

@bind("SLARTGP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def slartgp(
    F: Float32,
    G: Float32,
    CS: Float32,
    SN: Float32,
    R: Float32
) -> None: ...

@bind("SLARTGS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def slartgs(
    X: Float32,
    Y: Float32,
    SIGMA: Float32,
    CS: Float32,
    SN: Float32
) -> None: ...

@bind("SLARTV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def slartv(
    N: Int32,
    X: Float32[Flat],
    INCX: Int32,
    Y: Float32[Flat],
    INCY: Int32,
    C: Float32[Flat],
    S: Float32[Flat],
    INCC: Int32
) -> None: ...

@bind("SLARUV")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2)])
def slaruv(
    ISEED: Int32[4],
    N: Int32,
    X: Float32[N]
) -> None: ...

@bind("SLARZ")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9)])
def slarz(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    L: Int32,
    V: Float32[Flat],
    INCV: Int32,
    TAU: Float32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat]
) -> None: ...

@bind("SLARZB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15))])
def slarzb(
    SIDE: String[1],
    TRANS: String[1],
    DIRECT: String[1],
    STOREV: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("SLARZT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def slarzt(
    DIRECT: String[1],
    STOREV: String[1],
    N: Int32,
    K: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    TAU: Float32[Flat],
    T: Float32[LDT, Flat],
    LDT: Int32
) -> None: ...

@bind("SLAS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def slas2(
    F: Float32,
    G: Float32,
    H: Float32,
    SSMIN: Float32,
    SSMAX: Float32
) -> None: ...

@bind("SLASCL")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def slascl(
    TYPE: String[1],
    KL: Int32,
    KU: Int32,
    CFROM: Float32,
    CTO: Float32,
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("SLASCL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def slascl2(
    M: Int32,
    N: Int32,
    D: Float32[Flat],
    X: Float32[LDX, Flat],
    LDX: Int32
) -> None: ...

@bind("SLASD0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def slasd0(
    N: Int32,
    SQRE: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    U: Float32[LDU, Flat],
    LDU: Int32,
    VT: Float32[LDVT, Flat],
    LDVT: Int32,
    SMLSIZ: Int32,
    IWORK: Int32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLASD1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def slasd1(
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    D: Float32[Flat],
    ALPHA: Float32,
    BETA: Float32,
    U: Float32[LDU, Flat],
    LDU: Int32,
    VT: Float32[LDVT, Flat],
    LDVT: Int32,
    IDXQ: Int32[Flat],
    IWORK: Int32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLASD2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Addr(Arg(22))])
def slasd2(
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    K: Int32,
    D: Float32[Flat],
    Z: Float32[Flat],
    ALPHA: Float32,
    BETA: Float32,
    U: Float32[LDU, Flat],
    LDU: Int32,
    VT: Float32[LDVT, Flat],
    LDVT: Int32,
    DSIGMA: Float32[Flat],
    U2: Float32[LDU2, Flat],
    LDU2: Int32,
    VT2: Float32[LDVT2, Flat],
    LDVT2: Int32,
    IDXP: Int32[Flat],
    IDX: Int32[Flat],
    IDXC: Int32[Flat],
    IDXQ: Int32[Flat],
    COLTYP: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLASD3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def slasd3(
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    K: Int32,
    D: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    DSIGMA: Float32[Flat],
    U: Float32[LDU, Flat],
    LDU: Int32,
    U2: Float32[LDU2, Flat],
    LDU2: Int32,
    VT: Float32[LDVT, Flat],
    LDVT: Int32,
    VT2: Float32[LDVT2, Flat],
    LDVT2: Int32,
    IDXC: Int32[Flat],
    CTOT: Int32[Flat],
    Z: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLASD4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def slasd4(
    N: Int32,
    I: Int32,
    D: Float32[Flat],
    Z: Float32[Flat],
    DELTA: Float32[Flat],
    RHO: Float32,
    SIGMA: Float32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLASD5")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6)])
def slasd5(
    I: Int32,
    D: Float32[2],
    Z: Float32[2],
    DELTA: Float32[2],
    RHO: Float32,
    DSIGMA: Float32,
    WORK: Float32[2]
) -> None: ...

@bind("SLASD6")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Addr(Arg(21)), Addr(Arg(22)), Arg(23), Arg(24), Addr(Arg(25))])
def slasd6(
    ICOMPQ: Int32,
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    D: Float32[Flat],
    VF: Float32[Flat],
    VL: Float32[Flat],
    ALPHA: Float32,
    BETA: Float32,
    IDXQ: Int32[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32,
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    GIVNUM: Float32[LDGNUM, Flat],
    LDGNUM: Int32,
    POLES: Float32[LDGNUM, Flat],
    DIFL: Float32[Flat],
    DIFR: Float32[Flat],
    Z: Float32[Flat],
    K: Int32,
    C: Float32,
    S: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLASD7")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26))])
def slasd7(
    ICOMPQ: Int32,
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    K: Int32,
    D: Float32[Flat],
    Z: Float32[Flat],
    ZW: Float32[Flat],
    VF: Float32[Flat],
    VFW: Float32[Flat],
    VL: Float32[Flat],
    VLW: Float32[Flat],
    ALPHA: Float32,
    BETA: Float32,
    DSIGMA: Float32[Flat],
    IDX: Int32[Flat],
    IDXP: Int32[Flat],
    IDXQ: Int32[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32,
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    GIVNUM: Float32[LDGNUM, Flat],
    LDGNUM: Int32,
    C: Float32,
    S: Float32,
    INFO: Int32
) -> None: ...

@bind("SLASD8")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def slasd8(
    ICOMPQ: Int32,
    K: Int32,
    D: Float32[Flat],
    Z: Float32[Flat],
    VF: Float32[Flat],
    VL: Float32[Flat],
    DIFL: Float32[Flat],
    DIFR: Float32[LDDIFR, Flat],
    LDDIFR: Int32,
    DSIGMA: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLASDA")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def slasda(
    ICOMPQ: Int32,
    SMLSIZ: Int32,
    N: Int32,
    SQRE: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    U: Float32[LDU, Flat],
    LDU: Int32,
    VT: Float32[LDU, Flat],
    K: Int32[Flat],
    DIFL: Float32[LDU, Flat],
    DIFR: Float32[LDU, Flat],
    Z: Float32[LDU, Flat],
    POLES: Float32[LDU, Flat],
    GIVPTR: Int32[Flat],
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    PERM: Int32[LDGCOL, Flat],
    GIVNUM: Float32[LDU, Flat],
    C: Float32[Flat],
    S: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLASDQ")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15))])
def slasdq(
    UPLO: String[1],
    SQRE: Int32,
    N: Int32,
    NCVT: Int32,
    NRU: Int32,
    NCC: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    VT: Float32[LDVT, Flat],
    LDVT: Int32,
    U: Float32[LDU, Flat],
    LDU: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLASDT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def slasdt(
    N: Int32,
    LVL: Int32,
    ND: Int32,
    INODE: Int32[Flat],
    NDIML: Int32[Flat],
    NDIMR: Int32[Flat],
    MSUB: Int32
) -> None: ...

@bind("SLASET")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def slaset(
    UPLO: String[1],
    M: Int32,
    N: Int32,
    ALPHA: Float32,
    BETA: Float32,
    A: Float32[LDA, Flat],
    LDA: Int32
) -> None: ...

@bind("SLASQ1")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4))])
def slasq1(
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLASQ2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2))])
def slasq2(
    N: Int32,
    Z: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLASQ3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Addr(Arg(18)), Addr(Arg(19))])
def slasq3(
    I0: Int32,
    N0: Int32,
    Z: Float32[Flat],
    PP: Int32,
    DMIN: Float32,
    SIGMA: Float32,
    DESIG: Float32,
    QMAX: Float32,
    NFAIL: Int32,
    ITER: Int32,
    NDIV: Int32,
    IEEE: Bool,
    TTYPE: Int32,
    DMIN1: Float32,
    DMIN2: Float32,
    DN: Float32,
    DN1: Float32,
    DN2: Float32,
    G: Float32,
    TAU: Float32
) -> None: ...

@bind("SLASQ4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13))])
def slasq4(
    I0: Int32,
    N0: Int32,
    Z: Float32[Flat],
    PP: Int32,
    N0IN: Int32,
    DMIN: Float32,
    DMIN1: Float32,
    DMIN2: Float32,
    DN: Float32,
    DN1: Float32,
    DN2: Float32,
    TAU: Float32,
    TTYPE: Int32,
    G: Float32
) -> None: ...

@bind("SLASQ5")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13))])
def slasq5(
    I0: Int32,
    N0: Int32,
    Z: Float32[Flat],
    PP: Int32,
    TAU: Float32,
    SIGMA: Float32,
    DMIN: Float32,
    DMIN1: Float32,
    DMIN2: Float32,
    DN: Float32,
    DNM1: Float32,
    DNM2: Float32,
    IEEE: Bool,
    EPS: Float32
) -> None: ...

@bind("SLASQ6")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def slasq6(
    I0: Int32,
    N0: Int32,
    Z: Float32[Flat],
    PP: Int32,
    DMIN: Float32,
    DMIN1: Float32,
    DMIN2: Float32,
    DN: Float32,
    DNM1: Float32,
    DNM2: Float32
) -> None: ...

@bind("SLASR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8))])
def slasr(
    SIDE: String[1],
    PIVOT: String[1],
    DIRECT: String[1],
    M: Int32,
    N: Int32,
    C: Float32[Flat],
    S: Float32[Flat],
    A: Float32[LDA, Flat],
    LDA: Int32
) -> None: ...

@bind("SLASRT")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def slasrt(
    ID: String[1],
    N: Int32,
    D: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLASSQ")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def slassq(
    n: Int32,
    x: Float32[Flat],
    incx: Int32,
    scale: Float32,
    sumsq: Float32
) -> None: ...

@bind("SLASV2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8))])
def slasv2(
    F: Float32,
    G: Float32,
    H: Float32,
    SSMIN: Float32,
    SSMAX: Float32,
    SNR: Float32,
    CSR: Float32,
    SNL: Float32,
    CSL: Float32
) -> None: ...

@bind("SLASWLQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def slaswlq(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SLASWP")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def slaswp(
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    K1: Int32,
    K2: Int32,
    IPIV: Int32[Flat],
    INCX: Int32
) -> None: ...

@bind("SLASY2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15))])
def slasy2(
    LTRANL: Bool,
    LTRANR: Bool,
    ISGN: Int32,
    N1: Int32,
    N2: Int32,
    TL: Float32[LDTL, Flat],
    LDTL: Int32,
    TR: Float32[LDTR, Flat],
    LDTR: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    SCALE: Float32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    XNORM: Float32,
    INFO: Int32
) -> None: ...

@bind("SLASYF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def slasyf(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    W: Float32[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("SLASYF_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9)])
def slasyf_aa(
    UPLO: String[1],
    J1: Int32,
    M: Int32,
    NB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    H: Float32[LDH, Flat],
    LDH: Int32,
    WORK: Float32[Flat]
) -> None: ...

@bind("SLASYF_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def slasyf_rk(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    E: Float32[Flat],
    IPIV: Int32[Flat],
    W: Float32[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("SLASYF_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def slasyf_rook(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    W: Float32[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("SLATBS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def slatbs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    X: Float32[Flat],
    SCALE: Float32,
    CNORM: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLATDF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8)])
def slatdf(
    IJOB: Int32,
    N: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    RHS: Float32[Flat],
    RDSUM: Float32,
    RDSCAL: Float32,
    IPIV: Int32[Flat],
    JPIV: Int32[Flat]
) -> None: ...

@bind("SLATPS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def slatps(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    AP: Float32[Flat],
    X: Float32[Flat],
    SCALE: Float32,
    CNORM: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLATRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8))])
def slatrd(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    E: Float32[Flat],
    TAU: Float32[Flat],
    W: Float32[LDW, Flat],
    LDW: Int32
) -> None: ...

@bind("SLATRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def slatrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    X: Float32[Flat],
    SCALE: Float32,
    CNORM: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SLATRS3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def slatrs3(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    SCALE: Float32[Flat],
    CNORM: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SLATRZ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6)])
def slatrz(
    M: Int32,
    N: Int32,
    L: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat]
) -> None: ...

@bind("SLATSQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def slatsqr(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SLAUU2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def slauu2(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("SLAUUM")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def slauum(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("SOPGTR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def sopgtr(
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    TAU: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SOPMTR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def sopmtr(
    SIDE: String[1],
    UPLO: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    AP: Float32[Flat],
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SORBDB")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Addr(Arg(21))])
def sorbdb(
    TRANS: String[1],
    SIGNS: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float32[LDX11, Flat],
    LDX11: Int32,
    X12: Float32[LDX12, Flat],
    LDX12: Int32,
    X21: Float32[LDX21, Flat],
    LDX21: Int32,
    X22: Float32[LDX22, Flat],
    LDX22: Int32,
    THETA: Float32[Flat],
    PHI: Float32[Flat],
    TAUP1: Float32[Flat],
    TAUP2: Float32[Flat],
    TAUQ1: Float32[Flat],
    TAUQ2: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORBDB1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def sorbdb1(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float32[LDX11, Flat],
    LDX11: Int32,
    X21: Float32[LDX21, Flat],
    LDX21: Int32,
    THETA: Float32[Flat],
    PHI: Float32[Flat],
    TAUP1: Float32[Flat],
    TAUP2: Float32[Flat],
    TAUQ1: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORBDB2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def sorbdb2(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float32[LDX11, Flat],
    LDX11: Int32,
    X21: Float32[LDX21, Flat],
    LDX21: Int32,
    THETA: Float32[Flat],
    PHI: Float32[Flat],
    TAUP1: Float32[Flat],
    TAUP2: Float32[Flat],
    TAUQ1: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORBDB3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def sorbdb3(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float32[LDX11, Flat],
    LDX11: Int32,
    X21: Float32[LDX21, Flat],
    LDX21: Int32,
    THETA: Float32[Flat],
    PHI: Float32[Flat],
    TAUP1: Float32[Flat],
    TAUP2: Float32[Flat],
    TAUQ1: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORBDB4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def sorbdb4(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float32[LDX11, Flat],
    LDX11: Int32,
    X21: Float32[LDX21, Flat],
    LDX21: Int32,
    THETA: Float32[Flat],
    PHI: Float32[Flat],
    TAUP1: Float32[Flat],
    TAUP2: Float32[Flat],
    TAUQ1: Float32[Flat],
    PHANTOM: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORBDB5")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def sorbdb5(
    M1: Int32,
    M2: Int32,
    N: Int32,
    X1: Float32[Flat],
    INCX1: Int32,
    X2: Float32[Flat],
    INCX2: Int32,
    Q1: Float32[LDQ1, Flat],
    LDQ1: Int32,
    Q2: Float32[LDQ2, Flat],
    LDQ2: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORBDB6")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def sorbdb6(
    M1: Int32,
    M2: Int32,
    N: Int32,
    X1: Float32[Flat],
    INCX1: Int32,
    X2: Float32[Flat],
    INCX2: Int32,
    Q1: Float32[LDQ1, Flat],
    LDQ1: Int32,
    Q2: Float32[LDQ2, Flat],
    LDQ2: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORCSD")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25)), Arg(26), Addr(Arg(27)), Arg(28), Addr(Arg(29))])
def sorcsd(
    JOBU1: String[1],
    JOBU2: String[1],
    JOBV1T: String[1],
    JOBV2T: String[1],
    TRANS: String[1],
    SIGNS: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float32[LDX11, Flat],
    LDX11: Int32,
    X12: Float32[LDX12, Flat],
    LDX12: Int32,
    X21: Float32[LDX21, Flat],
    LDX21: Int32,
    X22: Float32[LDX22, Flat],
    LDX22: Int32,
    THETA: Float32[Flat],
    U1: Float32[LDU1, Flat],
    LDU1: Int32,
    U2: Float32[LDU2, Flat],
    LDU2: Int32,
    V1T: Float32[LDV1T, Flat],
    LDV1T: Int32,
    V2T: Float32[LDV2T, Flat],
    LDV2T: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SORCSD2BY1")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20))])
def sorcsd2by1(
    JOBU1: String[1],
    JOBU2: String[1],
    JOBV1T: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Float32[LDX11, Flat],
    LDX11: Int32,
    X21: Float32[LDX21, Flat],
    LDX21: Int32,
    THETA: Float32[Flat],
    U1: Float32[LDU1, Flat],
    LDU1: Int32,
    U2: Float32[LDU2, Flat],
    LDU2: Int32,
    V1T: Float32[LDV1T, Flat],
    LDV1T: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SORG2L")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def sorg2l(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SORG2R")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def sorg2r(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SORGBR")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def sorgbr(
    VECT: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORGHR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def sorghr(
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORGL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def sorgl2(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SORGLQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def sorglq(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORGQL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def sorgql(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORGQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def sorgqr(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORGR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def sorgr2(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SORGRQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def sorgrq(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORGTR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def sorgtr(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORGTSQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def sorgtsqr(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORGTSQR_ROW")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def sorgtsqr_row(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORHR_COL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def sorhr_col(
    M: Int32,
    N: Int32,
    NB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    D: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SORM22")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def sorm22(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    N1: Int32,
    N2: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORM2L")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def sorm2l(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SORM2R")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def sorm2r(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SORMBR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def sormbr(
    VECT: String[1],
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORMHR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def sormhr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORML2")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def sorml2(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SORMLQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def sormlq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORMQL")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def sormql(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORMQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def sormqr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORMR2")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def sormr2(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SORMR3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def sormr3(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SORMRQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def sormrq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORMRZ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def sormrz(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SORMTR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def sormtr(
    SIDE: String[1],
    UPLO: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    C: Float32[LDC, Flat],
    LDC: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SPBCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def spbcon(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    ANORM: Float32,
    RCOND: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPBEQU")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8))])
def spbequ(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("SPBRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def spbrfs(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    AFB: Float32[LDAFB, Flat],
    LDAFB: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPBSTF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def spbstf(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    INFO: Int32
) -> None: ...

@bind("SPBSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def spbsv(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SPBSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20))])
def spbsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    AFB: Float32[LDAFB, Flat],
    LDAFB: Int32,
    EQUED: String[1],
    S: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPBTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def spbtf2(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    INFO: Int32
) -> None: ...

@bind("SPBTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def spbtrf(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    INFO: Int32
) -> None: ...

@bind("SPBTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def spbtrs(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SPFTRF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4))])
def spftrf(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPFTRI")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4))])
def spftri(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPFTRS")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def spftrs(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SPOCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def spocon(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    ANORM: Float32,
    RCOND: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPOEQU")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def spoequ(
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("SPOEQUB")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def spoequb(
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("SPORFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15))])
def sporfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPORFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Addr(Arg(22))])
def sporfsx(
    UPLO: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    S: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPOSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def sposv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SPOSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def sposvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    EQUED: String[1],
    S: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPOSVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def sposvxx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    EQUED: String[1],
    S: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    RPVGRW: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPOTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def spotf2(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("SPOTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def spotrf(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("SPOTRF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def spotrf2(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("SPOTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def spotri(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("SPOTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def spotrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SPPCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def sppcon(
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPPEQU")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def sppequ(
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    INFO: Int32
) -> None: ...

@bind("SPPRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def spprfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float32[Flat],
    AFP: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPPSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def sppsv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SPPSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Arg(14), Arg(15), Arg(16), Addr(Arg(17))])
def sppsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float32[Flat],
    AFP: Float32[Flat],
    EQUED: String[1],
    S: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPPTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def spptrf(
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPPTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def spptri(
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPPTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def spptrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SPSTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def spstf2(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    PIV: Int32[N],
    RANK: Int32,
    TOL: Float32,
    WORK: Float32[2 * N],
    INFO: Int32
) -> None: ...

@bind("SPSTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def spstrf(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    PIV: Int32[N],
    RANK: Int32,
    TOL: Float32,
    WORK: Float32[2 * N],
    INFO: Int32
) -> None: ...

@bind("SPTCON")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def sptcon(
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPTEQR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def spteqr(
    COMPZ: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPTRFS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def sptrfs(
    N: Int32,
    NRHS: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    DF: Float32[Flat],
    EF: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPTSV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def sptsv(
    N: Int32,
    NRHS: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SPTSVX")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Addr(Arg(15))])
def sptsvx(
    FACT: String[1],
    N: Int32,
    NRHS: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    DF: Float32[Flat],
    EF: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPTTRF")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3))])
def spttrf(
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SPTTRS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def spttrs(
    N: Int32,
    NRHS: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SPTTS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5))])
def sptts2(
    N: Int32,
    NRHS: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("SRSCL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def srscl(
    N: Int32,
    SA: Float32,
    SX: Float32[Flat],
    INCX: Int32
) -> None: ...

@bind("SSB2ST_KERNELS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14)])
def ssb2st_kernels(
    UPLO: String[1],
    WANTZ: Bool,
    TTYPE: Int32,
    ST: Int32,
    ED: Int32,
    SWEEP: Int32,
    N: Int32,
    NB: Int32,
    IB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    V: Float32[Flat],
    TAU: Float32[Flat],
    LDVT: Int32,
    WORK: Float32[Flat]
) -> None: ...

@bind("SSBEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def ssbev(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSBEV_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def ssbev_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSBEVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def ssbevd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSBEVD_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def ssbevd_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSBEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def ssbevx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSBEVX_2STAGE")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22))])
def ssbevx_2stage(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSBGST")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def ssbgst(
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    BB: Float32[LDBB, Flat],
    LDBB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSBGV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def ssbgv(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    BB: Float32[LDBB, Flat],
    LDBB: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSBGVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def ssbgvd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    BB: Float32[LDBB, Flat],
    LDBB: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSBGVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def ssbgvx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    BB: Float32[LDBB, Flat],
    LDBB: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSBTRD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def ssbtrd(
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSFRK")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9)])
def ssfrk(
    TRANSR: String[1],
    UPLO: String[1],
    TRANS: String[1],
    N: Int32,
    K: Int32,
    ALPHA: Float32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    BETA: Float32,
    C: Float32[Flat]
) -> None: ...

@bind("SSPCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def sspcon(
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSPEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def sspev(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSPEVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def sspevd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSPEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17))])
def sspevx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSPGST")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def sspgst(
    ITYPE: Int32,
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    BP: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSPGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def sspgv(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    BP: Float32[Flat],
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSPGVD")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def sspgvd(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    BP: Float32[Flat],
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSPGVX")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def sspgvx(
    ITYPE: Int32,
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    BP: Float32[Flat],
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSPRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14))])
def ssprfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float32[Flat],
    AFP: Float32[Flat],
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSPSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def sspsv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float32[Flat],
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SSPSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def sspsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float32[Flat],
    AFP: Float32[Flat],
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSPTRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def ssptrd(
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    D: Float32[Flat],
    E: Float32[Flat],
    TAU: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSPTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def ssptrf(
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSPTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5))])
def ssptri(
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    IPIV: Int32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSPTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def ssptrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float32[Flat],
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SSTEBZ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Arg(16), Addr(Arg(17))])
def sstebz(
    RANGE: String[1],
    ORDER: String[1],
    N: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    D: Float32[Flat],
    E: Float32[Flat],
    M: Int32,
    NSPLIT: Int32,
    W: Float32[Flat],
    IBLOCK: Int32[Flat],
    ISPLIT: Int32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSTEDC")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def sstedc(
    COMPZ: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSTEGR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Addr(Arg(19))])
def sstegr(
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSTEIN")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12))])
def sstein(
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    M: Int32,
    W: Float32[Flat],
    IBLOCK: Int32[Flat],
    ISPLIT: Int32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSTEMR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Addr(Arg(20))])
def sstemr(
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    NZC: Int32,
    ISUPPZ: Int32[Flat],
    TRYRAC: Bool,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSTEQR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def ssteqr(
    COMPZ: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSTERF")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3))])
def ssterf(
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSTEV")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def sstev(
    JOBZ: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSTEVD")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def sstevd(
    JOBZ: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSTEVR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Addr(Arg(19))])
def sstevr(
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSTEVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17))])
def sstevx(
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def ssycon(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYCON_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def ssycon_3(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    E: Float32[Flat],
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYCON_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def ssycon_rook(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    ANORM: Float32,
    RCOND: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYCONV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def ssyconv(
    UPLO: String[1],
    WAY: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    E: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYCONVF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def ssyconvf(
    UPLO: String[1],
    WAY: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    E: Float32[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYCONVF_ROOK")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def ssyconvf_rook(
    UPLO: String[1],
    WAY: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    E: Float32[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYEQUB")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def ssyequb(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    S: Float32[Flat],
    SCOND: Float32,
    AMAX: Float32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def ssyev(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    W: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYEV_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def ssyev_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    W: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYEVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def ssyevd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    W: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYEVD_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def ssyevd_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    W: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYEVR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Addr(Arg(20))])
def ssyevr(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYEVR_2STAGE")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Addr(Arg(20))])
def ssyevr_2stage(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19))])
def ssyevx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYEVX_2STAGE")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19))])
def ssyevx_2stage(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYGS2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def ssygs2(
    ITYPE: Int32,
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYGST")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def ssygst(
    ITYPE: Int32,
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def ssygv(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    W: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYGV_2STAGE")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def ssygv_2stage(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    W: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYGVD")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def ssygvd(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    W: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYGVX")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22))])
def ssygvx(
    ITYPE: Int32,
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    VL: Float32,
    VU: Float32,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float32,
    M: Int32,
    W: Float32[Flat],
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def ssyrfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYRFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def ssyrfsx(
    UPLO: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    S: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def ssysv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYSV_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def ssysv_aa(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYSV_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def ssysv_aa_2stage(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TB: Float32[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYSV_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def ssysv_rk(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    E: Float32[Flat],
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYSV_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def ssysv_rook(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def ssysvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYSVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Arg(24), Addr(Arg(25))])
def ssysvxx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AF: Float32[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    S: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    RCOND: Float32,
    RPVGRW: Float32,
    BERR: Float32[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float32[NRHS, Flat],
    ERR_BNDS_COMP: Float32[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYSWAPR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def ssyswapr(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    I1: Int32,
    I2: Int32
) -> None: ...

@bind("SSYTD2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7))])
def ssytd2(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    TAU: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def ssytf2(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYTF2_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def ssytf2_rk(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    E: Float32[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYTF2_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def ssytf2_rook(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYTRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def ssytrd(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRD_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def ssytrd_2stage(
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    TAU: Float32[Flat],
    HOUS2: Float32[Flat],
    LHOUS2: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRD_SB2ST")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def ssytrd_sb2st(
    STAGE1: String[1],
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    D: Float32[Flat],
    E: Float32[Flat],
    HOUS: Float32[Flat],
    LHOUS: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRD_SY2SB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def ssytrd_sy2sb(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def ssytrf(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRF_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def ssytrf_aa(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRF_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def ssytrf_aa_2stage(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TB: Float32[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRF_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def ssytrf_rk(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    E: Float32[Flat],
    IPIV: Int32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRF_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def ssytrf_rook(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def ssytri(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYTRI2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def ssytri2(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRI2X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def ssytri2x(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float32[N + NB + 1, Flat],
    NB: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRI_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def ssytri_3(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    E: Float32[Flat],
    IPIV: Int32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRI_3X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def ssytri_3x(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    E: Float32[Flat],
    IPIV: Int32[Flat],
    WORK: Float32[N + NB + 1, Flat],
    NB: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRI_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def ssytri_rook(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def ssytrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRS2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def ssytrs2(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("SSYTRS_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def ssytrs_3(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    E: Float32[Flat],
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRS_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def ssytrs_aa(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRS_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def ssytrs_aa_2stage(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TB: Float32[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("SSYTRS_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def ssytrs_rook(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("STBCON")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def stbcon(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    KD: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    RCOND: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("STBRFS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def stbrfs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("STBTRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def stbtrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Float32[LDAB, Flat],
    LDAB: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("STFSM")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def stfsm(
    TRANSR: String[1],
    SIDE: String[1],
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    M: Int32,
    N: Int32,
    ALPHA: Float32,
    A: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("STFTRI")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def stftri(
    TRANSR: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("STFTTP")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def stfttp(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    ARF: Float32[Flat],
    AP: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("STFTTR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def stfttr(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    ARF: Float32[Flat],
    A: Float32[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("STGEVC")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15))])
def stgevc(
    SIDE: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    S: Float32[LDS, Flat],
    LDS: Int32,
    P: Float32[LDP, Flat],
    LDP: Int32,
    VL: Float32[LDVL, Flat],
    LDVL: Int32,
    VR: Float32[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("STGEX2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def stgex2(
    WANTQ: Bool,
    WANTZ: Bool,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    J1: Int32,
    N1: Int32,
    N2: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("STGEXC")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def stgexc(
    WANTQ: Bool,
    WANTZ: Bool,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    IFST: Int32,
    ILST: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("STGSEN")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Addr(Arg(24))])
def stgsen(
    IJOB: Int32,
    WANTQ: Bool,
    WANTZ: Bool,
    SELECT: Bool[Flat],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    ALPHAR: Float32[Flat],
    ALPHAI: Float32[Flat],
    BETA: Float32[Flat],
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    Z: Float32[LDZ, Flat],
    LDZ: Int32,
    M: Int32,
    PL: Float32,
    PR: Float32,
    DIF: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("STGSJA")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Addr(Arg(24))])
def stgsja(
    JOBU: String[1],
    JOBV: String[1],
    JOBQ: String[1],
    M: Int32,
    P: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    TOLA: Float32,
    TOLB: Float32,
    ALPHA: Float32[Flat],
    BETA: Float32[Flat],
    U: Float32[LDU, Flat],
    LDU: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    WORK: Float32[Flat],
    NCYCLE: Int32,
    INFO: Int32
) -> None: ...

@bind("STGSNA")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def stgsna(
    JOB: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    VL: Float32[LDVL, Flat],
    LDVL: Int32,
    VR: Float32[LDVR, Flat],
    LDVR: Int32,
    S: Float32[Flat],
    DIF: Float32[Flat],
    MM: Int32,
    M: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("STGSY2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Addr(Arg(21))])
def stgsy2(
    TRANS: String[1],
    IJOB: Int32,
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    D: Float32[LDD, Flat],
    LDD: Int32,
    E: Float32[LDE, Flat],
    LDE: Int32,
    F: Float32[LDF, Flat],
    LDF: Int32,
    SCALE: Float32,
    RDSUM: Float32,
    RDSCAL: Float32,
    IWORK: Int32[Flat],
    PQ: Int32,
    INFO: Int32
) -> None: ...

@bind("STGSYL")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21))])
def stgsyl(
    TRANS: String[1],
    IJOB: Int32,
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    D: Float32[LDD, Flat],
    LDD: Int32,
    E: Float32[LDE, Flat],
    LDE: Int32,
    F: Float32[LDF, Flat],
    LDF: Int32,
    SCALE: Float32,
    DIF: Float32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("STPCON")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def stpcon(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    AP: Float32[Flat],
    RCOND: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("STPLQT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def stplqt(
    M: Int32,
    N: Int32,
    L: Int32,
    MB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("STPLQT2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def stplqt2(
    M: Int32,
    N: Int32,
    L: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("STPMLQT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def stpmlqt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    MB: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("STPMQRT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def stpmqrt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    NB: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("STPQRT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def stpqrt(
    M: Int32,
    N: Int32,
    L: Int32,
    NB: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("STPQRT2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def stpqrt2(
    M: Int32,
    N: Int32,
    L: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("STPRFB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def stprfb(
    SIDE: String[1],
    TRANS: String[1],
    DIRECT: String[1],
    STOREV: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    V: Float32[LDV, Flat],
    LDV: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    WORK: Float32[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("STPRFS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14))])
def stprfs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("STPTRI")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4))])
def stptri(
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    AP: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("STPTRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def stptrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Float32[Flat],
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("STPTTF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def stpttf(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    ARF: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("STPTTR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def stpttr(
    UPLO: String[1],
    N: Int32,
    AP: Float32[Flat],
    A: Float32[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("STRCON")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def strcon(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    RCOND: Float32,
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("STREVC")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def strevc(
    SIDE: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    VL: Float32[LDVL, Flat],
    LDVL: Int32,
    VR: Float32[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("STREVC3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def strevc3(
    SIDE: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    VL: Float32[LDVL, Flat],
    LDVL: Int32,
    VR: Float32[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("STREXC")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def strexc(
    COMPQ: String[1],
    N: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    IFST: Int32,
    ILST: Int32,
    WORK: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("STRRFS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15))])
def strrfs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    X: Float32[LDX, Flat],
    LDX: Int32,
    FERR: Float32[Flat],
    BERR: Float32[Flat],
    WORK: Float32[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("STRSEN")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Addr(Arg(17))])
def strsen(
    JOB: String[1],
    COMPQ: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    Q: Float32[LDQ, Flat],
    LDQ: Int32,
    WR: Float32[Flat],
    WI: Float32[Flat],
    M: Int32,
    S: Float32,
    SEP: Float32,
    WORK: Float32[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("STRSNA")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def strsna(
    JOB: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Float32[LDT, Flat],
    LDT: Int32,
    VL: Float32[LDVL, Flat],
    LDVL: Int32,
    VR: Float32[LDVR, Flat],
    LDVR: Int32,
    S: Float32[Flat],
    SEP: Float32[Flat],
    MM: Int32,
    M: Int32,
    WORK: Float32[LDWORK, Flat],
    LDWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("STRSYL")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12))])
def strsyl(
    TRANA: String[1],
    TRANB: String[1],
    ISGN: Int32,
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    SCALE: Float32,
    INFO: Int32
) -> None: ...

@bind("STRSYL3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def strsyl3(
    TRANA: String[1],
    TRANB: String[1],
    ISGN: Int32,
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    C: Float32[LDC, Flat],
    LDC: Int32,
    SCALE: Float32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    SWORK: Float32[LDSWORK, Flat],
    LDSWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("STRTI2")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def strti2(
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("STRTRI")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def strtri(
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("STRTRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def strtrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    B: Float32[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("STRTTF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def strttf(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    ARF: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("STRTTP")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def strttp(
    UPLO: String[1],
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    AP: Float32[Flat],
    INFO: Int32
) -> None: ...

@bind("STZRZF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def stzrzf(
    M: Int32,
    N: Int32,
    A: Float32[LDA, Flat],
    LDA: Int32,
    TAU: Float32[Flat],
    WORK: Float32[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("XERBLA")
@external
@native_call([Arg(0), Addr(Arg(1))])
def xerbla(
    SRNAME: String,
    INFO: Int32
) -> None: ...

@bind("XERBLA_ARRAY")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2))])
def xerbla_array(
    SRNAME_ARRAY: String[1][SRNAME_LEN],
    SRNAME_LEN: Int32,
    INFO: Int32
) -> None: ...

@bind("ZBBCSD")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Arg(23), Arg(24), Arg(25), Arg(26), Addr(Arg(27)), Addr(Arg(28))])
def zbbcsd(
    JOBU1: String[1],
    JOBU2: String[1],
    JOBV1T: String[1],
    JOBV2T: String[1],
    TRANS: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    THETA: Float64[Flat],
    PHI: Float64[Flat],
    U1: Complex128[LDU1, Flat],
    LDU1: Int32,
    U2: Complex128[LDU2, Flat],
    LDU2: Int32,
    V1T: Complex128[LDV1T, Flat],
    LDV1T: Int32,
    V2T: Complex128[LDV2T, Flat],
    LDV2T: Int32,
    B11D: Float64[Flat],
    B11E: Float64[Flat],
    B12D: Float64[Flat],
    B12E: Float64[Flat],
    B21D: Float64[Flat],
    B21E: Float64[Flat],
    B22D: Float64[Flat],
    B22E: Float64[Flat],
    RWORK: Float64[Flat],
    LRWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZBDSQR")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14))])
def zbdsqr(
    UPLO: String[1],
    N: Int32,
    NCVT: Int32,
    NRU: Int32,
    NCC: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    VT: Complex128[LDVT, Flat],
    LDVT: Int32,
    U: Complex128[LDU, Flat],
    LDU: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZCGESV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zcgesv(
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    WORK: Complex128[N, Flat],
    SWORK: Complex64[Flat],
    RWORK: Float64[Flat],
    ITER: Int32,
    INFO: Int32
) -> None: ...

@bind("ZCPOSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zcposv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    WORK: Complex128[N, Flat],
    SWORK: Complex64[Flat],
    RWORK: Float64[Flat],
    ITER: Int32,
    INFO: Int32
) -> None: ...

@bind("ZDRSCL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def zdrscl(
    N: Int32,
    SA: Float64,
    SX: Complex128[Flat],
    INCX: Int32
) -> None: ...

@bind("ZGBBRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Addr(Arg(18))])
def zgbbrd(
    VECT: String[1],
    M: Int32,
    N: Int32,
    NCC: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    PT: Complex128[LDPT, Flat],
    LDPT: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGBCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def zgbcon(
    NORM: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGBEQU")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11))])
def zgbequ(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    R: Float64[Flat],
    C: Float64[Flat],
    ROWCND: Float64,
    COLCND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("ZGBEQUB")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11))])
def zgbequb(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    R: Float64[Flat],
    C: Float64[Flat],
    ROWCND: Float64,
    COLCND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("ZGBRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Addr(Arg(18))])
def zgbrfs(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex128[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGBRFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22)), Arg(23), Arg(24), Arg(25), Addr(Arg(26))])
def zgbrfsx(
    TRANS: String[1],
    EQUED: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex128[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    R: Float64[Flat],
    C: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGBSV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def zgbsv(
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGBSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def zgbsvx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex128[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float64[Flat],
    C: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGBSVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Addr(Arg(24)), Arg(25), Arg(26), Arg(27), Addr(Arg(28))])
def zgbsvxx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex128[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float64[Flat],
    C: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    RPVGRW: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGBTF2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def zgbtf2(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGBTRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def zgbtrf(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGBTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zgbtrs(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGEBAK")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def zgebak(
    JOB: String[1],
    SIDE: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    SCALE: Float64[Flat],
    M: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGEBAL")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def zgebal(
    JOB: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    ILO: Int32,
    IHI: Int32,
    SCALE: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEBD2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9))])
def zgebd2(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    TAUQ: Complex128[Flat],
    TAUP: Complex128[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEBRD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zgebrd(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    TAUQ: Complex128[Flat],
    TAUP: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGECON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def zgecon(
    NORM: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEDMD")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Return('K', 0), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Arg(21), Addr(Arg(22)), Arg(23), Addr(Arg(24)), Arg(25), Addr(Arg(26)), Arg(27), Addr(Arg(28)), Return('INFO', 1)])
def zgedmd(
    JOBS: String[1],
    JOBZ: String[1],
    JOBR: String[1],
    JOBF: String[1],
    WHTSVD: Int32,
    M: Int32,
    N: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    Y: Complex128[LDY, Flat],
    LDY: Int32,
    NRNK: Int32,
    TOL: Float64,
    EIGS: Complex128[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    RES: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    W: Complex128[LDW, Flat],
    LDW: Int32,
    S: Complex128[LDS, Flat],
    LDS: Int32,
    ZWORK: Complex128[Flat],
    LZWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32
) -> tuple[Int32, Int32]: ...

@bind("ZGEDMDQ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Return('K', 0), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22)), Arg(23), Addr(Arg(24)), Arg(25), Addr(Arg(26)), Arg(27), Addr(Arg(28)), Arg(29), Addr(Arg(30)), Arg(31), Addr(Arg(32)), Return('INFO', 1)])
def zgedmdq(
    JOBS: String[1],
    JOBZ: String[1],
    JOBR: String[1],
    JOBQ: String[1],
    JOBT: String[1],
    JOBF: String[1],
    WHTSVD: Int32,
    M: Int32,
    N: Int32,
    F: Complex128[LDF, Flat],
    LDF: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    Y: Complex128[LDY, Flat],
    LDY: Int32,
    NRNK: Int32,
    TOL: Float64,
    EIGS: Complex128[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    RES: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    S: Complex128[LDS, Flat],
    LDS: Int32,
    ZWORK: Complex128[Flat],
    LZWORK: Int32,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32
) -> tuple[Int32, Int32]: ...

@bind("ZGEEQU")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def zgeequ(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    R: Float64[Flat],
    C: Float64[Flat],
    ROWCND: Float64,
    COLCND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("ZGEEQUB")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9))])
def zgeequb(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    R: Float64[Flat],
    C: Float64[Flat],
    ROWCND: Float64,
    COLCND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("ZGEES")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14))])
def zgees(
    JOBVS: String[1],
    SORT: String[1],
    SELECT: Bool,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    SDIM: Int32,
    W: Complex128[Flat],
    VS: Complex128[LDVS, Flat],
    LDVS: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEESX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17))])
def zgeesx(
    JOBVS: String[1],
    SORT: String[1],
    SELECT: Bool,
    SENSE: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    SDIM: Int32,
    W: Complex128[Flat],
    VS: Complex128[LDVS, Flat],
    LDVS: Int32,
    RCONDE: Float64,
    RCONDV: Float64,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def zgeev(
    JOBVL: String[1],
    JOBVR: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    W: Complex128[Flat],
    VL: Complex128[LDVL, Flat],
    LDVL: Int32,
    VR: Complex128[LDVR, Flat],
    LDVR: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21))])
def zgeevx(
    BALANC: String[1],
    JOBVL: String[1],
    JOBVR: String[1],
    SENSE: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    W: Complex128[Flat],
    VL: Complex128[LDVL, Flat],
    LDVL: Int32,
    VR: Complex128[LDVR, Flat],
    LDVR: Int32,
    ILO: Int32,
    IHI: Int32,
    SCALE: Float64[Flat],
    ABNRM: Float64,
    RCONDE: Float64[Flat],
    RCONDV: Float64[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEHD2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def zgehd2(
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEHRD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zgehrd(
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGEJSV")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20))])
def zgejsv(
    JOBA: String[1],
    JOBU: String[1],
    JOBV: String[1],
    JOBR: String[1],
    JOBT: String[1],
    JOBP: String[1],
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    SVA: Float64[N],
    U: Complex128[LDU, Flat],
    LDU: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    CWORK: Complex128[LWORK],
    LWORK: Int32,
    RWORK: Float64[LRWORK],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGELQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zgelq(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[Flat],
    TSIZE: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGELQ2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def zgelq2(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGELQF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zgelqf(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGELQT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def zgelqt(
    M: Int32,
    N: Int32,
    MB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGELQT3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def zgelqt3(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGELS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zgels(
    TRANS: String[1],
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGELSD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14))])
def zgelsd(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    S: Float64[Flat],
    RCOND: Float64,
    RANK: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGELSS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def zgelss(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    S: Float64[Flat],
    RCOND: Float64,
    RANK: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGELST")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zgelst(
    TRANS: String[1],
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGELSY")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def zgelsy(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    JPVT: Int32[Flat],
    RCOND: Float64,
    RANK: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEMLQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zgemlq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[Flat],
    TSIZE: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGEMLQT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def zgemlqt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    MB: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEMQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zgemqr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[Flat],
    TSIZE: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGEMQRT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13))])
def zgemqrt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    NB: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEQL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def zgeql2(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEQLF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zgeqlf(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGEQP3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def zgeqp3(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    JPVT: Int32[Flat],
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEQP3RK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17))])
def zgeqp3rk(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    KMAX: Int32,
    ABSTOL: Float64,
    RELTOL: Float64,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    K: Int32,
    MAXC2NRMK: Float64,
    RELMAXC2NRMK: Float64,
    JPIV: Int32[Flat],
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zgeqr(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[Flat],
    TSIZE: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGEQR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def zgeqr2(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEQR2P")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def zgeqr2p(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEQRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zgeqrf(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGEQRFP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zgeqrfp(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGEQRT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def zgeqrt(
    M: Int32,
    N: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGEQRT2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def zgeqrt2(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGEQRT3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def zgeqrt3(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGERFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def zgerfs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGERFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def zgerfsx(
    TRANS: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    R: Float64[Flat],
    C: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGERQ2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def zgerq2(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGERQF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zgerqf(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGESC2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def zgesc2(
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    RHS: Complex128[Flat],
    IPIV: Int32[Flat],
    JPIV: Int32[Flat],
    SCALE: Float64
) -> None: ...

@bind("ZGESDD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14))])
def zgesdd(
    JOBZ: String[1],
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    U: Complex128[LDU, Flat],
    LDU: Int32,
    VT: Complex128[LDVT, Flat],
    LDVT: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGESV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zgesv(
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGESVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14))])
def zgesvd(
    JOBU: String[1],
    JOBVT: String[1],
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    U: Complex128[LDU, Flat],
    LDU: Int32,
    VT: Complex128[LDVT, Flat],
    LDVT: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGESVDQ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Addr(Arg(21))])
def zgesvdq(
    JOBA: String[1],
    JOBP: String[1],
    JOBR: String[1],
    JOBU: String[1],
    JOBV: String[1],
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    U: Complex128[LDU, Flat],
    LDU: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    NUMRANK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    CWORK: Complex128[Flat],
    LCWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGESVDX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Addr(Arg(21))])
def zgesvdx(
    JOBU: String[1],
    JOBVT: String[1],
    RANGE: String[1],
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    NS: Int32,
    S: Float64[Flat],
    U: Complex128[LDU, Flat],
    LDU: Int32,
    VT: Complex128[LDVT, Flat],
    LDVT: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGESVJ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def zgesvj(
    JOBA: String[1],
    JOBU: String[1],
    JOBV: String[1],
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    SVA: Float64[N],
    MV: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    CWORK: Complex128[LWORK],
    LWORK: Int32,
    RWORK: Float64[LRWORK],
    LRWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGESVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def zgesvx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float64[Flat],
    C: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGESVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Addr(Arg(22)), Arg(23), Arg(24), Arg(25), Addr(Arg(26))])
def zgesvxx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    R: Float64[Flat],
    C: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    RPVGRW: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGETC2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def zgetc2(
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    JPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGETF2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def zgetf2(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGETRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def zgetrf(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGETRF2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def zgetrf2(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGETRI")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def zgetri(
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGETRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zgetrs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGETSLS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zgetsls(
    TRANS: String[1],
    M: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGETSQRHRT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def zgetsqrhrt(
    M: Int32,
    N: Int32,
    MB1: Int32,
    NB1: Int32,
    NB2: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGGBAK")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zggbak(
    JOB: String[1],
    SIDE: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    LSCALE: Float64[Flat],
    RSCALE: Float64[Flat],
    M: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGGBAL")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11))])
def zggbal(
    JOB: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    ILO: Int32,
    IHI: Int32,
    LSCALE: Float64[Flat],
    RSCALE: Float64[Flat],
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGGES")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20))])
def zgges(
    JOBVSL: String[1],
    JOBVSR: String[1],
    SORT: String[1],
    SELCTG: Bool,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    SDIM: Int32,
    ALPHA: Complex128[Flat],
    BETA: Complex128[Flat],
    VSL: Complex128[LDVSL, Flat],
    LDVSL: Int32,
    VSR: Complex128[LDVSR, Flat],
    LDVSR: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGGES3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20))])
def zgges3(
    JOBVSL: String[1],
    JOBVSR: String[1],
    SORT: String[1],
    SELCTG: Bool,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    SDIM: Int32,
    ALPHA: Complex128[Flat],
    BETA: Complex128[Flat],
    VSL: Complex128[LDVSL, Flat],
    LDVSL: Int32,
    VSR: Complex128[LDVSR, Flat],
    LDVSR: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGGESX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25))])
def zggesx(
    JOBVSL: String[1],
    JOBVSR: String[1],
    SORT: String[1],
    SELCTG: Bool,
    SENSE: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    SDIM: Int32,
    ALPHA: Complex128[Flat],
    BETA: Complex128[Flat],
    VSL: Complex128[LDVSL, Flat],
    LDVSL: Int32,
    VSR: Complex128[LDVSR, Flat],
    LDVSR: Int32,
    RCONDE: Float64[2],
    RCONDV: Float64[2],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    LIWORK: Int32,
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGGEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def zggev(
    JOBVL: String[1],
    JOBVR: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    ALPHA: Complex128[Flat],
    BETA: Complex128[Flat],
    VL: Complex128[LDVL, Flat],
    LDVL: Int32,
    VR: Complex128[LDVR, Flat],
    LDVR: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGGEV3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def zggev3(
    JOBVL: String[1],
    JOBVR: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    ALPHA: Complex128[Flat],
    BETA: Complex128[Flat],
    VL: Complex128[LDVL, Flat],
    LDVL: Int32,
    VR: Complex128[LDVR, Flat],
    LDVR: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGGEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24)), Arg(25), Arg(26), Arg(27), Addr(Arg(28))])
def zggevx(
    BALANC: String[1],
    JOBVL: String[1],
    JOBVR: String[1],
    SENSE: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    ALPHA: Complex128[Flat],
    BETA: Complex128[Flat],
    VL: Complex128[LDVL, Flat],
    LDVL: Int32,
    VR: Complex128[LDVR, Flat],
    LDVR: Int32,
    ILO: Int32,
    IHI: Int32,
    LSCALE: Float64[Flat],
    RSCALE: Float64[Flat],
    ABNRM: Float64,
    BBNRM: Float64,
    RCONDE: Float64[Flat],
    RCONDV: Float64[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    BWORK: Bool[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGGGLM")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zggglm(
    N: Int32,
    M: Int32,
    P: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    D: Complex128[Flat],
    X: Complex128[Flat],
    Y: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGGHD3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def zgghd3(
    COMPQ: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGGHRD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zgghrd(
    COMPQ: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGGLSE")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zgglse(
    M: Int32,
    N: Int32,
    P: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    C: Complex128[Flat],
    D: Complex128[Flat],
    X: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGGQRF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def zggqrf(
    N: Int32,
    M: Int32,
    P: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAUA: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    TAUB: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGGRQF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def zggrqf(
    M: Int32,
    P: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAUA: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    TAUB: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGGSVD3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Addr(Arg(24))])
def zggsvd3(
    JOBU: String[1],
    JOBV: String[1],
    JOBQ: String[1],
    M: Int32,
    N: Int32,
    P: Int32,
    K: Int32,
    L: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    ALPHA: Float64[Flat],
    BETA: Float64[Flat],
    U: Complex128[LDU, Flat],
    LDU: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGGSVP3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Arg(23), Addr(Arg(24)), Addr(Arg(25))])
def zggsvp3(
    JOBU: String[1],
    JOBV: String[1],
    JOBQ: String[1],
    M: Int32,
    P: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    TOLA: Float64,
    TOLB: Float64,
    K: Int32,
    L: Int32,
    U: Complex128[LDU, Flat],
    LDU: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    IWORK: Int32[Flat],
    RWORK: Float64[Flat],
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGSVJ0")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def zgsvj0(
    JOBV: String[1],
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    D: Complex128[N],
    SVA: Float64[N],
    MV: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    EPS: Float64,
    SFMIN: Float64,
    TOL: Float64,
    NSWEEP: Int32,
    WORK: Complex128[LWORK],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGSVJ1")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Addr(Arg(17))])
def zgsvj1(
    JOBV: String[1],
    M: Int32,
    N: Int32,
    N1: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    D: Complex128[N],
    SVA: Float64[N],
    MV: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    EPS: Float64,
    SFMIN: Float64,
    TOL: Float64,
    NSWEEP: Int32,
    WORK: Complex128[LWORK],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGTCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def zgtcon(
    NORM: String[1],
    N: Int32,
    DL: Complex128[Flat],
    D: Complex128[Flat],
    DU: Complex128[Flat],
    DU2: Complex128[Flat],
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGTRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def zgtrfs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    DL: Complex128[Flat],
    D: Complex128[Flat],
    DU: Complex128[Flat],
    DLF: Complex128[Flat],
    DF: Complex128[Flat],
    DUF: Complex128[Flat],
    DU2: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGTSV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zgtsv(
    N: Int32,
    NRHS: Int32,
    DL: Complex128[Flat],
    D: Complex128[Flat],
    DU: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGTSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def zgtsvx(
    FACT: String[1],
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    DL: Complex128[Flat],
    D: Complex128[Flat],
    DU: Complex128[Flat],
    DLF: Complex128[Flat],
    DF: Complex128[Flat],
    DUF: Complex128[Flat],
    DU2: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGTTRF")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def zgttrf(
    N: Int32,
    DL: Complex128[Flat],
    D: Complex128[Flat],
    DU: Complex128[Flat],
    DU2: Complex128[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZGTTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zgttrs(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    DL: Complex128[Flat],
    D: Complex128[Flat],
    DU: Complex128[Flat],
    DU2: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZGTTS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9))])
def zgtts2(
    ITRANS: Int32,
    N: Int32,
    NRHS: Int32,
    DL: Complex128[Flat],
    D: Complex128[Flat],
    DU: Complex128[Flat],
    DU2: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("ZHB2ST_KERNELS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14)])
def zhb2st_kernels(
    UPLO: String[1],
    WANTZ: Bool,
    TTYPE: Int32,
    ST: Int32,
    ED: Int32,
    SWEEP: Int32,
    N: Int32,
    NB: Int32,
    IB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    V: Complex128[Flat],
    TAU: Complex128[Flat],
    LDVT: Int32,
    WORK: Complex128[Flat]
) -> None: ...

@bind("ZHBEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def zhbev(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHBEV_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def zhbev_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHBEVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def zhbevd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHBEVD_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def zhbevd_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHBEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Arg(20), Arg(21), Addr(Arg(22))])
def zhbevx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHBEVX_2STAGE")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def zhbevx_2stage(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHBGST")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13))])
def zhbgst(
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    BB: Complex128[LDBB, Flat],
    LDBB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHBGV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14))])
def zhbgv(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    BB: Complex128[LDBB, Flat],
    LDBB: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHBGVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18))])
def zhbgvd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    BB: Complex128[LDBB, Flat],
    LDBB: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHBGVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Arg(24), Addr(Arg(25))])
def zhbgvx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    KA: Int32,
    KB: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    BB: Complex128[LDBB, Flat],
    LDBB: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHBTRD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def zhbtrd(
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHECON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def zhecon(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHECON_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def zhecon_3(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHECON_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def zhecon_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHEEQUB")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def zheequb(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHEEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def zheev(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    W: Float64[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHEEV_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def zheev_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    W: Float64[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHEEVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zheevd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    W: Float64[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHEEVD_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zheevd_2stage(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    W: Float64[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHEEVR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Addr(Arg(22))])
def zheevr(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHEEVR_2STAGE")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Addr(Arg(22))])
def zheevr_2stage(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHEEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Addr(Arg(20))])
def zheevx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHEEVX_2STAGE")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Addr(Arg(20))])
def zheevx_2stage(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHEGS2")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zhegs2(
    ITYPE: Int32,
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHEGST")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zhegst(
    ITYPE: Int32,
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHEGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def zhegv(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    W: Float64[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHEGV_2STAGE")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def zhegv_2stage(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    W: Float64[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHEGVD")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def zhegvd(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    W: Float64[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHEGVX")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def zhegvx(
    ITYPE: Int32,
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHERFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def zherfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHERFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def zherfsx(
    UPLO: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    S: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHESV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zhesv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHESV_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zhesv_aa(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHESV_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zhesv_aa_2stage(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TB: Complex128[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHESV_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def zhesv_rk(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHESV_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zhesv_rook(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHESVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def zhesvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHESVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Arg(24), Addr(Arg(25))])
def zhesvxx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    S: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    RPVGRW: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHESWAPR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def zheswapr(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, N],
    LDA: Int32,
    I1: Int32,
    I2: Int32
) -> None: ...

@bind("ZHETD2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7))])
def zhetd2(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    TAU: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHETF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def zhetf2(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHETF2_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def zhetf2_rk(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHETF2_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def zhetf2_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHETRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def zhetrd(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRD_2STAGE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zhetrd_2stage(
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    TAU: Complex128[Flat],
    HOUS2: Complex128[Flat],
    LHOUS2: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRD_HB2ST")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zhetrd_hb2st(
    STAGE1: String[1],
    VECT: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    HOUS: Complex128[Flat],
    LHOUS: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRD_HE2HB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zhetrd_he2hb(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zhetrf(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRF_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zhetrf_aa(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRF_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zhetrf_aa_2stage(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TB: Complex128[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRF_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zhetrf_rk(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRF_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zhetrf_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def zhetri(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHETRI2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zhetri2(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRI2X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zhetri2x(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[N + NB + 1, Flat],
    NB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRI_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zhetri_3(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRI_3X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zhetri_3x(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    WORK: Complex128[N + NB + 1, Flat],
    NB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRI_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def zhetri_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHETRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zhetrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRS2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def zhetrs2(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHETRS_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def zhetrs_3(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRS_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zhetrs_aa(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRS_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def zhetrs_aa_2stage(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TB: Complex128[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHETRS_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zhetrs_rook(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHFRK")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9)])
def zhfrk(
    TRANSR: String[1],
    UPLO: String[1],
    TRANS: String[1],
    N: Int32,
    K: Int32,
    ALPHA: Float64,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    BETA: Float64,
    C: Complex128[Flat]
) -> None: ...

@bind("ZHGEQZ")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def zhgeqz(
    JOB: String[1],
    COMPQ: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Complex128[LDH, Flat],
    LDH: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    ALPHA: Complex128[Flat],
    BETA: Complex128[Flat],
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHPCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def zhpcon(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHPEV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def zhpev(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHPEVD")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zhpevd(
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHPEVX")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Addr(Arg(18))])
def zhpevx(
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHPGST")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def zhpgst(
    ITYPE: Int32,
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    BP: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHPGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11))])
def zhpgv(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    BP: Complex128[Flat],
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHPGVD")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def zhpgvd(
    ITYPE: Int32,
    JOBZ: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    BP: Complex128[Flat],
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHPGVX")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20))])
def zhpgvx(
    ITYPE: Int32,
    JOBZ: String[1],
    RANGE: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    BP: Complex128[Flat],
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHPRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14))])
def zhprfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    AFP: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHPSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zhpsv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHPSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def zhpsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    AFP: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHPTRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def zhptrd(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    D: Float64[Flat],
    E: Float64[Flat],
    TAU: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHPTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def zhptrf(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHPTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5))])
def zhptri(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHPTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zhptrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZHSEIN")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Addr(Arg(18))])
def zhsein(
    SIDE: String[1],
    EIGSRC: String[1],
    INITV: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    H: Complex128[LDH, Flat],
    LDH: Int32,
    W: Complex128[Flat],
    VL: Complex128[LDVL, Flat],
    LDVL: Int32,
    VR: Complex128[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    IFAILL: Int32[Flat],
    IFAILR: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZHSEQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zhseqr(
    JOB: String[1],
    COMPZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Complex128[LDH, Flat],
    LDH: Int32,
    W: Complex128[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLA_GBAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def zla_gbamv(
    TRANS: Int32,
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    ALPHA: Float64,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    X: Complex128[Flat],
    INCX: Int32,
    BETA: Float64,
    Y: Float64[Flat],
    INCY: Int32
) -> None: ...

@bind("ZLA_GBRCOND_C")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13)])
def zla_gbrcond_c(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex128[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    C: Float64[Flat],
    CAPPLY: Bool,
    INFO: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat]
) -> Float64: ...

@bind("ZLA_GBRCOND_X")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Arg(12)])
def zla_gbrcond_x(
    TRANS: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex128[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    X: Complex128[Flat],
    INFO: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat]
) -> Float64: ...

@bind("ZLA_GBRFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Arg(22), Arg(23), Arg(24), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28)), Addr(Arg(29)), Addr(Arg(30))])
def zla_gbrfsx_extended(
    PREC_TYPE: Int32,
    TRANS_TYPE: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    NRHS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex128[LDAFB, Flat],
    LDAFB: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    Y: Complex128[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float64[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    RES: Complex128[Flat],
    AYB: Float64[Flat],
    DY: Complex128[Flat],
    Y_TAIL: Complex128[Flat],
    RCOND: Float64,
    ITHRESH: Int32,
    RTHRESH: Float64,
    DZ_UB: Float64,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("ZLA_GBRPVGRW")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def zla_gbrpvgrw(
    N: Int32,
    KL: Int32,
    KU: Int32,
    NCOLS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex128[LDAFB, Flat],
    LDAFB: Int32
) -> Float64: ...

@bind("ZLA_GEAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def zla_geamv(
    TRANS: Int32,
    M: Int32,
    N: Int32,
    ALPHA: Float64,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    X: Complex128[Flat],
    INCX: Int32,
    BETA: Float64,
    Y: Float64[Flat],
    INCY: Int32
) -> None: ...

@bind("ZLA_GERCOND_C")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11)])
def zla_gercond_c(
    TRANS: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    C: Float64[Flat],
    CAPPLY: Bool,
    INFO: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat]
) -> Float64: ...

@bind("ZLA_GERCOND_X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10)])
def zla_gercond_x(
    TRANS: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    X: Complex128[Flat],
    INFO: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat]
) -> Float64: ...

@bind("ZLA_GERFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28))])
def zla_gerfsx_extended(
    PREC_TYPE: Int32,
    TRANS_TYPE: Int32,
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    Y: Complex128[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float64[Flat],
    N_NORMS: Int32,
    ERRS_N: Float64[NRHS, Flat],
    ERRS_C: Float64[NRHS, Flat],
    RES: Complex128[Flat],
    AYB: Float64[Flat],
    DY: Complex128[Flat],
    Y_TAIL: Complex128[Flat],
    RCOND: Float64,
    ITHRESH: Int32,
    RTHRESH: Float64,
    DZ_UB: Float64,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("ZLA_GERPVGRW")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def zla_gerpvgrw(
    N: Int32,
    NCOLS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32
) -> Float64: ...

@bind("ZLA_HEAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def zla_heamv(
    UPLO: Int32,
    N: Int32,
    ALPHA: Float64,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    X: Complex128[Flat],
    INCX: Int32,
    BETA: Float64,
    Y: Float64[Flat],
    INCY: Int32
) -> None: ...

@bind("ZLA_HERCOND_C")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11)])
def zla_hercond_c(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    C: Float64[Flat],
    CAPPLY: Bool,
    INFO: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat]
) -> Float64: ...

@bind("ZLA_HERCOND_X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10)])
def zla_hercond_x(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    X: Complex128[Flat],
    INFO: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat]
) -> Float64: ...

@bind("ZLA_HERFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28))])
def zla_herfsx_extended(
    PREC_TYPE: Int32,
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    Y: Complex128[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float64[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    RES: Complex128[Flat],
    AYB: Float64[Flat],
    DY: Complex128[Flat],
    Y_TAIL: Complex128[Flat],
    RCOND: Float64,
    ITHRESH: Int32,
    RTHRESH: Float64,
    DZ_UB: Float64,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("ZLA_HERPVGRW")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8)])
def zla_herpvgrw(
    UPLO: String[1],
    N: Int32,
    INFO: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLA_LIN_BERR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5)])
def zla_lin_berr(
    N: Int32,
    NZ: Int32,
    NRHS: Int32,
    RES: Complex128[N, NRHS],
    AYB: Float64[N, NRHS],
    BERR: Float64[NRHS]
) -> None: ...

@bind("ZLA_PORCOND_C")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10)])
def zla_porcond_c(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    C: Float64[Flat],
    CAPPLY: Bool,
    INFO: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat]
) -> Float64: ...

@bind("ZLA_PORCOND_X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9)])
def zla_porcond_x(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    X: Complex128[Flat],
    INFO: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat]
) -> Float64: ...

@bind("ZLA_PORFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Addr(Arg(22)), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27))])
def zla_porfsx_extended(
    PREC_TYPE: Int32,
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    COLEQU: Bool,
    C: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    Y: Complex128[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float64[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    RES: Complex128[Flat],
    AYB: Float64[Flat],
    DY: Complex128[Flat],
    Y_TAIL: Complex128[Flat],
    RCOND: Float64,
    ITHRESH: Int32,
    RTHRESH: Float64,
    DZ_UB: Float64,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("ZLA_PORPVGRW")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def zla_porpvgrw(
    UPLO: String[1],
    NCOLS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLA_SYAMV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def zla_syamv(
    UPLO: Int32,
    N: Int32,
    ALPHA: Float64,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    X: Complex128[Flat],
    INCX: Int32,
    BETA: Float64,
    Y: Float64[Flat],
    INCY: Int32
) -> None: ...

@bind("ZLA_SYRCOND_C")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11)])
def zla_syrcond_c(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    C: Float64[Flat],
    CAPPLY: Bool,
    INFO: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat]
) -> Float64: ...

@bind("ZLA_SYRCOND_X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10)])
def zla_syrcond_x(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    X: Complex128[Flat],
    INFO: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat]
) -> Float64: ...

@bind("ZLA_SYRFSX_EXTENDED")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Arg(19), Arg(20), Arg(21), Arg(22), Addr(Arg(23)), Addr(Arg(24)), Addr(Arg(25)), Addr(Arg(26)), Addr(Arg(27)), Addr(Arg(28))])
def zla_syrfsx_extended(
    PREC_TYPE: Int32,
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    COLEQU: Bool,
    C: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    Y: Complex128[LDY, Flat],
    LDY: Int32,
    BERR_OUT: Float64[Flat],
    N_NORMS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    RES: Complex128[Flat],
    AYB: Float64[Flat],
    DY: Complex128[Flat],
    Y_TAIL: Complex128[Flat],
    RCOND: Float64,
    ITHRESH: Int32,
    RTHRESH: Float64,
    DZ_UB: Float64,
    IGNORE_CWISE: Bool,
    INFO: Int32
) -> None: ...

@bind("ZLA_SYRPVGRW")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8)])
def zla_syrpvgrw(
    UPLO: String[1],
    N: Int32,
    INFO: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLA_WWADDW")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3)])
def zla_wwaddw(
    N: Int32,
    X: Complex128[Flat],
    Y: Complex128[Flat],
    W: Complex128[Flat]
) -> None: ...

@bind("ZLABRD")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def zlabrd(
    M: Int32,
    N: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    TAUQ: Complex128[Flat],
    TAUP: Complex128[Flat],
    X: Complex128[LDX, Flat],
    LDX: Int32,
    Y: Complex128[LDY, Flat],
    LDY: Int32
) -> None: ...

@bind("ZLACGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2))])
def zlacgv(
    N: Int32,
    X: Complex128[Flat],
    INCX: Int32
) -> None: ...

@bind("ZLACN2")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5)])
def zlacn2(
    N: Int32,
    V: Complex128[Flat],
    X: Complex128[Flat],
    EST: Float64,
    KASE: Int32,
    ISAVE: Int32[3]
) -> None: ...

@bind("ZLACON")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def zlacon(
    N: Int32,
    V: Complex128[N],
    X: Complex128[N],
    EST: Float64,
    KASE: Int32
) -> None: ...

@bind("ZLACP2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def zlacp2(
    UPLO: String[1],
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("ZLACPY")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def zlacpy(
    UPLO: String[1],
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("ZLACRM")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def zlacrm(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Float64[LDB, Flat],
    LDB: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    RWORK: Float64[Flat]
) -> None: ...

@bind("ZLACRT")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def zlacrt(
    N: Int32,
    CX: Complex128[Flat],
    INCX: Int32,
    CY: Complex128[Flat],
    INCY: Int32,
    C: Complex128,
    S: Complex128
) -> None: ...

@bind("ZLADIV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def zladiv(
    X: Complex128,
    Y: Complex128
) -> Complex128: ...

@bind("ZLAED0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def zlaed0(
    QSIZ: Int32,
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    QSTORE: Complex128[LDQS, Flat],
    LDQS: Int32,
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZLAED7")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21))])
def zlaed7(
    N: Int32,
    CUTPNT: Int32,
    QSIZ: Int32,
    TLVLS: Int32,
    CURLVL: Int32,
    CURPBM: Int32,
    D: Float64[Flat],
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    RHO: Float64,
    INDXQ: Int32[Flat],
    QSTORE: Float64[Flat],
    QPTR: Int32[Flat],
    PRMPTR: Int32[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32[Flat],
    GIVCOL: Int32[2, Flat],
    GIVNUM: Float64[2, Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZLAED8")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20))])
def zlaed8(
    K: Int32,
    N: Int32,
    QSIZ: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    D: Float64[Flat],
    RHO: Float64,
    CUTPNT: Int32,
    Z: Float64[Flat],
    DLAMBDA: Float64[Flat],
    Q2: Complex128[LDQ2, Flat],
    LDQ2: Int32,
    W: Float64[Flat],
    INDXP: Int32[Flat],
    INDX: Int32[Flat],
    INDXQ: Int32[Flat],
    PERM: Int32[Flat],
    GIVPTR: Int32,
    GIVCOL: Int32[2, Flat],
    GIVNUM: Float64[2, Flat],
    INFO: Int32
) -> None: ...

@bind("ZLAEIN")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12))])
def zlaein(
    RIGHTV: Bool,
    NOINIT: Bool,
    N: Int32,
    H: Complex128[LDH, Flat],
    LDH: Int32,
    W: Complex128,
    V: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    RWORK: Float64[Flat],
    EPS3: Float64,
    SMLNUM: Float64,
    INFO: Int32
) -> None: ...

@bind("ZLAESY")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7))])
def zlaesy(
    A: Complex128,
    B: Complex128,
    C: Complex128,
    RT1: Complex128,
    RT2: Complex128,
    EVSCAL: Complex128,
    CS1: Complex128,
    SN1: Complex128
) -> None: ...

@bind("ZLAEV2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def zlaev2(
    A: Complex128,
    B: Complex128,
    C: Complex128,
    RT1: Float64,
    RT2: Float64,
    CS1: Float64,
    SN1: Complex128
) -> None: ...

@bind("ZLAG2C")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def zlag2c(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    SA: Complex64[LDSA, Flat],
    LDSA: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLAGS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12))])
def zlags2(
    UPPER: Bool,
    A1: Float64,
    A2: Complex128,
    A3: Float64,
    B1: Float64,
    B2: Complex128,
    B3: Float64,
    CSU: Float64,
    SNU: Complex128,
    CSV: Float64,
    SNV: Complex128,
    CSQ: Float64,
    SNQ: Complex128
) -> None: ...

@bind("ZLAGTM")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def zlagtm(
    TRANS: String[1],
    N: Int32,
    NRHS: Int32,
    ALPHA: Float64,
    DL: Complex128[Flat],
    D: Complex128[Flat],
    DU: Complex128[Flat],
    X: Complex128[LDX, Flat],
    LDX: Int32,
    BETA: Float64,
    B: Complex128[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("ZLAHEF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def zlahef(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    W: Complex128[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLAHEF_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9)])
def zlahef_aa(
    UPLO: String[1],
    J1: Int32,
    M: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    H: Complex128[LDH, Flat],
    LDH: Int32,
    WORK: Complex128[Flat]
) -> None: ...

@bind("ZLAHEF_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zlahef_rk(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    W: Complex128[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLAHEF_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def zlahef_rook(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    W: Complex128[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLAHQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zlahqr(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Complex128[LDH, Flat],
    LDH: Int32,
    W: Complex128[Flat],
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLAHR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def zlahr2(
    N: Int32,
    K: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[NB],
    T: Complex128[LDT, NB],
    LDT: Int32,
    Y: Complex128[LDY, NB],
    LDY: Int32
) -> None: ...

@bind("ZLAIC1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8))])
def zlaic1(
    JOB: Int32,
    J: Int32,
    X: Complex128[J],
    SEST: Float64,
    W: Complex128[J],
    GAMMA: Complex128,
    SESTPR: Float64,
    S: Complex128,
    C: Complex128
) -> None: ...

@bind("ZLALS0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19)), Addr(Arg(20)), Addr(Arg(21)), Arg(22), Addr(Arg(23))])
def zlals0(
    ICOMPQ: Int32,
    NL: Int32,
    NR: Int32,
    SQRE: Int32,
    NRHS: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    BX: Complex128[LDBX, Flat],
    LDBX: Int32,
    PERM: Int32[Flat],
    GIVPTR: Int32,
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    GIVNUM: Float64[LDGNUM, Flat],
    LDGNUM: Int32,
    POLES: Float64[LDGNUM, Flat],
    DIFL: Float64[Flat],
    DIFR: Float64[LDGNUM, Flat],
    Z: Float64[Flat],
    K: Int32,
    C: Float64,
    S: Float64,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZLALSA")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Arg(22), Arg(23), Arg(24), Addr(Arg(25))])
def zlalsa(
    ICOMPQ: Int32,
    SMLSIZ: Int32,
    N: Int32,
    NRHS: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    BX: Complex128[LDBX, Flat],
    LDBX: Int32,
    U: Float64[LDU, Flat],
    LDU: Int32,
    VT: Float64[LDU, Flat],
    K: Int32[Flat],
    DIFL: Float64[LDU, Flat],
    DIFR: Float64[LDU, Flat],
    Z: Float64[LDU, Flat],
    POLES: Float64[LDU, Flat],
    GIVPTR: Int32[Flat],
    GIVCOL: Int32[LDGCOL, Flat],
    LDGCOL: Int32,
    PERM: Int32[LDGCOL, Flat],
    GIVNUM: Float64[LDU, Flat],
    C: Float64[Flat],
    S: Float64[Flat],
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZLALSD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def zlalsd(
    UPLO: String[1],
    SMLSIZ: Int32,
    N: Int32,
    NRHS: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    RCOND: Float64,
    RANK: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZLAMSWLQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def zlamswlq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    MB: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLAMTSQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def zlamtsqr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    MB: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLANGB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def zlangb(
    NORM: String[1],
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLANGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def zlange(
    NORM: String[1],
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLANGT")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4)])
def zlangt(
    NORM: String[1],
    N: Int32,
    DL: Complex128[Flat],
    D: Complex128[Flat],
    DU: Complex128[Flat]
) -> Float64: ...

@bind("ZLANHB")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def zlanhb(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    K: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLANHE")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def zlanhe(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLANHF")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5)])
def zlanhf(
    NORM: String[1],
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[Flat],
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLANHP")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4)])
def zlanhp(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLANHS")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4)])
def zlanhs(
    NORM: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLANHT")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3)])
def zlanht(
    NORM: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Complex128[Flat]
) -> Float64: ...

@bind("ZLANSB")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6)])
def zlansb(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    K: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLANSP")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4)])
def zlansp(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLANSY")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def zlansy(
    NORM: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLANTB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def zlantb(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    K: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLANTP")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5)])
def zlantp(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    AP: Complex128[Flat],
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLANTR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def zlantr(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    WORK: Float64[Flat]
) -> Float64: ...

@bind("ZLAPLL")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def zlapll(
    N: Int32,
    X: Complex128[Flat],
    INCX: Int32,
    Y: Complex128[Flat],
    INCY: Int32,
    SSMIN: Float64
) -> None: ...

@bind("ZLAPMR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def zlapmr(
    FORWRD: Bool,
    M: Int32,
    N: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    K: Int32[Flat]
) -> None: ...

@bind("ZLAPMT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def zlapmt(
    FORWRD: Bool,
    M: Int32,
    N: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    K: Int32[Flat]
) -> None: ...

@bind("ZLAQGB")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11)])
def zlaqgb(
    M: Int32,
    N: Int32,
    KL: Int32,
    KU: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    R: Float64[Flat],
    C: Float64[Flat],
    ROWCND: Float64,
    COLCND: Float64,
    AMAX: Float64,
    EQUED: String[1]
) -> None: ...

@bind("ZLAQGE")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9)])
def zlaqge(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    R: Float64[Flat],
    C: Float64[Flat],
    ROWCND: Float64,
    COLCND: Float64,
    AMAX: Float64,
    EQUED: String[1]
) -> None: ...

@bind("ZLAQHB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8)])
def zlaqhb(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    EQUED: String[1]
) -> None: ...

@bind("ZLAQHE")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7)])
def zlaqhe(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    EQUED: String[1]
) -> None: ...

@bind("ZLAQHP")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6)])
def zlaqhp(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    EQUED: String[1]
) -> None: ...

@bind("ZLAQP2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Arg(8), Arg(9)])
def zlaqp2(
    M: Int32,
    N: Int32,
    OFFSET: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    JPVT: Int32[Flat],
    TAU: Complex128[Flat],
    VN1: Float64[Flat],
    VN2: Float64[Flat],
    WORK: Complex128[Flat]
) -> None: ...

@bind("ZLAQP2RK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def zlaqp2rk(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    IOFFSET: Int32,
    KMAX: Int32,
    ABSTOL: Float64,
    RELTOL: Float64,
    KP1: Int32,
    MAXC2NRM: Float64,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    K: Int32,
    MAXC2NRMK: Float64,
    RELMAXC2NRMK: Float64,
    JPIV: Int32[Flat],
    TAU: Complex128[Flat],
    VN1: Float64[Flat],
    VN2: Float64[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZLAQP3RK")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23))])
def zlaqp3rk(
    M: Int32,
    N: Int32,
    NRHS: Int32,
    IOFFSET: Int32,
    NB: Int32,
    ABSTOL: Float64,
    RELTOL: Float64,
    KP1: Int32,
    MAXC2NRM: Float64,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    DONE: Bool,
    KB: Int32,
    MAXC2NRMK: Float64,
    RELMAXC2NRMK: Float64,
    JPIV: Int32[Flat],
    TAU: Complex128[Flat],
    VN1: Float64[Flat],
    VN2: Float64[Flat],
    AUXV: Complex128[Flat],
    F: Complex128[LDF, Flat],
    LDF: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZLAQPS")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def zlaqps(
    M: Int32,
    N: Int32,
    OFFSET: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    JPVT: Int32[Flat],
    TAU: Complex128[Flat],
    VN1: Float64[Flat],
    VN2: Float64[Flat],
    AUXV: Complex128[Flat],
    F: Complex128[LDF, Flat],
    LDF: Int32
) -> None: ...

@bind("ZLAQR0")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def zlaqr0(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Complex128[LDH, Flat],
    LDH: Int32,
    W: Complex128[Flat],
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLAQR1")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5)])
def zlaqr1(
    N: Int32,
    H: Complex128[LDH, Flat],
    LDH: Int32,
    S1: Complex128,
    S2: Complex128,
    V: Complex128[Flat]
) -> None: ...

@bind("ZLAQR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Addr(Arg(20)), Arg(21), Addr(Arg(22)), Arg(23), Addr(Arg(24))])
def zlaqr2(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    KTOP: Int32,
    KBOT: Int32,
    NW: Int32,
    H: Complex128[LDH, Flat],
    LDH: Int32,
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    NS: Int32,
    ND: Int32,
    SH: Complex128[Flat],
    V: Complex128[LDV, Flat],
    LDV: Int32,
    NH: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    NV: Int32,
    WV: Complex128[LDWV, Flat],
    LDWV: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32
) -> None: ...

@bind("ZLAQR3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Addr(Arg(20)), Arg(21), Addr(Arg(22)), Arg(23), Addr(Arg(24))])
def zlaqr3(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    KTOP: Int32,
    KBOT: Int32,
    NW: Int32,
    H: Complex128[LDH, Flat],
    LDH: Int32,
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    NS: Int32,
    ND: Int32,
    SH: Complex128[Flat],
    V: Complex128[LDV, Flat],
    LDV: Int32,
    NH: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    NV: Int32,
    WV: Complex128[LDWV, Flat],
    LDWV: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32
) -> None: ...

@bind("ZLAQR4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def zlaqr4(
    WANTT: Bool,
    WANTZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    H: Complex128[LDH, Flat],
    LDH: Int32,
    W: Complex128[Flat],
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLAQR5")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Addr(Arg(21)), Arg(22), Addr(Arg(23))])
def zlaqr5(
    WANTT: Bool,
    WANTZ: Bool,
    KACC22: Int32,
    N: Int32,
    KTOP: Int32,
    KBOT: Int32,
    NSHFTS: Int32,
    S: Complex128[Flat],
    H: Complex128[LDH, Flat],
    LDH: Int32,
    ILOZ: Int32,
    IHIZ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    U: Complex128[LDU, Flat],
    LDU: Int32,
    NV: Int32,
    WV: Complex128[LDWV, Flat],
    LDWV: Int32,
    NH: Int32,
    WH: Complex128[LDWH, Flat],
    LDWH: Int32
) -> None: ...

@bind("ZLAQSB")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8)])
def zlaqsb(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    EQUED: String[1]
) -> None: ...

@bind("ZLAQSP")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6)])
def zlaqsp(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    EQUED: String[1]
) -> None: ...

@bind("ZLAQSY")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7)])
def zlaqsy(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    EQUED: String[1]
) -> None: ...

@bind("ZLAQZ0")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Return('INFO', 0)])
def zlaqz0(
    WANTS: String[1],
    WANTQ: String[1],
    WANTZ: String[1],
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    ALPHA: Complex128[Flat],
    BETA: Complex128[Flat],
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    REC: Int32
) -> Int32: ...

@bind("ZLAQZ1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def zlaqz1(
    ILQ: Bool,
    ILZ: Bool,
    K: Int32,
    ISTARTM: Int32,
    ISTOPM: Int32,
    IHI: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    NQ: Int32,
    QSTART: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    NZ: Int32,
    ZSTART: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32
) -> None: ...

@bind("ZLAQZ2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Return('NS', 0), Return('ND', 1), Arg(15), Arg(16), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Arg(21), Addr(Arg(22)), Arg(23), Addr(Arg(24)), Return('INFO', 2)])
def zlaqz2(
    ILSCHUR: Bool,
    ILQ: Bool,
    ILZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    NW: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    ALPHA: Complex128[Flat],
    BETA: Complex128[Flat],
    QC: Complex128[LDQC, Flat],
    LDQC: Int32,
    ZC: Complex128[LDZC, Flat],
    LDZC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    REC: Int32
) -> tuple[Int32, Int32, Int32]: ...

@bind("ZLAQZ3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Return('INFO', 0)])
def zlaqz3(
    ILSCHUR: Bool,
    ILQ: Bool,
    ILZ: Bool,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    NSHIFTS: Int32,
    NBLOCK_DESIRED: Int32,
    ALPHA: Complex128[Flat],
    BETA: Complex128[Flat],
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    QC: Complex128[LDQC, Flat],
    LDQC: Int32,
    ZC: Complex128[LDZC, Flat],
    LDZC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32
) -> Int32: ...

@bind("ZLAR1V")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Addr(Arg(18)), Addr(Arg(19)), Arg(20)])
def zlar1v(
    N: Int32,
    B1: Int32,
    BN: Int32,
    LAMBDA: Float64,
    D: Float64[Flat],
    L: Float64[Flat],
    LD: Float64[Flat],
    LLD: Float64[Flat],
    PIVMIN: Float64,
    GAPTOL: Float64,
    Z: Complex128[Flat],
    WANTNC: Bool,
    NEGCNT: Int32,
    ZTZ: Float64,
    MINGMA: Float64,
    R: Int32,
    ISUPPZ: Int32[Flat],
    NRMINV: Float64,
    RESID: Float64,
    RQCORR: Float64,
    WORK: Float64[Flat]
) -> None: ...

@bind("ZLAR2V")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def zlar2v(
    N: Int32,
    X: Complex128[Flat],
    Y: Complex128[Flat],
    Z: Complex128[Flat],
    INCX: Int32,
    C: Float64[Flat],
    S: Complex128[Flat],
    INCC: Int32
) -> None: ...

@bind("ZLARCM")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def zlarcm(
    M: Int32,
    N: Int32,
    A: Float64[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    RWORK: Float64[Flat]
) -> None: ...

@bind("ZLARF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def zlarf(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Complex128[Flat],
    INCV: Int32,
    TAU: Complex128,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat]
) -> None: ...

@bind("ZLARF1F")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def zlarf1f(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Complex128[Flat],
    INCV: Int32,
    TAU: Complex128,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat]
) -> None: ...

@bind("ZLARF1L")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8)])
def zlarf1l(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Complex128[Flat],
    INCV: Int32,
    TAU: Complex128,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat]
) -> None: ...

@bind("ZLARFB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14))])
def zlarfb(
    SIDE: String[1],
    TRANS: String[1],
    DIRECT: String[1],
    STOREV: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("ZLARFB_GETT")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def zlarfb_gett(
    IDENT: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("ZLARFG")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def zlarfg(
    N: Int32,
    ALPHA: Complex128,
    X: Complex128[Flat],
    INCX: Int32,
    TAU: Complex128
) -> None: ...

@bind("ZLARFGP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def zlarfgp(
    N: Int32,
    ALPHA: Complex128,
    X: Complex128[Flat],
    INCX: Int32,
    TAU: Complex128
) -> None: ...

@bind("ZLARFT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def zlarft(
    DIRECT: String[1],
    STOREV: String[1],
    N: Int32,
    K: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    TAU: Complex128[Flat],
    T: Complex128[LDT, Flat],
    LDT: Int32
) -> None: ...

@bind("ZLARFX")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def zlarfx(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    V: Complex128[Flat],
    TAU: Complex128,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat]
) -> None: ...

@bind("ZLARFY")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7)])
def zlarfy(
    UPLO: String[1],
    N: Int32,
    V: Complex128[Flat],
    INCV: Int32,
    TAU: Complex128,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat]
) -> None: ...

@bind("ZLARGV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def zlargv(
    N: Int32,
    X: Complex128[Flat],
    INCX: Int32,
    Y: Complex128[Flat],
    INCY: Int32,
    C: Float64[Flat],
    INCC: Int32
) -> None: ...

@bind("ZLARNV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3)])
def zlarnv(
    IDIST: Int32,
    ISEED: Int32[4],
    N: Int32,
    X: Complex128[Flat]
) -> None: ...

@bind("ZLARRV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def zlarrv(
    N: Int32,
    VL: Float64,
    VU: Float64,
    D: Float64[Flat],
    L: Float64[Flat],
    PIVMIN: Float64,
    ISPLIT: Int32[Flat],
    M: Int32,
    DOL: Int32,
    DOU: Int32,
    MINRGP: Float64,
    RTOL1: Float64,
    RTOL2: Float64,
    W: Float64[Flat],
    WERR: Float64[Flat],
    WGAP: Float64[Flat],
    IBLOCK: Int32[Flat],
    INDEXW: Int32[Flat],
    GERS: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZLARSCL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def zlarscl2(
    M: Int32,
    N: Int32,
    D: Float64[Flat],
    X: Complex128[LDX, Flat],
    LDX: Int32
) -> None: ...

@bind("ZLARTG")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def zlartg(
    f: Complex128,
    g: Complex128,
    c: Float64,
    s: Complex128,
    r: Complex128
) -> None: ...

@bind("ZLARTV")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def zlartv(
    N: Int32,
    X: Complex128[Flat],
    INCX: Int32,
    Y: Complex128[Flat],
    INCY: Int32,
    C: Float64[Flat],
    S: Complex128[Flat],
    INCC: Int32
) -> None: ...

@bind("ZLARZ")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9)])
def zlarz(
    SIDE: String[1],
    M: Int32,
    N: Int32,
    L: Int32,
    V: Complex128[Flat],
    INCV: Int32,
    TAU: Complex128,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat]
) -> None: ...

@bind("ZLARZB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15))])
def zlarzb(
    SIDE: String[1],
    TRANS: String[1],
    DIRECT: String[1],
    STOREV: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("ZLARZT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def zlarzt(
    DIRECT: String[1],
    STOREV: String[1],
    N: Int32,
    K: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    TAU: Complex128[Flat],
    T: Complex128[LDT, Flat],
    LDT: Int32
) -> None: ...

@bind("ZLASCL")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def zlascl(
    TYPE: String[1],
    KL: Int32,
    KU: Int32,
    CFROM: Float64,
    CTO: Float64,
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLASCL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def zlascl2(
    M: Int32,
    N: Int32,
    D: Float64[Flat],
    X: Complex128[LDX, Flat],
    LDX: Int32
) -> None: ...

@bind("ZLASET")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def zlaset(
    UPLO: String[1],
    M: Int32,
    N: Int32,
    ALPHA: Complex128,
    BETA: Complex128,
    A: Complex128[LDA, Flat],
    LDA: Int32
) -> None: ...

@bind("ZLASR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8))])
def zlasr(
    SIDE: String[1],
    PIVOT: String[1],
    DIRECT: String[1],
    M: Int32,
    N: Int32,
    C: Float64[Flat],
    S: Float64[Flat],
    A: Complex128[LDA, Flat],
    LDA: Int32
) -> None: ...

@bind("ZLASSQ")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4))])
def zlassq(
    n: Int32,
    x: Complex128[Flat],
    incx: Int32,
    scale: Float64,
    sumsq: Float64
) -> None: ...

@bind("ZLASWLQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zlaswlq(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLASWP")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def zlaswp(
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    K1: Int32,
    K2: Int32,
    IPIV: Int32[Flat],
    INCX: Int32
) -> None: ...

@bind("ZLASYF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def zlasyf(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    W: Complex128[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLASYF_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Arg(9)])
def zlasyf_aa(
    UPLO: String[1],
    J1: Int32,
    M: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    H: Complex128[LDH, Flat],
    LDH: Int32,
    WORK: Complex128[Flat]
) -> None: ...

@bind("ZLASYF_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zlasyf_rk(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    W: Complex128[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLASYF_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def zlasyf_rook(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    KB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    W: Complex128[LDW, Flat],
    LDW: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLAT2C")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def zlat2c(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    SA: Complex64[LDSA, Flat],
    LDSA: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLATBS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def zlatbs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    X: Complex128[Flat],
    SCALE: Float64,
    CNORM: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZLATDF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8)])
def zlatdf(
    IJOB: Int32,
    N: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    RHS: Complex128[Flat],
    RDSUM: Float64,
    RDSCAL: Float64,
    IPIV: Int32[Flat],
    JPIV: Int32[Flat]
) -> None: ...

@bind("ZLATPS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def zlatps(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    AP: Complex128[Flat],
    X: Complex128[Flat],
    SCALE: Float64,
    CNORM: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZLATRD")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8))])
def zlatrd(
    UPLO: String[1],
    N: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Float64[Flat],
    TAU: Complex128[Flat],
    W: Complex128[LDW, Flat],
    LDW: Int32
) -> None: ...

@bind("ZLATRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def zlatrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    X: Complex128[Flat],
    SCALE: Float64,
    CNORM: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZLATRS3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def zlatrs3(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    NORMIN: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    SCALE: Float64[Flat],
    CNORM: Float64[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLATRZ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6)])
def zlatrz(
    M: Int32,
    N: Int32,
    L: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat]
) -> None: ...

@bind("ZLATSQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zlatsqr(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLAUNHR_COL_GETRFNP")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def zlaunhr_col_getrfnp(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    D: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZLAUNHR_COL_GETRFNP2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def zlaunhr_col_getrfnp2(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    D: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZLAUU2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def zlauu2(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("ZLAUUM")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def zlauum(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPBCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def zpbcon(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPBEQU")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8))])
def zpbequ(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("ZPBRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def zpbrfs(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex128[LDAFB, Flat],
    LDAFB: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPBSTF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def zpbstf(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPBSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zpbsv(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPBSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20))])
def zpbsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    AFB: Complex128[LDAFB, Flat],
    LDAFB: Int32,
    EQUED: String[1],
    S: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPBTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def zpbtf2(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPBTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def zpbtrf(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPBTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zpbtrs(
    UPLO: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPFTRF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4))])
def zpftrf(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPFTRI")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4))])
def zpftri(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPFTRS")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zpftrs(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPOCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def zpocon(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPOEQU")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def zpoequ(
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("ZPOEQUB")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def zpoequb(
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("ZPORFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15))])
def zporfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPORFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Arg(21), Addr(Arg(22))])
def zporfsx(
    UPLO: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    S: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPOSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zposv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPOSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Arg(16), Arg(17), Arg(18), Addr(Arg(19))])
def zposvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    EQUED: String[1],
    S: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPOSVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Arg(22), Arg(23), Addr(Arg(24))])
def zposvxx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    EQUED: String[1],
    S: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    RPVGRW: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPOTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def zpotf2(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPOTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def zpotrf(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPOTRF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def zpotrf2(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPOTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4))])
def zpotri(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPOTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zpotrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPPCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def zppcon(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPPEQU")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def zppequ(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    INFO: Int32
) -> None: ...

@bind("ZPPRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13))])
def zpprfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    AFP: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPPSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def zppsv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPPSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Arg(13), Arg(14), Arg(15), Arg(16), Addr(Arg(17))])
def zppsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    AFP: Complex128[Flat],
    EQUED: String[1],
    S: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPPTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def zpptrf(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPPTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def zpptri(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPPTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def zpptrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPSTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def zpstf2(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    PIV: Int32[N],
    RANK: Int32,
    TOL: Float64,
    WORK: Float64[2 * N],
    INFO: Int32
) -> None: ...

@bind("ZPSTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def zpstrf(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    PIV: Int32[N],
    RANK: Int32,
    TOL: Float64,
    WORK: Float64[2 * N],
    INFO: Int32
) -> None: ...

@bind("ZPTCON")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def zptcon(
    N: Int32,
    D: Float64[Flat],
    E: Complex128[Flat],
    ANORM: Float64,
    RCOND: Float64,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPTEQR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def zpteqr(
    COMPZ: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPTRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15))])
def zptrfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    D: Float64[Flat],
    E: Complex128[Flat],
    DF: Float64[Flat],
    EF: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPTSV")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def zptsv(
    N: Int32,
    NRHS: Int32,
    D: Float64[Flat],
    E: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPTSVX")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def zptsvx(
    FACT: String[1],
    N: Int32,
    NRHS: Int32,
    D: Float64[Flat],
    E: Complex128[Flat],
    DF: Float64[Flat],
    EF: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPTTRF")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3))])
def zpttrf(
    N: Int32,
    D: Float64[Flat],
    E: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZPTTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zpttrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    D: Float64[Flat],
    E: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZPTTS2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6))])
def zptts2(
    IUPLO: Int32,
    N: Int32,
    NRHS: Int32,
    D: Float64[Flat],
    E: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("ZROT")
@external
@native_call([Addr(Arg(0)), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6))])
def zrot(
    N: Int32,
    CX: Complex128[Flat],
    INCX: Int32,
    CY: Complex128[Flat],
    INCY: Int32,
    C: Float64,
    S: Complex128
) -> None: ...

@bind("ZRSCL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3))])
def zrscl(
    N: Int32,
    A: Complex128,
    X: Complex128[Flat],
    INCX: Int32
) -> None: ...

@bind("ZSPCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def zspcon(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSPMV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def zspmv(
    UPLO: String[1],
    N: Int32,
    ALPHA: Complex128,
    AP: Complex128[Flat],
    X: Complex128[Flat],
    INCX: Int32,
    BETA: Complex128,
    Y: Complex128[Flat],
    INCY: Int32
) -> None: ...

@bind("ZSPR")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5)])
def zspr(
    UPLO: String[1],
    N: Int32,
    ALPHA: Complex128,
    X: Complex128[Flat],
    INCX: Int32,
    AP: Complex128[Flat]
) -> None: ...

@bind("ZSPRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14))])
def zsprfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    AFP: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSPSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zspsv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSPSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def zspsvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    AFP: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSPTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4))])
def zsptrf(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSPTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5))])
def zsptri(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSPTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zsptrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSTEDC")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zstedc(
    COMPZ: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSTEGR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Addr(Arg(10)), Arg(11), Arg(12), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Addr(Arg(19))])
def zstegr(
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    ABSTOL: Float64,
    M: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    ISUPPZ: Int32[Flat],
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSTEIN")
@external
@native_call([Addr(Arg(0)), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12))])
def zstein(
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    M: Int32,
    W: Float64[Flat],
    IBLOCK: Int32[Flat],
    ISPLIT: Int32[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    IWORK: Int32[Flat],
    IFAIL: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSTEMR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Addr(Arg(20))])
def zstemr(
    JOBZ: String[1],
    RANGE: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    VL: Float64,
    VU: Float64,
    IL: Int32,
    IU: Int32,
    M: Int32,
    W: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    NZC: Int32,
    ISUPPZ: Int32[Flat],
    TRYRAC: Bool,
    WORK: Float64[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSTEQR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def zsteqr(
    COMPZ: String[1],
    N: Int32,
    D: Float64[Flat],
    E: Float64[Flat],
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    WORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYCON")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def zsycon(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYCON_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def zsycon_3(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYCON_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def zsycon_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    ANORM: Float64,
    RCOND: Float64,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYCONV")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def zsyconv(
    UPLO: String[1],
    WAY: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    E: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYCONVF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def zsyconvf(
    UPLO: String[1],
    WAY: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYCONVF_ROOK")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def zsyconvf_rook(
    UPLO: String[1],
    WAY: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYEQUB")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def zsyequb(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    S: Float64[Flat],
    SCOND: Float64,
    AMAX: Float64,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYMV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def zsymv(
    UPLO: String[1],
    N: Int32,
    ALPHA: Complex128,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    X: Complex128[Flat],
    INCX: Int32,
    BETA: Complex128,
    Y: Complex128[Flat],
    INCY: Int32
) -> None: ...

@bind("ZSYR")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def zsyr(
    UPLO: String[1],
    N: Int32,
    ALPHA: Complex128,
    X: Complex128[Flat],
    INCX: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32
) -> None: ...

@bind("ZSYRFS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def zsyrfs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYRFSX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Arg(21), Arg(22), Addr(Arg(23))])
def zsyrfsx(
    UPLO: String[1],
    EQUED: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    S: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYSV")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zsysv(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYSV_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zsysv_aa(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYSV_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zsysv_aa_2stage(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TB: Complex128[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYSV_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def zsysv_rk(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYSV_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zsysv_rook(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYSVX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def zsysvx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYSVXX")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Arg(20), Addr(Arg(21)), Arg(22), Arg(23), Arg(24), Addr(Arg(25))])
def zsysvxx(
    FACT: String[1],
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AF: Complex128[LDAF, Flat],
    LDAF: Int32,
    IPIV: Int32[Flat],
    EQUED: String[1],
    S: Float64[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    RCOND: Float64,
    RPVGRW: Float64,
    BERR: Float64[Flat],
    N_ERR_BNDS: Int32,
    ERR_BNDS_NORM: Float64[NRHS, Flat],
    ERR_BNDS_COMP: Float64[NRHS, Flat],
    NPARAMS: Int32,
    PARAMS: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYSWAPR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5))])
def zsyswapr(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    I1: Int32,
    I2: Int32
) -> None: ...

@bind("ZSYTF2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def zsytf2(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYTF2_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def zsytf2_rk(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYTF2_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def zsytf2_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYTRF")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zsytrf(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYTRF_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zsytrf_aa(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYTRF_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zsytrf_aa_2stage(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TB: Complex128[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYTRF_RK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zsytrf_rk(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYTRF_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zsytrf_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYTRI")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def zsytri(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYTRI2")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zsytri2(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYTRI2X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zsytri2x(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[N + NB + 1, Flat],
    NB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYTRI_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zsytri_3(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYTRI_3X")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zsytri_3x(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    WORK: Complex128[N + NB + 1, Flat],
    NB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYTRI_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6))])
def zsytri_rook(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYTRS")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zsytrs(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYTRS2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9))])
def zsytrs2(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZSYTRS_3")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def zsytrs_3(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    E: Complex128[Flat],
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYTRS_AA")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zsytrs_aa(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYTRS_AA_2STAGE")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Addr(Arg(10)), Addr(Arg(11))])
def zsytrs_aa_2stage(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TB: Complex128[Flat],
    LTB: Int32,
    IPIV: Int32[Flat],
    IPIV2: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZSYTRS_ROOK")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zsytrs_rook(
    UPLO: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    IPIV: Int32[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTBCON")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def ztbcon(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    KD: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    RCOND: Float64,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTBRFS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Arg(14), Arg(15), Addr(Arg(16))])
def ztbrfs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTBTRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def ztbtrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    KD: Int32,
    NRHS: Int32,
    AB: Complex128[LDAB, Flat],
    LDAB: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTFSM")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10))])
def ztfsm(
    TRANSR: String[1],
    SIDE: String[1],
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    M: Int32,
    N: Int32,
    ALPHA: Complex128,
    A: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32
) -> None: ...

@bind("ZTFTRI")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def ztftri(
    TRANSR: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTFTTP")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def ztfttp(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    ARF: Complex128[Flat],
    AP: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTFTTR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5)), Addr(Arg(6))])
def ztfttr(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    ARF: Complex128[Flat],
    A: Complex128[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTGEVC")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Addr(Arg(16))])
def ztgevc(
    SIDE: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    S: Complex128[LDS, Flat],
    LDS: Int32,
    P: Complex128[LDP, Flat],
    LDP: Int32,
    VL: Complex128[LDVL, Flat],
    LDVL: Int32,
    VR: Complex128[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTGEX2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12))])
def ztgex2(
    WANTQ: Bool,
    WANTZ: Bool,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    J1: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTGEXC")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13))])
def ztgexc(
    WANTQ: Bool,
    WANTZ: Bool,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    IFST: Int32,
    ILST: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTGSEN")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Arg(19), Addr(Arg(20)), Arg(21), Addr(Arg(22)), Addr(Arg(23))])
def ztgsen(
    IJOB: Int32,
    WANTQ: Bool,
    WANTZ: Bool,
    SELECT: Bool[Flat],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    ALPHA: Complex128[Flat],
    BETA: Complex128[Flat],
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    Z: Complex128[LDZ, Flat],
    LDZ: Int32,
    M: Int32,
    PL: Float64,
    PR: Float64,
    DIF: Float64[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    LIWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTGSJA")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Arg(15), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Addr(Arg(24))])
def ztgsja(
    JOBU: String[1],
    JOBV: String[1],
    JOBQ: String[1],
    M: Int32,
    P: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    TOLA: Float64,
    TOLB: Float64,
    ALPHA: Float64[Flat],
    BETA: Float64[Flat],
    U: Complex128[LDU, Flat],
    LDU: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    WORK: Complex128[Flat],
    NCYCLE: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTGSNA")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14)), Addr(Arg(15)), Arg(16), Addr(Arg(17)), Arg(18), Addr(Arg(19))])
def ztgsna(
    JOB: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    VL: Complex128[LDVL, Flat],
    LDVL: Int32,
    VR: Complex128[LDVR, Flat],
    LDVR: Int32,
    S: Float64[Flat],
    DIF: Float64[Flat],
    MM: Int32,
    M: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTGSY2")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Addr(Arg(18)), Addr(Arg(19))])
def ztgsy2(
    TRANS: String[1],
    IJOB: Int32,
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    D: Complex128[LDD, Flat],
    LDD: Int32,
    E: Complex128[LDE, Flat],
    LDE: Int32,
    F: Complex128[LDF, Flat],
    LDF: Int32,
    SCALE: Float64,
    RDSUM: Float64,
    RDSCAL: Float64,
    INFO: Int32
) -> None: ...

@bind("ZTGSYL")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16)), Addr(Arg(17)), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21))])
def ztgsyl(
    TRANS: String[1],
    IJOB: Int32,
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    D: Complex128[LDD, Flat],
    LDD: Int32,
    E: Complex128[LDE, Flat],
    LDE: Int32,
    F: Complex128[LDF, Flat],
    LDF: Int32,
    SCALE: Float64,
    DIF: Float64,
    WORK: Complex128[Flat],
    LWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTPCON")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8))])
def ztpcon(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    AP: Complex128[Flat],
    RCOND: Float64,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTPLQT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def ztplqt(
    M: Int32,
    N: Int32,
    L: Int32,
    MB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTPLQT2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def ztplqt2(
    M: Int32,
    N: Int32,
    L: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTPMLQT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def ztpmlqt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    MB: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTPMQRT")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16))])
def ztpmqrt(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    NB: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTPQRT")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def ztpqrt(
    M: Int32,
    N: Int32,
    L: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTPQRT2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def ztpqrt2(
    M: Int32,
    N: Int32,
    L: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTPRFB")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def ztprfb(
    SIDE: String[1],
    TRANS: String[1],
    DIRECT: String[1],
    STOREV: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    V: Complex128[LDV, Flat],
    LDV: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    WORK: Complex128[LDWORK, Flat],
    LDWORK: Int32
) -> None: ...

@bind("ZTPRFS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14))])
def ztprfs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTPTRI")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4))])
def ztptri(
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    AP: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTPTRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def ztptrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    AP: Complex128[Flat],
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTPTTF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Arg(4), Addr(Arg(5))])
def ztpttf(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    ARF: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTPTTR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def ztpttr(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    A: Complex128[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTRCON")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9))])
def ztrcon(
    NORM: String[1],
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    RCOND: Float64,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTREVC")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Arg(13), Addr(Arg(14))])
def ztrevc(
    SIDE: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    VL: Complex128[LDVL, Flat],
    LDVL: Int32,
    VR: Complex128[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTREVC3")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Addr(Arg(16))])
def ztrevc3(
    SIDE: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    VL: Complex128[LDVL, Flat],
    LDVL: Int32,
    VR: Complex128[LDVR, Flat],
    LDVR: Int32,
    MM: Int32,
    M: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTREXC")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8))])
def ztrexc(
    COMPQ: String[1],
    N: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    IFST: Int32,
    ILST: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTRRFS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Arg(12), Arg(13), Arg(14), Addr(Arg(15))])
def ztrrfs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    X: Complex128[LDX, Flat],
    LDX: Int32,
    FERR: Float64[Flat],
    BERR: Float64[Flat],
    WORK: Complex128[Flat],
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTRSEN")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def ztrsen(
    JOB: String[1],
    COMPQ: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    W: Complex128[Flat],
    M: Int32,
    S: Float64,
    SEP: Float64,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTRSNA")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Addr(Arg(13)), Arg(14), Addr(Arg(15)), Arg(16), Addr(Arg(17))])
def ztrsna(
    JOB: String[1],
    HOWMNY: String[1],
    SELECT: Bool[Flat],
    N: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    VL: Complex128[LDVL, Flat],
    LDVL: Int32,
    VR: Complex128[LDVR, Flat],
    LDVR: Int32,
    S: Float64[Flat],
    SEP: Float64[Flat],
    MM: Int32,
    M: Int32,
    WORK: Complex128[LDWORK, Flat],
    LDWORK: Int32,
    RWORK: Float64[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTRSYL")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Addr(Arg(12))])
def ztrsyl(
    TRANA: String[1],
    TRANB: String[1],
    ISGN: Int32,
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    SCALE: Float64,
    INFO: Int32
) -> None: ...

@bind("ZTRSYL3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Addr(Arg(11)), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def ztrsyl3(
    TRANA: String[1],
    TRANB: String[1],
    ISGN: Int32,
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    SCALE: Float64,
    SWORK: Float64[LDSWORK, Flat],
    LDSWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTRTI2")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def ztrti2(
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTRTRI")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Addr(Arg(5))])
def ztrtri(
    UPLO: String[1],
    DIAG: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTRTRS")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def ztrtrs(
    UPLO: String[1],
    TRANS: String[1],
    DIAG: String[1],
    N: Int32,
    NRHS: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    B: Complex128[LDB, Flat],
    LDB: Int32,
    INFO: Int32
) -> None: ...

@bind("ZTRTTF")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6))])
def ztrttf(
    TRANSR: String[1],
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    ARF: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTRTTP")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Addr(Arg(5))])
def ztrttp(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    AP: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZTZRZF")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def ztzrzf(
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNBDB")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Arg(14), Arg(15), Arg(16), Arg(17), Arg(18), Arg(19), Addr(Arg(20)), Addr(Arg(21))])
def zunbdb(
    TRANS: String[1],
    SIGNS: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex128[LDX11, Flat],
    LDX11: Int32,
    X12: Complex128[LDX12, Flat],
    LDX12: Int32,
    X21: Complex128[LDX21, Flat],
    LDX21: Int32,
    X22: Complex128[LDX22, Flat],
    LDX22: Int32,
    THETA: Float64[Flat],
    PHI: Float64[Flat],
    TAUP1: Complex128[Flat],
    TAUP2: Complex128[Flat],
    TAUQ1: Complex128[Flat],
    TAUQ2: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNBDB1")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def zunbdb1(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex128[LDX11, Flat],
    LDX11: Int32,
    X21: Complex128[LDX21, Flat],
    LDX21: Int32,
    THETA: Float64[Flat],
    PHI: Float64[Flat],
    TAUP1: Complex128[Flat],
    TAUP2: Complex128[Flat],
    TAUQ1: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNBDB2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def zunbdb2(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex128[LDX11, Flat],
    LDX11: Int32,
    X21: Complex128[LDX21, Flat],
    LDX21: Int32,
    THETA: Float64[Flat],
    PHI: Float64[Flat],
    TAUP1: Complex128[Flat],
    TAUP2: Complex128[Flat],
    TAUQ1: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNBDB3")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Addr(Arg(13)), Addr(Arg(14))])
def zunbdb3(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex128[LDX11, Flat],
    LDX11: Int32,
    X21: Complex128[LDX21, Flat],
    LDX21: Int32,
    THETA: Float64[Flat],
    PHI: Float64[Flat],
    TAUP1: Complex128[Flat],
    TAUP2: Complex128[Flat],
    TAUQ1: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNBDB4")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Arg(9), Arg(10), Arg(11), Arg(12), Arg(13), Addr(Arg(14)), Addr(Arg(15))])
def zunbdb4(
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex128[LDX11, Flat],
    LDX11: Int32,
    X21: Complex128[LDX21, Flat],
    LDX21: Int32,
    THETA: Float64[Flat],
    PHI: Float64[Flat],
    TAUP1: Complex128[Flat],
    TAUP2: Complex128[Flat],
    TAUQ1: Complex128[Flat],
    PHANTOM: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNBDB5")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zunbdb5(
    M1: Int32,
    M2: Int32,
    N: Int32,
    X1: Complex128[Flat],
    INCX1: Int32,
    X2: Complex128[Flat],
    INCX2: Int32,
    Q1: Complex128[LDQ1, Flat],
    LDQ1: Int32,
    Q2: Complex128[LDQ2, Flat],
    LDQ2: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNBDB6")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zunbdb6(
    M1: Int32,
    M2: Int32,
    N: Int32,
    X1: Complex128[Flat],
    INCX1: Int32,
    X2: Complex128[Flat],
    INCX2: Int32,
    Q1: Complex128[LDQ1, Flat],
    LDQ1: Int32,
    Q2: Complex128[LDQ2, Flat],
    LDQ2: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNCSD")
@external
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7)), Addr(Arg(8)), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Arg(18), Addr(Arg(19)), Arg(20), Addr(Arg(21)), Arg(22), Addr(Arg(23)), Arg(24), Addr(Arg(25)), Arg(26), Addr(Arg(27)), Arg(28), Addr(Arg(29)), Arg(30), Addr(Arg(31))])
def zuncsd(
    JOBU1: String[1],
    JOBU2: String[1],
    JOBV1T: String[1],
    JOBV2T: String[1],
    TRANS: String[1],
    SIGNS: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex128[LDX11, Flat],
    LDX11: Int32,
    X12: Complex128[LDX12, Flat],
    LDX12: Int32,
    X21: Complex128[LDX21, Flat],
    LDX21: Int32,
    X22: Complex128[LDX22, Flat],
    LDX22: Int32,
    THETA: Float64[Flat],
    U1: Complex128[LDU1, Flat],
    LDU1: Int32,
    U2: Complex128[LDU2, Flat],
    LDU2: Int32,
    V1T: Complex128[LDV1T, Flat],
    LDV1T: Int32,
    V2T: Complex128[LDV2T, Flat],
    LDV2T: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZUNCSD2BY1")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Arg(11), Addr(Arg(12)), Arg(13), Addr(Arg(14)), Arg(15), Addr(Arg(16)), Arg(17), Addr(Arg(18)), Arg(19), Addr(Arg(20)), Arg(21), Addr(Arg(22))])
def zuncsd2by1(
    JOBU1: String[1],
    JOBU2: String[1],
    JOBV1T: String[1],
    M: Int32,
    P: Int32,
    Q: Int32,
    X11: Complex128[LDX11, Flat],
    LDX11: Int32,
    X21: Complex128[LDX21, Flat],
    LDX21: Int32,
    THETA: Float64[Flat],
    U1: Complex128[LDU1, Flat],
    LDU1: Int32,
    U2: Complex128[LDU2, Flat],
    LDU2: Int32,
    V1T: Complex128[LDV1T, Flat],
    LDV1T: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    RWORK: Float64[Flat],
    LRWORK: Int32,
    IWORK: Int32[Flat],
    INFO: Int32
) -> None: ...

@bind("ZUNG2L")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def zung2l(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZUNG2R")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def zung2r(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZUNGBR")
@external
@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Arg(7), Addr(Arg(8)), Addr(Arg(9))])
def zungbr(
    VECT: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNGHR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zunghr(
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNGL2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def zungl2(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZUNGLQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zunglq(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNGQL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zungql(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNGQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zungqr(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNGR2")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7))])
def zungr2(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZUNGRQ")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Arg(6), Addr(Arg(7)), Addr(Arg(8))])
def zungrq(
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNGTR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Addr(Arg(3)), Arg(4), Arg(5), Addr(Arg(6)), Addr(Arg(7))])
def zungtr(
    UPLO: String[1],
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNGTSQR")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zungtsqr(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNGTSQR_ROW")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Addr(Arg(3)), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Addr(Arg(10))])
def zungtsqr_row(
    M: Int32,
    N: Int32,
    MB: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNHR_COL")
@external
@native_call([Addr(Arg(0)), Addr(Arg(1)), Addr(Arg(2)), Arg(3), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Addr(Arg(8))])
def zunhr_col(
    M: Int32,
    N: Int32,
    NB: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    T: Complex128[LDT, Flat],
    LDT: Int32,
    D: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZUNM22")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zunm22(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    N1: Int32,
    N2: Int32,
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNM2L")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def zunm2l(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZUNM2R")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def zunm2r(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZUNMBR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zunmbr(
    VECT: String[1],
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNMHR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zunmhr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    ILO: Int32,
    IHI: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNML2")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def zunml2(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZUNMLQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zunmlq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNMQL")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zunmql(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNMQR")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zunmqr(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNMR2")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11))])
def zunmr2(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZUNMR3")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12))])
def zunmr3(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZUNMRQ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zunmrq(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNMRZ")
@external
@native_call([Arg(0), Arg(1), Addr(Arg(2)), Addr(Arg(3)), Addr(Arg(4)), Addr(Arg(5)), Arg(6), Addr(Arg(7)), Arg(8), Arg(9), Addr(Arg(10)), Arg(11), Addr(Arg(12)), Addr(Arg(13))])
def zunmrz(
    SIDE: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    K: Int32,
    L: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUNMTR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Addr(Arg(6)), Arg(7), Arg(8), Addr(Arg(9)), Arg(10), Addr(Arg(11)), Addr(Arg(12))])
def zunmtr(
    SIDE: String[1],
    UPLO: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    A: Complex128[LDA, Flat],
    LDA: Int32,
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    LWORK: Int32,
    INFO: Int32
) -> None: ...

@bind("ZUPGTR")
@external
@native_call([Arg(0), Addr(Arg(1)), Arg(2), Arg(3), Arg(4), Addr(Arg(5)), Arg(6), Addr(Arg(7))])
def zupgtr(
    UPLO: String[1],
    N: Int32,
    AP: Complex128[Flat],
    TAU: Complex128[Flat],
    Q: Complex128[LDQ, Flat],
    LDQ: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...

@bind("ZUPMTR")
@external
@native_call([Arg(0), Arg(1), Arg(2), Addr(Arg(3)), Addr(Arg(4)), Arg(5), Arg(6), Arg(7), Addr(Arg(8)), Arg(9), Addr(Arg(10))])
def zupmtr(
    SIDE: String[1],
    UPLO: String[1],
    TRANS: String[1],
    M: Int32,
    N: Int32,
    AP: Complex128[Flat],
    TAU: Complex128[Flat],
    C: Complex128[LDC, Flat],
    LDC: Int32,
    WORK: Complex128[Flat],
    INFO: Int32
) -> None: ...
