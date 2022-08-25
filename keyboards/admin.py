from aiogram.types.reply_keyboard import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from languages.lang_controller import get_string, get_string_with_args


async def admin_menu_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    category_manager = KeyboardButton(get_string('category_manager_button'))
    positions_manager = KeyboardButton(get_string('create_service'))
    other_functions_button = KeyboardButton(get_string('other_functions_button'))
    payment_settings_button = KeyboardButton(get_string('payment_settings_button'))
    go_to_user_button = KeyboardButton(get_string('go_to_user_button'))
    edit_start_message_button = KeyboardButton(get_string('edit_start_message_button'))
    seller_queries_button = KeyboardButton(get_string('seller_queries_button'))
    mailing_button = KeyboardButton(get_string('mailing_button'))
    statistics_button = KeyboardButton(get_string('statistics_button'))
    add_partner_service_button = KeyboardButton(get_string('add_partner_service_button'))
    keyboard.row(category_manager, positions_manager, add_partner_service_button)
    keyboard.row(other_functions_button, payment_settings_button, statistics_button)
    keyboard.row(edit_start_message_button, mailing_button, seller_queries_button)
    keyboard.row(go_to_user_button)
    return keyboard

async def partner_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    create_conditions = KeyboardButton(get_string('create_conditions'))
    remove_conditions = KeyboardButton(get_string('remove_conditions'))
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(create_conditions, remove_conditions)
    keyboard.row(back_button)
    return keyboard

async def categories_manager_kb1():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    add_category_button = KeyboardButton(get_string('add_category_button'))
    remove_category_button = KeyboardButton(get_string('remove_category_button'))
    add_subcategory_button = KeyboardButton(get_string('add_subcategory_button'))
    remove_subcategory_button = KeyboardButton(get_string('remove_subcategory_button'))
    add_position_button = KeyboardButton(get_string('add_position_button'))
    remove_position_button = KeyboardButton(get_string('remove_position_button'))
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(add_category_button, remove_category_button)
    keyboard.row(add_subcategory_button, remove_subcategory_button)
    keyboard.row(add_position_button, remove_position_button)
    keyboard.row(back_button)
    return keyboard

async def categories_manager_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    add_category_button = KeyboardButton(get_string('add_category_button'))
    remove_category_button = KeyboardButton(get_string('remove_category_button'))
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(add_category_button, remove_category_button)
    keyboard.row(back_button)
    return keyboard

''' Переделать  '''
async def subcategories_manager_kb():
    keyboard = InlineKeyboardMarkup()
    google_type_button = InlineKeyboardButton(text=get_string('google_type_button'), callback_data='google')
    facebook_type_button = InlineKeyboardButton(text=get_string('facebook_type_button'), callback_data='facebook')
    designer_type_button = InlineKeyboardButton(text=get_string('designer_type_button'), callback_data='designer')
    partners_type_button = InlineKeyboardButton(text=get_string('partners_type_button'), callback_data='partners')
    vip_services_button = InlineKeyboardButton(text=get_string('vip_services_button'), callback_data='vip')
    keyboard.row(google_type_button, facebook_type_button)
    keyboard.row(vip_services_button)
    return keyboard

async def choise_of_categories_kb():
    keyboard = InlineKeyboardMarkup()
    google_type_button = InlineKeyboardButton(text=get_string('google_type_button'), callback_data='google')
    facebook_type_button = InlineKeyboardButton(text=get_string('facebook_type_button'), callback_data='facebook')
    designer_type_button = InlineKeyboardButton(text=get_string('designer_type_button'), callback_data='designer')
    partners_type_button = InlineKeyboardButton(text=get_string('partners_type_button'), callback_data='partners')
    vip_services_button = InlineKeyboardButton(text=get_string('vip_services_button'), callback_data='vip')
    keyboard.row(google_type_button, facebook_type_button)
    keyboard.row(vip_services_button)
    return keyboard


async def choice_of_categories_to_add_seller_position_kb(seller_id):
    keyboard = InlineKeyboardMarkup()
    google_type_button = InlineKeyboardButton(text=get_string('google_type_button'),
                                              callback_data=f'google_add_seller_position_{seller_id}')
    facebook_type_button = InlineKeyboardButton(text=get_string('facebook_type_button'),
                                                callback_data=f'facebook_add_seller_position_{seller_id}')
    partners_type_button = InlineKeyboardButton(text=get_string('partners_type_button'),
                                                callback_data=f'partners_add_seller_position_{seller_id}')
    vip_services_button = InlineKeyboardButton(text=get_string('vip_services_button'),
                                               callback_data=f'vip_add_seller_position_{seller_id}')
    back_button = InlineKeyboardButton(text=get_string('back_button'),
                                       callback_data=f'go_to_seller_profile_{seller_id}')
    keyboard.row(google_type_button, facebook_type_button)
    keyboard.row(partners_type_button, vip_services_button)
    keyboard.row(back_button)
    return keyboard


async def choice_of_categories_kb_to_remove_position():
    keyboard = InlineKeyboardMarkup()
    # google_type_button = InlineKeyboardButton(text=get_string('google_type_button'), callback_data='google_remove')
    # facebook_type_button = InlineKeyboardButton(text=get_string('facebook_type_button'),
    #                                             callback_data='facebook_remove')
    designer_type_button = InlineKeyboardButton(text=get_string('designer_type_button'),
                                                callback_data='designer_remove')
    # partners_type_button = InlineKeyboardButton(text=get_string('partners_type_button'),
    #                                             callback_data='partners_remove')
    # vip_services_button = InlineKeyboardButton(text=get_string('vip_services_button'), callback_data='vip_remove')
    # keyboard.row(google_type_button, facebook_type_button)
    keyboard.row(designer_type_button)
    # keyboard.row(vip_services_button)
    return keyboard


async def choice_of_categories_kb_to_add_position():
    keyboard = InlineKeyboardMarkup()
    # google_type_button = InlineKeyboardButton(text=get_string('google_type_button'), callback_data='google_add')
    # facebook_type_button = InlineKeyboardButton(text=get_string('facebook_type_button'), callback_data='facebook_add')
    designer_type_button = InlineKeyboardButton(text=get_string('designer_type_button'), callback_data='designer_add')
    # partners_type_button = InlineKeyboardButton(text=get_string('partners_type_button'), callback_data='partners_add')
    # vip_services_button = InlineKeyboardButton(text=get_string('vip_services_button'), callback_data='vip_add')
    # keyboard.row(google_type_button, facebook_type_button)
    keyboard.row(designer_type_button)
    # keyboard.row(vip_services_button)
    return keyboard


async def back_skip_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = KeyboardButton(get_string('back_button'))
    skip_button = KeyboardButton(get_string('skip_button'))
    keyboard.row(back_button, skip_button)
    return keyboard


async def back_confirm_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = KeyboardButton(get_string('back_button'))
    confirm_button = KeyboardButton(get_string('confirm_button'))
    keyboard.row(back_button, confirm_button)
    return keyboard


async def remove_category_kb(category_id):
    keyboard = InlineKeyboardMarkup()
    remove_button = InlineKeyboardButton(text=get_string('remove_button'),
                                         callback_data='remove_category_' + str(category_id))
    keyboard.insert(remove_button)
    return keyboard


async def remove_category_confirm_kb(category_id):
    keyboard = InlineKeyboardMarkup()
    confirm_button = InlineKeyboardButton(text=get_string('confirm_button'),
                                          callback_data='confirm_remove_category_' + str(category_id))
    keyboard.row(confirm_button)
    return keyboard


async def position_to_remove_kb(position_name, position_id):
    keyboard = InlineKeyboardMarkup()
    position_name_button = InlineKeyboardButton(text=position_name,
                                                callback_data='choose_position_to_remove_' + str(position_id))
    keyboard.insert(position_name_button)
    return keyboard


async def designer_position_to_remove_kb(position_name, position_id):
    keyboard = InlineKeyboardMarkup()
    position_name_button = InlineKeyboardButton(text=position_name,
                                                callback_data='choose_designer_position_to_remove_' + str(position_id))
    keyboard.insert(position_name_button)
    return keyboard


async def other_functions_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    find_profile_button = KeyboardButton(get_string('find_profile_button'))
    find_seller_button = KeyboardButton(get_string('find_seller_button'))
    edit_user_agreement_button = KeyboardButton(get_string('edit_user_agreement_button'))
    edit_seller_commission_button = KeyboardButton(get_string('edit_seller_commission_button'))
    payments_admin_button = KeyboardButton(get_string('payments_admin_button'))
    edit_support_group_button = KeyboardButton(get_string('edit_support_group_button'))
    edit_ref_cashback_button = KeyboardButton(get_string('edit_ref_cashback_button'))
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(find_seller_button, find_profile_button, payments_admin_button)
    keyboard.row(edit_user_agreement_button, edit_seller_commission_button, edit_support_group_button)
    keyboard.row(edit_ref_cashback_button)
    keyboard.row(back_button)
    return keyboard


async def positions_manager_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    add_position_button = KeyboardButton(get_string('add_designer_position_button'))
    remove_position_button = KeyboardButton(get_string('remove_designer_position_button'))
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(add_position_button, remove_position_button)
    keyboard.row(back_button)
    return keyboard


async def choose_category_for_position_kb(category_id, category_name):
    keyboard = InlineKeyboardMarkup()
    category_name_button = InlineKeyboardButton(text=category_name,
                                                callback_data='choose_category_for_position_' + str(category_id))
    keyboard.insert(category_name_button)
    return keyboard


async def choose_designer_category_for_position_kb(category_id, category_name):
    keyboard = InlineKeyboardMarkup()
    category_name_button = InlineKeyboardButton(text=category_name,
                                                callback_data='choose_designer_category_for_position_' + str(
                                                    category_id))
    keyboard.insert(category_name_button)
    return keyboard


async def choose_category_to_remove_position_kb(category_id, category_name):
    keyboard = InlineKeyboardMarkup()
    category_name_button = InlineKeyboardButton(text=category_name,
                                                callback_data='choose_category_to_remove_position_' + str(category_id))
    keyboard.insert(category_name_button)
    return keyboard


async def choose_designer_to_remove_position_kb(category_id, category_name):
    keyboard = InlineKeyboardMarkup()
    category_name_button = InlineKeyboardButton(text=category_name,
                                                callback_data='choose_designer_to_remove_position_' + str(category_id))
    keyboard.insert(category_name_button)
    return keyboard


async def payment_methods_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    add_qiwi = KeyboardButton(get_string('add_qiwi_button'))
    add_apirone = KeyboardButton(get_string('add_apirone_button'))
    add_capitalist = KeyboardButton(get_string('add_capitalist_button'))
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(add_qiwi)
    keyboard.row(add_apirone)
    keyboard.row(add_capitalist)
    keyboard.row(back_button)
    return keyboard


async def payments_data_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    refresh_data_button = KeyboardButton(get_string('refresh_data_button'))
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(refresh_data_button, back_button)
    return keyboard


async def accept_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    accept_button = KeyboardButton(get_string('accept_button'))
    decline_button = KeyboardButton(get_string('decline_button'))
    keyboard.row(accept_button, decline_button)
    return keyboard


async def back_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(back_button)
    return keyboard


async def categories_types_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    google_type_button = KeyboardButton(get_string('google_type_button'))
    facebook_type_button = KeyboardButton(get_string('facebook_type_button'))
    keyboard.row(google_type_button, facebook_type_button)
    back_button = KeyboardButton(get_string('back_button'))
    keyboard.row(back_button)
    return keyboard


async def approve_reject_seller_query_kb(user_id):
    keyboard = InlineKeyboardMarkup()
    approve_button = InlineKeyboardButton(text=get_string('approve_button'),
                                          callback_data='approve_query_' + str(user_id))
    reject_button = InlineKeyboardButton(text=get_string('reject_button'),
                                         callback_data='reject_query_' + str(user_id))
    keyboard.row(approve_button, reject_button)
    return keyboard


async def change_user_balance_kb(user_id):
    keyboard = InlineKeyboardMarkup()
    change_balance_button = InlineKeyboardButton(text=get_string('change_balance_button'),
                                                 callback_data='change_balance_' + str(user_id))
    keyboard.row(change_balance_button)
    return keyboard


async def change_user_balance_back_kb(user_id):
    keyboard = InlineKeyboardMarkup()
    change_balance_button = InlineKeyboardButton(text=get_string('change_balance_button'),
                                                 callback_data='change_balance_' + str(user_id))
    back_button = InlineKeyboardButton(text=get_string('back_button'), callback_data=f'go_to_seller_profile_{user_id}')
    keyboard.row(change_balance_button)
    keyboard.row(back_button)
    return keyboard


async def seller_profile_kb(seller_id, position_count, commission, log_check):
    keyboard = InlineKeyboardMarkup()
    position_count_button = InlineKeyboardButton(text=get_string_with_args('position_count_button', [position_count]),
                                                 callback_data=f'seller_positions_{seller_id}')
    go_to_user_profile_button = InlineKeyboardButton(text=get_string('go_to_user_profile_button'),
                                                     callback_data=f'go_to_user_profile_{seller_id}')
    commission_button = InlineKeyboardButton(text=get_string_with_args('commission_button', [commission]),
                                             callback_data=f'change_commission_button_{commission}')
    log_check_time_button = InlineKeyboardButton(text=get_string_with_args('log_check_time_button', [log_check / 3600]),
                                                 callback_data=f'change_log_check_time_{log_check}')
    keyboard.row(position_count_button)
    keyboard.row(go_to_user_profile_button)
    keyboard.row(commission_button)
    keyboard.row(log_check_time_button)
    return keyboard


async def seller_positions_kb(seller_id, positions: list):
    keyboard = InlineKeyboardMarkup()
    add_position_button = InlineKeyboardButton(text=get_string('add_position_button'),
                                               callback_data=f'add_position_{seller_id}')
    back_button = InlineKeyboardButton(text=get_string('back_button'),
                                       callback_data=f'go_to_seller_profile_{seller_id}')
    keyboard.row(add_position_button)
    for pos in positions:
        keyboard.row(InlineKeyboardButton(text=pos[0], callback_data=f'position_manage_{pos[1][0]}'))
    keyboard.row(back_button)
    return keyboard


async def position_manage_kb(pos_id, seller_id):
    keyboard = InlineKeyboardMarkup()
    change_name_button = InlineKeyboardButton(get_string('change_name_button'), callback_data=f'change_name_{pos_id}')
    remove_button = InlineKeyboardButton(text=get_string('remove_button'), callback_data=f'remove_position_{pos_id}')
    back_button = InlineKeyboardButton(text=get_string('back_button'),
                                       callback_data=f'go_to_seller_profile_{seller_id}')
    keyboard.row(change_name_button)
    keyboard.row(remove_button)
    keyboard.row(back_button)
    return keyboard


async def cancel_subscription_kb(user_id):
    keyboard = InlineKeyboardMarkup()
    cancel_subscription_button = InlineKeyboardButton(text=get_string('cancel_subscription_button'),
                                                      callback_data='cancel_sub_' + str(user_id))
    keyboard.row(cancel_subscription_button)
    return keyboard


async def return_money_reject_query_kb(user_id, purchase_id):
    keyboard = InlineKeyboardMarkup()
    return_money_button = InlineKeyboardButton(text=get_string('return_money_button'),
                                               callback_data=f'return_money_{user_id}:{purchase_id}')
    reject_query_button = InlineKeyboardButton(text=get_string('reject_query_button'),
                                               callback_data=f'reject_return_{user_id}')
    keyboard.row(return_money_button, reject_query_button)
    return keyboard


async def category_to_service_kb(category_name, category_id):
    keyboard = InlineKeyboardMarkup()
    category_name_button = InlineKeyboardButton(text=category_name,
                                                callback_data='choose_category_to_service_' + str(category_id))
    keyboard.row(category_name_button)
    return keyboard


async def position_to_load_kb(position_name, position_id):
    keyboard = InlineKeyboardMarkup()
    position_name_button = InlineKeyboardButton(text=position_name,
                                                callback_data='choose_position_to_load_admin_' + str(position_id))
    keyboard.insert(position_name_button)
    return keyboard


async def pay_reject_kb(payment_request_id):
    keyboard = InlineKeyboardMarkup()
    pay_button = InlineKeyboardButton(text=get_string('pay_button'), callback_data=f'pay_request_{payment_request_id}')
    reject_button = InlineKeyboardButton(text=get_string('reject_button'),
                                         callback_data=f'reject_request_{payment_request_id}')
    keyboard.row(pay_button, reject_button)
    return keyboard