import json
import logging
import os
import time
import re
from jsonschema import validate, ValidationError
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer, util

from bot.devices.service import DeviceService
from bot.users.service import UserService
from bot.config import settings


# Устанавливаем переменные окружения для GROQ API
os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Настройка логирования
logger = logging.getLogger("smart_home_bot")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Инициализация LLM моделей (GROQ)
llm_reasoning = ChatGroq(model="llama3-70b-8192", temperature=0)

# Инициализация модели для векторизации (RAG)
embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")


# Функции для работы с LLM (GROQ) и RAG
def invoke_with_retry(
        llm, prompt, chain_name, question_id, attempt_label, max_attempts=3, initial_delay=5
):
    """
    Вызывает LLM с повторными попытками в случае ошибки (например, 429).
    """
    attempt = 0
    delay = initial_delay
    while attempt < max_attempts:
        try:
            result = llm.invoke(prompt).content.strip()
            return result
        except Exception as e:
            if "429" in str(e):
                logger.info(
                    f"Chain {chain_name} для вопроса {question_id}, {attempt_label} - получена ошибка 429. Повтор через {delay} секунд..."
                )
                time.sleep(delay)
                delay *= 2
                attempt += 1
            else:
                logger.error(
                    f"Chain {chain_name} для вопроса {question_id}, {attempt_label} - ошибка: {e}"
                )
                break
    logger.error(
        f"Chain {chain_name} для вопроса {question_id}, {attempt_label} - превышено число попыток. Возвращаем пустой ответ."
    )
    return ""


def llm_pipeline(prompt, max_new_tokens=100):
    """
    Обертка для вызова LLM с использованием invoke_with_retry.
    Возвращает список словарей с ключом 'generated_text'.
    """
    response = invoke_with_retry(
        llm_reasoning,
        prompt,
        "LLM Pipeline",
        "N/A",
        "attempt 1",
        max_attempts=3,
        initial_delay=5,
    )
    return [{"generated_text": response}]


def choose_action(text):
    """
    Определяет тип действия по введенной команде:
    - 'create'  - создать новое устройство
    - 'update'  - изменить состояние существующего устройства
    - 'chat'    - обычное общение
    """
    text_lower = text.lower()
    if any(
            keyword in text_lower for keyword in
            ["добавь", "создай", "новое устройство", "зарегистрируй", "подключи", "добавление"]
    ):
        return "create"

    elif any(
            keyword in text_lower for keyword in
            ["удали", "исключи", "убери", "стереть", "очисти", "деактивируй", "разорви связь"]
    ):
        return "delete"

    elif any(
            keyword in text_lower for keyword in [
                "включи", "выключи", "поставь", "измени", "смени", "установи", "поменяй",
                "увеличь", "уменьш", "сделай", "подними", "опусти", "открой", "закрой",
                "запусти", "останови", "перезапусти", "прекрати", "переключи", "настрой",
                "задай", "запрограммируй"
            ]
    ):
        return "update"

    else:
        return "chat"

def extract_command_from_text(text, devices):
    """
    Извлекает команду для изменения устройства.
    Использует LLM для разбора команды и возвращает JSON:
    {"device": "название устройства", "command": "изменение параметра", "value": "значение"}
    """
    prompt = f"""
Ты помощник по умному дому. Разбери команду пользователя.
- Определи устройство и параметры.
- Если подходящих устройств несколько, уточни у пользователя, какое именно.
- Если устройство отсутствует, сообщи об этом.
- Отвечай в JSON-формате:
  {{"device": "название устройства", "command": "изменение параметра", "value": "значение"}}

Используй следующий список доступных девайсов для поиска схожего устройства:
{devices}

Примеры:
- "Включи люстру в кухне" → {{"device": "Люстра Кухня", "command": "condition", "value": "ON"}}
- "Кондиционер в кухне поставь 20 градусов" → {{"device": "Кондиционер Кухня", "command": "temperature", "value": "20"}}
- "Телевизор" (если есть "Телевизор А" и "Телевизор Б") → {{"error": "Уточните, какой именно девайс: Телевизор А, Телевизор Б"}}
- "Включи кристалл" (если такого устройства нет) → {{"error": "Устройство 'Кристалл' не найдено"}}

Никакого текста, только JSON
Команда: {text}
    """
    response = llm_pipeline(prompt, max_new_tokens=100)[0]["generated_text"]
    print(f'{response}')
    try:
        command = json.loads(response)
        return command
    except json.JSONDecodeError:
        logger.error("LLM не смог корректно распарсить JSON из команды.")
        return None


def extract_creation_command_from_text(text, devices):
    prompt = f"""
    Ты помощник по умному дому. Твоя задача – разобрать команду пользователя для добавления нового устройства и вернуть исключительно валидный JSON-объект без каких-либо дополнительных символов или текста.

    Структура JSON должна быть следующей:
    {{
        "name": "название устройства (строка)",
        "device_id": "id схожего устройства из списка (строка)",
        "params": {{
            "ключ": "значение", ...
        }}
    }}

    Используй следующий список доступных девайсов для поиска схожего устройства:
    {devices}

    Порядок действий:
    1. Определи тип нового устройства и его параметры на основе команды.
    2. Найди наиболее схожее устройство из списка, чтобы взять его id в качестве "device_id".
    3. Сформируй JSON согласно приведённой выше схеме.

    Примеры:
    - Для команды "Добавь чайник на кухню" ожидаемый ответ:
    {{"name": "Чайник Кухня", "device_id": "8", "params": {{"temperature": "100", "work_time": "2", "condition": "OFF"}}}}
    - Для команды "Добавь телевизор в гостиную с громкостью 70" ожидаемый ответ:
    {{"name": "Телевизор Гостиная", "device_id": "4", "params": {{"channel": "1", "volume": "70", "condition": "OFF"}}}}

    Команда: {text}
    """

    response = llm_pipeline(prompt, max_new_tokens=150)[0]["generated_text"]
    try:
        command = json.loads(response)
        return command
    except json.JSONDecodeError:
        logger.error("LLM не смог корректно распарсить JSON для создания устройства.")
        return None


def extract_delete_from_text(text, devices):
    """
    Извлекает команду для изменения устройства.
    Использует LLM для разбора команды и возвращает JSON:
    {"device": "название устройства", "command": "изменение параметра", "value": "значение"}
    """
    prompt = f"""
Ты помощник по умному дому. Найди устройство которое нужно удалить
- Определи устройство и его id
- Если подходящих устройств несколько, уточни у пользователя, какое именно.
- Отвечай в JSON-формате:
  {{"device": "название устройства", "id": "id"}}

Используй следующий список доступных девайсов для поиска схожего устройства:
{devices}

Примеры:
- "Удали люстру в кухне" → {{"device": "Люстра Кухня", "id": "2"}}
- "Удали Кондиционер → {{"device": "Кондиционер", "id": "8"}}

Команда: {text}
    """
    response = llm_pipeline(prompt, max_new_tokens=100)[0]["generated_text"]
    print(response)
    try:
        delete = json.loads(response)
        return delete
    except json.JSONDecodeError:
        logger.error("LLM не смог корректно распарсить JSON из команды.")
        return None


def get_relevant_device(query, devices):
    """
    Находит наиболее релевантное устройство из списка devices на основе запроса.
    Использует SentenceTransformer для вычисления косинусного сходства.
    """
    device_descriptions = []
    for device in devices:
        params = device.get("params", {})
        params_str = " ".join([f"{k}:{v}" for k, v in params.items()])
        description = f"{device.get('type', '')} {params_str}"
        device_descriptions.append(description)
    query_embedding = embedding_model.encode(query, convert_to_tensor=True)
    device_embeddings = embedding_model.encode(
        device_descriptions, convert_to_tensor=True
    )
    cosine_scores = util.cos_sim(query_embedding, device_embeddings)[0]
    best_idx = int(cosine_scores.argmax())
    best_device = devices[best_idx]
    logger.info(
        f"Найдено устройство: {best_device.get('type')} с описанием: {device_descriptions[best_idx]}"
    )
    return best_device


command_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "device": {"type": "string"},
            "command": {"type": "string"},
            "value": {"type": "string"}
        },
        "required": ["device", "command", "value"],
        "additionalProperties": False
    }
}


def extract_group_commands_from_text(text, devices):
    """
    Используя LLM, разбирает команду пользователя, которая может содержать инструкции для нескольких устройств.
    Ожидаемый формат ответа – список JSON-объектов вида:
    [{"device": "название устройства", "command": "имя команды", "value": "значение"}, ...]
    """
    prompt = f"""
    Ты — JSON API умного дома. Разбери команду пользователя, которая может содержать инструкции для нескольких устройств.

    📌 Правила:
    - Ты обязан вернуть **ТОЛЬКО** JSON — без текста, комментариев или пояснений.
    - JSON должен быть **валидным списком объектов**.
    - Каждый объект описывает одно действие с устройством.

    ❌ Запрещено:
    - Писать текст до или после JSON (например: "Вот результат:", "Команды:")
    - Добавлять комментарии или markdown
    - Делать объяснения

    ✅ Формат ответа (ТОЛЬКО ЭТО):
    [
    {{"device": "название устройства", "command": "имя команды", "value": "значение"}},
    ...
    ]

    📎 Пример 1:
    Команда: "выключи свет на кухне, выключи свет в гостиной"
    Ответ:
    [
    {{"device": "свет на кухне", "command": "condition", "value": "OFF"}},
    {{"device": "свет в гостиной", "command": "condition", "value": "OFF"}}
    ]

    📎 Пример 2:
    Команда: "выключи свет во всех комнатах"
    Ответ:
    [
    {{"device": "свет в спальне", "command": "condition", "value": "OFF"}},
    {{"device": "свет в гостиной", "command": "condition", "value": "OFF"}},
    {{"device": "свет на кухне", "command": "condition", "value": "OFF"}}
    ]

    Доступные устройства: {devices}
    Команда: {text}
    """
    response = llm_pipeline(prompt, max_new_tokens=200)[0]["generated_text"]
    print("Raw LLM response:\n", response)

    # Извлекаем JSON-массив между первым '[' и последним ']'
    start_index = response.find('[')
    end_index = response.rfind(']')
    if start_index == -1 or end_index == -1 or end_index <= start_index:
        logger.error("JSON массив не найден в ответе.")
        return None

    json_substring = response[start_index:end_index + 1]

    # Дополнительная проверка: нет ли лишнего текста вне JSON
    before = response[:start_index].strip()
    after = response[end_index + 1:].strip()
    if before or after:
        logger.warning("Обнаружен лишний текст вне JSON массива. Будет использован только извлеченный JSON.")

    try:
        commands = json.loads(json_substring)
    except json.JSONDecodeError as e:
        logger.error("Ошибка декодирования JSON: " + str(e))
        return None

    # Валидация структуры через jsonschema
    try:
        validate(instance=commands, schema=command_schema)
    except ValidationError as ve:
        logger.error("Полученный JSON не соответствует схеме: " + str(ve))
        return None

    return commands


async def process_device_update(text, devices):
    """
    Обрабатывает команду изменения состояния устройства.
    1. Если команда содержит несколько инструкций (например, разделитель ',' или 'и'),
       используем LLM для разбора группы команд.
    2. Иначе – разбираем команду как единичную.
    3. Для каждой инструкции находим наиболее релевантное устройство и обновляем соответствующий параметр.
    """
    # Если в команде присутствуют разделители, предполагаем, что это группа команд
    if ("," in text) or (" и " in text) or ("все" in text) or ("кажд" in text) or ("везде" in text):
        group_commands = extract_group_commands_from_text(text, devices)
        if not group_commands:
            return "Команда не распознана или устройство не найдено\nУточните девайс"
        messages = []
        for command in group_commands:
            if "error" in command:
                messages.append(command["error"])
                continue
            target_device = get_relevant_device(command.get("device", ""), devices)
            if not target_device:
                messages.append("Устройство не найдено: " + command.get("device", ""))
                continue
            param = command.get("command")
            value = command.get("value")
            if param and value is not None:
                target_device["params"][param] = value
                await DeviceService.update_device_state(
                    target_device["id"], target_device["params"]
                )
                logger.info(
                    f"Устройство {target_device.get('type')} обновлено: {param} = {value}"
                )
                messages.append(
                    f"Устройство {target_device.get('type')} обновлено: {param} = {value}"
                )
            else:
                messages.append(
                    "Некорректная команда для обновления устройства: " + str(command)
                )
        return "\n".join(messages)
    else:
        command = extract_command_from_text(text, devices)
        if not command:
            return "Команда не распознана или устройство не найдено\nУточните девайс"
        if "error" in command:
            return command["error"]
        target_device = get_relevant_device(command.get("device", ""), devices)
        if not target_device:
            return "Устройство не найдено."
        param = command.get("command")
        value = command.get("value")
        if param and value is not None:
            target_device["params"][param] = value
            await DeviceService.update_device_state(
                target_device["id"], target_device["params"]
            )
            logger.info(
                f"Устройство {target_device.get('type')} обновлено: {param} = {value}"
            )
            return (
                f"Устройство {target_device.get('type')} обновлено: {param} = {value}"
            )
        else:
            return "Некорректная команда для обновления устройства."


async def process_device_creation(text, devices, user_id):
    """
    Обрабатывает команду создания нового устройства.
    1. Извлекает команду с параметрами нового устройства.
    2. Находит наиболее схожее устройство из локального списка для присвоения device_id.
    3. Добавляет устройство в список DEVICES.
    """
    command = extract_creation_command_from_text(text, devices)
    if not command:
        return "Команда для создания устройства не распознана."

    # Находим схожее устройство по имени из команды
    similar_device = get_relevant_device(command.get("name", ""), devices)
    if not similar_device:
        return "Не удалось определить схожее устройство для создания."

    # Формируем новое устройство с обязательным полем device_id
    new_device = {
        "type": command.get("name"),
        "device_id": similar_device.get("id"),  # обязательное поле device_id
        "params": command.get("params", {}),
    }

    user = await UserService.get_user_by_tg_id(user_id)

    await DeviceService.add_llm_user_device(user.id, new_device)

    logger.info(
        f"Добавлено новое устройство: {new_device.get('type')} с device_id: {new_device.get('device_id')}"
    )
    return f"Добавлено новое устройство: {new_device.get('type')}"


async def process_device_delete(text, devices):
    """
    Обрабатывает команду изменения состояния устройства.
    1. Извлекает команду (device, command, value) с помощью LLM.
    2. Находит наиболее релевантное устройство из списка.
    3. Обновляет соответствующий параметр в устройстве.
    """
    delete = extract_delete_from_text(text, devices)
    if not delete:
        return "Команда не распознана или устройство не найдено\nУточните девайс"
    # Ищем устройство среди локальных данных
    await DeviceService.remove_user_device(int(delete["id"]))

    logger.info(f"Устройство {delete['device']} удалено")
    return f"Устройство {delete['device']} удалено"


def chat_with_bot(text):
    """
    Обрабатывает обычное общение с ботом: одноразовый ответ, без диалога и уточняющих вопросов.
    """
    prompt = f"""
Ты помощник по умному дому. Отвечай на сообщения пользователя одноразово, без продолжения диалога.
Никогда не задавай вопросов, не предлагай помощь, не проси уточнений.
Просто дай краткий, понятный и завершённый ответ по существу.

Сообщение пользователя: {text}
    """
    response = invoke_with_retry(
        llm_reasoning,
        prompt,
        "Chat",
        "N/A",
        "attempt 1",
        max_attempts=3,
        initial_delay=5,
    )
    return response


# Основная функция обработки пользовательского ввода
async def process_user_input(text, user_id):
    action = choose_action(text)
    logger.info(f"Определено действие: {action}")

    if action == "update":
        user_devices_info = await DeviceService.get_user_devices_info(user_id)
        result = await process_device_update(text, user_devices_info)
    elif action == "create":
        new_devices = await DeviceService.get_all_devices_info()
        result = await process_device_creation(text, new_devices, user_id)
    elif action == "delete":
        user_devices_info = await DeviceService.get_user_devices_info(user_id)
        result = await process_device_delete(text, user_devices_info)
    else:
        result = chat_with_bot(text)

    return result
