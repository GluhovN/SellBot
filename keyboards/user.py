from aiogram.types.reply_keyboard import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from languages.lang_controller import get_string

from tg_bot import DB


async def back_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(back_button)
    return keyboard


async def user_menu_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    buy_button = KeyboardButton(get_string('goods_button'))
    partnership_button = KeyboardButton(get_string('partnership_button'))
    seller_list_button = KeyboardButton(get_string('seller_list_button'))
    my_purchases_button = KeyboardButton(get_string('my_purchases_button'))
    ref_system_button = KeyboardButton(get_string('ref_system_button'))
    support_button = KeyboardButton(get_string('support_button'))
    chat_button = KeyboardButton(get_string('chat_button'))
    keyboard.row(seller_list_button, ref_system_button)
    keyboard.row(partnership_button, my_purchases_button)
    keyboard.row(buy_button, support_button, chat_button)
    return keyboard

async def categories_types_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    google_type_button = KeyboardButton(get_string('google_type_button'))
    facebook_type_button = KeyboardButton(get_string('facebook_type_button'))
    keyboard.row(google_type_button, facebook_type_button)
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(back_button)
    return keyboard


async def category_to_buy_kb(category_name, category_id, goods_count):
    keyboard = InlineKeyboardMarkup()
    category_name_button = InlineKeyboardButton(text=f'{goods_count} | {category_name}',
                                                callback_data='choose_category_to_buy_' + str(category_id))
    back_button = InlineKeyboardButton(text=get_string('back_button'), callback_data='back_to_user_profile')
    keyboard.row(category_name_button)
    keyboard.row(back_button)
    return keyboard


async def designer_category_to_buy_kb(category_name, category_id):
    keyboard = InlineKeyboardMarkup()
    category_name_button = InlineKeyboardButton(text=category_name,
                                                callback_data='choose_designer_category_to_buy_' + str(category_id))
    back_button = InlineKeyboardButton(text=get_string('back_button'), callback_data='back_to_user_profile')
    keyboard.insert(category_name_button)
    keyboard.row(back_button)
    return keyboard


async def designers_list_kb(designers: list):
    keyboard = InlineKeyboardMarkup()
    for des in designers:
        keyboard.insert(InlineKeyboardButton(text=des[0], callback_data=f'open_designer_card_{des[1]}'))
    back_button = InlineKeyboardButton(text=get_string('back_button'), callback_data='back_to_user_profile')
    keyboard.row(back_button)
    return keyboard


async def position_to_buy_kb(position_name, position_id, categories_type, goods_count):
    keyboard = InlineKeyboardMarkup()
    position_name_button = InlineKeyboardButton(text=f'{goods_count} | {position_name}',
                                                callback_data='choose_position_to_buy_' + str(position_id))
    back_button = InlineKeyboardButton(text=get_string('back_button'), callback_data=categories_type)
    keyboard.insert(position_name_button)
    keyboard.row(back_button)
    return keyboard


async def open_designer_card_kb(url, list_message_id, designer_id, user_id, designer_tg_id, position_id):
    keyboard = InlineKeyboardMarkup()
    designer_portfolio_link_button = InlineKeyboardButton(text=get_string('designer_portfolio_link_button'),
                                                          url=url)
    make_order_button = InlineKeyboardButton(text=get_string('make_order_button'),
                                             callback_data=f'make_order_{designer_id}')
    back_button = InlineKeyboardButton(text=get_string('back_button'),
                                       callback_data=f'back_to_designers_list_{list_message_id}')
    keyboard.row(designer_portfolio_link_button)
    keyboard.row(make_order_button)
    if designer_tg_id is not None:
        chat_ended = await DB.get_chat(designer_id=designer_tg_id, orderer_id=user_id, is_ended=True)
        chat_open = await DB.get_chat(designer_id=designer_tg_id, orderer_id=user_id, is_ended=False)
        if chat_open is not None or chat_ended is not None:
            keyboard.row(
                InlineKeyboardButton(text=get_string('rate_designer_button'),
                                     callback_data=f'rate_designer_{position_id}'))
    keyboard.row(back_button)
    return keyboard


async def designer_position_kb(position_name, position_id, url):
    keyboard = InlineKeyboardMarkup()
    position_name_button = InlineKeyboardButton(text=position_name,
                                                callback_data='designer_position_' + str(position_id))
    designer_portfolio_link_button = InlineKeyboardButton(text=get_string('designer_portfolio_link_button'), url=url)
    keyboard.row(position_name_button)
    keyboard.row(designer_portfolio_link_button)
    return keyboard


async def user_profile_kb(user):
    keyboard = InlineKeyboardMarkup()
    top_up_balance_button = InlineKeyboardButton(text=get_string('top_up_balance_button'),
                                                 callback_data='top_up_balance')
    buy_google_accounts_button = InlineKeyboardButton(text=get_string('buy_google_accounts_button'),
                                                      callback_data='google_user')
    buy_facebook_accounts_button = InlineKeyboardButton(text=get_string('buy_facebook_accounts_button'),
                                                        callback_data='facebook_user')
#    creatives_button = InlineKeyboardButton(text=get_string('creatives_button'), callback_data='creatives')
    vip_services_button = InlineKeyboardButton(text=get_string('vip_services_button'), callback_data='vip_user')
#    partners_button = InlineKeyboardButton(text=get_string('partners_type_button'), callback_data='partners_user')
    keyboard.row(top_up_balance_button)
    keyboard.row(buy_google_accounts_button)
    keyboard.row(buy_facebook_accounts_button)
#    keyboard.row(creatives_button)
    keyboard.row(vip_services_button)
#    keyboard.row(partners_button)
    return keyboard


async def choice_of_categories_kb():
    keyboard = InlineKeyboardMarkup()
    google_type_button = InlineKeyboardButton(text=get_string('google_type_button'), callback_data='google_user')
    facebook_type_button = InlineKeyboardButton(text=get_string('facebook_type_button'), callback_data='facebook_user')
    keyboard.row(google_type_button, facebook_type_button)
    return keyboard


async def send_back_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    send_button = KeyboardButton(get_string('send_button'))
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(send_button, back_button)
    return keyboard


async def payments_methods_kb(qiwi, apirone, capitalist):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    qiwi_data = KeyboardButton(get_string('qiwi_payment_data'))
    apirone_data = KeyboardButton(get_string('apirone_payment_data'))
    capitalist_data = KeyboardButton(get_string('capitalist_payment_data'))
    back_button = KeyboardButton(get_string('back_button'))
    if qiwi:
        keyboard.row(qiwi_data)
    if apirone:
        keyboard.row(apirone_data)
    if capitalist:
        keyboard.row(capitalist_data)
    keyboard.row(back_button)
    return keyboard


async def confirm_user_agreement_kb(user_id):
    keyboard = InlineKeyboardMarkup()
    approve_button = InlineKeyboardButton(text=get_string('approve_button'),
                                          callback_data='approve_user_agreement_' + str(user_id))
    keyboard.row(approve_button)
    return keyboard


async def seller_question_kb(question_id):
    keyboard = InlineKeyboardMarkup()
    to_answer_button = InlineKeyboardButton(text=get_string('to_answer_button'),
                                            callback_data='seller_question_' + question_id)
    if question_id != '1':
        back_button = InlineKeyboardButton(text=get_string('back_button'),
                                           callback_data='previous_question_' + question_id)
        keyboard.row(to_answer_button, back_button)
    else:
        keyboard.row(to_answer_button)
    return keyboard


async def back_to_question_kb(qid):
    keyboard = InlineKeyboardMarkup()
    back_button = InlineKeyboardButton(text=get_string('back_button'),
                                       callback_data='previous_question_' + qid)
    keyboard.row(back_button)
    return keyboard


async def send_back_query_kb(user_id, qid):
    keyboard = InlineKeyboardMarkup()
    send_button = InlineKeyboardButton(text=get_string('send_button'), callback_data='send_query_' + str(user_id))
    back_button = InlineKeyboardButton(text=get_string('back_button'), callback_data='previous_question_' + str(qid))
    keyboard.row(send_button, back_button)
    return keyboard


async def seller_mailing_kb(seller_id):
    keyboard = InlineKeyboardMarkup()
    subscribe_to_mailing_button = InlineKeyboardButton(text=get_string('subscribe_to_mailing_button'),
                                                       callback_data=f'subscribe_to_mailing_{seller_id}')
    keyboard.row(subscribe_to_mailing_button)
    return keyboard


async def cancel_mailing_kb(seller_id):
    keyboard = InlineKeyboardMarkup()
    cancel_mailing_button = InlineKeyboardButton(text=get_string('cancel_subscription_button'),
                                                 callback_data=f'cancel_mailing_{seller_id}')
    keyboard.row(cancel_mailing_button)
    return keyboard


async def buy_kb(prod_id, category_id):
    keyboard = InlineKeyboardMarkup()
    buy_button = InlineKeyboardButton(text=get_string('buy_button'), callback_data=f'buy_prod_{prod_id}')
    back_button = InlineKeyboardButton(text=get_string('back_button'),
                                       callback_data=f'choose_category_to_buy_{category_id}')
    keyboard.row(buy_button)
    keyboard.row(back_button)
    return keyboard


async def pay_order_kb(prod_id):
    keyboard = InlineKeyboardMarkup()
    pay_order_button = InlineKeyboardButton(text=get_string('pay_order_button'), callback_data=f'pay_order_{prod_id}')
    keyboard.row(pay_order_button)
    return keyboard


async def return_invalid_kb(purchase_id):
    keyboard = InlineKeyboardMarkup()
    return_invalid_button = InlineKeyboardButton(text=get_string('return_invalid_button'),
                                                 callback_data=f'return_invalid_{purchase_id}')
    keyboard.row(return_invalid_button)
    return keyboard


async def get_reject_order_kb(from_user):
    keyboard = InlineKeyboardMarkup()
    get_order_button = InlineKeyboardButton(text=get_string('get_order_button'), callback_data=f'get_order_{from_user}')
    reject_order_button = InlineKeyboardButton(text=get_string('reject_order_button'),
                                               callback_data=f'reject_order_{from_user}')
    keyboard.row(get_order_button, reject_order_button)
    return keyboard


async def chats_kb(designers: list):
    if len(designers) == 0:
        return None
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(back_button)
    for des in designers:
        des_button = KeyboardButton(des[0])
        keyboard.row(des_button)
    return keyboard


async def set_creatives_quality_kb(position_id):
    keyboard = InlineKeyboardMarkup()
    for i in range(10):
        keyboard.insert(InlineKeyboardButton(text=f'{i + 1}⭐️', callback_data=f'set_creatives_quality_{i + 1}'))
    back_button = InlineKeyboardButton(text=get_string('back_button'),
                                       callback_data=f'back_to_designer_card_{position_id}')
    keyboard.row(back_button)
    return keyboard


async def set_designer_professionalism_kb(position_id):
    keyboard = InlineKeyboardMarkup()
    for i in range(10):
        keyboard.insert(InlineKeyboardButton(text=f'{i + 1}⭐️', callback_data=f'set_designer_professionalism_{i + 1}'))
    back_button = InlineKeyboardButton(text=get_string('back_button'),
                                       callback_data=f'back_to_creatives_quality_{position_id}')
    keyboard.row(back_button)
    return keyboard


async def replace_invalid_kb(prod_id):
    keyboard = InlineKeyboardMarkup()
    replace_invalid_button = InlineKeyboardButton(text=get_string('replace_invalid_button'),
                                                  callback_data=f'replace_invalid_{prod_id}')
    keyboard.row(replace_invalid_button)
    return keyboard
