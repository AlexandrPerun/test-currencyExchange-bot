import telebot
import config
import pb
import datetime
import pytz
import json

P_TIMEZONE = pytz.timezone(config.TIMEZONE)
TIMEZONE_COMMON_NAME = config.TIMEZONE_COMMON_NAME

bot = telebot.TeleBot(config.TOKEN)

# обработчик команды start
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(
        message.chat.id,
        'Привет! Я могу отобразить текущий курс валют.\n' +
        'Для отображения текущего курса напиши /exchange.\n' +
        'Для конвертирования валюты напиши /convert.\n' +
        'Для получения помощи напиши /help.'
    )

# обработчик команды help
@bot.message_handler(commands=['help'])
def help_command(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton(
            'Message the developer', url='https://t.me/AlexPerun'
        )
    )
    bot.send_message(
        message.chat.id,
        'Для получения курса валют введите /exchange:\n' +
        '    1) Выберите валюту;\n' +
        '    2) Вы получите сообщение, \n' +
        '    содержащее информацию о \n' +
        '    стоимости продажи и покупки \n' +
        '    выбранной валюты;\n' +
        '    3) Кнопка “Update” обновляет \n' +
        '    курс выбранной валюты;\n' +
        '    4) Нажав на кнопку "Share" \n' +
        '    можно поделиться курсом \n' +
        '    с другими пользователями.\n' +
        'Для конвертирования валюты введите /convert:\n' +
        '    1) Выберите валюту из которой \n' +
        '    необходимо конвертировать;\n' +
        '    2) Выберите валюту в которую \n' +
        '    необходимо конвертировать;\n' +
        '    3) Введите сумму для конвертации;\n' +
        '    4) Нажав на кнопку "Share" \n' +
        '    можно поделиться конвертацией \n' +
        '    с другими пользователями.',
        reply_markup=keyboard
    )

# обработчик команды exchange
@bot.message_handler(commands=['exchange'])
def exchange_command(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton('USD', callback_data='get-USD')
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton('EUR', callback_data='get-EUR')
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton('RUR', callback_data='get-RUR')
    )
    bot.send_message(
        message.chat.id,
        'Выберите валюту:',
        reply_markup=keyboard
    )

# обработчик команды convert
@bot.message_handler(commands=['convert'])
def convert_from_command(message):
    keyboard_from = telebot.types.InlineKeyboardMarkup()
    keyboard_from.row(
        telebot.types.InlineKeyboardButton('UAH', callback_data='from-UAH')
    )
    keyboard_from.row(
        telebot.types.InlineKeyboardButton('USD', callback_data='from-USD')
    )
    keyboard_from.row(
        telebot.types.InlineKeyboardButton('EUR', callback_data='from-EUR')
    )
    keyboard_from.row(
        telebot.types.InlineKeyboardButton('RUR', callback_data='from-RUR')
    )

    bot.send_message(
        message.chat.id,
        'Выберите валюту, которую нужно конвертировать:',
        reply_markup=keyboard_from
    )

# обработчик кнопок
@bot.callback_query_handler(func=lambda call: True)
def iq_callback(query):
    data = query.data

    if data.startswith('get-'):
        get_ex_callback(query)

    elif data.startswith('from-'):
        get_convert_callback(query)
        config.from_code = data[5:]

    elif data.startswith('to-'):
        bot.answer_callback_query(query.id)
        config.to_code = data[3:]
        bot.send_message(
            query.message.chat.id,
            'Введите сумму в {0}:'.format(config.from_code),
        )

    else:
        try:
            if json.loads(data)['t'] == 'u':
                edit_message_callback(query)
        except ValueError:
            pass

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    flag = True
    while flag:
        flag = False
        try:
            sum = message.text
            sum = float(sum.replace(',', '.'))
        except:
            flag = True
            # bot.send_message(
            #     message.chat.id,
            #     'Ошибка! Введите числовое значение...'
            # )
    # result = convertation(config.from_code, config.to_code, sum)
    # bot.send_message(
    #     message.chat.id,
    #     '{0} {1} = {2} {3}'.format(sum, config.from_code, round(result, 4), config.to_code),
    #     reply_markup=
    # )
    convertation(message, config.from_code, config.to_code, sum)

def convertation(message, from_code, to_code, sum):
    result = sum
    if from_code != 'UAH':
        ex = pb.get_exchange(from_code)
        result *= float(ex['buy'])

    if to_code != 'UAH':
        ex = pb.get_exchange(to_code)
        result /= float(ex['sale'])

    bot.send_message(
        message.chat.id,
        '{0} {1} = {2} {3}'.format(sum, config.from_code, round(result, 4), config.to_code),
        reply_markup=share_convert_keyboard(ex),
        parse_mode='HTML'
    )
    #return result

# передает CallbackQuery в функцию для отображения курса
def get_ex_callback(query):
    bot.answer_callback_query(query.id)
    send_exchange_result(query.message, query.data[4:])

# возвращает курс валют
def send_exchange_result(message, ex_code):
    bot.send_chat_action(message.chat.id, 'typing')
    ex = pb.get_exchange(ex_code)
    bot.send_message(
        message.chat.id, serialize_ex(ex),
        reply_markup=get_update_keyboard(ex),
        parse_mode='HTML'
    )

# кнопки обновления курса и поделиться
def get_update_keyboard(ex):
   keyboard = telebot.types.InlineKeyboardMarkup()
   keyboard.row(
       telebot.types.InlineKeyboardButton(
           'Update',
           callback_data=json.dumps({
               't': 'u',
               'e': {
                   'b': ex['buy'],
                   's': ex['sale'],
                   'c': ex['ccy']
               }
           }).replace(' ', '')
       ),
       telebot.types.InlineKeyboardButton('Share', switch_inline_query=ex['ccy'])
   )
   return keyboard

# для отображения разниці между предідущим и текущим курсом после обновления
def serialize_ex(ex_json, diff=None):
    result = '<b>' + ex_json['base_ccy'] + ' -> ' + ex_json['ccy'] + ':</b>\n\n' + \
        'Buy: ' + ex_json['buy']
    if diff:
        result += ' ' + serialize_exchange_diff(diff['buy_diff']) + '\n' + \
            'Sell: ' + ex_json['sale'] + \
            ' ' + serialize_exchange_diff(diff['sale_diff']) + '\n'
    else:
        result += '\nSell: ' + ex_json['sale'] + '\n'
    return result

def serialize_exchange_diff(diff):
    result = ''
    if diff > 0:
        result = '(' + str(diff) + ' <img draggable="false" data-mce-resize="false" data-mce-placeholder="1" data-wp-emoji="1" class="emoji" alt="<img draggable="false" data-mce-resize="false" data-mce-placeholder="1" data-wp-emoji="1" class="emoji" alt="<img draggable="false" data-mce-resize="false" data-mce-placeholder="1" data-wp-emoji="1" class="emoji" alt="<img draggable="false" data-mce-resize="false" data-mce-placeholder="1" data-wp-emoji="1" class="emoji" alt="<img draggable="false" data-mce-resize="false" data-mce-placeholder="1" data-wp-emoji="1" class="emoji" alt="↗️" src="https://s.w.org/images/core/emoji/2.3/svg/2197.svg">" src="https://s.w.org/images/core/emoji/2.3/svg/2197.svg">" src="https://s.w.org/images/core/emoji/2.3/svg/2197.svg">" src="https://s.w.org/images/core/emoji/72x72/2197.png">" src="https://s.w.org/images/core/emoji/72x72/2197.png">)'
    elif diff < 0:
        result = '(' + str(diff)[
                       1:] + ' <img draggable="false" data-mce-resize="false" data-mce-placeholder="1" data-wp-emoji="1" class="emoji" alt="<img draggable="false" data-mce-resize="false" data-mce-placeholder="1" data-wp-emoji="1" class="emoji" alt="<img draggable="false" data-mce-resize="false" data-mce-placeholder="1" data-wp-emoji="1" class="emoji" alt="<img draggable="false" data-mce-resize="false" data-mce-placeholder="1" data-wp-emoji="1" class="emoji" alt="<img draggable="false" data-mce-resize="false" data-mce-placeholder="1" data-wp-emoji="1" class="emoji" alt="↘️" src="https://s.w.org/images/core/emoji/2.3/svg/2198.svg">" src="https://s.w.org/images/core/emoji/2.3/svg/2198.svg">" src="https://s.w.org/images/core/emoji/2.3/svg/2198.svg">" src="https://s.w.org/images/core/emoji/72x72/2198.png">" src="https://s.w.org/images/core/emoji/72x72/2198.png">)'
    return result

# функция редактирует сообщение с курсом обновляя его
def edit_message_callback(query):
    data = json.loads(query.data)['e']
    exchange_now = pb.get_exchange(data['c'])
    text = serialize_ex(
        exchange_now,
        get_exchange_diff(
            get_ex_from_iq_data(data),
            exchange_now
        )
    ) + '\n' + get_edited_signature()
    if query.message:
        bot.edit_message_text(
            text,
            query.message.chat.id,
            query.message.message_id,
            reply_markup=get_update_keyboard(exchange_now),
            parse_mode='HTML'
        )
    elif query.inline_messsage_id:
        bot.edit_message_text(
            text,
            inline_message_id=query.inline_message_id,
            reply_markup=get_update_keyboard(exchange_now),
            parse_mode='HTML'
        )

def get_ex_from_iq_data(exc_json):
    return {
        'buy': exc_json['b'],
        'sale': exc_json['s']
    }

def get_exchange_diff(last, now):
    return {
        'sale_diff': float("%.6f" % (float(now['sale']) - float(last['sale']))),
	'buy_diff': float("%.6f" % (float(now['buy']) - float(last['buy'])))
    }

def get_edited_signature():
    return '<i>Updated ' + \
           str(datetime.datetime.now(P_TIMEZONE).strftime('%H:%M:%S')) + \
           ' (' + TIMEZONE_COMMON_NAME + ')</i>'

# вызов кнопок для выбора валюты для конвертирования
def get_convert_callback(query):
    bot.answer_callback_query(query.id)
    convert_to_command(query.message)

# клавиатура с кодами валюты для конвертирования
def convert_to_command(message):
    bot.send_chat_action(message.chat.id, 'typing')
    keyboard_to = telebot.types.InlineKeyboardMarkup()
    keyboard_to.row(
        telebot.types.InlineKeyboardButton('UAH', callback_data='to-UAH')
    )
    keyboard_to.row(
        telebot.types.InlineKeyboardButton('USD', callback_data='to-USD')
    )
    keyboard_to.row(
        telebot.types.InlineKeyboardButton('EUR', callback_data='to-EUR')
    )
    keyboard_to.row(
        telebot.types.InlineKeyboardButton('RUR', callback_data='to-RUR')
    )

    bot.send_message(
        message.chat.id,
        'также выберите валюту, в которую нужно конвертировать:',
        reply_markup=keyboard_to
    )

# кнопки поделиться конвертацией
def share_convert_keyboard(ex):
   keyboard = telebot.types.InlineKeyboardMarkup()
   keyboard.row(
       telebot.types.InlineKeyboardButton('Share', switch_inline_query=ex['ccy'])
   )
   return keyboard

bot.polling(none_stop=True)