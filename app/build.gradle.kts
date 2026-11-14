plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
}

// The content base the app loads the feed and explainers from.
// Override it for local testing: ./gradlew installDebug -Ppaperboy.contentBase=http://localhost:8765/
val contentBase: String = providers.gradleProperty("paperboy.contentBase")
    .getOrElse("https://paperboy.ntrpydev.workers.dev")

// The package name, shared by both flavors. The worker's PLAY_PACKAGE_NAME must match it.
val appId = "io.github.ntrpydev.paperboy"

// The paid build's subscription in Play Console (see productFlavors below).
val subscriptionProductId: String = providers.gradleProperty("paperboy.productId")
    .getOrElse("placeholder.subscription")
val subscriptionBasePlanId: String = providers.gradleProperty("paperboy.basePlanId")
    .getOrElse("placeholder-monthly")

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
        applicationId = appId
        minSdk = 26
        targetSdk = 36
        versionCode = 2
        versionName = "0.1.1"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField("String", "CONTENT_BASE", "\"$contentBase\"")
    }

    // Two builds from one codebase, chosen at build time (README "Two builds"):
    //   free: today's app. Reads the open feed, gets updates from GitHub releases.
    //   paid: the Google Play app. Play Billing, the entitlement call, the pass on content
    //         requests, and the Play Store listing for updates. Only this flavor depends on the
    //         Play Billing Library and asks for the billing permission (src/paid/AndroidManifest.xml).
    // Both keep the same application id, so a Play install can replace a GitHub one when both
    // are signed with the same key (.private/research/play-store.md section 9).
    flavorDimensions += "edition"
    productFlavors {
        create("free") {
            dimension = "edition"
            buildConfigField("boolean", "PAID", "false")
            buildConfigField("String", "UPDATE_URL", "\"https://github.com/NtrpyDev/paperboy-app/releases\"")
        }
        create("paid") {
            dimension = "edition"
            buildConfigField("boolean", "PAID", "true")
            // The store listing link, https://play.google.com/store/apps/details?id=<package_name>
            // (https://developer.android.com/distribute/marketing-tools/linking-to-google-play).
            buildConfigField("String", "UPDATE_URL", "\"https://play.google.com/store/apps/details?id=$appId\"")
            // The subscription's product id and base plan id as created in Play Console. No store
            // listing exists yet, so both are placeholders until then: set them with
            // -Ppaperboy.productId=... -Ppaperboy.basePlanId=... or change the defaults here.
            buildConfigField("String", "SUBSCRIPTION_PRODUCT_ID", "\"$subscriptionProductId\"")
            buildConfigField("String", "SUBSCRIPTION_BASE_PLAN_ID", "\"$subscriptionBasePlanId\"")
        }
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
    // src/sharedTest holds FakeBillingGateway, used by the unit tests and the paid instrumented tests.
    sourceSets {
        named("test") {
            resources.directories += "src/fixtures"
            resources.directories += "../schema"
            kotlin.directories += "src/sharedTest/java"
        }
        named("androidTest") { assets.directories += "src/fixtures" }
        named("androidTestPaid") { kotlin.directories += "src/sharedTest/java" }
    }
}

// Packaging a release APK or signing a release bundle (either flavor) fails here, with the names
// of the missing variables, instead of writing an unsigned file. Compiling and testing the
// release variants still work without them.
val checkReleaseSigning = tasks.register("checkReleaseSigning") {
    val missing = missingReleaseSigning
    doLast {
        if (missing.isNotEmpty()) {
            throw GradleException(
                "Release signing is not configured. Set these environment variables: " +
                    missing.joinToString(", ") +
                    ". PAPERBOY_KEYSTORE_FILE is the path to the PKCS12 release keystore. " +
                    "Debug builds (assembleFreeDebug, assemblePaidDebug) need none of them.",
            )
        }
    }
}
val releasePackaging = Regex("package(Free|Paid)Release|sign(Free|Paid)ReleaseBundle")
tasks.matching { releasePackaging.matches(it.name) }.configureEach {
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
    "paidImplementation"(libs.billing)
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
