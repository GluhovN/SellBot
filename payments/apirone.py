from apirone_api.client import ApironeSaving

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

import json

import asyncio

from config import API_KEY_CRYPT_CURSE

from tg_bot import DB, bot

from languages.lang_controller import get_string


async def create_address():
    apirone_data = await DB.get_apirone_data()
    wallet_id = apirone_data[0][0]
    transfer_key = apirone_data[0][1]

    aapi = ApironeSaving(wallet_id=wallet_id, transfer_key=transfer_key)

    json = await aapi.create_address()
    address = json['address']

    loop = asyncio.new_event_loop()
    loop.create_task(coro=pay_check(aapi, wallet_id, address))

    return address


async def pay_check(aapi, wallet_id, address):
    while True:
        res = await aapi.make_request(method="GET",
                                      url=f"https://apirone.com/api/v2/wallets/{wallet_id}/history?limit={10}&offset={0}&q=address:{address}")
        print(res)
        if len(res['items']) == 0:
            continue
        for item in res['items']:
            if item['is_confirmed']:
                parameters = {
                    'start': '1',
                    'limit': '5000',
                    'convert': 'RUB'
                }
                headers = {
                    'Accepts': 'application/json',
                    'X-CMC_PRO_API_KEY': API_KEY_CRYPT_CURSE,
                }
                session = Session()
                session.headers.update(headers)
                pay_amount = 0
                try:
                    response = session.get('https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest',
                                           params=parameters)
                    data = json.loads(response.text)
                    for i in data["data"]:
                        if i['symbol'] == 'BTC':
                            pay_amount = int(float(i['quote']['RUB']['price']) * 0.00000001 * item['amount'])
                            break
                except (ConnectionError, Timeout, TooManyRedirects) as e:
                    print(e)
                user = await DB.get_user_by_apirone_address(address)
                cfg = await DB.get_config()
                cashback = cfg[7]
                user_rec = await DB.get_user(user[0])
                username = user_rec[3]
                inviter = await DB.get_inviter(username)
                if inviter is not None:
                    await DB.top_up_balances([0.0, pay_amount * (cashback / 100), 0.0, 0.0], inviter)
                    await DB.add_new_ref_cashback(inviter, pay_amount * (cashback / 100))
                await DB.top_up_balances([0.0, pay_amount, 0.0, 0.0], user[0])
                await bot.send_message(user[0], get_string('success_pay'))
                return
