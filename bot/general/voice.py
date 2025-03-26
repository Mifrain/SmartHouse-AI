import os
import speech_recognition as sr
from aiogram import Router
from aiogram.types import Message, FSInputFile
from pydub import AudioSegment

from gtts import gTTS #text-to-speech

from bot.AI.llm import process_user_input
from bot.users.service import UserService

router = Router()

VOICE_DIR = "voice_messages"
os.makedirs(VOICE_DIR, exist_ok=True)

AUDIO_DIR = "generated_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)


@router.message(lambda message: message.voice)
async def handle_voice_message(message: Message):
    voice = message.voice
    file_info = await message.bot.get_file(voice.file_id)
    file_path = file_info.file_path
    local_filename = os.path.join(VOICE_DIR, f"{message.message_id}.ogg")

    # Скачиваем голосовое сообщение
    await message.bot.download_file(file_path, local_filename)

    # Конвертируем в WAV
    wav_filename = local_filename.replace(".ogg", ".wav")
    AudioSegment.from_file(local_filename).export(wav_filename, format="wav")

    wait_message = await message.answer("Обрабатываю ваш запрос")

    # Распознаем речь
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_filename) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="ru-RU")

            answer = await process_user_input(text, message.from_user.id)

            user = await UserService.get_user_by_tg_id(message.from_user.id)
            if user.voice_on:
                tts = gTTS(answer, lang="ru")

                audio_path = os.path.join(AUDIO_DIR, f"{message.message_id}.ogg")
                tts.save(audio_path)

                await message.answer_voice(FSInputFile(audio_path))

                os.remove(audio_path)
            else:
                await message.answer(answer)

            await wait_message.delete()
        except sr.UnknownValueError:
            await message.answer("Не удалось распознать речь.")
        except sr.RequestError:
            await message.answer("Ошибка сервиса распознавания речи.")

    os.remove(local_filename)
    os.remove(wav_filename)
