
import asyncio, json, os, requests
import os.path
from os import path
from google.colab import userdata

amvera_var = 0
#amvera_var = os.environ["MY_VAR"]
if amvera_var == 1:
  # Импортировать ключ для авторизации в GigaChat и токен от Telegram бота
  sber = os.environ('SBER_AUTH')
  bot_token = os.environ('ASKLLM_BOT_TOKEN')
else:
  # Импортировать ключ для авторизации в GigaChat и токен от Telegram бота
  sber = userdata.get('SBER_AUTH')
  bot_token = userdata.get('ASKLLM_BOT_TOKEN')

####################################################################################################
####################################################################################################
#######################################  AskLLM_bot  ###############################################
####################################################################################################
####################################################################################################
from langchain.chat_models.gigachat import GigaChat
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain

####################################################################################################
#                                            Инициализация                                         #
####################################################################################################

user_conversations = {} # Словарь для хранения ConversationBufferMemory каждого пользователя
user_conv_chain = {} # Словарь для хранения цепочек диалога каждого пользователя
#user_prompts = {} # Словарь для хранения промптов каждого пользователя

# Создать промпт по умолчанию
conv_prompt = '''
Ты являешься экспертом-универсалом в различных областях науки и техники, экономики и юриспруденции. \
Твоя задача дополнить текст, введенный пользователем в качестве запроса. \
Ты можешь дополнять текст используя только проверенную информацию. Это важно! \
\n\nТекущий разговор:\n{history}\nHuman: {input}\nAI:
'''

####################################################################################################
#                                             LLM                                                  #
####################################################################################################

# Создать объект LLM GigaChat
llm = GigaChat(credentials=sber,
          model='GigaChat:latest',
          verify_ssl_certs=False,
          profanity_check=False)

# Создать цепочку диалога
####################################################
def create_conversation_chain(user_id, llm):
    # Создать объект цепочки диалога - инициализация ConversationChain
    conversation = ConversationChain(llm=llm,
                                 verbose=True,
                                 memory=ConversationBufferMemory())
    conversation.prompt.template = conv_prompt # <<<<<<<<<<<<<<<<<<<<<< Промпт диалога по умолчанию
    # Обращение к системе
    # conversation.predict(input='Как меня зовут и чем я занимаюсь?')
    return(conversation)

####################################################################################################
##########################################    БОТ    ###############################################
####################################################################################################

from time import sleep

import telebot
from time import sleep
from telebot import types

bot = telebot.TeleBot(bot_token)
kbd = 0;

####################################################################################################
#                                    Функции обработки команд                                      #
####################################################################################################

# `/start` - функция, обрабатывающая команду
#############################################
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id

    # Проверка словарей для данного пользователя
    if user_id not in user_conversations:
        user_conversations[user_id] = ConversationBufferMemory()
    if user_id not in user_conv_chain:
        user_conv_chain[user_id] = create_conversation_chain(user_id, llm)
    conversation = user_conv_chain[user_id]
    conversation.memory = user_conversations[user_id]

    # SetMiniApp(message)
    bot.send_message(user_id, 'Готов к работе', parse_mode="Markdown", reply_markup=webAppKeyboard())

# `/help` - функция, обрабатывающая команду
#############################################
@bot.message_handler(commands=['help'])
def help(message):
    user_id = message.chat.id

    bot.send_message(user_id, 'Я - бот-помощник в работе с промптами. Для вызова MiniApp для настройки промптов - команда /start.')
#    bot.send.message(user_id, '''Я - бот-помощник в работе с промптами. Вы можете активировать MiniApp,\
#     сформировать с его помощью промпт и использовать его \
#     в дальнейшем диалоге с LLM''')

# `/stop` - функция, обрабатывающая команду
#############################################
@bot.message_handler(commands=['stop'])
def stop(message):
    user_id = message.chat.id

    bot.send_message(user_id, 'До свидания!')

####################################################################################################
#                                  Функции обработки сообщений                                     #
####################################################################################################

# Функция, обрабатывающая неправильные форматы ввода
####################################################
@bot.message_handler(content_types=['audio',
                                    'video',
                                    'document',
                                    'photo',
                                    'sticker',
                                    'voice',
                                    'location',
                                    'contact'])
def not_text(message):
  user_id = message.chat.id
  bot.send_message(user_id, 'Я работаю только с текстовыми сообщениями!')

# Функция, обрабатывающая текстовые сообщения
#############################################
@bot.message_handler(content_types=['text'])
def handle_text_message(message):
    user_id = message.chat.id

    # Проверка словарей для данного пользователя
    if user_id not in user_conversations:
        user_conversations[user_id] = ConversationBufferMemory()
    if user_id not in user_conv_chain:
        user_conv_chain[user_id] = create_conversation_chain(user_id, llm)
    conversation = user_conv_chain[user_id]
    conversation.memory = user_conversations[user_id]

    # Получение и отправка ответа через GigaChat
    q = message.text
    # (LLM)
    conversation.predict(input=q)
    bot.send_message(user_id, conversation.memory.chat_memory.messages[-1].content)

    # ........

    sleep(2)

# Функция, обрабатывающая нового пользователя
#############################################
#@bot.message_handler(content_types=['new_chat_members'])
@bot.message_handler(func=lambda message: True, content_types=['new_chat_members'])
def welcome_new_members(message):
#    new_members = message.new_chat_members
#    for new_member in new_members:
    user_id = message.chat.id
    # Проверка словарей для данного пользователя
    if user_id not in user_conversations:
        user_conversations[user_id] = ConversationBufferMemory()
    if user_id not in user_conv_chain:
        user_conv_chain[user_id] = create_conversation_chain(user_id, llm)
    conversation = user_conv_chain[user_id]
    conversation.memory = user_conversations[user_id]
    # SetMiniApp(message)
#        bot.send_message(chat_id=message.chat.id, text='Готов к работе', parse_mode="Markdown", reply_markup=webAppKeyboard())
    bot.send_message(user_id, 'Приветствую Вас!', parse_mode="Markdown", reply_markup=webAppKeyboard())

####################################################################################################
#                                           MiniApp                                                #
####################################################################################################
def webAppKeyboard(): #создание клавиатуры с webapp кнопкой
    keyboard = types.ReplyKeyboardMarkup(row_width=1) #создаем клавиатуру
    webApp = types.WebAppInfo("https://binomfx.github.io/AskLLM_bot/") #создаем webappinfo - формат хранения url
    appButton = types.KeyboardButton(text="Задать промпт", web_app=webApp) #создаем кнопку типа webapp
    keyboard.add(appButton) #добавляем кнопки в клавиатуру (если больше одной кнопки - через запятую)
    return keyboard #возвращаем клавиатуру

# Функция обработки данных от MiniApp
####################################################
#@bot.message_handler(func=lambda message: bool(message.web_app_data))
@bot.message_handler(content_types="web_app_data")
def web_app_data(message):
    user_id = message.chat.id
    data = message.web_app_data.data
    conversation = user_conv_chain[user_id]
    conversation.prompt.template = data # <<<<<<<<<<<<<<<<<<<<<< Новый промпт диалога
    bot.send_message(user_id, 'Новый промпт задан.')
    #bot.send_message(user_id, 'Новый промпт = ' + data)


####################################################################################################
#                                         Запуск бота                                              #
####################################################################################################
def main() -> None:
    # Запустить бот
    bot.polling(none_stop=True)

if __name__ == "__main__":
    main()

