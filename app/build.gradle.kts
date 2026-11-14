plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
}

// The content base the app loads the feed and explainers from.
// Override it for local testing: ./gradlew installDebug -Ppaperboy.contentBase=http://localhost:8765/
val contentBase: String = providers.gradleProperty("paperboy.contentBase")
    .getOrElse("https://paperboy.ntrpydev.workers.dev")

// Release signing comes from these environment variables, never from files in the repo.
// The release workflow sets them from repository secrets. Debug builds need none of them.
val releaseSigningVariables = listOf(
    "PAPERBOY_KEYSTORE_FILE",
    "PAPERBOY_KEYSTORE_PASSWORD",
    "PAPERBOY_KEY_ALIAS",
    "PAPERBOY_KEY_PASSWORD",
)
val releaseSigning: Map<String, String> = releaseSigningVariables
    .mapNotNull { name -> providers.environmentVariable(name).orNull?.takeIf { it.isNotEmpty() }?.let { name to it } }
    .toMap()
val missingReleaseSigning: List<String> = releaseSigningVariables.filterNot { it in releaseSigning }

android {
    namespace = "io.github.ntrpydev.paperboy"
    compileSdk = 37

    defaultConfig {
        applicationId = "io.github.ntrpydev.paperboy"
        minSdk = 26
        targetSdk = 36
        versionCode = 2
        versionName = "0.1.1"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField("String", "CONTENT_BASE", "\"$contentBase\"")
    }

    signingConfigs {
        if (missingReleaseSigning.isEmpty()) {
            create("release") {
                storeFile = file(releaseSigning.getValue("PAPERBOY_KEYSTORE_FILE"))
                storePassword = releaseSigning.getValue("PAPERBOY_KEYSTORE_PASSWORD")
                keyAlias = releaseSigning.getValue("PAPERBOY_KEY_ALIAS")
                keyPassword = releaseSigning.getValue("PAPERBOY_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
            signingConfig = signingConfigs.findByName("release")
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
    // fake servers in both test suites serve. The unit tests also read the repo's schemas,
    // so the app's field list is checked against schema/feed-item.schema.json.
    sourceSets {
        named("test") {
            resources.directories += "src/fixtures"
            resources.directories += "../schema"
        }
        named("androidTest") { assets.directories += "src/fixtures" }
    }
}

// Packaging a release fails here, with the names of the missing variables, instead of
// writing an unsigned APK. Compiling and testing the release variant still work without them.
val checkReleaseSigning = tasks.register("checkReleaseSigning") {
    val missing = missingReleaseSigning
    doLast {
        if (missing.isNotEmpty()) {
            throw GradleException(
                "Release signing is not configured. Set these environment variables: " +
                    missing.joinToString(", ") +
                    ". PAPERBOY_KEYSTORE_FILE is the path to the PKCS12 release keystore. " +
                    "Debug builds (assembleDebug) need none of them.",
            )
        }
    }
}
tasks.matching { it.name == "packageRelease" || it.name == "signReleaseBundle" }.configureEach {
    dependsOn(checkReleaseSigning)
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
