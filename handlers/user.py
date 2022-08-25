import datetime

from aiogram.types import Message, CallbackQuery, ContentTypes, BotCommand
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import BadRequest, ChatIdIsEmpty, MessageToDeleteNotFound

from bit import PrivateKeyTestnet

from qrcode import make

from os import remove

from random import randint

import datetime

from tg_bot import bot, dp, DB

from keyboards.user import *
from keyboards.admin import approve_reject_seller_query_kb
from keyboards.seller import replace_remove_product_kb

from states.user import *

from filters.all_filters import *

from languages.lang_controller import get_string, get_string_with_args

from utils.start_message_writer import get_start_message, get_start_banner
from utils.seller_questions_reader import get_seller_questions
from utils.user_agreement_writer import get_user_agreement

from config import admin_ids

from payments import qiwi, apirone


@dp.message_handler(commands=['start'], state="*")
async def start_command_handler(message: Message, state: FSMContext):
    user_agreement_status = await DB.get_user_agreement_status(message.from_user.id)
    await bot.set_my_commands([
        BotCommand('start', 'Обновить')
    ])
    if not await DB.user_exists(tg_id=message.from_user.id):
        await DB.add_user(tg_id=message.from_user.id, username=message.from_user.username)
    if user_agreement_status:
        user_menu = await user_menu_kb()
        await bot.set_my_commands([
            BotCommand('start', 'Обновить')
        ])
        start_banner = get_start_banner()
        if start_banner == '' or start_banner is None:
            await bot.send_message(message.from_user.id, get_start_message(), reply_markup=user_menu)
        elif len(start_banner) > 0:
            await bot.send_photo(message.from_user.id, start_banner, get_start_message(), reply_markup=user_menu)
        else:
            await bot.send_message(message.from_user.id, get_start_message(), reply_markup=user_menu)
        user = await DB.get_user(message.from_user.id)
        user_profile = await user_profile_kb(user)
        seller = await DB.get_seller(message.from_user.id)
        balance = await DB.get_balance(message.from_user.id)
        extra_menu = ''
        if message.from_user.id in admin_ids:
            status = get_string('admin_status') if seller is None else get_string(
                'admin_status') + ', ' + get_string('seller_status')
            admin_cfg = await DB.get_config()
            holds = await DB.get_holds_sum()
            holds_sum = [0, 0, 0]
            for i in range(len(holds)):
                if holds[i] is not None:
                    holds_sum[i] = holds[i]
            purchases = await DB.get_all_purchases()
            invalid = await DB.get_invalid() if await DB.get_invalid() else 0
            valid = f"{(1 - invalid / len(purchases)) * 100}%" if len(purchases) else '100%'
            facebook = await DB.get_facebook_sellers()
            google = await DB.get_google_sellers()
            extra_menu = get_string_with_args('admin_profile_message', [admin_cfg[0], admin_cfg[1], admin_cfg[2],
                                                                        holds_sum[0] + holds_sum[1] + holds_sum[2],
                                                                        admin_cfg[3],
                                                                        admin_cfg[3] * (1 - admin_cfg[4] / 100),
                                                                        valid, len(purchases), invalid, facebook,
                                                                        google])
        else:
            status = get_string('user_status') if seller is None else get_string('seller_status')
            if seller:
                seller_balances = await DB.get_seller_balances(message.from_user.id)
                holds = await DB.get_holds_sum_by_seller_id(message.from_user.id)
                holds_sum = [0, 0, 0]
                summa = 0
                for i in range(len(holds)):
                    if holds[i] is not None:
                        holds_sum[i] = holds[i]
                    summa += holds_sum[i]
                invalid = await DB.get_invalid_for_seller(message.from_user.id)
                all_goods = await DB.get_all_goods_for_seller(message.from_user.id)
                valid = f"{(1 - invalid / all_goods) * 100}%" if all_goods != 0 else '100%'
                last_payment = await DB.get_last_payment(message.from_user.id)
                became_partner = await DB.get_became_partner(message.from_user.id)
                extra_menu = get_string_with_args('seller_profile_message',
                                                  [seller_balances[0], seller_balances[1], seller_balances[2], summa,
                                                   valid, all_goods, invalid,
                                                   last_payment if last_payment is not None else get_string(
                                                       'no_payment_yet_message'),
                                                   datetime.datetime.fromtimestamp(became_partner)])
        referrals = await DB.get_referrals(message.from_user.id)
        ref_count = len(referrals) if referrals is not None else 0
        await bot.send_message(message.from_user.id, get_string_with_args('user_profile_message',
                                                                          [message.from_user.id, balance, user[9],
                                                                           user[10], ref_count, user[12],
                                                                           status]) + f"\n*****\n{extra_menu}",
                               reply_markup=user_profile)
        await UserMenu.IsUser.set()
    else:
        confirm_user_agreement = await confirm_user_agreement_kb(message.from_user.id)
        await bot.send_message(message.from_user.id, get_user_agreement(), reply_markup=confirm_user_agreement)


@dp.callback_query_handler(text_startswith='approve_user_agreement_', state='*')
async def confirm_user_agreement(call: CallbackQuery, state: FSMContext):
    await call.answer(text=get_string('user_agreement_was_confirmed'))
    user = int(call.data.replace('approve_user_agreement_', ''))
    user_menu = await user_menu_kb()
    await DB.confirm_user_agreement(user)
    await bot.delete_message(call.from_user.id, call.message.message_id)
    start_banner = get_start_banner()
    if start_banner == '' or start_banner is None:
        await bot.send_message(call.from_user.id, get_start_message(), reply_markup=user_menu)
    elif len(start_banner) > 0:
        await bot.send_photo(call.from_user.id, start_banner, get_start_message(), reply_markup=user_menu)
    else:
        await bot.send_message(call.from_user.id, get_start_message(), reply_markup=user_menu)
    user = await DB.get_user(call.from_user.id)
    user_profile = await user_profile_kb(user)
    seller = await DB.get_seller(call.from_user.id)
    balance = await DB.get_balance(call.from_user.id)
    extra_menu = ''
    if call.from_user.id in admin_ids:
        status = get_string('admin_status') if seller is None else get_string(
            'admin_status') + ', ' + get_string('seller_status')
        admin_cfg = await DB.get_config()
        holds = await DB.get_holds_sum()
        holds_sum = [0, 0, 0]
        for i in range(len(holds)):
            if holds[i] is not None:
                holds_sum[i] = holds[i]
        purchases = await DB.get_all_purchases()
        invalid = await DB.get_invalid() if await DB.get_invalid() else 0
        valid = f"{(1 - invalid / len(purchases)) * 100}%" if len(purchases) else '100%'
        facebook = await DB.get_facebook_sellers()
        google = await DB.get_google_sellers()
        extra_menu = get_string_with_args('admin_profile_message', [admin_cfg[0], admin_cfg[1], admin_cfg[2],
                                                                    holds_sum[0] + holds_sum[1] + holds_sum[2],
                                                                    admin_cfg[3],
                                                                    admin_cfg[3] * (1 - admin_cfg[4] / 100),
                                                                    valid, len(purchases), invalid, facebook,
                                                                    google])
    else:
        status = get_string('user_status') if seller is None else get_string('seller_status')
        if seller:
            seller_balances = await DB.get_seller_balances(call.from_user.id)
            holds = await DB.get_holds_sum_by_seller_id(call.from_user.id)
            holds_sum = [0, 0, 0]
            summa = 0
            for i in range(len(holds)):
                if holds[i] is not None:
                    holds_sum[i] = holds[i]
                summa += holds_sum[i]
            invalid = await DB.get_invalid_for_seller(call.from_user.id)
            all_goods = await DB.get_all_goods_for_seller(call.from_user.id)
            valid = f"{(1 - invalid / all_goods) * 100}%" if all_goods != 0 else '100%'
            last_payment = await DB.get_last_payment(call.from_user.id)
            became_partner = await DB.get_became_partner(call.from_user.id)
            extra_menu = get_string_with_args('seller_profile_menu',
                                              [seller_balances[0], seller_balances[1], seller_balances[2], summa,
                                               valid, all_goods, invalid,
                                               last_payment if last_payment is not None else get_string(
                                                   'no_payment_yet_message'),
                                               datetime.datetime.fromtimestamp(became_partner)])
    referrals = await DB.get_referrals(call.from_user.id)
    ref_count = len(referrals) if referrals is not None else 0
    await bot.send_message(call.from_user.id, get_string_with_args('user_profile_message',
                                                                      [call.from_user.id, balance, user[9],
                                                                       user[10], ref_count, user[12],
                                                                       status]) + f"\n*****\n{extra_menu}",
                           reply_markup=user_profile)
    await UserMenu.IsUser.set()


@dp.callback_query_handler(text_startswith='choose_category_to_buy_', state="*")
async def choose_category_to_buy_handler(call: CallbackQuery, state: FSMContext):
    all_positions = await DB.get_all_positions(category_id=int(call.data.replace('choose_category_to_buy_', '')))
    async with state.proxy() as data:
        try:
            goods_messages = data['goods_messages']
        except KeyError:
            goods_messages = []
        messages = data['categories_messages']
        category_type = data['categories_type']
    if len(all_positions) == 0:
        await call.answer(get_string('empty'))
        return
    await call.answer()
    for msg in messages:
        try:
            await bot.delete_message(call.from_user.id, msg)
        except MessageToDeleteNotFound:
            pass
    for msg in goods_messages:
        await bot.delete_message(call.from_user.id, msg)
    positions_messages = []
    for pos in all_positions:
        goods = await DB.get_goods_for_position(pos[0])
        goods_count = len(goods)
        pos_to_buy_kb = await position_to_buy_kb(pos[1], pos[0], category_type, goods_count)
        if pos[4] == 'photo':
            msg = await bot.send_photo(chat_id=call.from_user.id,
                                       caption=get_string_with_args('position_card', [pos[2]]),
                                       photo=pos[3], reply_markup=pos_to_buy_kb)
            positions_messages.insert(-1, msg.message_id)
        if pos[4] == 'file':
            msg = await bot.send_document(chat_id=call.from_user.id,
                                          caption=get_string_with_args('position_card', [pos[2]]),
                                          document=pos[3], reply_markup=pos_to_buy_kb)
            positions_messages.insert(-1, msg.message_id)
        if pos[4] == 'None':
            msg = await bot.send_message(call.from_user.id,
                                         get_string_with_args('position_card', [pos[2]]),
                                         reply_markup=pos_to_buy_kb)
            positions_messages.insert(-1, msg.message_id)
        async with state.proxy() as data:
            data['positions_messages'] = positions_messages


@dp.callback_query_handler(text_startswith='choose_position_to_buy_', state='*')
async def choose_position_to_buy_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    all_goods = await DB.get_all_goods(int(call.data.replace('choose_position_to_buy_', '')))
    async with state.proxy() as data:
        try:
            positions_messages = data['positions_messages']
        except KeyError:
            positions_messages = []
    if len(all_goods) == 0:
        await call.answer(get_string('empty'))
        return
    for msg in positions_messages:
        await bot.delete_message(call.from_user.id, msg)
    goods_messages = []
    for prod in all_goods:
        buy = await buy_kb(prod[0], int(call.data.replace('choose_position_to_buy_', '')))
        seller = await DB.get_seller(prod[3])
        msg = await bot.send_message(call.from_user.id,
                                     get_string_with_args('product_to_buy_card_message',
                                                          [f'@{seller[2]}', prod[1], prod[6]]),
                                     reply_markup=buy)
        goods_messages.insert(-1, msg.message_id)
    async with state.proxy() as data:
        data['goods_messages'] = goods_messages


@dp.callback_query_handler(text_startswith='choose_designer_category_to_buy_', state="*")
async def choose_designer_category_to_buy_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    all_positions = await DB.get_all_designers(
        category_id=int(call.data.replace('choose_designer_category_to_buy_', '')))
    if len(all_positions) == 0:
        try:
            await bot.edit_message_text(text=get_string('empty'), chat_id=call.from_user.id,
                                        message_id=call.message.message_id, reply_markup=None)
        except BadRequest:
            await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                           caption=get_string('empty'), reply_markup=None)
        return
    des_list = [(i[1], i[0]) for i in all_positions]
    designers_list = await designers_list_kb(des_list)
    try:
        await bot.edit_message_text(get_string('designers_list_message'), call.from_user.id, call.message.message_id,
                                    reply_markup=designers_list)
    except BadRequest:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=get_string('designers_list_message'), reply_markup=designers_list)
    async with state.proxy() as data:
        data['des_category_id'] = int(call.data.replace('choose_designer_category_to_buy_', ''))


@dp.callback_query_handler(text_startswith='open_designer_card_', state='*')
async def open_designer_card(call: CallbackQuery, state: FSMContext):
    try:
        await bot.edit_message_text(call.message.text, call.from_user.id, call.message.message_id,
                                    reply_markup=None)
    except BadRequest:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=call.message.caption, reply_markup=None)
    designer = await DB.get_designer_profile(int(call.data.replace('open_designer_card_', '')))
    position_id = int(call.data.replace('open_designer_card_', ''))
    open_designer_card_keyboard = await open_designer_card_kb(designer[7], call.message.message_id, designer[8],
                                                              call.from_user.id, designer[9], position_id)
    count = designer[10] if designer[10] != 0 else 1
    if designer[5] == 'photo':
        await bot.send_photo(chat_id=call.from_user.id, photo=designer[4],
                             caption=get_string_with_args('designer_profile',
                                                          [designer[6],
                                                           f'{(designer[1] + designer[2]) / (2 * count)}/10',
                                                           f'{designer[1] / count}/10',
                                                           f'{designer[2] / count}/10',
                                                           f'{designer[3]}']),
                             reply_markup=open_designer_card_keyboard)
        return
    if designer[5] == 'file':
        await bot.send_document(chat_id=call.from_user.id, file=designer[4],
                                caption=get_string_with_args('designer_profile',
                                                             [designer[6],
                                                              f'{(designer[1] + designer[2]) / (2 * count)}/10',
                                                              f'{designer[1] / count}/10',
                                                              f'{designer[2] / count}/10',
                                                              f'{designer[3]}']),
                                reply_markup=open_designer_card_keyboard)
        return
    await bot.send_message(call.from_user.id,
                           get_string_with_args('designer_profile',
                                                [designer[6], f'{(designer[1] + designer[2]) / (2 * count)}/10',
                                                 f'{designer[1]}/10',
                                                 f'{designer[2]}/10', f'{designer[3]}']),
                           reply_markup=open_designer_card_keyboard)


@dp.callback_query_handler(text_startswith='make_order_', state='*')
async def make_order_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    designer_id = int(call.data.replace('make_order_', ''))
    async with state.proxy() as data:
        data['designer_id_order'] = designer_id
    back = await back_kb()
    await bot.send_message(call.from_user.id, get_string('send_technical_assignment_message'), reply_markup=back)
    await DesignerChat.EnterTechnicalAssignment.set()


@dp.callback_query_handler(text_startswith='back_to_designers_list_', state='*')
async def back_to_designers_list_message(call: CallbackQuery, state: FSMContext):
    await call.answer()
    async with state.proxy() as data:
        designer_category_id = data['des_category_id']
    await bot.delete_message(call.from_user.id, call.message.message_id)
    message_id = int(call.data.replace('back_to_designers_list_', ''))
    all_positions = await DB.get_all_designers(designer_category_id)
    des_list = [(i[1], i[0]) for i in all_positions]
    designers_list = await designers_list_kb(des_list)
    try:
        await bot.edit_message_text(text=get_string('designers_list_message'), chat_id=call.from_user.id,
                                    message_id=message_id,
                                    reply_markup=designers_list)
    except BadRequest:
        await bot.edit_message_caption(caption=get_string('designers_list_message'), chat_id=call.from_user.id,
                                       message_id=message_id, reply_markup=designers_list)


@dp.callback_query_handler(text='user_add_btc', state="*")
async def user_add_btc_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await DB.get_user(call.from_user.id)
    img_path = 'code_' + str(call.from_user.id) + '.png'
    address = PrivateKeyTestnet(wif=user[2]).address
    make(address).save(img_path)
    with open(img_path, 'rb') as code:
        await bot.send_photo(call.from_user.id, code.read(), caption=address)
    remove(img_path)


@dp.callback_query_handler(
    lambda c: c.data == 'google_user' or c.data == 'facebook_user' or c.data == 'partners_user' or c.data == 'vip_user',
    state='*')
async def get_categories_by_type_handler(call: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        try:
            positions_messages = data['positions_messages']
        except KeyError:
            positions_messages = []
    category_type = call.data.replace('_user', '')
    all_categories = await DB.get_all_categories(category_type)
    if len(all_categories) == 0:
        await call.answer(get_string('empty'))
        return
    await bot.delete_message(call.from_user.id, call.message.message_id)
    for msg in positions_messages:
        if msg != call.message.message_id:
            await bot.delete_message(call.from_user.id, msg)
    await call.answer(get_string('choose_category_name'))
    categories_messages = []
    for category in all_categories:
        positions = await DB.get_positions_for_category(category[0])
        goods_count = 0
        for pos in positions:
            goods = await DB.get_goods_for_position(pos[0])
            goods_count += len(goods)
        category_to_buy = await category_to_buy_kb(category[1], category[0], goods_count)
        if category[4] == 'photo':
            msg = await bot.send_photo(chat_id=call.from_user.id, photo=category[3],
                                       caption=get_string_with_args('category_card', [category[2]]),
                                       reply_markup=category_to_buy)
            categories_messages.insert(-1, msg.message_id)
        if category[4] == 'file':
            msg = await bot.send_document(chat_id=call.from_user.id, document=category[3],
                                          caption=get_string_with_args('category_card', [category[2]]),
                                          reply_markup=category_to_buy)
            categories_messages.insert(-1, msg.message_id)
        if category[4] == 'None':
            msg = await bot.send_message(call.from_user.id,
                                         get_string_with_args('category_card', [category[2]]),
                                         reply_markup=category_to_buy)
            categories_messages.insert(-1, msg.message_id)
        async with state.proxy() as data:
            data['categories_messages'] = categories_messages
            data['categories_type'] = call.data


@dp.callback_query_handler(text_startswith='cancel_sub_', state='*')
async def cancel_subscription(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = call.data.replace('cancel_sub_', '')
    await DB.cancel_mailing_subscription(int(user))
    await bot.edit_message_text(chat_id=call.from_user.id, text=get_string('subscription_was_canceled'),
                                message_id=call.message.message_id, reply_markup=None)


@dp.callback_query_handler(text_startswith='seller_question_', state=PartnerShip.Answering)
async def answering_question(call: CallbackQuery, state: FSMContext):
    await call.answer(get_string('send_the_answer'))
    qid = call.data.replace('seller_question_', '')
    async with state.proxy() as data:
        data['question_id'] = qid
    back_to_question = await back_to_question_kb(qid) if qid != '1' else None
    await bot.edit_message_text(call.message.text, call.from_user.id, call.message.message_id,
                                reply_markup=back_to_question)


@dp.callback_query_handler(text_startswith='previous_question_', state=PartnerShip.Answering)
async def previous_question(call: CallbackQuery, state: FSMContext):
    await call.answer()
    qid = call.data.replace('previous_question_', '')
    questions = get_seller_questions()
    async with state.proxy() as data:
        data['question_id'] = qid
    seller_question = await seller_question_kb(str(int(qid) - 1))
    await bot.edit_message_text(questions[str(int(qid) - 1)], call.from_user.id, call.message.message_id,
                                reply_markup=seller_question)


@dp.callback_query_handler(text_startswith='send_query_', state=PartnerShip.Answering)
async def send_seller_query(call: CallbackQuery, state: FSMContext):
    await call.answer(get_string('successful_send_query'))
    async with state.proxy() as data:
        questions = get_seller_questions()
        answers = ''
        for i in range(len(questions)):
            if i != 0:
                answers += questions[f'{i}'] + ': ' + data[f'q{i}'] + '\n'
    await DB.create_new_seller_query(call.from_user.id, call.from_user.username, answers)
    for admin in admin_ids:
        approve_reject_seller_query = await approve_reject_seller_query_kb(call.from_user.id)
        seller_balance = await DB.get_user(call.from_user.id)
        seller_balance = PrivateKeyTestnet(wif=seller_balance[2]).get_balance()
        await bot.send_message(admin, get_string_with_args('new_seller_query',
                                                           ['@' + call.from_user.username, call.from_user.id,
                                                            seller_balance, answers]),
                               reply_markup=approve_reject_seller_query)
    user_menu = await user_menu_kb()
    await bot.send_message(call.from_user.id, get_string('going_back_message'), reply_markup=user_menu)
    await bot.delete_message(call.from_user.id, call.message.message_id)
    await state.reset_data()
    await UserMenu.IsUser.set()


@dp.callback_query_handler(lambda c: c.data == 'buy_accounts', state='*')
async def buy_accounts(call: CallbackQuery, state: FSMContext):
    await call.answer()
    categories_types = await choice_of_categories_kb()
    await bot.edit_message_text(get_string('user_choose_goods_type'), call.from_user.id, call.message.message_id,
                                reply_markup=categories_types)


@dp.callback_query_handler(text_startswith='buy_prod_', state='*')
async def buy_account_handler(call: CallbackQuery, state: FSMContext):
    prod = await DB.get_product(int(call.data.replace('buy_prod_', '')))
    if prod is None:
        await call.answer(get_string('product_already_sold'))
        return
    prod_price = prod[6]
    balance = await DB.get_balance(call.from_user.id)
    if balance < prod_price:
        await call.answer(get_string('not_enough_money_message'))
        return
    all_balances = await DB.get_all_balances(call.from_user.id)
    qiwi_balance = all_balances[0]
    bit_balance = all_balances[1]
    capitalist_balance = all_balances[2]
    test_balance = all_balances[3]
    cost = prod_price
    write_off = [0.0, 0.0, 0.0, 0.0]
    if qiwi_balance >= cost:
        write_off[0] = cost
        cost = 0
    if bit_balance >= cost:
        write_off[1] = cost
        cost = 0
    if capitalist_balance >= cost:
        write_off[2] = cost
        cost = 0
    if test_balance >= cost:
        write_off[3] = cost
        cost = 0
    for i in range(len(write_off)):
        if cost == 0:
            break
        write_off[i] = all_balances[i] if cost >= all_balances[i] else cost
        cost -= write_off[i]
    date = int(datetime.datetime.now().timestamp())
    await call.answer(get_string('successfully_bought_message'))
    await DB.write_off_balances(write_off, call.from_user.id)
    await DB.add_purchase(call.from_user.id, int(call.data.replace('buy_prod_', '')), date)
    await bot.edit_message_text(call.message.text + '\n\n' + get_string('successfully_bought_message'),
                                call.from_user.id,
                                call.message.message_id, reply_markup=None)
    purchase = await DB.get_purchase_by_date(date, call.from_user.id)
    purchase_id = purchase[0]
    await DB.create_hold(write_off, purchase_id, prod[3],
                         date)
    seller = await DB.get_seller_by_product(purchase[2])
    await DB.increment_goods(seller)
    product_id = purchase[2]
    await DB.set_sold_status(product_id)
    replace_invalid = await replace_invalid_kb(product_id)
    await bot.send_document(chat_id=call.from_user.id, document=prod[2],
                            caption=get_string_with_args('purchase_card_message',
                                                         [purchase_id, prod[1]]), reply_markup=replace_invalid)


@dp.callback_query_handler(lambda c: c.data == 'top_up_balance', state='*')
async def top_up_methods(call: Message, state: FSMContext):
    payments_data = await DB.get_payments_data()
    if payments_data[0] is None and payments_data[1] is None and payments_data[2] is None:
        await call.answer(get_string('no_payments_methods_message'))
        return
    await call.answer()
    qiwi = True if payments_data[0] is not None else False
    apirone = True if payments_data[1] is not None else False
    capitalist = True if payments_data[2] is not None else False
    payments_methods = await payments_methods_kb(qiwi, apirone, capitalist)
    await bot.send_message(call.from_user.id, get_string('choose_payment_method_message'),
                           reply_markup=payments_methods)
    await TopUpBalance.InChoice.set()


@dp.callback_query_handler(lambda c: c.data == 'creatives', state='*')
async def creatives(call: CallbackQuery, state: FSMContext):
    all_categories = await DB.get_all_categories('designer')
    if len(all_categories) == 0:
        await call.answer(get_string('empty'))
        return
    await call.answer()
    await bot.delete_message(call.from_user.id, call.message.message_id)
    for category in all_categories:
        category_kb = await designer_category_to_buy_kb(category[1], category[0])
        if category[4] == 'photo':
            await bot.send_photo(call.from_user.id, category[3], category[2], reply_markup=category_kb)
        if category[4] == 'document':
            await bot.send_document(call.from_user.id, category[3], category[2], reply_markup=category_kb)
        if category[4] == None:
            await bot.send_message(call.from_user.id, category[2], reply_markup=category_kb)


@dp.callback_query_handler(text_startswith='back_to_user_profile', state='*')
async def back_to_user_profile(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await DB.get_user(call.from_user.id)
    user_profile = await user_profile_kb(user)
    seller = await DB.get_seller(call.from_user.id)
    balance = await DB.get_balance(call.from_user.id)
    await bot.delete_message(call.from_user.id, call.message.message_id)
    extra_menu = ''
    if call.from_user.id in admin_ids:
        status = get_string('admin_status') if seller is None else get_string(
            'admin_status') + ', ' + get_string('seller_status')
        admin_cfg = await DB.get_config()
        holds = await DB.get_holds_sum()
        holds_sum = [0, 0, 0]
        for i in range(len(holds)):
            if holds[i] is not None:
                holds_sum[i] = holds[i]
        purchases = await DB.get_all_purchases()
        invalid = await DB.get_invalid() if await DB.get_invalid() else 0
        valid = f"{(1 - invalid / len(purchases)) * 100}%" if len(purchases) else '100%'
        facebook = await DB.get_facebook_sellers()
        google = await DB.get_google_sellers()
        extra_menu = get_string_with_args('admin_profile_message', [admin_cfg[0], admin_cfg[1], admin_cfg[2],
                                                                    holds_sum[0] + holds_sum[1] + holds_sum[2],
                                                                    admin_cfg[3],
                                                                    admin_cfg[3] * (1 - admin_cfg[4] / 100),
                                                                    valid, len(purchases), invalid, facebook,
                                                                    google])
    else:
        status = get_string('user_status') if seller is None else get_string('seller_status')
        if seller:
            seller_balances = await DB.get_seller_balances(call.from_user.id)
            holds = await DB.get_holds_sum_by_seller_id(call.from_user.id)
            holds_sum = [0, 0, 0]
            summa = 0
            for i in range(len(holds)):
                if holds[i] is not None:
                    holds_sum[i] = holds[i]
                summa += holds_sum[i]
            invalid = await DB.get_invalid_for_seller(call.from_user.id)
            all_goods = await DB.get_all_goods_for_seller(call.from_user.id)
            valid = f"{(1 - invalid / all_goods) * 100}%" if all_goods != 0 else '100%'
            last_payment = await DB.get_last_payment(call.from_user.id)
            became_partner = await DB.get_became_partner(call.from_user.id)
            extra_menu = get_string_with_args('seller_profile_menu',
                                              [seller_balances[0], seller_balances[1], seller_balances[2], summa,
                                               valid, all_goods, invalid,
                                               last_payment if last_payment is not None else get_string(
                                                   'no_payment_yet_message'),
                                               datetime.datetime.fromtimestamp(became_partner)])
    referrals = await DB.get_referrals(call.from_user.id)
    ref_count = len(referrals) if referrals is not None else 0
    await bot.send_message(call.from_user.id, get_string_with_args('user_profile_message',
                                                                      [call.from_user.id, balance, user[9],
                                                                       user[10], ref_count, user[12],
                                                                       status]) + f"\n*****\n{extra_menu}",
                           reply_markup=user_profile)
    await state.reset_data()


@dp.callback_query_handler(text_startswith='subscribe_to_mailing_', state='*')
async def subscribe_to_mailing_handler(call: CallbackQuery, state: FSMContext):
    await call.answer(get_string("success_mailing_button"))
    await DB.add_new_mailing(call.from_user.id, int(call.data.replace('subscribe_to_mailing_', '')))
    cancel_mailing = await cancel_mailing_kb(int(call.data.replace('subscribe_to_mailing_', '')))
    await bot.edit_message_text(text=call.message.text,
                                chat_id=call.from_user.id, message_id=call.message.message_id,
                                reply_markup=cancel_mailing)


@dp.callback_query_handler(text_startswith='cancel_mailing_', state='*')
async def cancel_mailing_handler(call: CallbackQuery, state: FSMContext):
    await call.answer(get_string("success_cancel_mailing_message"))
    await DB.cancel_mailing(call.from_user.id, int(call.data.replace('cancel_mailing_', '')))
    seller_mailing = await seller_mailing_kb(int(call.data.replace('cancel_mailing_', '')))
    await bot.edit_message_text(text=call.message.text,
                                chat_id=call.from_user.id, message_id=call.message.message_id,
                                reply_markup=seller_mailing)


@dp.callback_query_handler(text_startswith='return_invalid_', state='*')
async def return_invalid_product_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    back = await back_kb()
    await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                   caption=call.message.caption, reply_markup=None)
    await bot.send_message(call.from_user.id, get_string('enter_cause_for_return_message'), reply_markup=back)
    async with state.proxy() as data:
        data['purchase_id'] = int(call.data.replace('return_invalid_', ''))
    await ReturnInvalid.EnterCause.set()


@dp.callback_query_handler(text_startswith='pay_order_', state='*')
async def pay_order_handler(call: CallbackQuery, state: FSMContext):
    chat_id = -int(call.data.replace('pay_order_', ''))
    price = await DB.get_order_price_from_chat_by_chat_id(chat_id)
    balances = await DB.get_all_balances(call.from_user.id)
    balances_sum = balances[0] + balances[1] + balances[2] + balances[3]
    if balances_sum < price:
        await call.answer(get_string('not_enough_money_to_order_message'))
    else:
        qiwi_balance = balances[0]
        bit_balance = balances[1]
        capitalist_balance = balances[2]
        test_balance = balances[3]
        cost = price
        write_off = [0.0, 0.0, 0.0, 0.0]
        if qiwi_balance >= cost:
            write_off[0] = cost
            cost = 0
        if bit_balance >= cost:
            write_off[1] = cost
            cost = 0
        if capitalist_balance >= cost:
            write_off[2] = cost
            cost = 0
        if test_balance >= cost:
            write_off[3] = cost
            cost = 0
        for i in range(len(write_off)):
            if cost == 0:
                break
            write_off[i] = balances[i] if cost >= balances[i] else cost
            cost -= write_off[i]
        date = int(datetime.datetime.now().timestamp())
        await call.answer(get_string('successfully_bought_message'))
        await DB.write_off_balances(write_off, call.from_user.id)
        chat = await DB.get_chat_by_chat_id(chat_id)
        await DB.add_purchase(call.from_user.id, -chat[0], date)
        purchase = await DB.get_purchase_by_date(date, call.from_user.id)
        purchase_id = purchase[0]
        await DB.create_hold(write_off, purchase_id, chat[2],
                             date)
        await DB.increment_creatives(call.from_user.id)
        return_invalid = await return_invalid_kb(purchase_id)
        await bot.delete_message(call.from_user.id, call.message.message_id)
        await DB.close_chat(chat_id)
        await bot.send_document(chat_id=call.from_user.id, document=chat[4],
                                reply_markup=return_invalid)
        user_menu = await user_menu_kb()
        await bot.send_message(call.from_user.id, get_string('chat_was_closed_message'), reply_markup=user_menu)
        await UserMenu.IsUser.set()


@dp.callback_query_handler(text_startswith='rate_designer_', state='*')
async def set_creatives_quality_menu_call(call: CallbackQuery, state: FSMContext):
    position_id = int(call.data.replace('rate_designer_', ''))
    rating_exist = await DB.get_rating_exist(call.from_user.id, position_id)
    if rating_exist:
        await call.answer(get_string('rating_exist_message'))
        return
    await call.answer()
    set_creatives_quality = await set_creatives_quality_kb(position_id)
    try:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=get_string('creatives_quality_message'),
                                       reply_markup=set_creatives_quality)
    except BadRequest:
        await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id,
                                    text=get_string('creatives_quality_message'),
                                    reply_markup=set_creatives_quality)
    async with state.proxy() as data:
        data['position_id'] = position_id


@dp.callback_query_handler(text_startswith='back_to_designer_card_', state='*')
async def back_to_designer_card(call: CallbackQuery, state: FSMContext):
    await call.answer()
    try:
        await bot.edit_message_text(call.message.text, call.from_user.id, call.message.message_id,
                                    reply_markup=None)
    except BadRequest:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=call.message.caption, reply_markup=None)
    designer = await DB.get_designer_profile(int(call.data.replace('back_to_designer_card_', '')))
    position_id = int(call.data.replace('back_to_designer_card_', ''))
    open_designer_card_keyboard = await open_designer_card_kb(designer[7], call.message.message_id, designer[8],
                                                              call.from_user.id, designer[9], position_id)
    count = designer[10] if designer[10] != 0 else 1
    await state.reset_data()
    if designer[5] == 'photo' or designer[5] == 'file':
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=get_string_with_args('designer_profile',
                                                                    [designer[6],
                                                                     f'{(designer[1] + designer[2]) / (2 * count)}/10',
                                                                     f'{designer[1] / count}/10',
                                                                     f'{designer[2] / count}/10',
                                                                     f'{designer[3]}']),
                                       reply_markup=open_designer_card_keyboard)
        return
    await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id,
                                text=get_string_with_args('designer_profile',
                                                          [designer[6],
                                                           f'{(designer[1] + designer[2]) / (2 * count)}/10',
                                                           f'{designer[1] / count}/10',
                                                           f'{designer[2] / count}/10',
                                                           f'{designer[3]}']),
                                reply_markup=open_designer_card_keyboard)


@dp.callback_query_handler(text_startswith='set_creatives_quality_', state='*')
async def set_quality_value(call: CallbackQuery, state: FSMContext):
    await call.answer()
    async with state.proxy() as data:
        data['creatives_quality'] = int(call.data.replace('set_creatives_quality_', ''))
        position_id = data['position_id']
    set_designer_professionalism = await set_designer_professionalism_kb(position_id)
    try:
        await bot.edit_message_text(get_string('professionalism_message'), call.from_user.id, call.message.message_id,
                                    reply_markup=set_designer_professionalism)
    except BadRequest:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=get_string('professionalism_message'),
                                       reply_markup=set_designer_professionalism)


@dp.callback_query_handler(text_startswith='back_to_creatives_quality_', state='*')
async def back_to_creatives_quality(call: CallbackQuery, state: FSMContext):
    await call.answer()
    async with state.proxy() as data:
        position_id = data['position_id']
    set_creatives_quality = await set_creatives_quality_kb(position_id)
    try:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=get_string('creatives_quality_message'),
                                       reply_markup=set_creatives_quality)
    except BadRequest:
        await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id,
                                    text=get_string('creatives_quality_message'),
                                    reply_markup=set_creatives_quality)


@dp.callback_query_handler(text_startswith='set_designer_professionalism_', state='*')
async def set_professionalism(call: CallbackQuery, state: FSMContext):
    await call.answer(get_string('rate_was_sent_message'))
    async with state.proxy() as data:
        data['professionalism'] = int(call.data.replace('set_designer_professionalism_', ''))
        position_id = data['position_id']
        creatives_quality = data['creatives_quality']
        professionalism = data['professionalism']
    await DB.add_new_rate(creatives_quality, professionalism, position_id, user_id=call.from_user.id)
    designer = await DB.get_designer_profile(position_id)
    open_designer_card_keyboard = await open_designer_card_kb(designer[7], call.message.message_id, designer[8],
                                                              call.from_user.id, designer[9], position_id)
    count = designer[10] if designer[10] != 0 else 1
    await state.reset_data()
    async with state.proxy() as data:
        data['des_category_id'] = designer[11]
    if designer[5] == 'photo' or designer[5] == 'file':
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=get_string_with_args('designer_profile',
                                                                    [designer[6],
                                                                     f'{(designer[1] + designer[2]) / (2 * count)}/10',
                                                                     f'{designer[1] / count}/10',
                                                                     f'{designer[2] / count}/10',
                                                                     f'{designer[3]}']),
                                       reply_markup=open_designer_card_keyboard)
        return
    await bot.edit_message_text(chat_id=call.from_user.id, message_id=call.message.message_id,
                                text=get_string_with_args('designer_profile',
                                                          [designer[6],
                                                           f'{(designer[1] + designer[2]) / (2 * count)}/10',
                                                           f'{designer[1] / designer[10]}/10',
                                                           f'{designer[2] / designer[10]}/10',
                                                           f'{designer[3]}']),
                                reply_markup=open_designer_card_keyboard)


@dp.callback_query_handler(text_startswith='replace_invalid_', state=UserMenu.IsUser)
async def replace_invalid_call(call: CallbackQuery, state: FSMContext):
    await call.answer()
    product = await DB.get_product(prod_id=int(call.data.replace('replace_invalid_', '')), is_sold=True)
    async with state.proxy() as data:
        data['seller'] = product[3]
        data['product'] = product
    back = await back_kb()
    await bot.send_message(call.from_user.id, get_string('enter_cause_for_return_message'), reply_markup=back)
    await ReturnInvalid.EnterCause.set()


@dp.message_handler(content_types=ContentTypes.DOCUMENT, state=DesignerChat.EnterTechnicalAssignment)
async def send_technical_assignment(message: Message, state: FSMContext):
    async with state.proxy() as data:
        designer_id = data['designer_id_order']
    designer = await DB.get_designer_tg_id_by_id(designer_id)
    user_menu = await user_menu_kb()
    get_reject_order = await get_reject_order_kb(message.from_user.id)
    try:
        await bot.send_message(designer,
                               get_string_with_args('new_order_by_message', ['@' + message.from_user.username]))
        await bot.send_document(chat_id=designer, document=message.document.file_id, caption=message.caption,
                                reply_markup=get_reject_order)
        await bot.send_message(message.from_user.id, get_string('order_was_successful_sent_message'),
                               reply_markup=user_menu)
    except ChatIdIsEmpty:
        await bot.send_message(message.from_user.id, get_string('designer_is_not_auth_yet'), reply_markup=user_menu)
    await UserMenu.IsUser.set()


@dp.message_handler(content_types=ContentTypes.PHOTO, state=DesignerChat.EnterTechnicalAssignment)
async def send_technical_assignment(message: Message, state: FSMContext):
    async with state.proxy() as data:
        designer_id = data['designer_id_order']
    designer = await DB.get_designer_tg_id_by_id(designer_id)
    get_reject_order = await get_reject_order_kb(message.from_user.id)
    user_menu = await user_menu_kb()
    try:
        await bot.send_message(designer,
                               get_string_with_args('new_order_by_message', ['@' + message.from_user.username]))
        await bot.send_photo(chat_id=designer, photo=message.photo[-1].file_id, caption=message.caption,
                             reply_markup=get_reject_order)
        await bot.send_message(message.from_user.id, get_string('order_was_successful_sent_message'),
                               reply_markup=user_menu)
    except ChatIdIsEmpty:
        await bot.send_message(message.from_user.id, get_string('designer_is_not_auth_yet'), reply_markup=user_menu)
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('back_button'), state=ReturnInvalid.EnterCause)
async def back_to_menu(message: Message, state: FSMContext):
    user_menu = await user_menu_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=user_menu)
    await state.reset_data()
    await UserMenu.IsUser


@dp.message_handler(TextEquals('back_button'), state=SellerStatusQuery.InSettingQuery)
async def back_to_user_menu(message: Message, state: FSMContext):
    user_menu = await user_menu_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=user_menu)
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('back_button'), state=TopUpBalance.InChoice)
async def back_user_menu(message: Message, state: FSMContext):
    user_menu = await user_menu_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=user_menu)
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('back_button'), state=TopUpBalance.Qiwi)
async def back_to_choice_of_payments_methods(message: Message, state: FSMContext):
    payments_data = await DB.get_payments_data()
    if payments_data[0] is None and payments_data[1] is None and payments_data[2] is None:
        user_menu = await user_menu_kb()
        await bot.send_message(message.from_user.id, get_string('no_payments_methods_message'), reply_markup=user_menu)
        await UserMenu.IsUser.set()
        return
    qiwi = True if payments_data[0] is not None else False
    apirone = True if payments_data[1] is not None else False
    capitalist = True if payments_data[2] is not None else False
    payments_methods = await payments_methods_kb(qiwi, apirone, capitalist)
    await bot.send_message(message.from_user.id, get_string('choose_payment_method_message'),
                           reply_markup=payments_methods)
    await TopUpBalance.InChoice.set()


@dp.message_handler(TextEquals('back_button'), state=PartnerShip.Answering)
async def back_to_user_menu(message: Message, state: FSMContext):
    user_menu = await user_menu_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=user_menu)
    await state.reset_data()
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('back_button'), state=DesignerChat.EnterTechnicalAssignment)
async def back_to_user_menu(message: Message, state: FSMContext):
    user_menu = await user_menu_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=user_menu)
    await state.reset_data()
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('back_button'), state=DesignerChat.InMenu)
async def back_to_user_menu(message: Message, state: FSMContext):
    user_menu = await user_menu_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=user_menu)
    await state.reset_data()
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('back_button'), state=DesignerChat.InChat)
async def get_all_chats(message: Message, state: FSMContext):
    designers = await DB.get_designers_for_chat(message.from_user.id)
    designers_nick_names = []
    for des in designers:
        des_by_id = await DB.get_designers_by_tg_id(des[0])
        nickname = des_by_id[0][1]
        designers_nick_names.insert(-1, [nickname, des[0]])
    chats = await chats_kb(designers_nick_names)
    await bot.send_message(message.from_user.id, get_string('choose_designer_message'), reply_markup=chats)
    async with state.proxy() as data:
        data['designers'] = designers_nick_names
    await DesignerChat.InMenu.set()


@dp.message_handler(TextEquals('goods_button'), state=UserMenu.IsUser)
async def user_goods_choose_category_type_handler(message: Message, state: FSMContext):
    categories_types = await choice_of_categories_kb()
    await bot.send_message(message.from_user.id, get_string('user_choose_goods_type'),
                           reply_markup=categories_types)


@dp.message_handler(TextEquals('profile_button'), state=UserMenu.IsUser)
async def user_profile_handler(message: Message, state: FSMContext):
    user = await DB.get_user(message.from_user.id)
    user_profile = await user_profile_kb(user)
    seller = await DB.get_seller(message.from_user.id)
    balance = await DB.get_balance(message.from_user.id)
    extra_menu = ''
    if message.from_user.id in admin_ids:
        status = get_string('admin_status') if seller is None else get_string(
            'admin_status') + ', ' + get_string('seller_status')
        admin_cfg = await DB.get_config()
        holds = await DB.get_holds_sum()
        holds_sum = [0, 0, 0]
        for i in range(len(holds)):
            if holds[i] is not None:
                holds_sum[i] = holds[i]
        purchases = await DB.get_all_purchases()
        invalid = await DB.get_invalid() if await DB.get_invalid() else 0
        valid = f"{(1 - invalid / len(purchases)) * 100}%" if len(purchases) else '100%'
        facebook = await DB.get_facebook_sellers()
        google = await DB.get_google_sellers()
        extra_menu = get_string_with_args('admin_profile_message', [admin_cfg[0], admin_cfg[1], admin_cfg[2],
                                                                    holds_sum[0] + holds_sum[1] + holds_sum[2],
                                                                    admin_cfg[3],
                                                                    admin_cfg[3] * (1 - admin_cfg[4] / 100),
                                                                    valid, len(purchases), invalid, facebook,
                                                                    google])
    else:
        status = get_string('user_status') if seller is None else get_string('seller_status')
        if seller:
            seller_balances = await DB.get_seller_balances(message.from_user.id)
            holds = await DB.get_holds_sum_by_seller_id(message.from_user.id)
            holds_sum = [0, 0, 0]
            summa = 0
            for i in range(len(holds)):
                if holds[i] is not None:
                    holds_sum[i] = holds[i]
                summa += holds_sum[i]
            invalid = await DB.get_invalid_for_seller(message.from_user.id)
            all_goods = await DB.get_all_goods_for_seller(message.from_user.id)
            valid = f"{(1 - invalid / all_goods) * 100}%" if all_goods != 0 else '100%'
            last_payment = await DB.get_last_payment(message.from_user.id)
            became_partner = await DB.get_became_partner(message.from_user.id)
            extra_menu = get_string_with_args('seller_profile_message',
                                              [seller_balances[0], seller_balances[1], seller_balances[2], summa,
                                               valid, all_goods, invalid,
                                               last_payment if last_payment is not None else get_string(
                                                   'no_payment_yet_message'),
                                               datetime.datetime.fromtimestamp(became_partner)])
    referrals = await DB.get_referrals(message.from_user.id)
    ref_count = len(referrals) if referrals is not None else 0
    await bot.send_message(message.from_user.id, get_string_with_args('user_profile_message',
                                                                      [message.from_user.id, balance, user[9],
                                                                       user[10], ref_count, user[12],
                                                                       status]) + f"\n*****\n{extra_menu}",
                           reply_markup=user_profile)


@dp.message_handler(TextEquals('partnership_button'), state=UserMenu.IsUser)
async def send_seller_status_query(message: Message, state: FSMContext):
    user = await DB.get_seller(message.from_user.id)
    user_menu = await user_menu_kb()
    if user is not None:
        if user[3] is None:
            await bot.send_message(message.from_user.id, get_string('query_already_sent'), reply_markup=user_menu)
            await UserMenu.IsUser.set()
            await state.reset_data()
            return
        if user[3] == 1:
            await bot.send_message(message.from_user.id, get_string('you_are_already_a_seller'), reply_markup=user_menu)
            await UserMenu.IsUser.set()
            await state.reset_data()
            return
    questions = get_seller_questions()
    start_seller_question = questions['0']
    back = await back_kb()
    await bot.send_message(message.from_user.id, start_seller_question,
                           reply_markup=back)
    seller_question = await seller_question_kb('1')
    question_message = await bot.send_message(message.from_user.id, questions['1'],
                                              reply_markup=seller_question)
    async with state.proxy() as data:
        data['question_id'] = None
        data['message_id'] = question_message.message_id
    await PartnerShip.Answering.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=PartnerShip.Answering)
async def answering_question(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if data['question_id'] is None:
            await bot.send_message(message.from_user.id, get_string('click_to_answer_button'))
            return
        qid = data['question_id']
        question_message_id = data['message_id']
        data[f'q{qid}'] = message.text
    questions = get_seller_questions()
    try:
        seller_question = await seller_question_kb(str(int(qid) + 1))
        question_message = await bot.send_message(message.from_user.id, questions[f'{int(qid) + 1}'],
                                                  reply_markup=seller_question)
        await bot.delete_message(message.from_user.id, question_message_id)
        async with state.proxy() as data:
            data['message_id'] = question_message.message_id
    except KeyError:
        await bot.delete_message(message.from_user.id, question_message_id)
        answers = ''
        async with state.proxy() as data:
            for i in range(len(questions)):
                if i != 0:
                    answers += questions[f'{i}'] + ': ' + data[f'q{i}'] + '\n'
        send_back_query = await send_back_query_kb(user_id=message.from_user.id, qid=len(questions))
        question_message = await bot.send_message(message.from_user.id,
                                                  get_string_with_args('confirm_to_send_seller_query', [answers]),
                                                  reply_markup=send_back_query)
        async with state.proxy() as data:
            data['message_id'] = question_message.message_id


@dp.message_handler(TextEquals('seller_list_button'), state=UserMenu.IsUser)
async def seller_list(message: Message, state: FSMContext):
    seller_list = await DB.get_all_sellers()
    if len(seller_list) == 0:
        await bot.send_message(message.from_user.id, get_string('empty'))
    for seller in seller_list:
        mailing = await DB.get_mailing_record(message.from_user.id, seller[1])
        seller_mailing = await seller_mailing_kb(seller[1]) if mailing is None else await cancel_mailing_kb(seller[1])
        goods = await DB.get_goods_by_seller(seller[1], False)
        all_goods = await DB.get_all_goods_for_seller(seller[1])
        invalid = await DB.get_invalid_for_seller(seller[1])
        await bot.send_message(message.from_user.id,
                               get_string_with_args('seller_card',
                                                    [seller[0], seller[1], '@' + seller[2], len(goods),
                                                     f'{(1 - invalid / all_goods) * 100}%']),
                               reply_markup=seller_mailing)


@dp.message_handler(TextEquals('top_up_balance_button'), state=UserMenu.IsUser)
async def top_up_methods(message: Message, state: FSMContext):
    payments_data = await DB.get_payments_data()
    if payments_data[0] is None and payments_data[1] is None and payments_data[2] is None:
        user_menu = await user_menu_kb()
        await bot.send_message(message.from_user.id, get_string('no_payments_methods_message'), reply_markup=user_menu)
        await UserMenu.IsUser.set()
        return
    qiwi = True if payments_data[0] is not None else False
    apirone = True if payments_data[1] is not None else False
    capitalist = True if payments_data[2] is not None else False
    payments_methods = await payments_methods_kb(qiwi, apirone, capitalist)
    await bot.send_message(message.from_user.id, get_string('choose_payment_method_message'),
                           reply_markup=payments_methods)
    await TopUpBalance.InChoice.set()


@dp.message_handler(TextEquals('qiwi_payment_data'), state=TopUpBalance.InChoice)
async def qiwi_pay(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_payment_value'), reply_markup=back)
    await TopUpBalance.Qiwi.set()


@dp.message_handler(TextEquals('apirone_payment_data'), state=TopUpBalance.InChoice)
async def qiwi_pay(message: Message, state: FSMContext):
    address = await apirone.create_address()
    img_path = 'code_' + str(message.from_user.id) + '.png'
    make(address).save(img_path)
    with open(img_path, 'rb') as code:
        await bot.send_photo(message.from_user.id, code.read(), caption=address)
    await DB.set_apirone_pay_address(message.from_user.id, address)
    remove(img_path)


@dp.message_handler(content_types=ContentTypes.TEXT, state=TopUpBalance.Qiwi)
async def send_qiwi_bill(message: Message, state: FSMContext):
    old_qiwi_pay = await DB.get_pay_id(message.from_user.id)
    rand = randint(1, 99999)
    if not message.text.isdigit():
        await bot.send_message(message.from_user.id, get_string('incorrect_value'))
        return
    amount = message.text
    uid = f"{amount}:" + f"{str(message.from_user.id)}:" + (5 - len(str(rand))) * '0' + str(rand)
    while str(uid) == str(old_qiwi_pay):
        rand = randint(1, 99999)
        uid = f"{amount}:" + f"{str(message.from_user.id)}:" + (5 - len(str(rand))) * '0' + str(rand)
    url = await qiwi.qiwi_pay(uid)
    user_menu = await user_menu_kb()
    await bot.send_message(message.from_user.id, get_string_with_args('qiwi_payment_link', [amount, url]),
                           reply_markup=user_menu)
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('my_purchases_button'), state=UserMenu.IsUser)
async def send_user_purchases_handler(message: Message, state: FSMContext):
    user_purchases = await DB.get_user_purchases(message.from_user.id)
    if len(user_purchases) == 0:
        await bot.send_message(message.from_user.id, get_string('empty'))
        return
    for purchase in user_purchases:
        purchase_id = purchase[0]
        product_id = purchase[2]
        if product_id < 0:
            product = await DB.get_order_file(-product_id)
            chat = await DB.get_chat_by_chat_id(-product_id)
            designer = await DB.get_designers_by_tg_id(chat[2])
            designer_nickname = designer[0][1]
            document = product
            description = get_string_with_args('order_from_message', [designer_nickname])
        else:
            product = await DB.get_product(product_id, is_sold=True)
            document = product[2]
            description = product[1]
        hold = await DB.get_hold(purchase_id)
        if len(hold) > 0:
            return_invalid = await return_invalid_kb(purchase_id)
            print(document)
            await bot.send_document(chat_id=message.from_user.id, document=document,
                                    caption=get_string_with_args('purchase_card_message',
                                                                 [purchase_id, description]),
                                    reply_markup=return_invalid)
        else:
            await bot.send_document(chat_id=message.from_user.id, document=document,
                                    caption=get_string_with_args('purchase_card_message',
                                                                 [purchase_id, description]))


@dp.message_handler(content_types=ContentTypes.TEXT, state=ReturnInvalid.EnterCause)
async def enter_cause_for_return(message: Message, state: FSMContext):
    async with state.proxy() as data:
        seller = data['seller']
        product = data['product']
    await DB.set_invalid(product[0])
    replace_reject = await replace_remove_product_kb(product[0])
    user_menu = await user_menu_kb()
    await bot.send_document(chat_id=seller, caption=get_string_with_args('new_replace_invalid_query_message',
                                                                         [product[1], product[0], message.text]),
                            document=product[2], reply_markup=replace_reject)
    await bot.send_message(message.from_user.id, get_string('success_request_message'), reply_markup=user_menu)
    await UserMenu.IsUser.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=DesignerChat.EnterTechnicalAssignment)
async def send_technical_assignment(message: Message, state: FSMContext):
    async with state.proxy() as data:
        designer_id = data['designer_id_order']
    designer = await DB.get_designer_tg_id_by_id(designer_id)
    get_reject_order = await get_reject_order_kb(message.from_user.id)
    user_menu = await user_menu_kb()
    try:
        await bot.send_message(designer,
                               get_string_with_args('new_order_by_message', ['@' + message.from_user.username]))
        await bot.send_message(designer, message.text,
                               reply_markup=get_reject_order)
        await bot.send_message(message.from_user.id, get_string('order_was_successful_sent_message'),
                               reply_markup=user_menu)
    except ChatIdIsEmpty:
        await bot.send_message(message.from_user.id, get_string('designer_is_not_auth_yet'), reply_markup=user_menu)
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('chat_button'), state=UserMenu.IsUser)
async def get_all_chats(message: Message, state: FSMContext):
    designers = await DB.get_designers_for_chat(message.from_user.id)
    designers_nick_names = []
    for des in designers:
        des_by_id = await DB.get_designers_by_tg_id(des[0])
        nickname = des_by_id[0][1]
        designers_nick_names.insert(-1, [nickname, des[0]])
    chats = await chats_kb(designers_nick_names)
    if chats is None:
        await bot.send_message(message.from_user.id, get_string('no_designers_for_chat_message'))
        return
    await bot.send_message(message.from_user.id, get_string('choose_designer_message'), reply_markup=chats)
    async with state.proxy() as data:
        data['designers'] = designers_nick_names
    await DesignerChat.InMenu.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=DesignerChat.InMenu)
async def start_to_chatting(message: Message, state: FSMContext):
    is_designer = False
    des_id = 0
    async with state.proxy() as data:
        designers = data['designers']
    for des in designers:
        if des[0] == message.text:
            des_id = des[1]
            is_designer = True
            break
    if not is_designer:
        await bot.send_message(message.from_user.id, get_string('is_not_designer_message'))
        return
    async with state.proxy() as data:
        data['des_id'] = des_id
    chat = await DB.get_chat(des_id, message.from_user.id)
    is_file = True if chat[4] is not None else False
    if is_file:
        purchase = await DB.get_purchase_by_prod_id(message.from_user.id, -chat[0])
        if purchase is None:
            pay_order = await pay_order_kb(-chat[0])
            await bot.send_message(message.from_user.id, get_string('your_order_is_not_paid_message'),
                                   reply_markup=pay_order)
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('chat_started_message'), reply_markup=back)
    await DesignerChat.InChat.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=DesignerChat.InChat)
async def in_chat_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        des_id = data['des_id']
    await bot.send_message(des_id, get_string_with_args('new_message_message',
                                                        ["@" + message.from_user.username, message.text]))


@dp.message_handler(content_types=ContentTypes.PHOTO, state=DesignerChat.InChat)
async def in_chat_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        des_id = data['des_id']
    await bot.send_photo(chat_id=des_id, photo=message.photo[-1].file_id,
                         caption=get_string_with_args('new_message_message',
                                                      ["@" + message.from_user.username, message.caption]))


@dp.message_handler(content_types=ContentTypes.DOCUMENT, state=DesignerChat.InChat)
async def in_chat_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        des_id = data['des_id']
    await bot.send_document(chat_id=des_id, document=message.document.file_id,
                            caption=get_string_with_args('new_message_message',
                                                         ["@" + message.from_user.username, message.caption]))


@dp.message_handler(content_types=ContentTypes.AUDIO, state=DesignerChat.InChat)
async def in_chat_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        des_id = data['des_id']
    await bot.send_audio(chat_id=des_id, audio=message.audio.file_id,
                         caption=get_string_with_args('new_message_message',
                                                      ["@" + message.from_user.username, message.caption]))


@dp.message_handler(content_types=ContentTypes.VOICE, state=DesignerChat.InChat)
async def in_chat_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        des_id = data['des_id']
    await bot.send_voice(chat_id=des_id, voice=message.voice.file_id,
                         caption=get_string_with_args('new_message_message',
                                                      ["@" + message.from_user.username, message.caption]))


@dp.message_handler(TextEquals('support_button'), state=UserMenu.IsUser)
async def send_support_group(message: Message, state: FSMContext):
    group = await DB.get_support_group()
    support = group[0] if group[0] is not None else get_string('no_support_group_message')
    await bot.send_message(message.from_user.id, support)


@dp.message_handler(content_types=ContentTypes.TEXT, state=Support.InMenu)
async def back_to_menu(message: Message, state: FSMContext):
    user_menu = await user_menu_kb()
    for admin in admin_ids:
        await bot.send_message(admin, get_string_with_args('problem_message_message',
                                                           [message.from_user.username, message.text]))
    await bot.send_message(message.from_user.id, get_string('success_sent'), reply_markup=user_menu)
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('ref_system_button'), state=UserMenu.IsUser)
async def ref_system(message: Message, state: FSMContext):
    inviter = await DB.get_inviter(message.from_user.username)
    inviter_username = None
    if inviter is not None:
        user_rec = await DB.get_user(inviter[0])
        inviter_username = f'@{user_rec[3]}'
    referrals = await DB.get_referrals(message.from_user.id)
    referrals_count = len(referrals) if referrals is not None else 0
    if inviter is None:
        back = await back_kb()
        await bot.send_message(message.from_user.id,
                               get_string_with_args('referrals_menu_message', [inviter_username, referrals_count]),
                               reply_markup=back)
        await Referrals.EnterInviter.set()
        return
    await bot.send_message(message.from_user.id,
                           get_string_with_args('referrals_menu_message', [inviter_username, referrals_count]))


@dp.message_handler(TextEquals('back_button'), state=Referrals.EnterInviter)
async def back_to_user_menu(message: Message, state: FSMContext):
    user_menu = await user_menu_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=user_menu)
    await UserMenu.IsUser.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=Referrals.EnterInviter)
async def enter_inviter(message: Message, state: FSMContext):
    user_menu = await user_menu_kb()
    login = message.text if message.text[0] != "@" else message.text[1:]
    user = await DB.get_user_by_login(login)
    print(user)
    if not len(user):
        await bot.send_message(message.from_user.id, get_string('no_user_message'))
        return
    await DB.add_referral(user[0][1], message.from_user.username)
    await bot.send_message(message.from_user.id, get_string('inviter_was_added_message'), reply_markup=user_menu)
    await UserMenu.IsUser.set()
