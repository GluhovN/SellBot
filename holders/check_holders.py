from asyncio import sleep

import datetime

from tg_bot import DB, bot


async def check_holds():
    while True:
        await sleep(60)
        all_holds = await DB.get_all_holds()
        print(f'holds: {all_holds}')
        if all_holds is not None:
            for hold in all_holds:
                seller_time = await DB.get_seller_log_check_time(hold[1])
                if hold[7] + seller_time >= datetime.datetime.now().timestamp():
                    seller_commission = await DB.get_seller_commission(hold[1])
                    commission = (100 - seller_commission) / 100
                    admin_amount = [hold[3], hold[4], hold[5]]
                    await DB.add_admin_balance(admin_amount)
                    amount = [hold[3] * commission, hold[4] * commission, hold[5] * commission]
                    await DB.top_up_seller_balances(hold[1], amount)
                    await DB.remove_hold(hold[2])
