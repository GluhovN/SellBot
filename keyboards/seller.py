from aiogram.types.reply_keyboard import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from languages.lang_controller import get_string


async def back_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(back_button)
    return keyboard


async def back_send_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = KeyboardButton(get_string('back_button'))
    send_button = KeyboardButton(get_string('send_button'))
    keyboard.row(back_button, send_button)
    return keyboard


async def back_confirm_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = KeyboardButton(get_string('back_button'))
    confirm_button = KeyboardButton(get_string('confirm_button'))
    keyboard.row(back_button, confirm_button)
    return keyboard


async def seller_menu_kb(is_seller: bool, is_designer: bool):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = KeyboardButton(get_string('back_button'))
    wallet_button = KeyboardButton(get_string('wallet_button'))
    order_button = KeyboardButton(get_string('order_button'))
    if is_seller:
        mailing_button = KeyboardButton(get_string('seller_mailing_button'))
        goods_load_button = KeyboardButton(get_string('goods_load_button'))
        replace_invalid_button = KeyboardButton(get_string('replace_invalid_button'))
        keyboard.row(goods_load_button, replace_invalid_button)
        keyboard.row(mailing_button, order_button)
    if is_designer:
        load_portfolio_button = KeyboardButton(get_string('load_portfolio_button'))
        chat_button = KeyboardButton(get_string('chat_button'))
        keyboard.row(load_portfolio_button, chat_button)
    keyboard.row(back_button)
    return keyboard


async def cancel_mailing_kb(seller_id):
    keyboard = InlineKeyboardMarkup()
    cancel_mailing_button = InlineKeyboardButton(text=get_string('cancel_subscription_button'),
                                                 callback_data=f'cancel_mailing_{seller_id}')
    keyboard.row(cancel_mailing_button)
    return keyboard


async def category_to_load_kb(category_name, category_id):
    keyboard = InlineKeyboardMarkup()
    category_name_button = InlineKeyboardButton(text=category_name,
                                                callback_data='choose_category_to_load_' + str(category_id))
    keyboard.row(category_name_button)
    return keyboard


async def position_to_load_kb(position_name, position_id):
    keyboard = InlineKeyboardMarkup()
    position_name_button = InlineKeyboardButton(text=position_name,
                                                callback_data='choose_position_to_load_' + str(position_id))
    keyboard.insert(position_name_button)
    return keyboard


async def category_types_kb():
    keyboard = InlineKeyboardMarkup()
    google_type_button = InlineKeyboardButton(text=get_string('google_type_button'),
                                              callback_data='google_type_goods_load')
    facebook_type_button = InlineKeyboardButton(text=get_string('facebook_type_button'),
                                                callback_data='facebook_type_goods_load')
    vip_services_button = InlineKeyboardButton(text=get_string('vip_services_button'),
                                               callback_data='vip_type_goods_load')
    keyboard.row(google_type_button, facebook_type_button)
    keyboard.row(vip_services_button)
    return keyboard


async def replace_remove_product_kb(prod_id):
    keyboard = InlineKeyboardMarkup()
    replace_invalid_button = InlineKeyboardButton(text=get_string('replace_invalid_button'),
                                                  callback_data=f'replace_invalid_seller_{prod_id}')
    remove_product_button = InlineKeyboardButton(text=get_string('remove_product_button'),
                                                 callback_data=f'remove_product_{prod_id}')
    keyboard.row(replace_invalid_button, remove_product_button)
    return keyboard


async def are_you_sure_kb(prod_id):
    keyboard = InlineKeyboardMarkup()
    are_you_sure_button = InlineKeyboardButton(text=get_string('are_you_sure_button'),
                                               callback_data=f'confirm_remove_product_{prod_id}')
    keyboard.row(are_you_sure_button)
    return keyboard


async def chats_kb(orderers: list):
    if len(orderers) == 0:
        return None
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(back_button)
    for order in orderers:
        des_button = KeyboardButton(order[0])
        keyboard.row(des_button)
    return keyboard


async def back_send_complete_order_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = KeyboardButton(get_string('back_button'))
    send_complete_order_button = KeyboardButton(get_string('send_complete_order_button'))
    keyboard.row(back_button, send_complete_order_button)
    return keyboard


async def return_invalid_kb(purchase_id):
    keyboard = InlineKeyboardMarkup()
    return_invalid_button = InlineKeyboardButton(text=get_string('return_invalid_button'),
                                                 callback_data=f'return_invalid_{purchase_id}')
    keyboard.row(return_invalid_button)
    return keyboard


async def designer_order_file_kb(purchase_id, designer_username):
    keyboard = InlineKeyboardMarkup()
    return_invalid_button = InlineKeyboardButton(text=get_string('return_invalid_button'),
                                                 callback_data=f'return_invalid_{purchase_id}')
    keyboard.row(return_invalid_button)
    return keyboard


async def send_payment_request_kb():
    keyboard = InlineKeyboardMarkup()
    send_payment_request_button = InlineKeyboardButton(text=get_string('send_payment_request_button'),
                                                       callback_data='send_payment_request')
    keyboard.row(send_payment_request_button)
    return keyboard


async def choose_balance_kb(balances: list):
    keyboard = InlineKeyboardMarkup()
    for i in range(len(balances)):
        balance_type = ''
        if balances[i] == 0.0:
            continue
        if i == 0:
            balance_type = 'qiwi_type'
        if i == 1:
            balance_type = 'bit_type'
        if i == 2:
            balance_type = 'capitalist_type'
        keyboard.insert(
            InlineKeyboardButton(text=get_string(balance_type), callback_data=f'payment_request_{balance_type}'))
    return keyboard


async def replace_reject_kb(product):
    keyboard = InlineKeyboardMarkup()
    replace_button = InlineKeyboardButton(text=get_string('replace_button'), callback_data=f'replace_product_{product}')
    reject_button = InlineKeyboardButton(text=get_string('reject_button'),
                                         callback_data=f'reject_replace_product_{product}')
    keyboard.row(replace_button, reject_button)
    return keyboard

async def payout_kb():
    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton('Capitalist', callback_data='capitalist')
    button2 = InlineKeyboardButton('Bitcoin', callback_data='bitcoin')
    button3 = InlineKeyboardButton('Litecoin', callback_data='litecoin')
    button4 = InlineKeyboardButton('Ethereum', callback_data='ethereum')
    button5 = InlineKeyboardButton('Monero', callback_data='monero')
    button6 = InlineKeyboardButton('Payeer', callback_data='payeer')
    button7 = InlineKeyboardButton('Киви', callback_data='qiwi')
    keyboard.row(button1)
    keyboard.row(button2)
    keyboard.row(button3)
    keyboard.row(button4)
    keyboard.row(button5)
    keyboard.row(button6)
    keyboard.row(button7)
    return keyboard

async def back_confirm_pay_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = KeyboardButton(get_string('back_button_pay'))
    confirm_button = KeyboardButton(get_string('confirm_button_pay'))
    keyboard.row(back_button, confirm_button)
    return keyboard

async def back_confirm_pay_kb_2():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = KeyboardButton(get_string('back_button_pay_2'))
    confirm_button = KeyboardButton(get_string('confirm_button_pay_2'))
    keyboard.row(back_button, confirm_button)
    return keyboard
