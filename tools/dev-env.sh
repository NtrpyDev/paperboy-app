# Source this file to get the Android build and emulator environment on the dev machine:
#   source tools/dev-env.sh
# Big caches live on the data drive when it exists, so the home drive stays small.
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk}"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
if [ -d /mnt/data/android ]; then
  export GRADLE_USER_HOME="${GRADLE_USER_HOME:-/mnt/data/android/gradle-home}"
  export ANDROID_AVD_HOME="${ANDROID_AVD_HOME:-/mnt/data/android/avd}"
fi
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools:$PATH"
