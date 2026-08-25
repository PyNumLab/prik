# ruff: noqa

from prik.contracts import Arg, Float32, Float64, Int, Return, Returns, native_call

def TA_Initialize() -> Int: ...
def TA_Shutdown() -> Int: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(6),
        Arg(7),
        Arg(8),
    ]
)
def TA_ACCBANDS(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInTimePeriod: Int,
    outRealUpperBand: Float64[:],
    outRealMiddleBand: Float64[:],
    outRealLowerBand: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(6),
        Arg(7),
        Arg(8),
    ]
)
def TA_S_ACCBANDS(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInTimePeriod: Int,
    outRealUpperBand: Float64[:],
    outRealMiddleBand: Float64[:],
    outRealLowerBand: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_ACOS(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_ACOS(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_AD(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    inVolume: Float64[:],
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_AD(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    inVolume: Float32[:],
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_ADD(
    startIdx: Int, endIdx: Int, inReal0: Float64[:], inReal1: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_ADD(
    startIdx: Int, endIdx: Int, inReal0: Float32[:], inReal1: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Arg(7),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(8),
    ]
)
def TA_ADOSC(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    inVolume: Float64[:],
    optInFastPeriod: Int,
    optInSlowPeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Arg(7),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(8),
    ]
)
def TA_S_ADOSC(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    inVolume: Float32[:],
    optInFastPeriod: Int,
    optInSlowPeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_ADX(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_ADX(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_ADXR(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_ADXR(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_APO(
    startIdx: Int,
    endIdx: Int,
    inReal: Float64[:],
    optInFastPeriod: Int,
    optInSlowPeriod: Int,
    optInMAType: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_APO(
    startIdx: Int,
    endIdx: Int,
    inReal: Float32[:],
    optInFastPeriod: Int,
    optInSlowPeriod: Int,
    optInMAType: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5), Arg(6)]
)
def TA_AROON(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    optInTimePeriod: Int,
    outAroonDown: Float64[:],
    outAroonUp: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5), Arg(6)]
)
def TA_S_AROON(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    optInTimePeriod: Int,
    outAroonDown: Float64[:],
    outAroonUp: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_AROONOSC(
    startIdx: Int, endIdx: Int, inHigh: Float64[:], inLow: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_AROONOSC(
    startIdx: Int, endIdx: Int, inHigh: Float32[:], inLow: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_ASIN(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_ASIN(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_ATAN(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_ATAN(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_ATR(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_ATR(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_AVGDEV(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_AVGDEV(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_AVGPRICE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_AVGPRICE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(7),
        Arg(8),
        Arg(9),
    ]
)
def TA_BBANDS(
    startIdx: Int,
    endIdx: Int,
    inReal: Float64[:],
    optInTimePeriod: Int,
    optInNbDevUp: Float64,
    optInNbDevDn: Float64,
    optInMAType: Int,
    outRealUpperBand: Float64[:],
    outRealMiddleBand: Float64[:],
    outRealLowerBand: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(7),
        Arg(8),
        Arg(9),
    ]
)
def TA_S_BBANDS(
    startIdx: Int,
    endIdx: Int,
    inReal: Float32[:],
    optInTimePeriod: Int,
    optInNbDevUp: Float64,
    optInNbDevDn: Float64,
    optInMAType: Int,
    outRealUpperBand: Float64[:],
    outRealMiddleBand: Float64[:],
    outRealLowerBand: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_BETA(
    startIdx: Int, endIdx: Int, inReal0: Float64[:], inReal1: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_BETA(
    startIdx: Int, endIdx: Int, inReal0: Float32[:], inReal1: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_BOP(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_BOP(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CCI(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CCI(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDL2CROWS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDL2CROWS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDL3BLACKCROWS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDL3BLACKCROWS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDL3INSIDE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDL3INSIDE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDL3LINESTRIKE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDL3LINESTRIKE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDL3OUTSIDE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDL3OUTSIDE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDL3STARSINSOUTH(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDL3STARSINSOUTH(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDL3WHITESOLDIERS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDL3WHITESOLDIERS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_CDLABANDONEDBABY(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_S_CDLABANDONEDBABY(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLADVANCEBLOCK(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLADVANCEBLOCK(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLBELTHOLD(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLBELTHOLD(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLBREAKAWAY(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLBREAKAWAY(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLCLOSINGMARUBOZU(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLCLOSINGMARUBOZU(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLCONCEALBABYSWALL(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLCONCEALBABYSWALL(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLCOUNTERATTACK(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLCOUNTERATTACK(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_CDLDARKCLOUDCOVER(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_S_CDLDARKCLOUDCOVER(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLDOJI(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLDOJI(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLDOJISTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLDOJISTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLDRAGONFLYDOJI(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLDRAGONFLYDOJI(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLENGULFING(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLENGULFING(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_CDLEVENINGDOJISTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_S_CDLEVENINGDOJISTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_CDLEVENINGSTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_S_CDLEVENINGSTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLGAPSIDESIDEWHITE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLGAPSIDESIDEWHITE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLGRAVESTONEDOJI(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLGRAVESTONEDOJI(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLHAMMER(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLHAMMER(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLHANGINGMAN(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLHANGINGMAN(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLHARAMI(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLHARAMI(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLHARAMICROSS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLHARAMICROSS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLHIGHWAVE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLHIGHWAVE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLHIKKAKE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLHIKKAKE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLHIKKAKEMOD(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLHIKKAKEMOD(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLHOMINGPIGEON(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLHOMINGPIGEON(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLIDENTICAL3CROWS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLIDENTICAL3CROWS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLINNECK(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLINNECK(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLINVERTEDHAMMER(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLINVERTEDHAMMER(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLKICKING(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLKICKING(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLKICKINGBYLENGTH(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLKICKINGBYLENGTH(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLLADDERBOTTOM(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLLADDERBOTTOM(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLLONGLEGGEDDOJI(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLLONGLEGGEDDOJI(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLLONGLINE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLLONGLINE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLMARUBOZU(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLMARUBOZU(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLMATCHINGLOW(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLMATCHINGLOW(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_CDLMATHOLD(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_S_CDLMATHOLD(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_CDLMORNINGDOJISTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_S_CDLMORNINGDOJISTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_CDLMORNINGSTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_S_CDLMORNINGSTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInPenetration: Float64,
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLONNECK(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLONNECK(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLPIERCING(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLPIERCING(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLRICKSHAWMAN(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLRICKSHAWMAN(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLRISEFALL3METHODS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLRISEFALL3METHODS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLSEPARATINGLINES(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLSEPARATINGLINES(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLSHOOTINGSTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLSHOOTINGSTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLSHORTLINE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLSHORTLINE(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLSPINNINGTOP(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLSPINNINGTOP(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLSTALLEDPATTERN(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLSTALLEDPATTERN(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLSTICKSANDWICH(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLSTICKSANDWICH(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLTAKURI(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLTAKURI(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLTASUKIGAP(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLTASUKIGAP(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLTHRUSTING(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLTHRUSTING(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLTRISTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLTRISTAR(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLUNIQUE3RIVER(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLUNIQUE3RIVER(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLUPSIDEGAP2CROWS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLUPSIDEGAP2CROWS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_CDLXSIDEGAP3METHODS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float64[:],
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_CDLXSIDEGAP3METHODS(
    startIdx: Int,
    endIdx: Int,
    inOpen: Float32[:],
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    outInteger: Int[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_CEIL(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_CEIL(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_CMO(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_CMO(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_CORREL(
    startIdx: Int, endIdx: Int, inReal0: Float64[:], inReal1: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_CORREL(
    startIdx: Int, endIdx: Int, inReal0: Float32[:], inReal1: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_COS(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_COS(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_COSH(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_COSH(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_DEMA(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_DEMA(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_DIV(
    startIdx: Int, endIdx: Int, inReal0: Float64[:], inReal1: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_DIV(
    startIdx: Int, endIdx: Int, inReal0: Float32[:], inReal1: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_DX(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_DX(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_EMA(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_EMA(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_EXP(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_EXP(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_FLOOR(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_FLOOR(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_HT_DCPERIOD(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_HT_DCPERIOD(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_HT_DCPHASE(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_HT_DCPHASE(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3), Arg(4)])
def TA_HT_PHASOR(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outInPhase: Float64[:], outQuadrature: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3), Arg(4)])
def TA_S_HT_PHASOR(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outInPhase: Float64[:], outQuadrature: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3), Arg(4)])
def TA_HT_SINE(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outSine: Float64[:], outLeadSine: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3), Arg(4)])
def TA_S_HT_SINE(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outSine: Float64[:], outLeadSine: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_HT_TRENDLINE(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_HT_TRENDLINE(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_HT_TRENDMODE(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outInteger: Int[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_HT_TRENDMODE(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outInteger: Int[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_IMI(
    startIdx: Int, endIdx: Int, inOpen: Float64[:], inClose: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_IMI(
    startIdx: Int, endIdx: Int, inOpen: Float32[:], inClose: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_KAMA(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_KAMA(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_LINEARREG(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_LINEARREG(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_LINEARREG_ANGLE(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_LINEARREG_ANGLE(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_LINEARREG_INTERCEPT(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_LINEARREG_INTERCEPT(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_LINEARREG_SLOPE(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_LINEARREG_SLOPE(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_LN(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_LN(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_LOG10(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_LOG10(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_MA(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, optInMAType: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_MA(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, optInMAType: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(6),
        Arg(7),
        Arg(8),
    ]
)
def TA_MACD(
    startIdx: Int,
    endIdx: Int,
    inReal: Float64[:],
    optInFastPeriod: Int,
    optInSlowPeriod: Int,
    optInSignalPeriod: Int,
    outMACD: Float64[:],
    outMACDSignal: Float64[:],
    outMACDHist: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(6),
        Arg(7),
        Arg(8),
    ]
)
def TA_S_MACD(
    startIdx: Int,
    endIdx: Int,
    inReal: Float32[:],
    optInFastPeriod: Int,
    optInSlowPeriod: Int,
    optInSignalPeriod: Int,
    outMACD: Float64[:],
    outMACDSignal: Float64[:],
    outMACDHist: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Arg(7),
        Arg(8),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(9),
        Arg(10),
        Arg(11),
    ]
)
def TA_MACDEXT(
    startIdx: Int,
    endIdx: Int,
    inReal: Float64[:],
    optInFastPeriod: Int,
    optInFastMAType: Int,
    optInSlowPeriod: Int,
    optInSlowMAType: Int,
    optInSignalPeriod: Int,
    optInSignalMAType: Int,
    outMACD: Float64[:],
    outMACDSignal: Float64[:],
    outMACDHist: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Arg(7),
        Arg(8),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(9),
        Arg(10),
        Arg(11),
    ]
)
def TA_S_MACDEXT(
    startIdx: Int,
    endIdx: Int,
    inReal: Float32[:],
    optInFastPeriod: Int,
    optInFastMAType: Int,
    optInSlowPeriod: Int,
    optInSlowMAType: Int,
    optInSignalPeriod: Int,
    optInSignalMAType: Int,
    outMACD: Float64[:],
    outMACDSignal: Float64[:],
    outMACDHist: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4), Arg(5), Arg(6)]
)
def TA_MACDFIX(
    startIdx: Int,
    endIdx: Int,
    inReal: Float64[:],
    optInSignalPeriod: Int,
    outMACD: Float64[:],
    outMACDSignal: Float64[:],
    outMACDHist: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4), Arg(5), Arg(6)]
)
def TA_S_MACDFIX(
    startIdx: Int,
    endIdx: Int,
    inReal: Float32[:],
    optInSignalPeriod: Int,
    outMACD: Float64[:],
    outMACDSignal: Float64[:],
    outMACDHist: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5), Arg(6)]
)
def TA_MAMA(
    startIdx: Int,
    endIdx: Int,
    inReal: Float64[:],
    optInFastLimit: Float64,
    optInSlowLimit: Float64,
    outMAMA: Float64[:],
    outFAMA: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5), Arg(6)]
)
def TA_S_MAMA(
    startIdx: Int,
    endIdx: Int,
    inReal: Float32[:],
    optInFastLimit: Float64,
    optInSlowLimit: Float64,
    outMAMA: Float64[:],
    outFAMA: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_MAVP(
    startIdx: Int,
    endIdx: Int,
    inReal: Float64[:],
    inPeriods: Float64[:],
    optInMinPeriod: Int,
    optInMaxPeriod: Int,
    optInMAType: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_S_MAVP(
    startIdx: Int,
    endIdx: Int,
    inReal: Float32[:],
    inPeriods: Float32[:],
    optInMinPeriod: Int,
    optInMaxPeriod: Int,
    optInMAType: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_MAX(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_MAX(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_MAXINDEX(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outInteger: Int[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_MAXINDEX(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outInteger: Int[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_MEDPRICE(
    startIdx: Int, endIdx: Int, inHigh: Float64[:], inLow: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_MEDPRICE(
    startIdx: Int, endIdx: Int, inHigh: Float32[:], inLow: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_MFI(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    inVolume: Float64[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Arg(6), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(7)]
)
def TA_S_MFI(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    inVolume: Float32[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_MIDPOINT(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_MIDPOINT(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_MIDPRICE(
    startIdx: Int, endIdx: Int, inHigh: Float64[:], inLow: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_MIDPRICE(
    startIdx: Int, endIdx: Int, inHigh: Float32[:], inLow: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_MIN(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_MIN(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_MININDEX(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outInteger: Int[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_MININDEX(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outInteger: Int[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4), Arg(5)])
def TA_MINMAX(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outMin: Float64[:], outMax: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4), Arg(5)])
def TA_S_MINMAX(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outMin: Float64[:], outMax: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4), Arg(5)])
def TA_MINMAXINDEX(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outMinIdx: Int[:], outMaxIdx: Int[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4), Arg(5)])
def TA_S_MINMAXINDEX(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outMinIdx: Int[:], outMaxIdx: Int[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_MINUS_DI(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_MINUS_DI(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_MINUS_DM(
    startIdx: Int, endIdx: Int, inHigh: Float64[:], inLow: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_MINUS_DM(
    startIdx: Int, endIdx: Int, inHigh: Float32[:], inLow: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_MOM(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_MOM(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_MULT(
    startIdx: Int, endIdx: Int, inReal0: Float64[:], inReal1: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_MULT(
    startIdx: Int, endIdx: Int, inReal0: Float32[:], inReal1: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_NATR(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_NATR(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_OBV(
    startIdx: Int, endIdx: Int, inReal: Float64[:], inVolume: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_OBV(
    startIdx: Int, endIdx: Int, inReal: Float32[:], inVolume: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_PLUS_DI(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_PLUS_DI(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_PLUS_DM(
    startIdx: Int, endIdx: Int, inHigh: Float64[:], inLow: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_PLUS_DM(
    startIdx: Int, endIdx: Int, inHigh: Float32[:], inLow: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_PPO(
    startIdx: Int,
    endIdx: Int,
    inReal: Float64[:],
    optInFastPeriod: Int,
    optInSlowPeriod: Int,
    optInMAType: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_PPO(
    startIdx: Int,
    endIdx: Int,
    inReal: Float32[:],
    optInFastPeriod: Int,
    optInSlowPeriod: Int,
    optInMAType: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_ROC(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_ROC(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_ROCP(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_ROCP(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_ROCR(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_ROCR(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_ROCR100(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_ROCR100(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_RSI(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_RSI(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_SAR(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    optInAcceleration: Float64,
    optInMaximum: Float64,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_SAR(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    optInAcceleration: Float64,
    optInMaximum: Float64,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Arg(7),
        Arg(8),
        Arg(9),
        Arg(10),
        Arg(11),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(12),
    ]
)
def TA_SAREXT(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    optInStartValue: Float64,
    optInOffsetOnReverse: Float64,
    optInAccelerationInitLong: Float64,
    optInAccelerationLong: Float64,
    optInAccelerationMaxLong: Float64,
    optInAccelerationInitShort: Float64,
    optInAccelerationShort: Float64,
    optInAccelerationMaxShort: Float64,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Arg(7),
        Arg(8),
        Arg(9),
        Arg(10),
        Arg(11),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(12),
    ]
)
def TA_S_SAREXT(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    optInStartValue: Float64,
    optInOffsetOnReverse: Float64,
    optInAccelerationInitLong: Float64,
    optInAccelerationLong: Float64,
    optInAccelerationMaxLong: Float64,
    optInAccelerationInitShort: Float64,
    optInAccelerationShort: Float64,
    optInAccelerationMaxShort: Float64,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_SIN(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_SIN(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_SINH(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_SINH(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_SMA(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_SMA(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_SQRT(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_SQRT(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_STDDEV(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, optInNbDev: Float64, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_STDDEV(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, optInNbDev: Float64, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Arg(7),
        Arg(8),
        Arg(9),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(10),
        Arg(11),
    ]
)
def TA_STOCH(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInFastK_Period: Int,
    optInSlowK_Period: Int,
    optInSlowK_MAType: Int,
    optInSlowD_Period: Int,
    optInSlowD_MAType: Int,
    outSlowK: Float64[:],
    outSlowD: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Arg(7),
        Arg(8),
        Arg(9),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(10),
        Arg(11),
    ]
)
def TA_S_STOCH(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInFastK_Period: Int,
    optInSlowK_Period: Int,
    optInSlowK_MAType: Int,
    optInSlowD_Period: Int,
    optInSlowD_MAType: Int,
    outSlowK: Float64[:],
    outSlowD: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Arg(7),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(8),
        Arg(9),
    ]
)
def TA_STOCHF(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInFastK_Period: Int,
    optInFastD_Period: Int,
    optInFastD_MAType: Int,
    outFastK: Float64[:],
    outFastD: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Arg(7),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(8),
        Arg(9),
    ]
)
def TA_S_STOCHF(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInFastK_Period: Int,
    optInFastD_Period: Int,
    optInFastD_MAType: Int,
    outFastK: Float64[:],
    outFastD: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(7),
        Arg(8),
    ]
)
def TA_STOCHRSI(
    startIdx: Int,
    endIdx: Int,
    inReal: Float64[:],
    optInTimePeriod: Int,
    optInFastK_Period: Int,
    optInFastD_Period: Int,
    optInFastD_MAType: Int,
    outFastK: Float64[:],
    outFastD: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(7),
        Arg(8),
    ]
)
def TA_S_STOCHRSI(
    startIdx: Int,
    endIdx: Int,
    inReal: Float32[:],
    optInTimePeriod: Int,
    optInFastK_Period: Int,
    optInFastD_Period: Int,
    optInFastD_MAType: Int,
    outFastK: Float64[:],
    outFastD: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_SUB(
    startIdx: Int, endIdx: Int, inReal0: Float64[:], inReal1: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_SUB(
    startIdx: Int, endIdx: Int, inReal0: Float32[:], inReal1: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_SUM(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_SUM(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_T3(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, optInVFactor: Float64, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_T3(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, optInVFactor: Float64, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_TAN(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_TAN(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_TANH(
    startIdx: Int, endIdx: Int, inReal: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(3)])
def TA_S_TANH(
    startIdx: Int, endIdx: Int, inReal: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_TEMA(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_TEMA(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_TRANGE(
    startIdx: Int, endIdx: Int, inHigh: Float64[:], inLow: Float64[:], inClose: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_TRANGE(
    startIdx: Int, endIdx: Int, inHigh: Float32[:], inLow: Float32[:], inClose: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_TRIMA(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_TRIMA(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_TRIX(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_TRIX(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_TSF(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_TSF(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_TYPPRICE(
    startIdx: Int, endIdx: Int, inHigh: Float64[:], inLow: Float64[:], inClose: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_TYPPRICE(
    startIdx: Int, endIdx: Int, inHigh: Float32[:], inLow: Float32[:], inClose: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Arg(7),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(8),
    ]
)
def TA_ULTOSC(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInTimePeriod1: Int,
    optInTimePeriod2: Int,
    optInTimePeriod3: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [
        Arg(0),
        Arg(1),
        Arg(2),
        Arg(3),
        Arg(4),
        Arg(5),
        Arg(6),
        Arg(7),
        Return("outBegIdx", 1),
        Return("outNBElement", 2),
        Arg(8),
    ]
)
def TA_S_ULTOSC(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInTimePeriod1: Int,
    optInTimePeriod2: Int,
    optInTimePeriod3: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_VAR(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, optInNbDev: Float64, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_VAR(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, optInNbDev: Float64, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_WCLPRICE(
    startIdx: Int, endIdx: Int, inHigh: Float64[:], inLow: Float64[:], inClose: Float64[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(5)])
def TA_S_WCLPRICE(
    startIdx: Int, endIdx: Int, inHigh: Float32[:], inLow: Float32[:], inClose: Float32[:], outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_WILLR(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float64[:],
    inLow: Float64[:],
    inClose: Float64[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call(
    [Arg(0), Arg(1), Arg(2), Arg(3), Arg(4), Arg(5), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(6)]
)
def TA_S_WILLR(
    startIdx: Int,
    endIdx: Int,
    inHigh: Float32[:],
    inLow: Float32[:],
    inClose: Float32[:],
    optInTimePeriod: Int,
    outReal: Float64[:],
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_WMA(
    startIdx: Int, endIdx: Int, inReal: Float64[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
@native_call([Arg(0), Arg(1), Arg(2), Arg(3), Return("outBegIdx", 1), Return("outNBElement", 2), Arg(4)])
def TA_S_WMA(
    startIdx: Int, endIdx: Int, inReal: Float32[:], optInTimePeriod: Int, outReal: Float64[:]
) -> tuple[Int, Returns["outBegIdx", Int], Returns["outNBElement", Int]]: ...
