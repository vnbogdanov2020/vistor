import cv2
import glob
import os
import moviepy.editor as mpe
import telebot
from telebot import types
import requests
from os import path
import time
from setting import bot_token

bot = telebot.TeleBot(bot_token)


dirpath = os.path.dirname(__file__)
picpath = os.path.join(dirpath, 'files/pic/')
videopath = os.path.join(dirpath, 'files/video/')
audiopath = os.path.join(dirpath, 'files/audio/')

keyboard1 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=1)
keyboard1.row('Получить фото')

keyboard2 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=1)
keyboard2.row('Выбрать мелодию')

#Первый запуск бота
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет! Я помогу составить из ваших фото видео-историю, которой можно поделиться с друзьями.', reply_markup=keyboard1)

#Обработка текстовых сообщений
@bot.message_handler(content_types=['text'])
def send_text(message):
    if message.text.lower() == 'получить фото':
       bot.send_message(message.chat.id, 'Сними или загрузи несколько фото в нужном порядке.', reply_markup=keyboard2)
    if message.text.lower() == 'выбрать мелодию':
        markup = types.InlineKeyboardMarkup()
        for file in glob.glob(audiopath+'*'):
            full_name = path.basename(file)
            name = path.splitext(full_name)[0]
            switch_button = types.InlineKeyboardButton(text=name, callback_data=name)
            markup.add(switch_button)
        bot.send_message(message.chat.id, "Выбери звуковую дорожу", reply_markup=markup)

#Сохраняем выбранное фото
@bot.message_handler(content_types=['photo'])
def sent_photo(message):

    raw = message.photo[2].file_id
    file_info = bot.get_file(raw)
    downloaded_file = 'https://api.telegram.org/file/bot' + bot_token + '/' + file_info.file_path
    myfile = requests.get(downloaded_file)
    open(picpath+str(message.chat.id) + '_' + file_info.file_id + str(int(round(time.time() * 1000)))+'.jpg', 'wb').write(myfile.content)

@bot.callback_query_handler(func=lambda c:True)
def inline(callback):
    #Обрабатываем все файлы пользователя
    img_array = []
    for filename in glob.glob(picpath + str(callback.message.chat.id) + '*.jpg'):
        if filename:
            img = cv2.imread(filename)
            #img = cv2.resize(img1, (480, 360))
            height, width, layers = img.shape
            size = (width, height)
            img_array.append(img)
    #Собираем из фото видеофайл
    if not img_array:
        bot.send_message(callback.message.chat.id, 'Сними или загрузи несколько фото в нужном порядке.', reply_markup=keyboard2)
    else:
        out = cv2.VideoWriter(videopath + str(callback.message.chat.id) + '.avi', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), .5, size)
        for i in range(len(img_array)):
            out.write(img_array[i])
        out.release()
        #Накладываем на видео звуковую дорожку
        my_clip = mpe.VideoFileClip(videopath + str(callback.message.chat.id) + '.avi')
        my_clip.write_videofile(videopath + str(callback.message.chat.id) + '.mp4', audio=audiopath + callback.data+'.mp3')

        # Отправим видео пользователю
        bot.send_video(callback.message.chat.id, data=open(videopath + str(callback.message.chat.id) + '.mp4', 'rb'), timeout=10000,
                       supports_streaming=True)

        # Удалим файлы после использования
        for file in glob.glob(picpath + str(callback.message.chat.id) + '_*.jpg'):
            os.remove(file)
        for file in glob.glob(videopath + str(callback.message.chat.id) + '*'):
            os.remove(file)
        bot.send_message(708061023, 'Кто-то сделал видео')
        bot.send_message(callback.message.chat.id, 'Готово! Чтобы сделать еще один ролик нажмите "Получить фото"', reply_markup=keyboard1)


bot.polling(none_stop=True)