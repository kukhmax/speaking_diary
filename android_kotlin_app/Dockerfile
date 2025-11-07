FROM gradle:8.4-jdk17

USER root

# Установим инструменты и Android SDK (cmdline-tools)
RUN apt-get update && apt-get install -y wget unzip && rm -rf /var/lib/apt/lists/*

ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV ANDROID_HOME=/opt/android-sdk
RUN mkdir -p $ANDROID_SDK_ROOT/cmdline-tools

# Загрузка и установка commandline tools
RUN wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O /tmp/cmdline-tools.zip && \
    unzip -q /tmp/cmdline-tools.zip -d /tmp/cmdline-tools && \
    mv /tmp/cmdline-tools/cmdline-tools $ANDROID_SDK_ROOT/cmdline-tools/latest && \
    rm -rf /tmp/cmdline-tools.zip /tmp/cmdline-tools

ENV PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools

# Принятие лицензий и установка нужных пакетов SDK
RUN yes | sdkmanager --licenses && \
    sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"

WORKDIR /workspace

# Копируем проект внутрь контейнера (для полноценной сборки на этапе build)
COPY . /workspace

# Выполняем сборку debug APK; без демона, чтобы не висеть
RUN gradle --no-daemon assembleDebug || (cat /root/.gradle/daemon/*/daemon.log || true)

# По умолчанию ничего не запускаем, контейнер используется для сборки
CMD ["bash", "-lc", "cp app/build/outputs/apk/debug/app-debug.apk /workspace/app-debug.apk && echo 'APK скопирован: /workspace/app-debug.apk' && ls -lah /workspace/app-debug.apk"]