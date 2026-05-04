import sys
from eth_abi import encode
from decimal import *
import math

PRECISION_2 = Decimal(1e2)
PRECISION_6 = Decimal(1e6)
PRECISION_18 = Decimal(1e18)
quantization_2 = Decimal('0.01')
quantization_3 = Decimal('0.001')
quantization_6 = Decimal('0.000001')
quantization_12 = Decimal('0.000000000001')
quantization_18 = Decimal('0.000000000000000001')

def getTargetFundingRate(normalizedOiDelta, hillInflectionPoint, maxFundingFeePerBlock, hillPosScale, hillNegScale):
    a = Decimal('1.84')
    n = 2
    K = Decimal('0.16')
    x = (a*normalizedOiDelta).quantize(quantization_6, rounding=ROUND_DOWN)
    x2 = (x**n).quantize(quantization_18, rounding=ROUND_DOWN)
    hill = (x2/(K + x2)).quantize(quantization_18, rounding=ROUND_DOWN)
    
    targetFr = (hillPosScale * hill).quantize(quantization_18, rounding=ROUND_DOWN) + hillInflectionPoint if normalizedOiDelta >= 0 \
    else (-hillNegScale * hill).quantize(quantization_18, rounding=ROUND_DOWN) + hillInflectionPoint
    
    if targetFr > Decimal('1'):
        targetFr = Decimal('1')
    elif targetFr < Decimal('-1'):
        targetFr = Decimal('-1')
    
    return (maxFundingFeePerBlock * targetFr).quantize(quantization_18, rounding=ROUND_DOWN)


def getPendingAccFundingFees(
        blockNumber: Decimal,
        lastUpdateBlock: Decimal,
        valueLong: Decimal, 
        valueShort: Decimal, 
        openInterestUsdcLong: Decimal, 
        openInterestUsdcShort: Decimal,
        OiCap: Decimal,        
        maxFundingFeePerBlock: Decimal,        
        lastFundingRate: Decimal,      
        hillInflectionPoint: Decimal,
        hillPosScale: Decimal,
        hillNegScale: Decimal,
        springFactor: Decimal,
        sFactorUpScale: Decimal,
        sFactorDownScaleP: Decimal,
    ):

    numBlocks = blockNumber - lastUpdateBlock
    openInterestMax = max(openInterestUsdcLong, openInterestUsdcShort)
    normalizedOiDelta = ((openInterestUsdcLong - openInterestUsdcShort).quantize(quantization_6, rounding=ROUND_DOWN) / max(OiCap, openInterestMax).quantize(quantization_6, rounding=ROUND_DOWN)).quantize(quantization_6, rounding=ROUND_DOWN)

    targetFr = getTargetFundingRate(normalizedOiDelta, hillInflectionPoint, maxFundingFeePerBlock, hillPosScale, hillNegScale)

    # New regime selection based on funding rates:
    if lastFundingRate * targetFr >= 0:  # Same sign
        if abs(targetFr) > abs(lastFundingRate):
            sFactor = springFactor
        else:
            sFactor = sFactorDownScaleP * springFactor / 100
    else:
        sFactor = sFactorUpScale * springFactor / 100

    expComp = exponentialApproximation(-sFactor * numBlocks)
    accFundingRate = (targetFr * numBlocks).quantize(quantization_18, rounding=ROUND_DOWN) + ((Decimal(1) - expComp) * (lastFundingRate - targetFr) / sFactor).quantize(quantization_18, rounding=ROUND_DOWN)

    fr = targetFr + ((lastFundingRate - targetFr) * expComp).quantize(quantization_18, rounding=ROUND_DOWN)
    
    if accFundingRate > 0:
        if openInterestUsdcLong > 0:
            valueLong += accFundingRate
            valueShort -= (accFundingRate * openInterestUsdcLong / openInterestUsdcShort).quantize(quantization_18, rounding=ROUND_DOWN) if openInterestUsdcShort > 0 else 0
    else:
        if openInterestUsdcShort > 0:
            valueShort -= accFundingRate
            valueLong += (accFundingRate * openInterestUsdcShort / openInterestUsdcLong).quantize(quantization_18, rounding=ROUND_DOWN) if openInterestUsdcLong > 0 else 0

    return (valueLong.quantize(quantization_18, rounding=ROUND_DOWN), valueShort.quantize(quantization_18, rounding=ROUND_DOWN), fr.quantize(quantization_18, rounding=ROUND_DOWN), targetFr.quantize(quantization_18, rounding=ROUND_DOWN))


def exponentialApproximation(value):
  if abs(value) < Decimal('0.7932312589092019'):
    numeratorTmp = value + Decimal('3');
    numerator = (numeratorTmp * numeratorTmp).quantize(quantization_18, rounding=ROUND_DOWN) + Decimal('3');
    denominatorTmp = value - Decimal('3');
    denominator = (denominatorTmp * denominatorTmp).quantize(quantization_18, rounding=ROUND_DOWN) + Decimal('3');

    return (numerator / denominator).quantize(quantization_18, rounding=ROUND_DOWN);
  elif abs(value) <= Decimal('6.906'):
    k = [Decimal('1.648721'), Decimal('1.284025'), Decimal('1.133148'), Decimal('1.064494'), Decimal('1.031743'), Decimal('1.015748'), Decimal('1.007843'), Decimal('1.003915'), Decimal('1.001955'), Decimal('1.000977')]
    product = Decimal('1.0')

    integer_part = math.floor(abs(value))
    decimal_part = abs(value) - integer_part
    
    for i in range(len(k)):
        decimal_part *= 2
        if decimal_part >= 1:
            product *= k[i]
            decimal_part -= 1
            product = product.quantize(quantization_6, rounding=ROUND_DOWN)
        if decimal_part == 0:
            break
    product = product.quantize(quantization_3, rounding=ROUND_DOWN) * Decimal(2)**(integer_part)

    return (Decimal(1) / product.quantize(quantization_18, rounding=ROUND_DOWN)).quantize(quantization_3, rounding=ROUND_DOWN)
  else:
    return Decimal(0)

if __name__ == "__main__":
    getcontext().prec = 128
    getcontext().rounding = ROUND_DOWN
    getcontext().clear_flags()

    if sys.argv[1] == "targetFundingRate":        
        normalizedOiDelta = Decimal(sys.argv[2]) / PRECISION_6
        hillInflectionPoint = Decimal(sys.argv[3]) / PRECISION_18
        maxFundingFeePerBlock = Decimal(sys.argv[4]) / PRECISION_18
        hillPosScale = Decimal(sys.argv[5]) / PRECISION_2
        hillNegScale = Decimal(sys.argv[6]) / PRECISION_2

        result = getTargetFundingRate(
            normalizedOiDelta,
            hillInflectionPoint,
            maxFundingFeePerBlock,
            hillPosScale,
            hillNegScale
        )
        encodedResult = "0x" + \
            encode(["int"], [int(result*PRECISION_18)]).hex()
        print(encodedResult)
    elif sys.argv[1] == "accFundingRate":
        blockNumber = Decimal(sys.argv[2])
        lastUpdateBlock = Decimal(sys.argv[3])
        valueLong = Decimal(sys.argv[4]) / PRECISION_18
        valueShort = Decimal(sys.argv[5]) / PRECISION_18
        openInterestUsdcLong = Decimal(sys.argv[6]) / PRECISION_6
        openInterestUsdcShort = Decimal(sys.argv[7]) / PRECISION_6
        oiCap = Decimal(sys.argv[8]) / PRECISION_6
        maxFundingFeePerBlock = Decimal(sys.argv[9]) / PRECISION_18
        lastFundingRate = Decimal(sys.argv[10]) / PRECISION_18
        hillInflectionPoint = Decimal(sys.argv[11]) / PRECISION_18
        hillPosScale = Decimal(sys.argv[12]) / PRECISION_2
        hillNegScale = Decimal(sys.argv[13]) / PRECISION_2
        springFactor = Decimal(sys.argv[14]) / PRECISION_18
        sFactorUpScale = Decimal(sys.argv[15]) / PRECISION_2
        sFactorDownScaleP = Decimal(sys.argv[16]) / PRECISION_2

        result = getPendingAccFundingFees(blockNumber, lastUpdateBlock, valueLong, valueShort, openInterestUsdcLong,
                                        openInterestUsdcShort, oiCap, maxFundingFeePerBlock, lastFundingRate,
                                        hillInflectionPoint, hillPosScale, hillNegScale, springFactor, sFactorUpScale, sFactorDownScaleP)
        encodedResult = "0x" + \
            encode(["int", "int", "int64"], [int(result[0]*PRECISION_18),
                int(result[1]*PRECISION_18), int(result[2]*PRECISION_18)]).hex()
        print(encodedResult)
    else:
        print("Invalid Operation")
        sys.exit(1)      
