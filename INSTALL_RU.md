# Как открыть, собрать и установить Suveren Files на Android

Коротко: проще всего открыть проект в Android Studio, нажать **Run**, выбрать телефон — Android Studio сама соберёт APK и установит приложение. Если нужен APK-файл для ручной установки, собери `app-debug.apk` или подписанный `release.apk` по шагам ниже.

## 0. Что нужно

- Компьютер: Windows, macOS или Linux.
- Android Studio: актуальная стабильная версия с Android SDK.
- Телефон: Android 6.0+.
- USB-кабель, если ставишь напрямую на свой телефон.
- Интернет при первой сборке: Gradle скачает Android Gradle Plugin и SDK-компоненты.

Версии проекта:

- `applicationId`: `dev.suveren.files`;
- `minSdk`: 23 / Android 6.0;
- `targetSdk`: 36;
- Android Gradle Plugin: `8.13.2`;
- рекомендуемый JDK: 17+.

## 1. Открыть проект в Android Studio

1. Установи Android Studio с официального сайта: <https://developer.android.com/studio>.
2. Запусти Android Studio.
3. Нажми **Open**.
4. Выбери папку проекта `Suverenfiles`, не папку `app` внутри неё.
5. Дождись окончания **Gradle Sync**.
6. Если Android Studio предложит установить SDK / Build Tools / Platform API 36 — соглашайся.

Если Gradle Sync упал из-за сети — это не ошибка кода. Нужен доступ к `google()` и `mavenCentral()`, потому что Android Gradle Plugin скачивается из репозиториев.

## 2. Установить сразу на телефон через Android Studio

Это самый надёжный вариант для разработки.

1. На телефоне включи режим разработчика:
   - **Настройки → О телефоне → Номер сборки**;
   - нажми 7 раз.
2. Включи USB debugging:
   - **Настройки → Для разработчиков → Отладка по USB**.
3. Подключи телефон к компьютеру.
4. На телефоне подтверди RSA-ключ отладки.
5. В Android Studio выбери устройство сверху в панели Run.
6. Нажми зелёную кнопку **Run ▶**.

Android Studio соберёт и установит debug-версию приложения сама.

## 3. Собрать APK-файл вручную

В Android Studio открой терминал в корне проекта и выполни:

```bash
./gradlew assembleDebug
```

На Windows PowerShell:

```powershell
.\gradlew.bat assembleDebug
```

Готовый debug APK будет здесь:

```text
app/build/outputs/apk/debug/app-debug.apk
```

Важно: debug APK предназначен для личной установки и тестов. Для публикации или постоянной раздачи лучше делать release APK с собственной подписью.

## 4. Установить APK на телефон

### Вариант A — через ADB

Проверь, что телефон виден:

```bash
adb devices
```

Установи APK:

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Что делает команда:

- `adb install` ставит APK на подключённое устройство;
- `-r` обновляет приложение поверх предыдущей версии без удаления данных.

Если Android ругается на debug/test-only APK, используй:

```bash
adb install -r -t app/build/outputs/apk/debug/app-debug.apk
```

### Вариант B — руками с телефона

1. Скопируй `app-debug.apk` на телефон, например в `Download`.
2. Открой APK через системный файловый менеджер.
3. Разреши установку из этого источника, если Android спросит.
4. Нажми **Install**.

На части устройств debug APK может ставиться только через Android Studio/ADB. Если нужна установка двойным тапом без сюрпризов — собери подписанный release APK.

## 5. Собрать подписанный release APK

В Android Studio:

1. **Build → Generate Signed App Bundle / APK**.
2. Выбери **APK**.
3. Создай новый keystore и сохрани его вне репозитория.
4. Выбери build variant `release`.
5. Нажми **Finish**.

Не клади keystore и пароли в git. Это ключ владения приложением: потеряешь ключ — нормальные обновления этого APK станут проблемой.

## 6. Первый запуск приложения

На Android 11+ приложение попросит системный режим **Доступ ко всем файлам**:

1. Нажми **Открыть настройки** в диалоге приложения.
2. Включи разрешение для **Suveren Files**.
3. Вернись назад в приложение.

Почему так: обычные разрешения `READ_MEDIA_*` не дают полноценный файловый менеджер. Для свободного просмотра папок нужен `MANAGE_EXTERNAL_STORAGE`. Для личного APK это нормально; для Google Play это отдельная политика и почти всегда дополнительная модерация.

## 7. Если что-то не работает

### `Plugin com.android.application ... was not found`

Причина: Gradle не смог скачать Android Gradle Plugin.

Проверь:

- интернет доступен;
- корпоративный VPN/proxy не блокирует `google()` / `mavenCentral()`;
- Android Studio открыта именно в корне `Suverenfiles`;
- в Android Studio установлен Android SDK Platform API 36.

### Телефон не виден в Android Studio

Проверь:

```bash
adb devices
```

Если статус `unauthorized` — разблокируй телефон и подтверди RSA-ключ. Если устройства нет — поменяй USB-режим на **File transfer / MTP** или кабель.

### Установилось, но файлы не видны

На Android 11+ проверь системное разрешение:

```text
Настройки → Приложения → Suveren Files → Специальный доступ → Доступ ко всем файлам
```

Название пункта отличается у Samsung/Xiaomi/Pixel, но смысл тот же: приложению нужен full file access.
