import speech_recognition as sr
import requests
from word2number import w2n
from deep_translator import GoogleTranslator

recognizer = sr.Recognizer()


def voice_input():
    with sr.Microphone() as source:
        print("Скажіть щось...")
        recognizer.adjust_for_ambient_noise(source)
        recognizer.pause_threshold = 1.5

        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="ru")
        print("Ви сказали:", text)
    except sr.UnknownValueError:
        print("Не вдалося розпізнати мову")
    except sr.RequestError:
        print("Не вдалося зв'язатися з сервісом розпізнавання мови")
    return text


text = voice_input()

sa = requests.get('http://127.0.0.1:8000/api/product/')

lst = sa.json()
l = [i.items() for i in lst]

# Текст для перевода
text_to_translate = text

# Перевод текста
translated = GoogleTranslator(source='ru', target='en').translate(text_to_translate)

names_product = [dict(i)['name'] for i in l]
l = dict(l)

products = {}
for (key_id, id_value), (key_name, name_value) in l.items():
    products[id_value] = name_value


data = []
words = translated.split()

for word in words:
    try:
        number = w2n.word_to_num(word)
        data.append(number)
    except ValueError:
        if word in names_product:
            data.append(word)

print(data)
value_to_find = data[1]

# Поиск ключа
found_key = next((key for key, value in products.items() if value == value_to_find), None)

url = 'http://127.0.0.1:8000/api/purchase/'

data = {
    "quantity": data[0],
    "user": 1,
    "product": found_key
}

headers = {
    'Content-Type': 'application/json'
}

response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    print('Успешный запрос!')