buildscript {
    dependencies {
        // AGP 9 has built-in Kotlin with an older Kotlin Gradle plugin at runtime.
        // This line moves it to the Kotlin version in the catalog
        // (https://developer.android.com/build/releases/agp-9-0-0-release-notes).
        classpath(libs.kotlin.gradle.plugin)
    }
}

plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.compose) apply false
    alias(libs.plugins.kotlin.serialization) apply false
}
