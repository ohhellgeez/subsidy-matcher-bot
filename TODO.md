# Что осталось доделать (по ролям)

Проект «Навигатор по мерам поддержки» (subsidy-matcher-bot). Разбивка по ролям — из `README.md`.

## Общий статус

| Роль | Название | Статус |
| --- | --- | --- |
| 1 | Core API & DevOps | ✅ готово |
| 2 | DB Architect | ✅ готово (миграция и seed починены) |
| 3 | Rule Engine (скоринг) | ❌ не реализовано |
| 4 | Bot Flow & FSM | ❌ не реализовано |

Сейчас бот стартует и отвечает заглушкой: «Начать подбор» → «Вопрос 1/4» с
захардкоженными кнопками «Регион А / Регион Б». Реального подбора мер нет.

---

## Роль 1 — Core API & DevOps

Статус: **готово**.

Уже сделано:
- `src/max_client/client.py` — `MaxClient`: `send_message` / `send_text` /
  `send_keyboard`, `edit_message`, `get_updates` (long polling),
  `subscribe_webhook` / `get_subscriptions` / `unsubscribe_webhook`,
  `answer_callback`; троттлинг ~2 сообщения/сек.
- `src/max_client/models.py` — `Update` / `Message` / `MessageBody` / `User` /
  `Callback` / `Button`, `inline_keyboard`; `Update.user_id` и `Update.text`
  корректно разбирают `message_callback`.
- `src/max_client/errors.py` — `MaxError`, `MaxConnectionError`, `MaxAPIError`,
  `MaxAuthError`, `MaxRateLimitError`.
- `src/config.py` — `Settings` из `.env` (`MAX_*`, `BOT_MODE`, `POLLING_*`,
  `WEBHOOK_*`, `POSTGRES_*`, `REDIS_*`), `postgres_dsn` / `redis_url`, `validate()`.
- `src/main.py` — точки входа polling / webhook.
- `src/webhook.py` — FastAPI-сервер, `/health`, проверка секрета.
- `Dockerfile`, `compose.yaml`, `certs/` (сертификаты Минцифры), `.env.example`, `README.md`.

Осталось (мелочи, опционально):
- В `src/handlers.py` обрабатываются только 3 события: `bot_started`,
  `message_created`, `message_callback`. Остальные (`message_edited/removed`,
  `comment_*`, `user_added/removed` и т.д.) игнорируются — для MVP ок.
- Webhook проверяется только секретом в заголовке `X-Max-Bot-Api-Secret`;
  если платформа поддерживает подпись тела — добавить её проверку.
- Graceful shutdown (корректно отписаться от webhook при остановке).

---

## Роль 2 — DB Architect

Статус: **готово** (недавно починено).

Уже сделано:
- `database/models.py` — 5 моделей: `SupportMeasure`, `MeasureRequirement`,
  `Document`, `Region`, `Company` (с CHECK / UNIQUE / FK и комментариями к колонкам).
- `migrations/versions/d44029bc4885_init_database_schema.py` — миграция
  переписана: теперь создаёт все таблицы (раньше содержала только `alter_column`
  и падала с `relation "companies" does not exist`).
- `migrations/env.py` — DSN берётся из `POSTGRES_*` env (не хардкод).
- `database/seed.py` — наполнение из JSON-фикстур (регионы, компании, меры,
  требования, документы); идемпотентно; DSN из env.
- `database/data/*.json` — фикстуры.
- `database/max_database.sql`, `database/erd.png`, `database/erd_uml.pml`.

Осталось (опционально / на будущее):
- Нет `database/__init__.py` (работает как namespace package, но явный пакет
  надёжнее — например для `python -m database.seed`).
- В `alembic.ini` осталась строка `sqlalchemy.url = ...` — она теперь
  перекрывается `env.py`, можно зачистить / закомментировать.
- Нет слоя доступа к данным (репозитория): бот пока вообще не читает БД.
  Для роли 3 понадобятся функции вида `find_active_measures(...)`,
  `get_regions()`, `get_company_by_inn(...)`.
- (Необязательно) добавить `naming_convention` в `Base.metadata` для единообразия
  имён ограничений.

---

## Роль 3 — Rule Engine (скоринг / подбор мер)

Статус: **не реализовано**. Пустая папка `src/services/` заготовлена под это.

Задача: по профилю пользователя отобрать и отранжировать подходящие меры поддержки.

Что нужно сделать:

1. Модуль, например `src/services/matcher.py` (или `scoring.py`):
   - вход — профиль пользователя (объект / словарь);
   - выход — список подходящих `SupportMeasure` + их `MeasureRequirement` и
     `Document` (ссылки на оформление), отсортированный по релевантности.

2. Правила соответствия (по полям `MeasureRequirement`):
   - регион/ОКАТО: `okato == '0'` → мера для всей РФ; иначе совпадение по ОКАТО региона;
   - `opf`: список допустимых ОПФ (`individual` / `legal` / `physical` / `self` /
     `selfindividual`) — профиль должен входить;
   - `okwed`: список допустимых ОКВЭД — ОКВЭД компании должен входить (уточнить: точное совпадение или по префиксу);
   - `not_okwed`: список недопустимых ОКВЭД — не должен входить;
   - `min_empl_amount` / `max_empl_amount`: число сотрудников в диапазоне (NULL = без ограничения);
   - `min_exist_term`: возраст бизнеса >= значения (NULL = без ограничения);
   - `ukep`: если `true` — проверить наличие УКЭП (данных пока нет — решить, откуда брать);
   - `scoring`: если `true` — пометить, что нужен скоринг.

3. Учитывать саму меру:
   - `active == 1`;
   - `start_date` / `end_date`: приём заявок открыт сейчас (или даты отсутствуют);
   - `support_count` / суммы — для вывода лимитов.

4. Скоринг / ранжирование: например, по числу совпавших критериев или по сумме
   поддержки; вернуть топ-N.

5. Покрыть тестами — фикстуры в `database/data/*.json` уже подходят как кейсы:
   - `meas-001` — ИТ-грант для `legal` / ОКВЭД `62.01`;
   - `meas-002` — субсидия для аграриев Алтайского края.

Формат результата (пример): текст с названием меры, суммой, условиями и
кнопками-ссылками на документы.

---

## Роль 4 — Bot Flow & FSM (анкета на Redis)

Статус: **не реализовано**. Пустая папка `src/handlers/` (пакет) заготовлена;
сейчас есть только файл `src/handlers.py` с заглушкой.

Задача: провести пользователя по анкете из 3–4 вопросов и показать результат.

Что нужно сделать:

1. Стейт-машина на Redis (`redis-py` уже в requirements, `settings.redis_url` есть):
   - ключ по `user_id` (например `fsm:{user_id}`);
   - шаги: `region → opf → okwed → employees → (exist_term)`;
   - сохранять выбранные ответы между сообщениями.

2. Заменить заглушку в `src/handlers.py`:
   - `_on_message` — в зависимости от текущего шага принимать текст (ОКВЭД, число сотрудников);
   - `_on_callback` — обрабатывать `payload` кнопок (`region=...`, `opf=...` и т.д.).

3. Вопросы и кнопки:
   - Регион — список из таблицы `regions` (или кнопка «пропустить»);
   - Форма бизнеса — кнопки (ИП / ООО / самозанятый / физлицо);
   - Отрасль — ввод ОКВЭД текстом (или подсказка);
   - Сотрудники — кнопки-диапазоны / число;
   - Возраст бизнеса — число (мес) или диапазон.

4. После последнего шага — вызвать движок роли 3 и вывести подборку:
   - карточка меры (название, сумма, условия);
   - кнопки-ссылки на документы;
   - кнопки «Начать заново» / «Назад».

5. Обработка краевых случаев: пользователь пишет «стоп» / «отмена», невалидный
   ввод (не число), отсутствие подходящих мер («ничего не найдено»).

6. TTL состояния в Redis (например 30 минут) и очистка.

---

## Рекомендуемый порядок работ

1. Роль 4: модуль хранения FSM в Redis + вопросы (задать контракт с ролью 3).
2. Роль 3: движок подбора (можно параллельно — вход/выход это контракт).
3. Соединить в `src/handlers.py`: анкета → matcher → вывод.
4. Мелочи ролей 1–2 — по желанию.

## Контракт между ролями 3 и 4 (предложение)

```python
# src/services/matcher.py
@dataclass
class UserProfile:
    region_okato: str
    opf: str
    okwed: str
    employees_count: int
    exist_term_months: int
    ukep: bool = False

def match(profile: UserProfile) -> list[MatchResult]: ...
```

`MatchResult` — мера + её требования + документы + итоговый скоринг-балл.

