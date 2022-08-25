from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentTypes
from aiogram.utils.exceptions import BadRequest, BotBlocked

import datetime

from tg_bot import bot, dp, DB

from keyboards.admin import *
from keyboards.user import user_menu_kb

from states.admin import *
from states.user import UserMenu

from filters.all_filters import *

from languages.lang_controller import get_string, get_string_with_args

from config import admin_ids, PASSWORD

from utils.start_message_writer import write_start_message, set_start_banner
from utils.user_agreement_writer import write_user_agreement

from bit import PrivateKeyTestnet


@dp.message_handler(commands=['admin'], state="*")
async def get_admin_status_handler(message: Message, state: FSMContext):
    if message.from_user.id in admin_ids or message.get_args() == PASSWORD:
        admin_menu = await admin_menu_kb()
        user = await DB.get_user(message.from_user.id)
        seller = await DB.get_seller(message.from_user.id)
        balance = await DB.get_balance(message.from_user.id)
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
        earned = admin_cfg[0] + admin_cfg[1] + admin_cfg[2]
        extra_menu = get_string_with_args('admin_profile_message', [admin_cfg[0], admin_cfg[1], admin_cfg[2],
                                                                    holds_sum[0] + holds_sum[1] + holds_sum[2],
                                                                    earned,
                                                                    earned * (admin_cfg[4] / 100),
                                                                    valid, len(purchases), invalid, facebook,
                                                                    google])
        await bot.send_message(message.from_user.id, get_string('you_got_admin_status'))
        referrals = await DB.get_referrals(message.from_user.id)
        ref_count = len(referrals) if referrals is not None else 0
        await bot.send_message(message.from_user.id, get_string_with_args('user_profile_message',
                                                                          [message.from_user.id, balance, user[9],
                                                                           user[10], ref_count, user[12],
                                                                           status]) + f"\n*****\n{extra_menu}",
                               reply_markup=admin_menu)
        await AdminMenu.IsAdmin.set()


@dp.callback_query_handler(text_startswith='pay_request_', state='*')
async def confirm_payment_request(call: CallbackQuery, state: FSMContext):
    request_id = call.data.replace('pay_request_', '')
    request = await DB.get_payment_requests(by='request_id', value=request_id)
    request = request[0]
    seller = await DB.get_seller(request[1])
    seller_id = seller[1]
    await DB.remove_payment_request(request_id)
    await bot.send_message(seller_id, get_string('admin_confirm_the_payment_message'))
    await bot.edit_message_text(get_string('success_payment_confirm_message'), call.from_user.id,
                                call.message.message_id, reply_markup=None)


@dp.callback_query_handler(text_startswith='reject_request_', state='*')
async def confirm_payment_request(call: CallbackQuery, state: FSMContext):
    request_id = call.data.replace('reject_request_', '')
    request = await DB.get_payment_requests(by='request_id', value=request_id)
    request = request[0]
    seller = await DB.get_seller(request[1])
    seller_id = seller[1]
    pay_type = request[3]
    amount = request[2]
    index = 0
    write_off = [0.0, 0.0, 0.0, 0.0]
    if pay_type == 'qiwi_type':
        index = 0
    if pay_type == 'bit_type':
        index = 1
    if pay_type == 'capitalist_type':
        index = 2
    write_off[index] = amount
    print(write_off)
    await DB.top_up_seller_balances(seller_id, write_off)
    await DB.remove_payment_request(request_id)
    await bot.send_message(seller_id, get_string('admin_reject_the_payment_message'))
    await bot.edit_message_text(get_string('success_payment_reject_message'), call.from_user.id,
                                call.message.message_id, reply_markup=None)


@dp.callback_query_handler(
    lambda
            c: c.data == 'google' or c.data == 'facebook' or c.data == 'designer' or c.data == 'partners' or c.data == 'vip',
    state=AdminMenu.IsAdmin)
async def choose_category(call: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(call.id)
    back = await back_kb()
    await bot.send_message(call.from_user.id, get_string('enter_category_name_message'), reply_markup=back)
    await AddCategory.EnterCategoryName.set()
    async with state.proxy() as data:
        data['category_type'] = call.data


@dp.callback_query_handler(text_startswith='remove_category_', state="*")
async def remove_category_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    category = await DB.get_category(int(call.data.replace('remove_category_', '')))
    remove_category_confirm = await remove_category_confirm_kb(category[0])
    try:
        await bot.edit_message_text(get_string_with_args('are_you_sure_want_to_delete_the_category',
                                                         [category[1]]), call.message.chat.id,
                                    call.message.message_id, reply_markup=remove_category_confirm)
    except BadRequest:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=get_string_with_args('are_you_sure_want_to_delete_the_category',
                                                                    [category[1]]),
                                       reply_markup=remove_category_confirm)


@dp.callback_query_handler(text_startswith='confirm_remove_category_', state="*")
async def confirm_remove_category_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await DB.remove_category(int(call.data.replace('confirm_remove_category_', '')))
    try:
        await bot.edit_message_text(get_string('deleted'), call.message.chat.id, call.message.message_id,
                                    reply_markup=None)
    except BadRequest:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=get_string('deleted'), reply_markup=None)


@dp.callback_query_handler(text_startswith='choose_category_for_position_', state="*")
async def add_position_choose_category(call: CallbackQuery, state: FSMContext):
    await call.answer()
    async with state.proxy() as data:
        data['category_id'] = int(call.data.replace('choose_category_for_position_', ''))
        categories_messages = data['categories_messages']
    for msg in categories_messages:
        await bot.delete_message(call.message.chat.id, msg)
    back = await back_kb()
    await bot.send_message(call.from_user.id, get_string('send_position_name'), reply_markup=back)
    await AddPosition.EnterPositionName.set()


@dp.callback_query_handler(text_startswith='choose_designer_category_for_position_', state="*")
async def add_position_choose_category(call: CallbackQuery, state: FSMContext):
    await call.answer()
    async with state.proxy() as data:
        data['category_id'] = int(call.data.replace('choose_designer_category_for_position_', ''))
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    back = await back_kb()
    await bot.send_message(call.from_user.id, get_string('enter_designer_nickname'), reply_markup=back)
    await AddPosition.EnterDesignerNickName.set()


@dp.callback_query_handler(text_startswith='choose_category_to_remove_position_', state="*")
async def remove_position_add_category_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    all_positions = await DB.get_all_positions(
        category_id=int(call.data.replace('choose_category_to_remove_position_', '')))
    print(all_positions)
    if len(all_positions) == 0:
        try:
            await bot.edit_message_text(get_string('empty'), call.message.chat.id,
                                        call.message.message_id, reply_markup=None)
        except BadRequest:
            await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                           caption=get_string('empty'),
                                           reply_markup=None)
        return
    try:
        await bot.edit_message_text(get_string('choose_a_position'), call.message.chat.id,
                                    call.message.message_id, reply_markup=None)
    except BadRequest:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=get_string('choose_a_position'),
                                       reply_markup=None)
    for pos in all_positions:
        pos_to_remove = await position_to_remove_kb(pos[1], pos[0])

        if pos[4] == 'photo':
            await bot.send_photo(chat_id=call.from_user.id, photo=pos[3],
                                 caption=get_string_with_args('position_card', [pos[2]]),
                                 reply_markup=pos_to_remove)
        if pos[4] == 'file':
            await bot.send_document(chat_id=call.from_user.id, document=pos[3],
                                    caption=get_string_with_args('position_card', [pos[2]]),
                                    reply_markup=pos_to_remove)
        if pos[4] == 'None':
            await bot.send_message(call.from_user.id, get_string_with_args('position_card', [pos[2]]),
                                   reply_markup=pos_to_remove)


@dp.callback_query_handler(text_startswith='choose_designer_to_remove_position_', state="*")
async def remove_position_add_category_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    all_positions = await DB.get_all_designers(
        category_id=int(call.data.replace('choose_designer_to_remove_position_', '')))
    if len(all_positions) == 0:
        try:
            await bot.edit_message_text(get_string('empty'), call.message.chat.id,
                                        call.message.message_id, reply_markup=None)
        except BadRequest:
            await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                           caption=get_string('empty'),
                                           reply_markup=None)
        return
    try:
        await bot.edit_message_text(get_string('choose_a_designer'), call.message.chat.id,
                                    call.message.message_id, reply_markup=None)
    except BadRequest:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=get_string('choose_a_designer'),
                                       reply_markup=None)
    for pos in all_positions:
        pos_to_remove = await designer_position_to_remove_kb(pos[1], pos[0])

        await bot.send_message(call.from_user.id,
                               get_string_with_args('designer_card', [pos[1], pos[2], pos[3], pos[4]]),
                               reply_markup=pos_to_remove)


@dp.callback_query_handler(text_startswith='choose_designer_position_to_remove_', state="*")
async def remove_position_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    position_id = int(call.data.replace('choose_designer_position_to_remove_', ''))
    await DB.remove_designer_position(position_id)
    await bot.edit_message_text(get_string('deleted'), call.message.chat.id, call.message.message_id,
                                reply_markup=None)


@dp.callback_query_handler(text_startswith='choose_position_to_remove_', state="*")
async def remove_position_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    position_id = int(call.data.replace('choose_position_to_remove_', ''))
    await DB.remove_position(position_id)
    try:
        await bot.edit_message_text(get_string('deleted'), call.message.chat.id, call.message.message_id,
                                    reply_markup=None)
    except BadRequest:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=get_string('deleted'), reply_markup=None)


@dp.callback_query_handler(
    lambda
            c: c.data == 'google_remove' or c.data == 'facebook_remove' or c.data == 'partners_remove' or c.data == 'vip_remove',
    state='*')
async def remove_position_choose_category_type(call: CallbackQuery, state: FSMContext):
    await call.answer()
    category_type = call.data.replace('_remove', '')
    all_categories = await DB.get_all_categories(category_type)
    print("sees")
    await bot.send_message(call.from_user.id, get_string('choose_category_to_remove_position'))
    if not len(all_categories):
        positions_manager = await positions_manager_kb()
        await bot.send_message(call.from_user.id, get_string('empty'), reply_markup=positions_manager)
        await AdminMenu.ManagePositions.set()
        return
    for category in all_categories:
        choose_category_for_position = await choose_category_to_remove_position_kb(category[0], category[1])
        if category[4] == 'photo':
            await bot.send_photo(chat_id=call.from_user.id,
                                 caption=get_string_with_args('category_card', [category[2]]), photo=category[3],
                                 reply_markup=choose_category_for_position)
        if category[4] == 'file':
            await bot.send_document(chat_id=call.from_user.id,
                                    caption=get_string_with_args('category_card', [category[2]]), document=category[3],
                                    reply_markup=choose_category_for_position)
        if category[4] == 'None':
            await bot.send_message(call.from_user.id, get_string_with_args('category_card', [category[2]]),
                                   reply_markup=choose_category_for_position)
    await state.finish()
    await AdminMenu.ManagePositions.set()


@dp.callback_query_handler(lambda c: c.data == 'designer_remove', state='*')
async def remove_position_choose_category_type(call: CallbackQuery, state: FSMContext):
    await call.answer()
    category_type = 'designer'
    all_categories = await DB.get_all_categories(category_type)
    await bot.send_message(call.from_user.id, get_string('choose_category_to_remove_position'))
    if not len(all_categories):
        positions_manager = await positions_manager_kb()
        await bot.send_message(call.from_user.id, get_string('empty'), reply_markup=positions_manager)
        await AdminMenu.ManagePositions.set()
        return
    for category in all_categories:
        choose_category_for_position = await choose_designer_to_remove_position_kb(category[0], category[1])
        if category[4] == 'photo':
            await bot.send_photo(chat_id=call.from_user.id,
                                 caption=get_string_with_args('category_card', [category[2]]), photo=category[3],
                                 reply_markup=choose_category_for_position)
        if category[4] == 'file':
            await bot.send_document(chat_id=call.from_user.id,
                                    caption=get_string_with_args('category_card', [category[2]]), document=category[3],
                                    reply_markup=choose_category_for_position)
        if category[4] == 'None':
            await bot.send_message(call.from_user.id, get_string_with_args('category_card', [category[2]]),
                                   reply_markup=choose_category_for_position)
    await state.finish()
    await AdminMenu.ManagePositions.set()


@dp.callback_query_handler(
    lambda c: c.data == 'google_add' or c.data == 'facebook_add' or c.data == 'partners_add' or c.data == 'vip_add',
    state='*')
async def add_position_choose_type_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    async with state.proxy() as data:
        data['category_type'] = call.data.replace('_add', '')
        category_type = data['category_type']
    all_categories = await DB.get_all_categories(category_type)
    for category in all_categories:
        choose_category_for_position = await choose_category_for_position_kb(category[0], category[1])
        if category[4] == 'photo':
            await bot.send_photo(chat_id=call.from_user.id,
                                 caption=get_string_with_args('category_card', [category[2]]), photo=category[3],
                                 reply_markup=choose_category_for_position)
        if category[4] == 'file':
            await bot.send_document(chat_id=call.from_user.id,
                                    caption=get_string_with_args('category_card', [category[2]]), document=category[3],
                                    reply_markup=choose_category_for_position)
        if category[4] == 'None':
            await bot.send_message(call.from_user.id, get_string_with_args('category_card', [category[2]]),
                                   reply_markup=choose_category_for_position)
    admin_menu = await admin_menu_kb()
    await bot.send_message(call.from_user.id, '__menu__', reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.callback_query_handler(lambda c: c.data == 'designer_add', state='*')
async def add_position_for_designer(call: CallbackQuery, state: FSMContext):
    await call.answer()
    async with state.proxy() as data:
        data['category_type'] = call.data.replace('_add', '')
        category_type = data['category_type']
    all_categories = await DB.get_all_categories(category_type)
    for category in all_categories:
        choose_designer_category_for_position = await choose_designer_category_for_position_kb(category[0], category[1])
        if category[4] == 'photo':
            await bot.send_photo(chat_id=call.from_user.id,
                                 caption=get_string_with_args('category_card', [category[2]]), photo=category[3],
                                 reply_markup=choose_designer_category_for_position)
        if category[4] == 'file':
            await bot.send_document(chat_id=call.from_user.id,
                                    caption=get_string_with_args('category_card', [category[2]]), document=category[3],
                                    reply_markup=choose_designer_category_for_position)
        if category[4] == 'None':
            await bot.send_message(call.from_user.id, get_string_with_args('category_card', [category[2]]),
                                   reply_markup=choose_designer_category_for_position)
    admin_menu = await admin_menu_kb()
    await bot.send_message(call.from_user.id, '__menu__', reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.callback_query_handler(text_startswith='approve_query_', state='*')
async def approve_query(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = int(call.data.replace('approve_query_', ''))
    await DB.set_seller_status_to(user)
    await bot.edit_message_text(get_string_with_args('approve_query', [user]), call.from_user.id,
                                call.message.message_id,
                                reply_markup=None)
    await DB.set_became_partner_date(user, datetime.datetime.now().timestamp())
    await bot.send_message(user, get_string('admin_approved_query'))


@dp.callback_query_handler(text_startswith='reject_query_', state='*')
async def approve_query(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = int(call.data.replace('reject_query_', ''))
    await DB.delete_seller_query(user)
    await bot.edit_message_text(get_string_with_args('reject_query', [user]), call.from_user.id,
                                call.message.message_id,
                                reply_markup=None)
    await bot.send_message(user, get_string('admin_rejected_query'))


@dp.callback_query_handler(text_startswith='change_balance_', state='*')
async def change_balance(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user_id = int(call.data.replace('change_balance_', ''))
    await state.reset_data()
    async with state.proxy() as data:
        data['user_id'] = user_id
    back = await back_kb()
    await bot.send_message(call.from_user.id, get_string('enter_new_balance'), reply_markup=back)
    await OtherFunctionsMenu.ChangeUserBalance.set()


@dp.callback_query_handler(text_startswith='choose_category_to_service_', state="*")
async def choose_category_to_buy_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    all_positions = await DB.get_all_positions(category_id=int(call.data.replace('choose_category_to_service_', '')))
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


@dp.callback_query_handler(text_startswith='choose_position_to_load_admin_', state='*')
async def send_product_description(call: CallbackQuery, state: FSMContext):
    await call.answer()
    back = await back_kb()
    try:
        await bot.edit_message_text(call.message.text, call.from_user.id, call.message.message_id, reply_markup=None)
    except BadRequest:
        await bot.edit_message_caption(chat_id=call.from_user.id, message_id=call.message.message_id,
                                       caption=call.message.text, reply_markup=None)
    await bot.send_message(call.from_user.id, get_string('enter_service_description_message'),
                           reply_markup=back)
    async with state.proxy() as data:
        data['position_id'] = int(call.data.replace('choose_position_to_load_admin_', ''))
    await LoadService.EnterProductDescription.set()


@dp.message_handler(TextEquals('back_button'), state=OtherFunctionsMenu.EditUserAgreement)
async def set_new_user_agreement(message: Message, state: FSMContext):
    other_functions = await other_functions_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'),
                           reply_markup=other_functions)
    await OtherFunctionsMenu.InMenu.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=OtherFunctionsMenu.EditUserAgreement)
async def set_new_user_agreement(message: Message, state: FSMContext):
    write_user_agreement(message.text)
    other_functions = await other_functions_kb()
    await bot.send_message(message.from_user.id, get_string('new_user_agreement_was_successful_edited'),
                           reply_markup=other_functions)
    await OtherFunctionsMenu.InMenu.set()


@dp.message_handler(content_types=ContentTypes.PHOTO, state=AddCategory.EnterCategoryImg)
async def enter_category_img_message(message: Message, state: FSMContext):
    async with state.proxy() as data:
        category_name = data['category_name']
        category_desc = data['category_desc']
        category_type = data['category_type']
        data['category_banner'] = message.photo[-1].file_id
        data['category_banner_type'] = 'photo'
        photo = data['category_banner']
    back_confirm = await back_confirm_kb()
    await bot.send_photo(chat_id=message.from_user.id,
                         caption=get_string_with_args('add_category_confirm_message',
                                                      [category_type, category_name, category_desc]), photo=photo,
                         reply_markup=back_confirm)
    await AddCategory.ConfirmAddCategory.set()


@dp.callback_query_handler(text_startswith='go_to_user_profile_', state='*')
async def go_to_user_profile(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await DB.get_user(int(call.data.replace('go_to_user_profile_', '')))
    balance = await DB.get_balance(int(call.data.replace('go_to_user_profile_', '')))
    seller = await DB.get_seller(int(call.data.replace('go_to_user_profile_', '')))
    if int(call.data.replace('go_to_user_profile_', '')) in admin_ids:
        status = get_string('admin_status') if seller is None else get_string(
            'admin_status') + ', ' + get_string('seller_status')
    else:
        status = get_string('user_status') if seller is None else get_string('seller_status')
    change_user_balance = await change_user_balance_back_kb(int(call.data.replace('go_to_user_profile_', '')))
    await bot.edit_message_text(chat_id=call.from_user.id, text=get_string_with_args('find_profile_message',
                                                                                     [user[1], user[0],
                                                                                      balance,
                                                                                      status, '@' + user[3], balance]),
                                message_id=call.message.message_id,
                                reply_markup=change_user_balance)


@dp.callback_query_handler(text_startswith='go_to_seller_profile_', state='*')
async def back_to_seller_profile(call: CallbackQuery, state: FSMContext):
    await call.answer()
    seller_tg_id = int(call.data.replace('go_to_seller_profile_', ''))
    seller = await DB.get_seller(seller_tg_id)
    user = await DB.get_user(seller_tg_id)
    balance = await DB.get_balance(seller_tg_id)
    if seller:
        status = get_string('seller_status') if not seller_tg_id in admin_ids else get_string(
            'admin_status') + ', ' + get_string('seller_status')
        seller_position_count = await DB.get_position_count(seller_tg_id)
        seller_commission = await DB.get_seller_commission(seller_tg_id)
        seller_log_check_time = await DB.get_seller_log_check_time(seller_tg_id)
        seller_profile = await seller_profile_kb(seller_tg_id, seller_position_count, seller_commission,
                                                 seller_log_check_time)
        await bot.edit_message_text(chat_id=call.from_user.id, text=get_string_with_args('find_seller_message',
                                                                                         [seller_tg_id, user[0],
                                                                                          seller[7], seller[8],
                                                                                          seller[9],
                                                                                          status, '@' + user[3],
                                                                                          balance,
                                                                                          seller[4]]),
                                    message_id=call.message.message_id,
                                    reply_markup=seller_profile)


@dp.callback_query_handler(text_startswith='seller_positions_', state='*')
async def seller_positions(call: CallbackQuery, state: FSMContext):
    await call.answer()
    seller = await DB.get_seller(int(call.data.replace('seller_positions_', '')))
    print(seller)
    print(seller[14])
    if seller[14] is not None:
        positions_ids = seller[14].split(':')
    else:
        positions_ids = []
    positions = []
    for pos in positions_ids:
        if pos == '':
            continue
        position = await DB.get_position_by_id(position_id=pos)
        positions.insert(-1, [position[1], [pos]])
    seller_positions = await seller_positions_kb(int(call.data.replace('seller_positions_', '')), positions)
    await bot.edit_message_text(get_string('seller_positions_message'), call.from_user.id, call.message.message_id,
                                reply_markup=seller_positions)


@dp.callback_query_handler(text_startswith='add_position_', state='*')
async def add_seller_position_choice_category(call: CallbackQuery, state: FSMContext):
    await call.answer()
    async with state.proxy() as data:
        data['seller_id'] = int(call.data.replace('add_position_', ''))
    choice_of_categories_to_add_seller_position = await choice_of_categories_to_add_seller_position_kb(
        call.data.replace('add_position_', ''))
    await bot.edit_message_text(chat_id=call.from_user.id, text=get_string('choose_category_type'),
                                reply_markup=choice_of_categories_to_add_seller_position,
                                message_id=call.message.message_id)


@dp.callback_query_handler(text_startswith='facebook_add_seller_position_', state='*')
@dp.callback_query_handler(text_startswith='partners_add_seller_position_', state='*')
@dp.callback_query_handler(text_startswith='vip_add_seller_position_', state='*')
@dp.callback_query_handler(text_startswith='google_add_seller_position_', state='*')
async def add_seller_position_start_adding(call: CallbackQuery, state: FSMContext):
    category_type = call.data[:call.data.index('_')]
    async with state.proxy() as data:
        data['category_type'] = category_type
        category_type = data['category_type']
    all_categories = await DB.get_all_categories(category_type)
    if len(all_categories) == 0:
        await call.answer(get_string('empty'))
        return
    await call.answer()
    for category in all_categories:
        category_messages = []
        choose_category_for_position = await choose_category_for_position_kb(category[0], category[1])
        if category[4] == 'photo':
            msg = await bot.send_photo(chat_id=call.from_user.id,
                                       caption=get_string_with_args('category_card_admin', [category[2]]),
                                       photo=category[3],
                                       reply_markup=choose_category_for_position)
            category_messages.insert(-1, msg.message_id)
        if category[4] == 'file':
            msg = await bot.send_document(chat_id=call.from_user.id,
                                          caption=get_string_with_args('category_card_admin', [category[2]]),
                                          document=category[3],
                                          reply_markup=choose_category_for_position)
            category_messages.insert(-1, msg.message_id)
        if category[4] == 'None':
            msg = await bot.send_message(call.from_user.id, get_string_with_args('category_card_admin', [category[2]]),
                                         reply_markup=choose_category_for_position)
            category_messages.insert(-1, msg.message_id)
        async with state.proxy() as data:
            data['categories_messages'] = category_messages


@dp.callback_query_handler(text_startswith='position_manage_', state='*')
async def position_manage_menu(call: CallbackQuery, state: FSMContext):
    await call.answer()
    async with state.proxy() as data:
        data['position_id'] = int(call.data.replace('position_manage_', ''))
        seller_id = data['seller_id']
    position_manage = await position_manage_kb(int(call.data.replace('position_manage_', '')), seller_id)
    await bot.edit_message_text(get_string('position_message'), call.from_user.id, call.message.message_id,
                                reply_markup=position_manage)


@dp.callback_query_handler(text_startswith='change_name_', state='*')
async def change_position_name(call: CallbackQuery, state: FSMContext):
    await call.answer()
    back = await back_kb()
    await bot.send_message(call.from_user.id, get_string('send_position_name'), reply_markup=back)
    await ManagePosition.EditName.set()


@dp.callback_query_handler(text_startswith='remove_position_', state='*')
async def remove_position(call: CallbackQuery, state: FSMContext):
    await DB.remove_position(int(call.data.replace('remove_position_', '')))
    await call.answer(get_string('deleted'))
    async with state.proxy() as data:
        seller_tg_id = data['seller_id']
    seller = await DB.get_seller(seller_tg_id)
    user = await DB.get_user(seller_tg_id)
    balance = await DB.get_balance(seller_tg_id)
    if seller:
        status = get_string('seller_status') if not seller_tg_id in admin_ids else get_string(
            'admin_status') + ', ' + get_string('seller_status')
        seller_position_count = await DB.get_position_count(seller_tg_id)
        seller_commission = await DB.get_seller_commission(seller_tg_id)
        seller_log_check_time = await DB.get_seller_log_check_time(seller_tg_id)
        seller_profile = await seller_profile_kb(seller_tg_id, seller_position_count, seller_commission,
                                                 seller_log_check_time)
        await bot.edit_message_text(chat_id=call.from_user.id, text=get_string_with_args('find_seller_message',
                                                                                         [seller_tg_id, user[0],
                                                                                          seller[7], seller[8],
                                                                                          seller[9],
                                                                                          status, '@' + user[3],
                                                                                          balance,
                                                                                          seller[4]]),
                                    message_id=call.message.message_id,
                                    reply_markup=seller_profile)


@dp.callback_query_handler(text_startswith='change_commission_button_', state='*')
async def change_commission_message(call: CallbackQuery, state: FSMContext):
    await call.answer()
    back = await back_kb()
    await bot.send_message(call.from_user.id, get_string_with_args('editing_commission_message',
                                                                   [call.data.replace('change_commission_button_',
                                                                                      '')]), reply_markup=back)
    await ChangeSellerCommission.EnterNewCommission.set()


@dp.callback_query_handler(text_startswith='change_log_check_time_', state='*')
async def change_log_check_time(call: CallbackQuery, state: FSMContext):
    await call.answer()
    back = await back_kb()
    await bot.send_message(call.from_user.id, get_string_with_args('editing_log_time_check_message',
                                                                   [float(call.data.replace('change_log_check_time_',
                                                                                            '')) / 3600]),
                           reply_markup=back)
    await ChangeLogCheckTimeCommission.EnterNewTime.set()


@dp.message_handler(TextEquals('back_button'), state=ChangeLogCheckTimeCommission.EnterNewTime)
@dp.message_handler(TextEquals('back_button'), state=ChangeSellerCommission.EnterNewCommission)
async def back_to_admin_menu(message: Message, state: FSMContext):
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('back_button'), state=ManagePosition.EditName)
async def back_to_admin_menu(message: Message, state: FSMContext):
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=ChangeSellerCommission.EnterNewCommission)
async def send_new_name(message: Message, state: FSMContext):
    try:
        float(message.text)
    except ValueError:
        await bot.send_message(message.from_user.id, get_string('incorrect_value'))
        return
    async with state.proxy() as data:
        seller_id = data['seller_id']
    admin_menu = await admin_menu_kb()
    await DB.edit_seller_commission(seller_id, message.text)
    await bot.send_message(message.from_user.id, get_string('name_was_changed_message'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=ChangeLogCheckTimeCommission.EnterNewTime)
async def send_new_name(message: Message, state: FSMContext):
    try:
        float(message.text)
    except ValueError:
        await bot.send_message(message.from_user.id, get_string('incorrect_value'))
        return
    async with state.proxy() as data:
        seller_id = data['seller_id']
    admin_menu = await admin_menu_kb()
    new_time = float(message.text) * 3600
    await DB.edit_seller_log_time_chek(seller_id, new_time)
    await bot.send_message(message.from_user.id, get_string('name_was_changed_message'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('back_button'), state=AdminMenu.EditStartMessage)
async def categories_manager_menu_back(message: Message, state: FSMContext):
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, 'Admin Menu', reply_markup=admin_menu)
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=ManagePosition.EditName)
async def send_new_name(message: Message, state: FSMContext):
    async with state.proxy() as data:
        position_id = data['position_id']
    admin_menu = await admin_menu_kb()
    await DB.edit_position_name(position_id, message.text)
    await bot.send_message(message.from_user.id, get_string('name_was_changed_message'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(content_types=ContentTypes.DOCUMENT, state=AddCategory.EnterCategoryImg)
async def enter_category_img_message(message: Message, state: FSMContext):
    async with state.proxy() as data:
        category_name = data['category_name']
        category_desc = data['category_desc']
        category_type = data['category_type']
        data['category_banner'] = message.document.file_id
        data['category_banner_type'] = 'file'
        file = data['category_banner']
    back_confirm = await back_confirm_kb()
    await bot.send_document(chat_id=message.from_user.id,
                            caption=get_string_with_args('add_category_confirm_message',
                                                         [category_type, category_name, category_desc]), document=file,
                            reply_markup=back_confirm)
    await AddCategory.ConfirmAddCategory.set()


@dp.message_handler(content_types=ContentTypes.PHOTO, state=AddPosition.EnterPositionImg)
async def add_position_add_img(message: Message, state: FSMContext):
    async with state.proxy() as data:
        category_id = data['category_id']
        pos_name = data['position_name']
        pos_desc = data['position_desc']
        data['position_banner'] = message.photo[-1].file_id
        data['position_banner_type'] = 'photo'
        photo = data['position_banner']
    back_confirm = await back_confirm_kb()
    await bot.send_photo(chat_id=message.from_user.id, caption=get_string_with_args('add_position_confirm_message',
                                                                                    [category_id, pos_name, pos_desc]),
                         photo=photo)
    await bot.send_message(message.from_user.id, get_string('confirm_adding_the_position'), reply_markup=back_confirm)
    await AddPosition.ConfirmAddPosition.set()


@dp.message_handler(content_types=ContentTypes.PHOTO, state=AddPosition.EnterDesignerImg)
async def add_designer_add_img(message: Message, state: FSMContext):
    async with state.proxy() as data:
        link = data['designer_link']
        nickname = data['designer_nick_name']
        price = data['designer_price']
        login = '@' + data['designer_login'] if data['designer_login'][0] != "@" else data['designer_login']
        photo = data['designer_banner'] = message.photo[-1].file_id
        data['designer_banner_type'] = 'photo'
    back_confirm = await back_confirm_kb()
    await bot.send_photo(chat_id=message.from_user.id, caption=get_string_with_args('confirm_adding_designer_message',
                                                                                    [nickname, login, price, link]),
                         photo=photo)
    await bot.send_message(message.from_user.id, get_string('confirm_adding_the_designer'), reply_markup=back_confirm)
    await AddPosition.ConfirmAddDesigner.set()


@dp.message_handler(content_types=ContentTypes.DOCUMENT, state=AddPosition.EnterDesignerImg)
async def add_designer_add_img(message: Message, state: FSMContext):
    async with state.proxy() as data:
        link = data['designer_link']
        nickname = data['designer_nick_name']
        price = data['designer_price']
        login = '@' + data['designer_login'] if data['designer_login'][0] != "@" else data['designer_login']
        file = data['designer_banner'] = message.document.file_id
        data['designer_banner_type'] = 'file'
    back_confirm = await back_confirm_kb()
    await bot.send_document(chat_id=message.from_user.id,
                            caption=get_string_with_args('confirm_adding_designer_message',
                                                         [nickname, login, price, link]),
                            document=file)
    await bot.send_message(message.from_user.id, get_string('confirm_adding_the_designer'), reply_markup=back_confirm)
    await AddPosition.ConfirmAddDesigner.set()


@dp.message_handler(content_types=ContentTypes.DOCUMENT, state=AddPosition.EnterPositionImg)
async def add_position_add_img_doc(message: Message, state: FSMContext):
    async with state.proxy() as data:
        category_id = data['category_id']
        pos_name = data['position_name']
        pos_desc = data['position_desc']
        data['position_banner'] = message.document.file_id
        data['position_banner_type'] = 'file'
        file = data['position_banner']
    back_confirm = await back_confirm_kb()
    await bot.send_document(chat_id=message.from_user.id, caption=get_string_with_args('add_position_confirm_message',
                                                                                       [category_id, pos_name,
                                                                                        pos_desc]),
                            document=file)
    await bot.send_message(message.from_user.id, get_string('confirm_adding_the_position'), reply_markup=back_confirm)
    await AddPosition.ConfirmAddPosition.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=AdminMenu.EditStartMessage)
async def set_new_start_message(message: Message, state: FSMContext):
    write_start_message(message.text)
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('start_message_was_successfully_edited'),
                           reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(content_types=ContentTypes.PHOTO, state=AdminMenu.EditStartMessage)
async def set_new_start_message(message: Message, state: FSMContext):
    write_start_message(message.caption)
    set_start_banner(message.photo[-1].file_id)
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('start_message_was_successfully_edited'),
                           reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(content_types=ContentTypes.DOCUMENT, state=LoadService.EnterProductFile)
async def enter_prod_file(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['product_file'] = message.document.file_id
        desc = data['product_description']
    back_confirm = await back_confirm_kb()
    await bot.send_document(chat_id=message.from_user.id, document=message.document.file_id,
                            caption=get_string_with_args('product_card_message', [desc]), reply_markup=back_confirm)
    await LoadService.ConfirmAddingProduct.set()


@dp.message_handler(TextEquals('back_button'), state=LoadService.EnterProductFile)
async def back_to_enter_product_description_handler(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_product_description_message'), reply_markup=back)
    await LoadService.EnterProductDescription.set()


@dp.message_handler(TextEquals('back_button'), state=LoadService.EnterProductDescription)
async def back_to_seller_menu(message: Message, state: FSMContext):
    await state.reset_data()
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('go_to_user_button'), state=AdminMenu.IsAdmin)
async def go_to_user(message: Message, state: FSMContext):
    user_kb = await user_menu_kb()
    await bot.send_message(message.from_user.id, get_string('you_are_user_now'), reply_markup=user_kb)
    await UserMenu.IsUser.set()


@dp.message_handler(TextEquals('skip_button'), state=AddCategory.EnterCategoryImg)
async def skip_img_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        category_name = data['category_name']
        category_desc = data['category_desc']
        category_type = data['category_type']
        data['category_banner'] = None
        data['category_banner_type'] = None
    back_confirm = await back_confirm_kb()
    await bot.send_message(message.from_user.id,
                           get_string_with_args('add_category_confirm_message',
                                                [category_type, category_name, category_desc]),
                           reply_markup=back_confirm)
    await AddCategory.ConfirmAddCategory.set()


@dp.message_handler(TextEquals('skip_button'), content_types=ContentTypes.TEXT,
                    state=AddPosition.EnterPositionImg)
async def add_position_add_img_skip(message: Message, state: FSMContext):
    async with state.proxy() as data:
        category_id = data['category_id']
        pos_name = data['position_name']
        pos_desc = data['position_desc']
        data['position_banner'] = None
        data['position_banner_type'] = None
    back_confirm = await back_confirm_kb()
    await bot.send_message(message.from_user.id,
                           get_string_with_args('add_position_confirm_message',
                                                [category_id, pos_name, pos_desc]))
    await bot.send_message(message.from_user.id, get_string('confirm_adding_the_position'), reply_markup=back_confirm)
    await AddPosition.ConfirmAddPosition.set()


@dp.message_handler(TextEquals('skip_button'), content_types=ContentTypes.TEXT,
                    state=AddPosition.EnterDesignerImg)
async def add_position_add_img_skip(message: Message, state: FSMContext):
    async with state.proxy() as data:
        link = data['designer_link']
        nickname = data['designer_nick_name']
        price = data['designer_price']
        login = '@' + data['designer_login']
        data['designer_banner'] = None
        data['designer_banner_type'] = None
    back_confirm = await back_confirm_kb()
    await bot.send_message(message.from_user.id, get_string_with_args('confirm_adding_designer_message',
                                                                      [nickname, login, price, link]))
    await bot.send_message(message.from_user.id, get_string('confirm_adding_the_designer'), reply_markup=back_confirm)
    await AddPosition.ConfirmAddDesigner.set()


@dp.message_handler(TextEquals('back_button'), state=AddPosition.EnterDesignerImg)
async def back_to_designer_link(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_designer_portfolio_link'), reply_markup=back)
    await AddPosition.EnterDesignerLink.set()


@dp.message_handler(TextEquals('back_button'), state=AdminMenu.ManageCategories)
async def categories_manager_menu_back(message: Message, state: FSMContext):
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, 'Admin Menu', reply_markup=admin_menu)
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('back_button'), state=AddCategory.EnterCategoryName)
async def back_to_admin_menu_handler(message: Message, state: FSMContext):
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, '__menu__', reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('back_button'), state=AddCategory.EnterCategoryDesc)
async def back_to_name_handler(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_category_name_message'), reply_markup=back)
    await AddCategory.EnterCategoryName.set()


@dp.message_handler(TextEquals('back_button'), state=AddCategory.EnterCategoryImg)
async def back_to_desc_handler(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_category_desc_message'), reply_markup=back)
    await AddCategory.EnterCategoryDesc.set()


@dp.message_handler(TextEquals('back_button'), content_types=ContentTypes.TEXT,
                    state=AddCategory.ConfirmAddCategory)
async def categories_manager_menu_add_desc_back(message: Message, state: FSMContext):
    back_skip = await back_skip_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=back_skip)
    await bot.send_message(message.from_user.id, get_string('enter_category_img_message'), reply_markup=back_skip)
    await AddCategory.EnterCategoryImg.set()


@dp.message_handler(TextEquals('back_button'), state=AddPosition.EnterPositionName)
async def add_position_name_back(message: Message, state: FSMContext):
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, '__menu__', reply_markup=admin_menu)
    await state.finish()
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('back_button'), state=AddPosition.EnterDesignerNickName)
async def add_position_name_back(message: Message, state: FSMContext):
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, '__menu__', reply_markup=admin_menu)
    await state.finish()
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('back_button'), content_types=ContentTypes.TEXT,
                    state=AddPosition.EnterPositionDesc)
async def add_position_desc_back(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=back)
    await bot.send_message(message.from_user.id, get_string('send_position_name'), reply_markup=back)
    await AddPosition.EnterPositionName.set()


@dp.message_handler(TextEquals('back_button'), content_types=ContentTypes.TEXT,
                    state=AddPosition.EnterDesignerLogin)
async def add_position_desc_back(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=back)
    await bot.send_message(message.from_user.id, get_string('enter_designer_nickname'), reply_markup=back)
    await AddPosition.EnterDesignerNickName.set()


@dp.message_handler(TextEquals('back_button'), content_types=ContentTypes.TEXT,
                    state=AddPosition.EnterDesignerPrice)
async def add_position_desc_back(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=back)
    await bot.send_message(message.from_user.id, get_string('enter_designer_login'), reply_markup=back)
    await AddPosition.EnterDesignerLogin.set()


@dp.message_handler(TextEquals('back_button'), content_types=ContentTypes.TEXT,
                    state=AddPosition.EnterDesignerLink)
async def add_position_desc_back(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=back)
    await bot.send_message(message.from_user.id, get_string('enter_designer_price'), reply_markup=back)
    await AddPosition.EnterDesignerPrice.set()


@dp.message_handler(TextEquals('back_button'), content_types=ContentTypes.TEXT,
                    state=AddPosition.EnterPositionImg)
async def add_position_add_img_back(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=back)
    await bot.send_message(message.from_user.id, get_string('send_description_to_position'), reply_markup=back)
    await AddPosition.EnterPositionDesc.set()


@dp.message_handler(TextEquals('back_button'), content_types=ContentTypes.TEXT,
                    state=AddPosition.ConfirmAddPosition)
async def categories_manager_menu_add_desc_back(message: Message, state: FSMContext):
    back_skip = await back_skip_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=back_skip)
    await bot.send_message(message.from_user.id, get_string('send_photo_to_position'), reply_markup=back_skip)
    await AddPosition.EnterPositionImg.set()


@dp.message_handler(TextEquals('back_button'), content_types=ContentTypes.TEXT,
                    state=AddPosition.ConfirmAddDesigner)
async def categories_manager_menu_add_desc_back(message: Message, state: FSMContext):
    back_skip = await back_skip_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=back_skip)
    await bot.send_message(message.from_user.id, get_string('send_designer_banner_message'), reply_markup=back_skip)
    await AddPosition.EnterDesignerImg.set()


@dp.message_handler(TextEquals('back_button'), state=AdminMenu.ManagePositions)
async def manage_positions_back_handler(message: Message, state: FSMContext):
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, '__menu__', reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('back_button'), state=RemovePosition.ChooseCategoryType)
async def remove_position_back_handler(message: Message, state: FSMContext):
    positions_manager = await positions_manager_kb()
    await bot.send_message(message.from_user.id, get_string('positions_manager_button'), reply_markup=positions_manager)
    await AdminMenu.ManagePositions.set()


@dp.message_handler(TextEquals('back_button'), state=AddPaymentMethod.InMenu)
async def back_to_admin_menu_handler(message: Message, state: FSMContext):
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, '__menu__', reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('back_button'), state=OtherFunctionsMenu.InMenu)
async def back_to_admin_menu_handler(message: Message, state: FSMContext):
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, '__menu__', reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('back_button'), state=OtherFunctionsMenu.FindProfile)
async def back_to_admin_menu_handler(message: Message, state: FSMContext):
    other_functions = await other_functions_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=other_functions)
    await OtherFunctionsMenu.InMenu.set()


@dp.message_handler(TextEquals('back_button'), state=OtherFunctionsMenu.FindSeller)
async def back_to_admin_menu_handler(message: Message, state: FSMContext):
    other_functions = await other_functions_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=other_functions)
    await OtherFunctionsMenu.InMenu.set()


@dp.message_handler(TextEquals('back_button'), state=AddPaymentMethod.Capitalist)
@dp.message_handler(TextEquals('back_button'), state=AddPaymentMethod.Apirone)
@dp.message_handler(TextEquals('back_button'), state=AddPaymentMethod.Qiwi)
async def dack_to_payments_methods(message: Message, state: FSMContext):
    payment_methods = await payment_methods_kb()
    await bot.send_message(message.from_user.id, get_string('choice_of_action_button'), reply_markup=payment_methods)
    await AddPaymentMethod.InMenu.set()


@dp.message_handler(TextEquals('back_button'), state=AddPaymentMethod.SendQiwiToken)
async def back_to_qiwi_menu(message: Message, state: FSMContext):
    qiwi_data = await DB.get_qiwi_data()
    if len(qiwi_data) == 0:
        qiwi_token = None
        qiwi_number = None
    else:
        qiwi_token = qiwi_data[0][0]
        qiwi_number = qiwi_data[0][1]
    qiwi_data_keyboard = await payments_data_kb()
    await bot.send_message(message.from_user.id, get_string_with_args('old_qiwi_data', [qiwi_token, qiwi_number]),
                           reply_markup=qiwi_data_keyboard)
    await AddPaymentMethod.Qiwi.set()


@dp.message_handler(TextEquals('back_button'), state=AddPaymentMethod.SendApironeWalletId)
async def back_to_apirone_menu(message: Message, state: FSMContext):
    apirone_data = await DB.get_apirone_data()
    if len(apirone_data) == 0:
        apirone_wallet_id = None
        apirone_transfer_key = None
    else:
        apirone_wallet_id = apirone_data[0][0]
        apirone_transfer_key = apirone_data[0][1]
    apirone_data_keyboard = await payments_data_kb()
    await bot.send_message(message.from_user.id,
                           get_string_with_args('old_apirone_data', [apirone_wallet_id, apirone_transfer_key]),
                           reply_markup=apirone_data_keyboard)
    await AddPaymentMethod.Apirone.set()


@dp.message_handler(TextEquals('back_button'), state=AddPaymentMethod.SendCapitalistLogin)
async def back_to_capitalist_menu(message: Message, state: FSMContext):
    capitalist_data = await DB.get_capitalist_data()
    if len(capitalist_data) == 0:
        capitalist_login = None
        capitalist_password = None
    else:
        capitalist_login = capitalist_data[0][0]
        capitalist_password = capitalist_data[0][1]
    capitalist_data_keyboard = await payments_data_kb()
    await bot.send_message(message.from_user.id,
                           get_string_with_args('old_capitalist_data', [capitalist_login, capitalist_password]),
                           reply_markup=capitalist_data_keyboard)
    await AddPaymentMethod.Apirone.set()


@dp.message_handler(TextEquals('back_button'), state=AddPaymentMethod.SendQiwiNumber)
async def back_to_qiwi_token(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_qiwi_token'), reply_markup=back)
    await AddPaymentMethod.SendQiwiToken.set()


@dp.message_handler(TextEquals('back_button'), state=AddPaymentMethod.SendQiwiPrivKey)
async def back_to_qiwi_number(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_qiwi_number'), reply_markup=back)
    await AddPaymentMethod.SendQiwiNumber.set()


@dp.message_handler(TextEquals('back_button'), state=AddPaymentMethod.SendApironeTransferKey)
async def back_to_apirone_wallet_id(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_apirone_wallet_id'), reply_markup=back)
    await AddPaymentMethod.SendApironeWalletId.set()


@dp.message_handler(TextEquals('back_button'), state=AddPaymentMethod.SendCapitalistPassword)
async def back_to_capitalist_login(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_capitalist_login'), reply_markup=back)
    await AddPaymentMethod.SendCapitalistLogin.set()


@dp.message_handler(TextEquals('back_button'), state=Mailing.EnterText)
async def back_to_admin_menu(message: Message, state: FSMContext):
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('back_button'), state=OtherFunctionsMenu.ChangeUserBalance)
async def back_to_find_user(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_user_id'), reply_markup=back)
    await OtherFunctionsMenu.FindProfile.set()


@dp.message_handler(TextEquals('back_button'), state=OtherFunctionsMenu.EditCommission)
async def back_to_other_function(message: Message, state: FSMContext):
    other_functions = await other_functions_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=other_functions)
    await OtherFunctionsMenu.InMenu.set()


@dp.message_handler(TextEquals('back_button'), state=OtherFunctionsMenu.EditCashback)
async def back_to_other_functions_menu(message: Message, state: FSMContext):
    other_functions = await other_functions_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=other_functions)
    await OtherFunctionsMenu.InMenu.set()


@dp.message_handler(TextEquals('decline_button'), state=Mailing.Accepting)
async def back_to_admin_menu(message: Message, state: FSMContext):
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=admin_menu)
    await state.reset_data()
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('mailing_button'), state=AdminMenu.IsAdmin)
async def mailing(message: Message, state: FSMContext):
    users = await DB.get_all_mailing_users()
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string_with_args('mailing_message', [len(users)]),
                           reply_markup=back)
    await Mailing.EnterText.set()


@dp.message_handler(TextEquals('statistics_button'), state=AdminMenu.IsAdmin)
async def send_statistics_handler(message: Message, state: FSMContext):
    user = await DB.get_user(message.from_user.id)
    seller = await DB.get_seller(message.from_user.id)
    balance = await DB.get_balance(message.from_user.id)
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
    referrals = await DB.get_referrals(message.from_user.id)
    ref_count = len(referrals) if referrals is not None else 0
    await bot.send_message(message.from_user.id, get_string_with_args('user_profile_message',
                                                                      [message.from_user.id, balance, user[9],
                                                                       user[10], ref_count, user[12],
                                                                       status]) + f"\n*****\n{extra_menu}")


@dp.message_handler(state=Mailing.EnterText)
async def enter_mailing_text(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text
    users = await DB.get_all_mailing_users()
    accept_kb = await accept_menu()
    await bot.send_message(message.from_user.id, get_string_with_args('mailing_accepting', [len(users), message.text]),
                           reply_markup=accept_kb)
    await Mailing.Accepting.set()


@dp.message_handler(TextEquals('accept_button'), state=Mailing.Accepting)
async def accept_mailing(message: Message, state: FSMContext):
    users = await DB.get_all_mailing_users()
    async with state.proxy() as data:
        text = data['text']
    success = 0
    fail = 0
    for user in users:
        try:
            cancel_kb = await cancel_subscription_kb(user[1])
            await bot.send_message(user[1], get_string_with_args('mailing_for_users_message', [text]),
                                   reply_markup=cancel_kb)
            success += 1
        except BotBlocked:
            fail += 1
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string_with_args('final_of_mailing_message', [success, fail]),
                           reply_markup=admin_menu)
    await state.reset_data()
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('edit_start_message_button'), state=AdminMenu.IsAdmin)
async def edit_start_message(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_new_start_message'), reply_markup=back)
    await AdminMenu.EditStartMessage.set()


@dp.message_handler(TextEquals('category_manager_button'), state=AdminMenu.IsAdmin)
async def categories_manager_handler(message: Message, state: FSMContext):
    categories_manager = await categories_manager_kb()
    await bot.send_message(message.from_user.id, 'Categories Manager', reply_markup=categories_manager)
    await AdminMenu.ManageCategories.set()


@dp.message_handler(TextEquals('add_category_button'), state=AdminMenu.ManageCategories)
async def categories_manager_menu_add(message: Message, state: FSMContext):
    categories = await choise_of_categories_kb()
    await bot.send_message(message.from_user.id, get_string('choose_category_type'), reply_markup=categories)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(state=AddCategory.EnterCategoryName)
async def enter_category_name_message(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['category_name'] = message.text
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_category_desc_message'), reply_markup=back)
    await AddCategory.EnterCategoryDesc.set()


@dp.message_handler(state=AddCategory.EnterCategoryDesc)
async def enter_category_desc_message(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['category_desc'] = message.text
    back_skip = await back_skip_kb()
    await bot.send_message(message.from_user.id, get_string('enter_category_img_message'), reply_markup=back_skip)
    await AddCategory.EnterCategoryImg.set()


@dp.message_handler(TextEquals('confirm_button'), state=AddCategory.ConfirmAddCategory)
async def categories_manager_menu_add_confirm(message: Message, state: FSMContext):
    async with state.proxy() as data:
        category_name = data['category_name']
        category_desc = data['category_desc']
        category_banner = data['category_banner']
        category_banner_type = data['category_banner_type']
        category_type = data['category_type']
    admin_menu = await admin_menu_kb()
    await DB.add_category(category_name=category_name, category_desc=category_desc, category_banner=category_banner,
                          category_banner_type=category_banner_type, category_type=category_type)
    await bot.send_message(message.from_user.id, get_string('category_added_message'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('remove_category_button'), state=AdminMenu.ManageCategories)
async def categories_manager_remove_category(message: Message, state: FSMContext):
    categories_manager = await categories_manager_kb()
    all_categories = await DB.get_all_categories(category_type=None)
    if not len(all_categories):
        await bot.send_message(message.from_user.id, 'Пусто!', reply_markup=categories_manager)
        return
    await bot.send_message(message.from_user.id, get_string('category_list'))
    for category in all_categories:
        remove_category = await remove_category_kb(category[0])
        if category[4] == 'photo':
            await bot.send_photo(chat_id=message.from_user.id, photo=category[3],
                                 caption=get_string_with_args('add_category_confirm_message',
                                                              [category[5], category[1], category[2]]),
                                 reply_markup=remove_category)
        if category[4] == 'file':
            await bot.send_document(chat_id=message.from_user.id, document=category[3],
                                    caption=get_string_with_args('add_category_confirm_message',
                                                                 [category[5], category[1], category[2]]),
                                    reply_markup=remove_category)
        if category[4] == 'None':
            await bot.send_message(message.from_user.id, get_string_with_args('add_category_confirm_message',
                                                                              [category[5], category[1], category[2]]),
                                   reply_markup=remove_category)


@dp.message_handler(TextEquals('other_functions_button'), state=AdminMenu.IsAdmin)
async def admin_menu_other_func(message: Message, state: FSMContext):
    other_functions = await other_functions_kb()
    await bot.send_message(message.from_user.id, get_string('other_functions_message'), reply_markup=other_functions)
    await OtherFunctionsMenu.InMenu.set()


@dp.message_handler(TextEquals('edit_ref_cashback_button'), state=OtherFunctionsMenu.InMenu)
async def edit_ref_cashback(message: Message, state: FSMContext):
    back = await back_kb()
    cfg = await DB.get_config()
    cashback = cfg[7]
    await bot.send_message(message.from_user.id, get_string_with_args('edit_ref_cashback_message', [cashback]),
                           reply_markup=back)
    await OtherFunctionsMenu.EditCashback.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=OtherFunctionsMenu.EditCashback)
async def change_cashback(message: Message, state: FSMContext):
    try:
        float(message.text)
    except ValueError:
        await bot.send_message(message.from_user.id, get_string('incorrect_value'))
        return
    other_functions = await other_functions_kb()
    await DB.set_cashback(float(message.text))
    await bot.send_message(message.from_user.id, get_string('cashback_was_changed_message'),
                           reply_markup=other_functions)
    await OtherFunctionsMenu.InMenu.set()


@dp.message_handler(TextEquals('edit_support_group_button'), state=OtherFunctionsMenu.InMenu)
async def edit_support_group(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_new_support_group_message'), reply_markup=back)
    await OtherFunctionsMenu.EditSupportGroup.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=OtherFunctionsMenu.EditSupportGroup)
async def change_support_group(message: Message, state: FSMContext):
    await DB.set_support_group(message.text)
    other_functions = await other_functions_kb()
    await bot.send_message(message.from_user.id, get_string('going_back_message'), reply_markup=other_functions)
    await OtherFunctionsMenu.InMenu.set()


@dp.message_handler(TextEquals('edit_seller_commission_button'), state=OtherFunctionsMenu.InMenu)
async def admin_edit_seller_commission(message: Message, state: FSMContext):
    current_commission = await DB.get_commission()
    back = await back_kb()
    await bot.send_message(message.from_user.id,
                           get_string_with_args('editing_commission_message', [f"{current_commission}%"]),
                           reply_markup=back)
    await OtherFunctionsMenu.EditCommission.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=OtherFunctionsMenu.EditCommission)
async def set_new_commission(message: Message, state: FSMContext):
    try:
        float(message.text)
    except ValueError:
        await bot.send_message(message.from_user.id, get_string('invalid_value'))
        return
    await DB.set_new_commission(float(message.text))
    other_functions = await other_functions_kb()
    await bot.send_message(message.from_user.id, get_string('successful_accept'), reply_markup=other_functions)
    await OtherFunctionsMenu.InMenu.set()


@dp.message_handler(TextEquals('edit_user_agreement_button'), state=OtherFunctionsMenu.InMenu)
async def admin_edit_user_agreement(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_new_user_agreement_text'), reply_markup=back)
    await OtherFunctionsMenu.EditUserAgreement.set()


@dp.message_handler(TextEquals('find_profile_button'), state=OtherFunctionsMenu.InMenu)
async def admin_find_profile(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_user_id'), reply_markup=back)
    await OtherFunctionsMenu.FindProfile.set()


@dp.message_handler(TextEquals('find_seller_button'), state=OtherFunctionsMenu.InMenu)
async def admin_find_seller(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_seller_id'), reply_markup=back)
    await OtherFunctionsMenu.FindSeller.set()


@dp.message_handler(state=OtherFunctionsMenu.FindSeller)
async def find_profile_proceed(message: Message, state: FSMContext):
    if message.text.isdigit():
        seller = await DB.get_seller(int(message.text))
        user = await DB.get_user(int(message.text))
        balance = await DB.get_balance(int(message.text))
        if seller:
            async with state.proxy() as data:
                data['seller_id'] = int(message.text)
            status = get_string('seller_status') if not int(message.text) in admin_ids else get_string(
                'admin_status') + ', ' + get_string('seller_status')
            seller_position_count = await DB.get_position_count(int(message.text))
            seller_commission = await DB.get_seller_commission(int(message.text))
            seller_log_check_time = await DB.get_seller_log_check_time(int(message.text))
            seller_profile = await seller_profile_kb(int(message.text), seller_position_count, seller_commission,
                                                     seller_log_check_time)
            await bot.send_message(message.from_user.id, get_string_with_args('find_seller_message',
                                                                              [message.from_user.id, user[0],
                                                                               seller[7], seller[8], seller[9],
                                                                               status, '@' + user[3], balance,
                                                                               seller[4]]),
                                   reply_markup=seller_profile)
        else:
            await bot.send_message(message.from_user.id, get_string('user_is_not_found'))
    else:
        await bot.send_message(message.from_user.id, get_string('incorrect_user_id'))


@dp.message_handler(state=OtherFunctionsMenu.FindProfile)
async def find_profile_proceed(message: Message, state: FSMContext):
    if message.text.isdigit():
        user = await DB.get_user(int(message.text))
        balance = await DB.get_balance(int(message.text))
        if user:
            seller = await DB.get_seller(int(message.text))
            if int(message.text) in admin_ids:
                status = get_string('admin_status') if seller is None else get_string(
                    'admin_status') + ', ' + get_string('seller_status')
            else:
                status = get_string('user_status') if seller is None else get_string('seller_status')
            change_user_balance = await change_user_balance_kb(message.text)
            await bot.send_message(message.from_user.id, get_string_with_args('find_profile_message',
                                                                              [message.from_user.id, user[0],
                                                                               balance,
                                                                               status, '@' + user[3], balance]),
                                   reply_markup=change_user_balance)
        else:
            await bot.send_message(message.from_user.id, get_string('user_is_not_found'))
    else:
        await bot.send_message(message.from_user.id, get_string('incorrect_user_id'))


@dp.message_handler(TextEquals('positions_manager_button'), state=AdminMenu.IsAdmin)
async def position_manager_handler(message: Message, state: FSMContext):
    positions_manager = await positions_manager_kb()
    await bot.send_message(message.from_user.id, get_string('positions_manager_button'), reply_markup=positions_manager)
    await AdminMenu.ManagePositions.set()


@dp.message_handler(TextEquals('add_designer_position_button'), state=AdminMenu.ManagePositions)
async def add_position_handler(message: Message, state: FSMContext):
    all_categories = await DB.get_all_categories('designer')
    await bot.send_message(message.from_user.id, get_string('choose_designer_message'))
    for category in all_categories:
        choose_designer_category_for_position = await choose_designer_category_for_position_kb(category[0], category[1])
        if category[4] == 'photo':
            await bot.send_photo(chat_id=message.from_user.id,
                                 caption=get_string_with_args('category_card', [category[2]]), photo=category[3],
                                 reply_markup=choose_designer_category_for_position)
        if category[4] == 'file':
            await bot.send_document(chat_id=message.from_user.id,
                                    caption=get_string_with_args('category_card', [category[2]]), document=category[3],
                                    reply_markup=choose_designer_category_for_position)
        if category[4] == 'None':
            await bot.send_message(message.from_user.id, get_string_with_args('category_card', [category[2]]),
                                   reply_markup=choose_designer_category_for_position)


@dp.message_handler(content_types=ContentTypes.TEXT, state=AddPosition.EnterPositionName)
async def add_position_title(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_description_to_position'), reply_markup=back)
    await AddPosition.EnterPositionDesc.set()
    async with state.proxy() as data:
        if message.text is None:
            data['position_name'] = message.html_text
        else:
            data['position_name'] = message.text


@dp.message_handler(content_types=ContentTypes.TEXT, state=AddPosition.EnterPositionDesc)
async def add_position_description(message: Message, state: FSMContext):
    back_skip = await back_skip_kb()
    await bot.send_message(message.from_user.id, get_string('send_photo_to_position'), reply_markup=back_skip)
    await AddPosition.EnterPositionImg.set()
    async with state.proxy() as data:
        if message.text is None:
            data['position_desc'] = message.html_text
        else:
            data['position_desc'] = message.text


@dp.message_handler(content_types=ContentTypes.TEXT, state=AddPosition.EnterDesignerNickName)
async def add_position_title(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_designer_login'), reply_markup=back)
    await AddPosition.EnterDesignerLogin.set()
    async with state.proxy() as data:
        if message.text is None:
            data['designer_nick_name'] = message.html_text
        else:
            data['designer_nick_name'] = message.text


@dp.message_handler(content_types=ContentTypes.TEXT, state=AddPosition.EnterDesignerLogin)
async def add_position_add_desc(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_designer_price'), reply_markup=back)
    await AddPosition.EnterDesignerPrice.set()
    async with state.proxy() as data:
        if message.text is None:
            data['designer_login'] = message.html_text
        else:
            data['designer_login'] = message.text


@dp.message_handler(content_types=ContentTypes.TEXT, state=AddPosition.EnterDesignerPrice)
async def add_position_add_desc(message: Message, state: FSMContext):
    try:
        float(message.text)
    except ValueError:
        await bot.send_message(message.from_user.id, get_string('incorrect_value'))
        return
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_designer_portfolio_link'), reply_markup=back)
    await AddPosition.EnterDesignerLink.set()
    async with state.proxy() as data:
        if message.text is None:
            data['designer_price'] = message.html_text
        else:
            data['designer_price'] = message.text


@dp.message_handler(content_types=ContentTypes.TEXT, state=AddPosition.EnterDesignerLink)
async def add_position_add_desc(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text is None:
            data['designer_link'] = message.html_text
        else:
            data['designer_link'] = message.text
    try:
        link_message = await bot.send_message(message.from_user.id, message.text,
                                              reply_markup=InlineKeyboardMarkup().row(
                                                  InlineKeyboardButton(text=message.text, url=message.text)))
        await bot.delete_message(message.from_user.id, link_message.message_id)
    except BadRequest:
        await bot.send_message(message.from_user.id, get_string('incorrect_value'))
        return
    back_skip = await back_skip_kb()
    await bot.send_message(message.from_user.id,
                           get_string('send_designer_banner_message'),
                           reply_markup=back_skip)
    await AddPosition.EnterDesignerImg.set()


@dp.message_handler(TextEquals('confirm_button'), state=AddPosition.ConfirmAddDesigner)
async def add_designer_confirm(message: Message, state: FSMContext):
    async with state.proxy() as data:
        nickname = data['designer_nick_name']
        login = '@' + data['designer_login'] if data['designer_login'][0] != '@' else data['designer_login']
        price = data['designer_price']
        link = data['designer_link']
        category_id = data['category_id']
        banner = data['designer_banner']
        banner_type = data['designer_banner_type']
    await DB.add_designer_position(nickname, login, float(price), link, category_id, banner, banner_type)
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('designer_was_successfully_added'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('confirm_button'), state=AddPosition.ConfirmAddPosition)
async def add_position_confirm(message: Message, state: FSMContext):
    async with state.proxy() as data:
        position_name = data['position_name']
        position_desc = data['position_desc']
        position_banner = data['position_banner']
        position_banner_type = data['position_banner_type']
        category_id = data['category_id']
        seller_id = data['seller_id']
    await DB.add_position(position_name=position_name, position_desc=position_desc, position_banner=position_banner,
                          position_banner_type=position_banner_type, category_id=category_id)
    await DB.add_seller_position(position_name, seller_id)
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('position_was_successfully_added'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('remove_designer_position_button'), state=AdminMenu.ManagePositions)
async def remove_position(message: Message, state: FSMContext):
    category_type = 'designer'
    all_categories = await DB.get_all_categories(category_type)
    await bot.send_message(message.from_user.id, get_string('choose_designer_message'))
    if not len(all_categories):
        positions_manager = await positions_manager_kb()
        await bot.send_message(message.from_user.id, get_string('empty'), reply_markup=positions_manager)
        await AdminMenu.ManagePositions.set()
        return
    for category in all_categories:
        choose_category_for_position = await choose_designer_to_remove_position_kb(category[0], category[1])
        if category[4] == 'photo':
            await bot.send_photo(chat_id=message.from_user.id,
                                 caption=get_string_with_args('category_card', [category[2]]), photo=category[3],
                                 reply_markup=choose_category_for_position)
        if category[4] == 'file':
            await bot.send_document(chat_id=message.from_user.id,
                                    caption=get_string_with_args('category_card', [category[2]]), document=category[3],
                                    reply_markup=choose_category_for_position)
        if category[4] == 'None':
            await bot.send_message(message.from_user.id, get_string_with_args('category_card', [category[2]]),
                                   reply_markup=choose_category_for_position)


@dp.message_handler(TextEquals('payment_settings_button'), state=AdminMenu.IsAdmin)
async def payment_methods_handlers(message: Message, state: FSMContext):
    payment_methods = await payment_methods_kb()
    await bot.send_message(message.from_user.id, get_string('choice_of_action_button'), reply_markup=payment_methods)
    await AddPaymentMethod.InMenu.set()


@dp.message_handler(TextEquals('seller_queries_button'), state=AdminMenu.IsAdmin)
async def send_queries_list(message: Message, state: FSMContext):
    sellers = await DB.get_all_unapproved_sellers()
    if len(sellers) == 0:
        await bot.send_message(message.from_user.id, get_string('no_queries'))
    for seller in sellers:
        seller_balance = await DB.get_user(seller[1])
        seller_balance = PrivateKeyTestnet(wif=seller_balance[2]).get_balance()
        approve_reject_seller_query = await approve_reject_seller_query_kb(seller[1])
        await bot.send_message(message.from_user.id, get_string_with_args('new_seller_query',
                                                                          ['@' + seller[2], seller[1], seller_balance,
                                                                           seller[4]]),
                               reply_markup=approve_reject_seller_query)


# qiwi handlers
@dp.message_handler(TextEquals('add_qiwi_button'), state=AddPaymentMethod.InMenu)
async def add_qiwi_wallet(message: Message, state: FSMContext):
    qiwi_data = await DB.get_qiwi_data()
    if len(qiwi_data) == 0:
        qiwi_token = None
        qiwi_number = None
        qiwi_priv_key = None
    else:
        qiwi_token = qiwi_data[0][0]
        qiwi_number = qiwi_data[0][1]
        qiwi_priv_key = qiwi_data[0][2]
    qiwi_data_keyboard = await payments_data_kb()
    await bot.send_message(message.from_user.id,
                           get_string_with_args('old_qiwi_data', [qiwi_token, qiwi_number, qiwi_priv_key]),
                           reply_markup=qiwi_data_keyboard)
    await AddPaymentMethod.Qiwi.set()


@dp.message_handler(TextEquals('refresh_data_button'), state=AddPaymentMethod.Qiwi)
async def refresh_qiwi_data(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_qiwi_token'), reply_markup=back)
    await AddPaymentMethod.SendQiwiToken.set()


@dp.message_handler(state=AddPaymentMethod.SendQiwiToken)
async def send_qiwi_token(message: Message, state: FSMContext):
    await DB.refresh_qiwi_token(message.text)
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_qiwi_number'), reply_markup=back)
    await AddPaymentMethod.SendQiwiNumber.set()


@dp.message_handler(state=AddPaymentMethod.SendQiwiNumber)
async def send_qiwi_number(message: Message, state: FSMContext):
    await DB.refresh_qiwi_number(message.text)
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_qiwi_priv_key'), reply_markup=back)
    await AddPaymentMethod.SendQiwiPrivKey.set()


@dp.message_handler(state=AddPaymentMethod.SendQiwiPrivKey)
async def send_qiwi_priv_key(message: Message, state: FSMContext):
    await DB.refresh_qiwi_priv_key(message.text)
    qiwi_data = await DB.get_qiwi_data(True)
    qiwi_token = qiwi_data[0][0]
    qiwi_number = qiwi_data[0][1]
    qiwi_priv_key = message.text
    final_qiwi_menu = await accept_menu()
    await bot.send_message(message.from_user.id,
                           get_string_with_args('final_qiwi_menu', [qiwi_token, qiwi_number, qiwi_priv_key]),
                           reply_markup=final_qiwi_menu)
    await AddPaymentMethod.AcceptQiwi.set()


@dp.message_handler(TextEquals('accept_button'), state=AddPaymentMethod.AcceptQiwi)
async def accept_qiwi_data(message: Message, state: FSMContext):
    await DB.accept_new_qiwi_data()
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('successful_accept'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(TextEquals('decline_button'), state=AddPaymentMethod.AcceptCapitalist)
@dp.message_handler(TextEquals('decline_button'), state=AddPaymentMethod.AcceptApirone)
@dp.message_handler(TextEquals('decline_button'), state=AddPaymentMethod.AcceptQiwi)
async def decline_data(message: Message, state: FSMContext):
    await DB.decline_new_data()
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('successful_decline'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


# apirone handlers
@dp.message_handler(TextEquals('add_apirone_button'), state=AddPaymentMethod.InMenu)
async def add_apirone_wallet(message: Message, state: FSMContext):
    apirone_data = await DB.get_apirone_data()
    if len(apirone_data) == 0:
        apirone_wallet_id = None
        apirone_transfer_key = None
    else:
        apirone_wallet_id = apirone_data[0][0]
        apirone_transfer_key = apirone_data[0][1]
    apirone_data_keyboard = await payments_data_kb()
    await bot.send_message(message.from_user.id,
                           get_string_with_args('old_apirone_data', [apirone_wallet_id, apirone_transfer_key]),
                           reply_markup=apirone_data_keyboard)
    await AddPaymentMethod.Apirone.set()


@dp.message_handler(TextEquals('refresh_data_button'), state=AddPaymentMethod.Apirone)
async def refresh_apirone_data(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_apirone_wallet_id'), reply_markup=back)
    await AddPaymentMethod.SendApironeWalletId.set()


@dp.message_handler(state=AddPaymentMethod.SendApironeWalletId)
async def send_apirone_wallet_id(message: Message, state: FSMContext):
    await DB.refresh_apirone_wallet_id(message.text)
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_apirone_transfer_key'), reply_markup=back)
    await AddPaymentMethod.SendApironeTransferKey.set()


@dp.message_handler(state=AddPaymentMethod.SendApironeTransferKey)
async def send_qiwi_number(message: Message, state: FSMContext):
    await DB.refresh_apirone_transfer_key(message.text)
    apirone_data = await DB.get_apirone_data(True)
    apirone_wallet_id = apirone_data[0][0]
    apirone_transfer_key = apirone_data[0][1]
    final_apirone_menu = await accept_menu()
    await bot.send_message(message.from_user.id,
                           get_string_with_args('final_apirone_menu', [apirone_wallet_id, apirone_transfer_key]),
                           reply_markup=final_apirone_menu)
    await AddPaymentMethod.AcceptApirone.set()


@dp.message_handler(TextEquals('accept_button'), state=AddPaymentMethod.AcceptApirone)
async def accept_apirone_data(message: Message, state: FSMContext):
    await DB.accept_new_apirone_data()
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('successful_accept'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


# capitalist handlers
@dp.message_handler(TextEquals('add_capitalist_button'), state=AddPaymentMethod.InMenu)
async def add_capitalist_login(message: Message, state: FSMContext):
    capitalist_data = await DB.get_capitalist_data()
    if len(capitalist_data) == 0:
        capitalist_login = None
        capitalist_password = None
    else:
        capitalist_login = capitalist_data[0][0]
        capitalist_password = capitalist_data[0][1]
    capitalist_data_keyboard = await payments_data_kb()
    await bot.send_message(message.from_user.id,
                           get_string_with_args('old_capitalist_data', [capitalist_login, capitalist_password]),
                           reply_markup=capitalist_data_keyboard)
    await AddPaymentMethod.Capitalist.set()


@dp.message_handler(TextEquals('refresh_data_button'), state=AddPaymentMethod.Capitalist)
async def refresh_capitalist_data(message: Message, state: FSMContext):
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_capitalist_login'), reply_markup=back)
    await AddPaymentMethod.SendCapitalistLogin.set()


@dp.message_handler(state=AddPaymentMethod.SendCapitalistLogin)
async def send_capitalist_login(message: Message, state: FSMContext):
    await DB.refresh_capitalist_login(message.text)
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('send_capitalist_password'), reply_markup=back)
    await AddPaymentMethod.SendCapitalistPassword.set()


@dp.message_handler(state=AddPaymentMethod.SendCapitalistPassword)
async def send_capitalist_password(message: Message, state: FSMContext):
    await DB.refresh_capitalist_password(message.text)
    capitalist_data = await DB.get_capitalist_data(True)
    capitalist_login = capitalist_data[0][0]
    capitalist_password = capitalist_data[0][1]
    final_capitalist_menu = await accept_menu()
    await bot.send_message(message.from_user.id,
                           get_string_with_args('final_capitalist_menu', [capitalist_login, capitalist_password]),
                           reply_markup=final_capitalist_menu)
    await AddPaymentMethod.AcceptCapitalist.set()


@dp.message_handler(TextEquals('accept_button'), state=AddPaymentMethod.AcceptCapitalist)
async def accept_capitalist_data(message: Message, state: FSMContext):
    await DB.accept_new_capitalist_data()
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('successful_accept'), reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()


@dp.message_handler(content_types=ContentTypes.TEXT, state=OtherFunctionsMenu.ChangeUserBalance)
async def set_new_balance(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await bot.send_message(message.from_user.id, get_string('incorrect_value'))
        return
    amount = message.text
    async with state.proxy() as data:
        user_id = data['user_id']
    await DB.set_user_balance(user_id, amount)
    await state.reset_data()
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('success_setting_balance'))
    await bot.send_message(message.from_user.id, get_string('send_user_id'), reply_markup=back)
    await OtherFunctionsMenu.FindProfile.set()


@dp.message_handler(TextEquals('add_partner_service_button'), state=AdminMenu.IsAdmin)
async def add_service_handler(message: Message, state: FSMContext):
    partner = await partner_kb()
    await bot.send_message(message.from_user.id, get_string('partner'), reply_markup=partner)
    category_type = 'partners'
    all_categories = await DB.get_all_categories(category_type)
    if len(all_categories) == 0:
        await bot.send_message(message.from_user.id, get_string('empty'))
        return
    await bot.send_message(message.from_user.id, get_string('choose_category_name'))
    for category in all_categories:
        category_to_load = await category_to_service_kb(category[1], category[0])
        if category[4] == 'photo':
            await bot.send_photo(chat_id=message.from_user.id, photo=category[3],
                                 caption=get_string_with_args('category_card', [category[2]]),
                                 reply_markup=category_to_load)
        if category[4] == 'file':
            await bot.send_document(chat_id=message.from_user.id, document=category[3],
                                    caption=get_string_with_args('category_card', [category[2]]),
                                    reply_markup=category_to_load)
        if category[4] == 'None':
            await bot.send_message(message.from_user.id, get_string_with_args('category_card', [category[2]]),
                                   reply_markup=category_to_load)


@dp.message_handler(content_types=ContentTypes.TEXT, state=LoadService.EnterProductDescription)
async def enter_prod_desc(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['product_description'] = message.text
    back = await back_kb()
    await bot.send_message(message.from_user.id, get_string('enter_product_file_message'), reply_markup=back)
    await LoadService.EnterProductFile.set()


@dp.message_handler(TextEquals('confirm_button'), state=LoadService.ConfirmAddingProduct)
async def confirm_adding_product_handler(message: Message, state: FSMContext):
    async with state.proxy() as data:
        position_id = data['position_id']
        product_desc = data['product_description']
        product_file = data['product_file']
    await DB.add_product(product_desc=product_desc, product_file=product_file, seller_id=message.from_user.id,
                         position_id=position_id, load_time=datetime.datetime.now().timestamp())
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('successfully_product_adding_message'),
                           reply_markup=admin_menu)
    await AdminMenu.IsAdmin.set()
'''
'''
@dp.message_handler(TextEquals('payments_admin_button'), state=OtherFunctionsMenu.InMenu)
async def payments_list(message: Message, state: FSMContext):
    payment_requests = await DB.get_payment_requests()
    if len(payment_requests) == 0:
        await bot.send_message(message.from_user.id, get_string('empty'))
        return
    for req in payment_requests:
        pay_reject = await pay_reject_kb(req[0])
        seller = await DB.get_seller(req[1])
        seller_id = seller[1]
        seller_username = seller[2]
        await bot.send_message(message.from_user.id, get_string_with_args('new_payment_request',
                                                                          [seller_username, seller_id,
                                                                           get_string(req[3]), req[2], req[4]]),
                               reply_markup=pay_reject)


@dp.message_handler(TextEquals('create_service'), state=AdminMenu.IsAdmin)
async def categories_manager_handler1(message: Message, state: FSMContext):
    categories_manager = await categories_manager_kb1()
    await bot.send_message(message.from_user.id, 'category_service', reply_markup=categories_manager)
    await AddCategory.EnterCategoryName.set()
    async with state.proxy() as data:
        data['category_type'] = call.data


@dp.message_handler(TextEquals('add_subcategory_button'), state=AdminMenu.ManageCategories)
async def categories_manager_menu_add1(message: Message, state: FSMContext):
    categories = await choise_of_categories_kb()
    admin_menu = await admin_menu_kb()
    await bot.send_message(message.from_user.id, get_string('choose_category_type'), reply_markup=categories)
    await AdminMenu.IsAdmin.set()


''' Подкатегория '''

@dp.message_handler(TextEquals('delete_subcategory_button'), state=AdminMenu.ManageCategories)
async def categories_manager_remove_category(message: Message, state: FSMContext):
    categories_manager = await categories_manager_kb()
    all_categories = await DB.get_all_categories(category_type=None)
    if not len(all_categories):
        await bot.send_message(message.from_user.id, 'Пусто!', reply_markup=categories_manager)
        return
    await bot.send_message(message.from_user.id, get_string('category_list'))
    for category in all_categories:
        remove_category = await remove_category_kb(category[0])
        if category[4] == 'photo':
            await bot.send_photo(chat_id=message.from_user.id, photo=category[3],
                                 caption=get_string_with_args('add_category_confirm_message',
                                                              [category[5], category[1], category[2]]),
                                 reply_markup=remove_category)
        if category[4] == 'file':
            await bot.send_document(chat_id=message.from_user.id, document=category[3],
                                    caption=get_string_with_args('add_category_confirm_message',
                                                                 [category[5], category[1], category[2]]),
                                    reply_markup=remove_category)
        if category[4] == 'None':
            await bot.send_message(message.from_user.id, get_string_with_args('add_category_confirm_message',
                                                                              [category[5], category[1], category[2]]),
                                   reply_markup=remove_category)

'''
@dp.message_handler(TextEquals('add_subcategory_button'), state=AdminMenu.ManageCategories)
async def categories_manager_remove_category(message: Message, state: FSMContext):
    main =

'''