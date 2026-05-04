from ostium_python_sdk import OstiumSDK
from ostium_python_sdk.config import NetworkConfig
import asyncio


async def main():
    # Initialize SDK
    config = NetworkConfig.testnet()
    sdk = OstiumSDK(config)

    # Get all latest prices
    prices = await sdk.price.get_latest_prices()
    print("\nAll Latest Prices:")
    print("----------------------------------------")
    for price_data in prices:
        price, is_open, _ = await sdk.price.get_price(price_data['from'], price_data['to'])
        print(
            f"{price_data['from']}/{price_data['to']}: {price:,.2f} {price_data['to']} (Market {'OPEN' if is_open else 'CLOSED'})")

    # Get specific asset pair prices
    btc_usd_price, btc_usd_open, _ = await sdk.price.get_price("BTC", "USD")
    nik_jpy_price, nik_jpy_open, _ = await sdk.price.get_price("NIK", "JPY")

    print("\nSpecific Pair Prices:")
    print("----------------------------------------")
    print(
        f"BTC/USD: {btc_usd_price:,.2f} USD (Market {'OPEN' if btc_usd_open else 'CLOSED'})")
    print(
        f"NIK/JPY: {nik_jpy_price:,.2f} JPY (Market {'OPEN' if nik_jpy_open else 'CLOSED'})")


if __name__ == "__main__":
    asyncio.run(main())
