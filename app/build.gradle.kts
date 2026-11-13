plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
}

// The content base the app loads the feed and explainers from.
// Override it for local testing: ./gradlew installDebug -Ppaperboy.contentBase=http://localhost:8765/
val contentBase: String = providers.gradleProperty("paperboy.contentBase")
    .getOrElse("https://paperboy.ntrpydev.workers.dev")

android {
    namespace = "io.github.ntrpydev.paperboy"
    compileSdk = 37

    defaultConfig {
        applicationId = "io.github.ntrpydev.paperboy"
        minSdk = 24
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField("String", "CONTENT_BASE", "\"$contentBase\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    // src/fixtures is a small content base (head, chunks, one explainer) that the
    // fake servers in both test suites serve.
    sourceSets {
        named("test") { resources.directories += "src/fixtures" }
        named("androidTest") { assets.directories += "src/fixtures" }
    }
}

dependencies {
    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.compose.material3)
    implementation(libs.activity.compose)
    implementation(libs.lifecycle.viewmodel.compose)
    implementation(libs.lifecycle.runtime.compose)
    implementation(libs.navigation3.runtime)
    implementation(libs.navigation3.ui)
    implementation(libs.webkit)
    implementation(libs.okhttp)
    implementation(libs.serialization.json)
    implementation(libs.coroutines.android)
    implementation(libs.coil.compose)
    implementation(libs.coil.network.okhttp)
    debugImplementation(libs.compose.ui.tooling)

    testImplementation(libs.junit)
    testImplementation(libs.mockwebserver)
    testImplementation(libs.coroutines.test)

    androidTestImplementation(platform(libs.compose.bom))
    androidTestImplementation(libs.compose.ui.test.junit4)
    androidTestImplementation(libs.androidx.test.runner)
    androidTestImplementation(libs.androidx.test.ext.junit)
    androidTestImplementation(libs.espresso.core)
    androidTestImplementation(libs.mockwebserver)
    debugImplementation(libs.compose.ui.test.manifest)
}
