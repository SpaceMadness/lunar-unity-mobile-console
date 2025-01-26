import org.apache.tools.ant.taskdefs.condition.Os

plugins {
    alias(libs.plugins.android.library)
    alias(libs.plugins.kotlin.android)
}

android {
    namespace = "spacemadness.com.lunarconsole"
    compileSdk = 35

    defaultConfig {
        minSdk = 24

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        consumerProguardFiles("consumer-rules.pro")
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    flavorDimensions += listOf("version")
    productFlavors {
        create("full") {
            dimension = "version"
        }
        create("free") {
            dimension = "version"
        }
    }

    configurations {
        create("fullDebug")
        create("fullRelease")
        create("freeDebug")
        create("freeRelease")
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = "11"
    }
}

dependencies {
    implementation(libs.appcompat)
    implementation(libs.material)
    implementation(libs.core.ktx)
    compileOnly(files(getUnityDependencyJar()))
    testImplementation(libs.junit)
    androidTestImplementation(libs.ext.junit)
    androidTestImplementation(libs.espresso.core)
}

private fun getUnityDependencyJar(): String {
    return if (Os.isFamily(Os.FAMILY_WINDOWS)) {
        "C:/Program Files/Unity-Export/Editor/Data/PlaybackEngines/AndroidPlayer/Variations/mono/Release/Classes/classes.jar"
    } else {
        "/Applications/Unity-Export/PlaybackEngines/AndroidPlayer/Variations/mono/Release/Classes/classes.jar"
    }
}
