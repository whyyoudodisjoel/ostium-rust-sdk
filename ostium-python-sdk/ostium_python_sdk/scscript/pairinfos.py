import sys
from eth_abi import encode
from decimal import *

PRECISION_2 = Decimal(1e2)
PRECISION_6 = Decimal(1e6)
PRECISION_18 = Decimal(1e18)
quantization_2 = Decimal('0.01')
quantization_6 = Decimal('0.000001')
quantization_18 = Decimal('0.000000000000000001')
    
def getTradeLiquidationPrice(
    liqMarginThresholdP: Decimal,
    openPrice: Decimal,
    long: bool,
    collateral: Decimal,
    leverage: Decimal,
    rolloverFee: Decimal,
    fundingFee: Decimal,
    maxLeverage: Decimal
) -> Decimal:
    rawAdjustedThreshold = (liqMarginThresholdP * leverage / maxLeverage).quantize(quantization_6, rounding=ROUND_DOWN)
    liqMarginValue = (collateral * rawAdjustedThreshold).quantize(quantization_6, rounding=ROUND_DOWN)
    targetCollateralAfterFees = (collateral - liqMarginValue - rolloverFee - fundingFee)
    liqPriceDistance = (openPrice * targetCollateralAfterFees / collateral / leverage).quantize(quantization_6, rounding=ROUND_DOWN)
    liqPrice = (openPrice - liqPriceDistance if long else openPrice + liqPriceDistance)
    return max(Decimal('0'), liqPrice)

def getTradeValue(
    liqMarginThresholdP: Decimal,
    collateral: Decimal,
    percentProfit: Decimal,
    rolloverFee: Decimal,
    fundingFee: Decimal,
    leverage: Decimal,
    maxLeverage: Decimal,
) -> (Decimal, Decimal):
    liqMarginValue = getTradeLiquidationMargin(liqMarginThresholdP, collateral, leverage, maxLeverage)
    value = getTradeValuePure(collateral, percentProfit, rolloverFee, fundingFee, liqMarginValue)

    return value, liqMarginValue

def getTradeValuePure(
    collateral: Decimal,
    percentProfit: Decimal,
    rolloverFee: Decimal,
    fundingFee: Decimal,
    liqMarginValue: Decimal
) -> Decimal:
    profitPart = (collateral * percentProfit / Decimal('100')).quantize(quantization_6, rounding=ROUND_DOWN)
    value = (collateral + profitPart - rolloverFee - fundingFee)
    if value <= liqMarginValue:
        return Decimal('0')
    return value

def getTradeLiquidationMargin(
    liqMarginThresholdP: Decimal,
    collateral: Decimal,
    leverage: Decimal,
    maxLeverage: Decimal
) -> Decimal:
    rawAdjustedThreshold = (liqMarginThresholdP * leverage / maxLeverage).quantize(quantization_6, rounding=ROUND_DOWN)
    return (collateral * rawAdjustedThreshold / Decimal('100')).quantize(quantization_6, rounding=ROUND_DOWN)

def getOpeningFee(
    tradeSize: Decimal, 
    leverage: Decimal,
    oiDelta: Decimal,
    makerMaxLeverage: Decimal,
    makerFeeP: Decimal,
    takerFeeP: Decimal
) -> Decimal:
    makerAmount: Decimal = Decimal(0)
    takerAmount: Decimal = Decimal(0)

    # Base Fee
    if (oiDelta * tradeSize < 0 and leverage <= makerMaxLeverage):
        if (oiDelta * (oiDelta + tradeSize) >= 0):
            makerAmount = abs(tradeSize)
        else:
            makerAmount = abs(oiDelta)
            takerAmount = abs(oiDelta + tradeSize)
    else:
        takerAmount = abs(tradeSize)

    baseFee: Decimal = (
        (makerFeeP * makerAmount).quantize(quantization_6, rounding=ROUND_DOWN) + 
        (takerFeeP * takerAmount).quantize(quantization_6, rounding=ROUND_DOWN)
    ) / Decimal('100')
    
    return baseFee.quantize(quantization_6, rounding=ROUND_DOWN)

if __name__ == "__main__":
    getcontext().prec = 128
    getcontext().rounding = ROUND_DOWN
    getcontext().clear_flags()
    
    calculationType = sys.argv[1]

    if (calculationType == "getTradeLiquidationPrice"):
        if len(sys.argv) != 10:
            print("Wrong arguments provided. Please provide all required arguments.")
            sys.exit(1)

        liqMarginThresholdP = Decimal(sys.argv[2]) / PRECISION_2
        openPrice = Decimal(sys.argv[3]) / PRECISION_18
        long = True if Decimal(sys.argv[4]) == Decimal(1) else False
        collateral = Decimal(sys.argv[5]) / PRECISION_6
        leverage = Decimal(sys.argv[6]) / PRECISION_2
        rolloverFee = Decimal(sys.argv[7]) / PRECISION_6
        fundingFee = Decimal(sys.argv[8]) / PRECISION_6
        maxLeverage = Decimal(sys.argv[9]) / PRECISION_2

        result = getTradeLiquidationPrice(liqMarginThresholdP, openPrice, long, collateral, leverage, rolloverFee, fundingFee, maxLeverage)
        encodedResult = "0x" + encode(["uint"], [int(result*PRECISION_18)]).hex()
        
    elif (calculationType == "getOpeningFee"):
        if len(sys.argv) != 8:
            print("Wrong arguments provided. Please provide all required arguments.")
            sys.exit(1)

        tradeSize = Decimal(sys.argv[2]) / PRECISION_6
        leverage = Decimal(sys.argv[3]) / PRECISION_2
        oiDelta = Decimal(sys.argv[4]) / PRECISION_6
        makerMaxLeverage = Decimal(sys.argv[5]) / PRECISION_2
        makerFeeP = Decimal(sys.argv[6]) / PRECISION_6
        takerFeeP = Decimal(sys.argv[7]) / PRECISION_6
        result = getOpeningFee(
            tradeSize,
            leverage,
            oiDelta,
            makerMaxLeverage,
            makerFeeP,
            takerFeeP
        )
        encodedResult = "0x" + encode(["uint"], [int(result*PRECISION_6)]).hex()

    elif (calculationType == "getTradeValue"):
        if len(sys.argv) != 9:
            print("Wrong arguments provided. Please provide all required arguments.")
            sys.exit(1)

        liqMarginThresholdP = Decimal(sys.argv[2])
        collateral = Decimal(sys.argv[3]) / PRECISION_6
        percentProfit = Decimal(sys.argv[4]) / PRECISION_6
        rolloverFee = Decimal(sys.argv[5]) / PRECISION_6
        fundingFee = Decimal(sys.argv[6]) / PRECISION_6
        leverage = Decimal(sys.argv[7]) / PRECISION_2
        maxLeverage = Decimal(sys.argv[8]) / PRECISION_2

        result = getTradeValue(liqMarginThresholdP, collateral, percentProfit, rolloverFee, fundingFee, leverage, maxLeverage)
        encodedResult = "0x" + encode(["uint", "uint"], [int(result[0]*PRECISION_6), int(result[1]*PRECISION_6)]).hex()
    
    elif (calculationType == "getTradeValuePure"):
        if len(sys.argv) != 7:
            print("Wrong arguments provided. Please provide all required arguments.")
            sys.exit(1)

        collateral = Decimal(sys.argv[2]) / PRECISION_6
        percentProfit = Decimal(sys.argv[3]) / PRECISION_6
        rolloverFee = Decimal(sys.argv[4]) / PRECISION_6
        fundingFee = Decimal(sys.argv[5]) / PRECISION_6
        liqMarginValue = Decimal(sys.argv[6]) / PRECISION_6

        result = getTradeValuePure(collateral, percentProfit, rolloverFee, fundingFee, liqMarginValue)
        encodedResult = "0x" + encode(["uint"], [int(result*PRECISION_6)]).hex()
    
    elif (calculationType == "getTradeLiquidationMargin"):
        if len(sys.argv) != 6:
            print("Wrong arguments provided. Please provide all required arguments.")
            sys.exit(1)

        liqMarginThresholdP = Decimal(sys.argv[2])
        collateral = Decimal(sys.argv[3]) / PRECISION_6
        leverage = Decimal(sys.argv[4]) / PRECISION_2
        maxLeverage = Decimal(sys.argv[5]) / PRECISION_2

        result = getTradeLiquidationMargin(liqMarginThresholdP, collateral, leverage, maxLeverage)
        encodedResult = "0x" + encode(["uint"], [int(result*PRECISION_6)]).hex()

    print(encodedResult)