import aiohttp
import asyncio
import pandas as pd
import matplotlib.pyplot as plt

PRICE_URL = 'https://api.binance.com/api/v3/ticker/price'
PRICE_HISTORY_URL = 'https://api.binance.com/api/v3/klines'
TIME_URl = 'https://api.binance.com/api/v3/time'
HTTP_OK = 200


async def check_price():
    params = {
        'symbol': 'ETHUSDT'
    }
    flag_time = await get_response(TIME_URl, 'serverTime')
    flag_price = await get_response(PRICE_URL, 'price', params)
    print(f'Начальная цена {flag_price}')
    while True:
        try:
            await asyncio.sleep(1)
            current_time = await get_response(TIME_URl, 'serverTime')
            current_price = await get_response(PRICE_URL, 'price', params)
            print(current_price)
            diff = (current_price / flag_price - 1) * 100
            if abs(diff) >= 1:
                print(f'Текущая цена {current_price} изменилась на {round(diff, 3)}%')
                flag_time = await get_response(TIME_URl, 'serverTime')
                flag_price = current_price
            if current_time - flag_time >= 3_600_000:
                print(
                    'Прошел час\n'
                    f'  Начальная цена {flag_price}\n'
                    f'  Текущая цена {current_price}\n'
                    f'  Текущие отклонение {round(diff, 3)}%\n'
                )
                flag_time = await get_response(TIME_URl, 'serverTime')
                flag_price = current_price
        except Exception as e:
            print(f'Exception: {e}')


async def get_response(url, keyword=None, params=None):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == HTTP_OK:
                    data = await response.json()
                    if keyword:
                        return float(data[keyword])
                    else:
                        return data
                else:
                    raise Exception(f'Error HTTP status {response.status}')
    except Exception as e:
        print(f'Exception: {e}')
        return []


async def foo():
    params = {
        'symbol': "ETHUSDT",
        'interval': "1s",
        'limit': 50
    }
    columns = [
        'kline_open_time',
        'open_price',
        'high_price',
        'low_price',
        'close_price',
        'volume',
        'kline_close_time',
        'quote_asset_volume',
        'number_of_trades',
        'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume',
        'unused_field,_ignore',
    ]
    span = 10  # параметр для сглаживания
    while True:
        data = await get_response(PRICE_HISTORY_URL, params=params)
        df = pd.DataFrame(columns=columns, data=data)
        df['EMA'] = df.close_price.ewm(span=span, adjust=False).mean()
        df['EMA1'] = df.EMA.ewm(span=span, adjust=False).mean()
        df['EMA2'] = df.EMA1.ewm(span=span, adjust=False).mean()
        df['TRIX'] = (df.EMA2 - df.EMA2.shift(periods=1)) / df.EMA2.shift(periods=1) * 100

        fig, (ax1, ax) = plt.subplots(2)
        fig.set_size_inches(10, 3)
        x = list(range(0, len(list(df.close_price))))
        ax.plot(x, list(df.TRIX), 'b')
        ax1.plot(x, list(df.close_price), 'r')
        ax.plot(x, [0 for i in range(len(df))], 'g')
        ax.set_title('TRX')
        ax1.set_title('Close price')
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax1.set_yticklabels([])
        ax1.set_xticklabels([])
        fig.tight_layout()
        plt.show()

        big = df[df.TRIX > 0].TRIX
        les = df[df.TRIX < 0].TRIX
        if len(big) != 0 and len(les):
            if big.index[-1] > les.index[-1]:
                print('Возможен рост цены')
            else:
                print('Возможно падение цены')
        await asyncio.sleep(25)


def main():
    ioloop = asyncio.new_event_loop()
    try:
        tasks = [ioloop.create_task(foo()), ioloop.create_task(check_price())]
        wait_tasks = asyncio.wait(tasks)
        ioloop.run_until_complete(wait_tasks)
    except KeyboardInterrupt:
        print("STOP")
    finally:
        ioloop.close()


if __name__ == '__main__':
    main()
