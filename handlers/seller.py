import datetime

from aiogram.types import Message, CallbackQuery, ContentTypes
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import BotBlocked, BadRequest
from aiogram.types.inline_keyboard import InlineKeyboardButton

from tg_bot import bot, dp, DB

from filters.all_filters import *

from languages.lang_controller import get_string, get_string_with_args

from states.seller import *
from states.user import UserMenu

from keyboards.seller import *
from keyboards.user import user_menu_kb
from keyboards.admin import pay_reject_kb

from config import admin_ids

from utils.check_status import check_status


@dp.message_handler(commands=['seller'], state='*')
async def go_to_seller(message: Message, state: FSMContext):
    seller = await DB.get_seller(message.from_user.id)
    is_seller, is_designer = await check_status(message)
    seller_menu = await seller_menu_kb(is_seller, is_designer)
    print(is_seller, is_designer)
    if not is_seller and not is_designer:
        await bot.send_message(message.from_user.id, get_string('you_are_not_a_seller'))
        return
    if is_seller:
        if seller[2] is None and not is_designer:
            await bot.send_message(message.from_user.id, get_string('you_are_not_a_seller_yet'))
            return
    await DB.create_new_seller_query(message.from_user.id, message.from_user.username, None)
    await DB.set_designer_tg_id(f"@{message.from_user.username}", message.from_user.id)
    await bot.send_message(message.from_user.id, get_string('you_are_a_seller'), reply_markup=seller_menu)
    await SellerMenu.InMenu.set()


@dp.callback_query_handler(
    lambda c: c.data == 'google_type_goods_load' or c.data == 'facebook_type_goods_load' or c.data == 'partners_type_goods_load' or c.data == 'vip_type_goods_load',
    state='*')
async def get_categories_by_type_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    category_type = call.data.replace('_type_goods_load', '')
    all_categories = await DB.get_all_categories(category_type)
    if len(all_categories) == 0:
        await bot.send_message(call.from_user.id, get_string('empty'))
        return
    await bot.send_message(call.from_user.id, get_string('choose_category_name'))
    for category in all_categories:
        category_to_load = await category_to_load_kb(category[1], category[0])
        if category[4] == 'photo':
            await bot.send_photo(chat_id=call.from_user.id, photo=category[3],
                                 caption=get_string_with_args('category_card', [category[2]]),
                                 reply_markup=category_to_load)
        if category[4] == 'file':
            await bot.send_document(chat_id=call.from_user.id, document=category[3],
                                    caption=get_string_with_args('category_card', [category[2]]),
                                    reply_markup=category_to_load)
        if category[4] == 'None':
            await bot.send_message(call.from_user.id, get_string_with_args('category_card', [category[2]]),
                                   reply_markup=category_to_load)


@dp.callback_query_handler(text_startswith='choose_category_to_load_', state="*")
async def choose_category_to_buy_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    all_positions = await DB.get_all_positions(category_id=int(call.data.replace('choose_category_to_load_', '')))
    if len(all_positions) == 0:
        try:
            await bot.edit_message_text(get_string('empty'), call.from_user.id, call.message.message_id,
                                        reply_markup=None)
        except BadRequest:
            await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                           caption=get_string('empty'), reply_markup=None)
        return
    await bot.send_message(call.from_user.id, get_string('choose_a_position'))
    for pos in all_positions:
        pos_to_load_kb = await position_to_load_kb(pos[1], pos[0])
        if pos[4] == 'photo':
            await bot.send_photo(chat_id=call.from_user.id,
                                 caption=get_string_with_args('position_card', [pos[2], pos[5]]),
                                 photo=pos[3], reply_markup=pos_to_load_kb)
        if pos[4] == 'file':
            await bot.send_document(chat_id=call.from_user.id,
                                    caption=get_string_with_args('position_card', [pos[2], pos[5]]),
                                    document=pos[3], reply_markup=pos_to_load_kb)
        if pos[4] == 'None':
            await bot.send_message(call.from_user.id, get_string_with_args('position_card', [pos[2], pos[5]]),
                                   reply_markup=pos_to_load_kb)


@dp.callback_query_handler(text_startswith='choose_position_to_load_', state='*')
async def send_product_description(call: CallbackQuery, state: FSMContext):
    await call.answer()
    back = await back_kb()
    try:
        await bot.edit_message_text(call.message.text, call.from_user.id, call.message.message_id, reply_markup=None)
    except BadRequest:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=call.message.text, reply_markup=None)
    await bot.send_message(call.from_user.id, get_string('enter_product_description_message'),
                           reply_markup=back)
    async with state.proxy() as data:
        data['position_id'] = int(call.data.replace('choose_position_to_load_', ''))
    await LoadGoods.EnterProductDescription.set()


@dp.callback_query_handler(text_startswith='replace_invalid_seller_', state='*')
async def replace_product_seller(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                   caption=get_string('send_new_file_message'), reply_markup=None)
    back = await back_kb()
    await bot.send_message(call.from_user.id, get_string('replace_to_valid_file_message'), reply_markup=back)
    async with state.proxy() as data:
        data['product_id'] = int(call.data.replace('replace_invalid_seller_', ''))
    await InvalidGoods.SendNewFile.set()


@dp.callback_query_handler(text_startswith='remove_product_', state='*')
async def remove_product(call: CallbackQuery, state: FSMContext):
    await call.answer()
    are_you_sure = await are_you_sure_kb(call.data.replace('remove_product_'))
    await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                   caption=call.message.caption, reply_markup=are_you_sure)


@dp.callback_query_handler(text_startswith='confirm_remove_product_', state='*')
async def confirm_remove_product(call: CallbackQuery, state: FSMContext):
    await call.answer(get_string('deleted'))
    await DB.remove_product(int(call.data.replace('confirm_remove_product_', '')))
    await bot.delete_message(chat_id=call.from_user.id, message_id=call.message.message_id)


@dp.callback_query_handler(text_startswith='get_order_', state='*')
async def get_order_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    designer = await DB.get_designers_by_tg_id(call.from_user.id)
    price = designer[0][3]
    await DB.create_new_chat(orderer_id=int(call.data.replace('get_order_', '')), designer_id=call.from_user.id,
                             order_price=price)
    try:
        await bot.edit_message_text(get_string('order_was_getting_message'), call.from_user.id, call.message.message_id,
                                    reply_markup=None)
    except BadRequest:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=call.message.message_id, reply_markup=None)
    await bot.send_message(int(call.data.replace('get_order_', '')), get_string('order_was_confirmed_message'))


@dp.callback_query_handler(text_startswith='reject_order_', state='*')
async def get_order_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await bot.delete_message(call.from_user.id, call.message.message_id)
    await bot.send_message(call.from_user.id, get_string('order_was_rejected_message'))
    await bot.send_message(int(call.data.replace('get_order_', '')), get_string('designer_rejected_order_message'))


@dp.callback_query_handler(text_startswith='send_payment_request', state='*')
async def send_request_callback_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    async with state.proxy() as data:
        balances = data['balances']
    if not any(balances):
        await bot.edit_message_text(call.message.text + f"\n\n{get_string('no_balances_for_payment_message')}",
                                    call.from_user.id, call.message.message_id)
        return
    choose_balance = await choose_balance_kb(balances)
    await bot.edit_message_text(call.message.text + f"\n\n{get_string('choose_balance_message')}", call.from_user.id,
                                call.message.message_id, reply_markup=choose_balance)


@dp.callback_query_handler(text_startswith='payment_request_', state='*')
async def choose_balance(call: CallbackQuery, state: FSMContext):
    await call.answer()
    back = await back_kb()
    async with state.proxy() as data:
        data['type'] = call.data.replace('payment_request_', '')
    await bot.send_message(call.from_user.id, get_string('send_payment_amount_message'), reply_markup=back)
    await PaymentRequest.EnterAmount.set()


@dp.message_handler(content_types=ContentTypes.DOCUMENT, state=InvalidGoods.SendNewFile)
async def get_new_file_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        prod_id = data['product_id']
    await DB.replace_invalid_file(prod_id, message.document.file_id)
    await DB.increment_invalid(message.from_user.id)
    is_seller, is_designer = await check_status(message)
    seller_menu = await seller_menu_kb(is_seller, is_designer)
    await bot.send_message(message.from_user.id, get_string('successful_replace_invalid_message'),
                           reply_markup=seller_menu)
    await SellerMenu.InMenu.set()


@dp.message_handler(content_types=ContentTypes.DOCUMENT, state=LoadGoods.EnterProductFile)
async def enter_prod_file(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['product_file'] = message.document.file_id
        desc = data['product_description']
        price = data['product_price']
    back_confirm = await back_confirm_kb()
    await bot.send_document(chat_id=message.from_user.id, document=message.document.file_id,
                            caption=get_string_with_args('product_card_message', [desc, price]),
                            reply_markup=back_confirm)
    await LoadGoods.ConfirmAddingProduct.set()


@dp.message_handler(TextEquals('back_button'), state=PaymentRequest.EnterAmount)
async def back_to_seller_menu(message: Message, state: FSMContext):
    is_seller, is_designer = await check_status(message)
    seller_menu = seller_menu_kb(is_seller, is_designer)
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=seller_menu)
    await state.reset_data()
    await SellerMenu.InMenu.set()


@dp.message_handler(TextEquals('back_button'), state=PaymentRequest.EnterRequisites)
async def back_to_amount(message: Message, state: FSMContext):
    await bot.send_message(message.from_user.id, get_string('send_payment_amount_message'))
    await PaymentRequest.EnterAmount.set()


@dp.message_handler(TextEquals('back_button'), state=PaymentRequest.Confirming)
async def back_to_requisites(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_payment_requisites_message'), reply_markup=back)
    await PaymentRequest.EnterAmount.set()


@dp.message_handler(TextEquals('back_button'), state=LoadGoods.EnterProductPrice)
async def back_to_enter_product_description_handler(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_product_description_message'), reply_markup=back)
    await LoadGoods.EnterProductDescription.set()


@dp.message_handler(TextEquals('back_button'), state=LoadGoods.EnterProductFile)
async def back_to_enter_product_description_handler(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_product_description_message'), reply_markup=back)
    await LoadGoods.EnterProductPrice.set()


@dp.message_handler(TextEquals('back_button'), state=SellerMenu.InMenu)
async def back_to_user(message: Message, state: FSMContext):
    user_menu = await user_menu_kb()
    await bot.send_message(message.from_user.id, get_string('you_are_user_now'), reply_markup=user_menu)
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('back_button'), state=InvalidGoods.SendNewFile)
async def back_to_menu(message: Message, state: FSMContext):
    is_seller, is_designer = await check_status(message)
    seller_menu = await seller_menu_kb(is_seller, is_designer)
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=seller_menu)
    await SellerMenu.InMenu.set()


@dp.message_handler(TextEquals('back_button'), state=SellerMailing.EnterText)
async def back_to_entering_mailing_text(message: Message, state: FSMContext):
    is_seller, is_designer = await check_status(message)
    seller_menu = await seller_menu_kb(is_seller, is_designer)
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=seller_menu)
    await SellerMenu.InMenu.set()


@dp.message_handler(TextEquals('back_button'), state=LoadGoods.EnterProductDescription)
async def back_to_seller_menu(message: Message, state: FSMContext):
    await state.reset_data()
    is_seller, is_designer = await check_status(message)
    seller_menu = await seller_menu_kb(is_seller, is_designer)
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=seller_menu)
    await SellerMenu.InMenu.set()


@dp.message_handler(TextEquals('back_button'), state=Designer.LoadPortfolio)
async def back_to_seller_menu(message: Message, state: FSMContext):
    is_seller, is_designer = await check_status(message)
    seller_menu = await seller_menu_kb(is_seller, is_designer)
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=seller_menu)
    await SellerMenu.InMenu.set()


@dp.message_handler(TextEquals('back_button'), state=Designer.InChoiceOfChats)
async def back_to_seller_menu(message: Message, state: FSMContext):
    is_seller, is_designer = await check_status(message)
    seller_menu = await seller_menu_kb(is_seller, is_designer)
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=seller_menu)
    await state.reset_data()
    await SellerMenu.InMenu.set()


@dp.message_handler(TextEquals('seller_mailing_button'), state=SellerMenu.InMenu)
async def seller_mailing_handler(message: Message, state: FSMContext):
    all_subscribers = await DB.get_subscribers_by_seller(message.from_user.id)
    if len(all_subscribers) == 0:
        await bot.send_message(message.from_user.id, get_string('no_subscribers_message'))
        return
    back_send = await back_send_kb()
    await bot.send_message(message.from_user.id, get_string_with_args('mailing_message', [len(all_subscribers)]),
                           reply_markup=back_send)
    await SellerMailing.EnterText.set()


@dp.message_handler(TextEquals('send_button'), state=SellerMailing.EnterText)
async def enter_mailing_text_handler(message: Message, state: FSMContext):
    all_subscribers = await DB.get_subscribers_by_seller(message.from_user.id)
    goods_count = await DB.get_all_logs_for_mailing(message.from_user.id, datetime.datetime.now().timestamp())
    last_mailing = await DB.get_last_mailing(message.from_user.id)
    if not goods_count > 0:
        await bot.send_message(message.from_user.id, get_string('no_logs_in_last_time_message'))
        return
    if last_mailing is not None:
        if datetime.datetime.now().timestamp() - last_mailing < 3600.0:
            await bot.send_message(message.from_user.id, get_string('cant_mailing_yet_message'))
            return
    if last_mailing is None or datetime.datetime.now().timestamp() - last_mailing >= 3600.0:
        success = 0
        blocked = 0
        for sub in all_subscribers:
            cancel_mailing = await cancel_mailing_kb(message.from_user.id)
            try:
                await bot.send_message(sub[0],
                                       get_string_with_args('mailing_from_sellers_message',
                                                            [message.from_user.username, goods_count]),
                                       reply_markup=cancel_mailing)
                success += 1
            except BotBlocked:
                blocked += 1
        is_seller, is_designer = await check_status(message)
        seller_menu = await seller_menu_kb(is_seller, is_designer)
        await state.reset_data()
        await bot.send_message(message.from_user.id,
                               get_string_with_args('final_of_mailing_message', [success, blocked]),
                               reply_markup=seller_menu)
        await SellerMenu.InMenu.set()


@dp.message_handler(TextEquals('goods_load_button'), state=SellerMenu.InMenu)
async def choice_category_for_goods_load(message: Message, state: FSMContext):
    positions_ids = await DB.get_positions_ids(message.from_user.id)
    if positions_ids == '' or positions_ids is None:
        await bot.send_message(message.from_user.id, get_string('empty'))
        return
    positions_ids = positions_ids.split(':')
    await bot.send_message(message.from_user.id, get_string('choose_a_position'))
    for pos in positions_ids:
        if pos == '':
            continue
        pos_rec = await DB.get_position_by_id(int(pos))
        pos_name = pos_rec[1]
        pos_to_load_kb = await position_to_load_kb(pos_name, pos)
        if pos_rec[4] == 'photo':
            await bot.send_photo(chat_id=message.from_user.id,
                                 caption=get_string_with_args('position_card_seller', [pos_rec[2]]),
                                 photo=pos_rec[3], reply_markup=pos_to_load_kb)
        if pos_rec[4] == 'file':
            await bot.send_document(chat_id=message.from_user.id,
                                    caption=get_string_with_args('position_card_seller', [pos_rec[2]]),
                                    document=pos_rec[3], reply_markup=pos_to_load_kb)
        if pos_rec[4] == 'None':
            await bot.send_message(message.from_user.id,
                                   get_string_with_args('position_card_seller', [pos_rec[2]]),
                                   reply_markup=pos_to_load_kb)


@dp.message_handler(content_types=ContentTypes.TEXT, state=LoadGoods.EnterProductDescription)
async def enter_prod_desc(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['product_description'] = message.text
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_product_price_message'), reply_markup=back)
    await LoadGoods.EnterProductPrice.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=LoadGoods.EnterProductPrice)
async def enter_prod_desc(message: Message, state: FSMContext):
    try:
        float(message.text)
    except ValueError:
        await bot.send_message(message.from_user.id, get_string('incorrect_value'))
        return
    async with state.proxy() as data:
        data['product_price'] = float(message.text)
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_product_file_message'), reply_markup=back)
    await LoadGoods.EnterProductFile.set()


@dp.message_handler(TextEquals('back_button'), state=LoadGoods.ConfirmAddingProduct)
async def enter_prod_desc(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_product_file_message'), reply_markup=back)
    await LoadGoods.EnterProductPrice.set()


@dp.message_handler(TextEquals('confirm_button'), state=LoadGoods.ConfirmAddingProduct)
async def confirm_adding_product_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        position_id = data['position_id']
        product_desc = data['product_description']
        product_file = data['product_file']
        product_price = data['product_price']
    await DB.add_product(product_desc=product_desc, product_file=product_file, seller_id=message.from_user.id,
                         position_id=position_id, product_price=product_price,
                         load_time=datetime.datetime.now().timestamp())
    is_seller, is_designer = await check_status(message)
    seller_menu = await seller_menu_kb(is_seller, is_designer)
    await bot.send_message(message.from_user.id, get_string('successfully_product_adding_message'),
                           reply_markup=seller_menu)
    await SellerMenu.InMenu.set()


@dp.message_handler(TextEquals('replace_invalid_button'), state=SellerMenu.InMenu)
async def send_invalid_goods_list(message: Message, state: FSMContext):
    invalid_goods = await DB.get_invalid_goods(message.from_user.id)
    if len(invalid_goods) == 0:
        await bot.send_message(message.from_user.id, get_string('empty'))
        return
    for prod in invalid_goods:
        replace_remove_product = await replace_remove_product_kb(prod[0])
        await bot.send_document(chat_id=message.from_user.id, document=prod[2], caption=prod[1],
                                reply_markup=replace_remove_product)


@dp.message_handler(TextEquals('load_portfolio_button'), state=SellerMenu.InMenu)
async def load_portfolio_handler(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_new_portfolio_url_message'), reply_markup=back)
    await Designer.LoadPortfolio.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=Designer.LoadPortfolio)
async def enter_portfolio_link(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton(text=message.text, url=message.text))
    try:
        test_message = await bot.send_message(message.from_user.id, message.text, reply_markup=keyboard)
        await bot.delete_message(message.from_user.id, test_message.message_id)
    except BadRequest:
        await bot.send_message(message.from_user.id, get_string('incorrect_value'))
        return
    await DB.set_new_portfolio_url(message.text, message.from_user.username)
    is_seller, is_digit = await check_status(message)
    seller_menu = await seller_menu_kb(is_seller, is_digit)
    await bot.send_message(message.from_user.id, get_string('url_success_edited_message'), reply_markup=seller_menu)
    await SellerMenu.InMenu.set()


@dp.message_handler(TextEquals('back_button'), state=Designer.InChat)
async def back_to_seller_menu(message: Message, state: FSMContext):
    is_seller, is_designer = await check_status(message)
    seller_menu = await seller_menu_kb(is_seller, is_designer)
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=seller_menu)
    await SellerMenu.InMenu.set()


@dp.message_handler(TextEquals('back_button'), state=Designer.SendOrderDocument)
@dp.message_handler(TextEquals('chat_button'), state=SellerMenu.InMenu)
async def get_all_chats(message: Message, state: FSMContext):
    orderers = await DB.get_orderers_for_chat(message.from_user.id)
    orderers_logins = []
    for order in orderers:
        ord_by_id = await DB.get_user(order[0])
        login = ord_by_id[3]
        orderers_logins.insert(-1, [login, order[0]])
    chats = await chats_kb(orderers_logins)
    if chats is None:
        is_seller, is_designer = await check_status(message)
        seller_menu = await seller_menu_kb(is_seller, is_designer)
        await bot.send_message(message.from_user.id, get_string('no_orderers_for_chat_message'),
                               reply_markup=seller_menu)
        await SellerMenu.InMenu.set()
        return
    await bot.send_message(message.from_user.id, get_string('choose_designer_message'), reply_markup=chats)
    async with state.proxy() as data:
        user = await DB.get_designer_by_login(message.from_user.username)
        data['nickname'] = user[1]
        data['orderers'] = orderers_logins
        print(data['nickname'])
    await Designer.InChoiceOfChats.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=Designer.InChoiceOfChats)
async def start_to_chatting(message: Message, state: FSMContext):
    is_orderer = False
    ord_id = 0
    async with state.proxy() as data:
        orderers = data['orderers']
    for order in orderers:
        if order[0] == message.text:
            ord_id = order[1]
            is_orderer = True
            break
    if not is_orderer:
        is_seller, is_designer = await check_status(message)
        seller_menu = await seller_menu_kb(is_seller, is_designer)
        await bot.send_message(message.from_user.id, get_string('is_not_orderer_message'), reply_markup=seller_menu)
        return
    async with state.proxy() as data:
        data['ord_id'] = ord_id
    back_send_complete_order = await back_send_complete_order_kb()
    await bot.send_message(message.from_user.id, get_string('chat_started_message'),
                           reply_markup=back_send_complete_order)
    await Designer.InChat.set()


@dp.message_handler(TextEquals('send_complete_order_button'), state=Designer.InChat)
async def send_complete_order_handler(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_order_document_message'), reply_markup=back)
    await Designer.SendOrderDocument.set()


@dp.message_handler(content_types=ContentTypes.DOCUMENT, state=Designer.SendOrderDocument)
async def send_order_document_handler(message: Message, state: FSMContext):
    back = await back_kb()
    async with state.proxy() as data:
        ord_id = data['ord_id']
    await DB.add_order_file_to_chat(message.from_user.id, ord_id, message.document.file_id)
    price = await DB.get_order_price_from_chat(ord_id, message.from_user.id)
    balances = await DB.get_all_balances(ord_id)
    balances_sum = balances[0] + balances[1] + balances[2] + balances[3]
    await bot.send_message(ord_id, get_string('designer_sent_order_message'))
    if balances_sum < price:
        await bot.send_message(ord_id, get_string('not_enough_money_to_order_message'))
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
        await bot.send_message(ord_id, get_string('successfully_bought_message'))
        await DB.write_off_balances(write_off, ord_id)
        chat = await DB.get_chat(message.from_user.id, ord_id)
        print(chat)
        await DB.add_purchase(ord_id, -chat[0], date)
        purchase = await DB.get_purchase_by_date(date, ord_id)
        purchase_id = purchase[0]
        await DB.create_hold(write_off, purchase_id, message.from_user.id,
                             date)
        await DB.close_chat(chat[0])
        await DB.increment_creatives(message.from_user.id)
        return_invalid = await designer_order_file_kb(purchase_id, message.from_user.username)
        await bot.send_document(chat_id=ord_id, document=message.document.file_id, caption=message.caption,
                                reply_markup=return_invalid)
    is_seller, is_designer = await check_status(message)
    seller_menu = await seller_menu_kb(is_seller, is_designer)
    await bot.send_message(message.from_user.id, get_string('order_was_successful_sent_message'),
                           reply_markup=seller_menu)


@dp.message_handler(content_types=ContentTypes.TEXT, state=Designer.InChat)
async def in_chat_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        nick = data['nickname']
        ord_id = data['ord_id']
    await bot.send_message(ord_id, get_string_with_args('new_message_message',
                                                        [nick, message.text]))


@dp.message_handler(content_types=ContentTypes.PHOTO, state=Designer.InChat)
async def in_chat_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        nick = data['nickname']
        ord_id = data['ord_id']
    await bot.send_photo(chat_id=ord_id, photo=message.photo[-1].file_id,
                         caption=get_string_with_args('new_message_message',
                                                      [nick, message.caption]))


@dp.message_handler(content_types=ContentTypes.DOCUMENT, state=Designer.InChat)
async def in_chat_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        nick = data['nickname']
        ord_id = data['ord_id']
    await bot.send_document(chat_id=ord_id, document=message.document.file_id,
                            caption=get_string_with_args('new_message_message',
                                                         [nick, message.caption]))


@dp.message_handler(content_types=ContentTypes.AUDIO, state=Designer.InChat)
async def in_chat_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        nick = data['nickname']
        ord_id = data['ord_id']
    await bot.send_audio(chat_id=ord_id, audio=message.audio.file_id,
                         caption=get_string_with_args('new_message_message',
                                                      [nick, message.caption]))


@dp.message_handler(content_types=ContentTypes.VOICE, state=Designer.InChat)
async def in_chat_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        nick = data['nickname']
        ord_id = data['ord_id']
    await bot.send_voice(chat_id=ord_id, voice=message.voice.file_id,
                         caption=get_string_with_args('new_message_message',
                                                      [nick, message.caption]))


@dp.message_handler(TextEquals('wallet_button'), state=SellerMenu.InMenu)
async def show_balances(message: Message, state: FSMContext):
    balances = await DB.get_seller_balances(message.from_user.id)
    holds = await DB.get_hold_by_seller(message.from_user.id)
    print(holds)
    hold_sum = 0.0
    if holds is not None:
        for hold in holds:
            hold_sum += hold[3] + hold[4] + hold[5]

    send_payment_request = await send_payment_request_kb()

    await bot.send_message(message.from_user.id, get_string_with_args('seller_balances_message',
                                                                      [balances[0], balances[1], balances[2],
                                                                       hold_sum]), reply_markup=send_payment_request)
    async with state.proxy() as data:
        data['balances'] = balances


@dp.message_handler(content_types=ContentTypes.TEXT, state=PaymentRequest.EnterAmount)
async def send_payment_amount(message: Message, state: FSMContext):
    async with state.proxy() as data:
        balances = data['balances']
        payment_type = data['type']
    try:
        float(message.text)
    except ValueError:
        await bot.send_message(message.from_user.id, get_string('incorrect_value'))
        return
    index = 0
    if payment_type == 'qiwi_type':
        index = 0
    if payment_type == 'bit_type':
        index = 1
    if payment_type == 'capitalist_type':
        index = 2
    if float(message.text) > balances[index]:
        await bot.send_message(message.from_user.id, get_string('enter_valid_amount_message'))
        return
    async with state.proxy() as data:
        data['amount'] = float(message.text)
    await bot.send_message(message.from_user.id, get_string('send_requisites_message'))
    await PaymentRequest.EnterRequisites.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=PaymentRequest.EnterRequisites)
async def send_requisites(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['requisites'] = message.text
        pay_type = data['type']
        amount = data['amount']
    back_send = await back_send_kb()
    await bot.send_message(message.from_user.id, get_string('check_your_data_and_send_message'), reply_markup=back_send)
    await PaymentRequest.Confirming.set()


@dp.message_handler(TextEquals('send_button'), state=PaymentRequest.Confirming)
async def confirm_to_send(message: Message, state: FSMContext):
    async with state.proxy() as data:
        pay_type = data['type']
        amount = data['amount']
        requisites = data['requisites']
    index = 0
    write_off = [0.0, 0.0, 0.0, 0.0]
    if pay_type == 'qiwi_type':
        index = 0
    if pay_type == 'bit_type':
        index = 1
    if pay_type == 'capitalist_type':
        index = 2
    write_off[index] -= amount
    request_id = await DB.create_payment_request(message.from_user.id, pay_type, amount, requisites)
    await DB.top_up_seller_balances(message.from_user.id, write_off)
    pay_reject = await pay_reject_kb(request_id)
    for admin in admin_ids:
        await bot.send_message(admin, get_string_with_args('new_payment_request',
                                                           [f"@{message.from_user.username}", message.from_user.id,
                                                            get_string(pay_type), amount, requisites]),
                               reply_markup=pay_reject)
    is_seller, is_designer = await check_status(message)
    seller_menu = await seller_menu_kb(is_seller, is_designer)
    await bot.send_message(message.from_user.id, get_string('success_request_message'), reply_markup=seller_menu)
    await SellerMenu.InMenu.set()

''' Переделка '''
@dp.message_handler(TextEquals('order_button'), state=SellerMenu.InMenu)
async def payout(message: Message, state: FSMContext):
    payout = await payout_kb()
    await bot.send_message(message.from_user.id, 'Выберите кошелек на выплату', reply_markup=payout)
''' Выплата текстом, отправить сообщение'''
@dp.callback_query_handler(
    lambda c: c.data == 'capitalist' or c.data == 'bitcoin' or c.data == 'litecoin' or c.data == 'ethereum' or c.data == 'monero'
    or c.data == 'payeer' or c.data == 'qiwi',
    state=SellerMenu.InMenu)
async def choose_payot(call: CallbackQuery, state: FSMContext):
    await call.answer()
    send = await back_confirm_pay_kb()
    await bot.send_message(call.from_user.id, 'Введите номер кошелька', reply_markup=send)

@dp.message_handler(TextEquals('confirm_button_pay'), state=SellerMenu.InMenu)
async def payout(message: Message, state: FSMContext):
    send = await back_confirm_pay_kb_2()
    await bot.send_message(message.from_user.id, 'Введите сумму', reply_markup=send)


