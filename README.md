# Suveren Files

Личный Android-файловый менеджер без рекламы, трекеров и внешних SDK.

## Возможности

- просмотр папок во внутреннем общем хранилище Android;
- открытие и шаринг файлов через безопасный `content://` provider;
- создание папок;
- копирование, перемещение, переименование и удаление файлов/папок;
- сортировка: сначала папки, потом файлы, внутри — по имени.

## Минимальные требования

- Android 6.0+ (`minSdk 23`);
- целевой SDK: Android API 36;
- Android Gradle Plugin `8.13.2`;
- Gradle `8.14.4+`;
- JDK 17+.

## Сборка

Открой проект в актуальной Android Studio или собери из CLI:

```bash
JAVA_HOME=/path/to/jdk-17 ./gradlew assembleDebug
```

Если wrapper ещё не создан локально:

```bash
gradle wrapper --gradle-version 8.14.4
./gradlew assembleDebug
```

## Важный Android gotcha

Для нормального файлового менеджера на Android 11+ нужен `MANAGE_EXTERNAL_STORAGE` — системный режим «Доступ ко всем файлам». Это удобно для личного APK, но Google Play жёстко ограничивает публикацию приложений с этим разрешением. Если цель — Play Store, следующий шаг лучше делать через Storage Access Framework (`ACTION_OPEN_DOCUMENT_TREE`) и работу с `DocumentsProvider`, но UX будет менее свободным.
