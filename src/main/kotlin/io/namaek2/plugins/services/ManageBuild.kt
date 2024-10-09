package io.namaek2.plugins.services

import com.intellij.openapi.progress.ProgressIndicator
import io.namaek2.plugins.toolWindow.MyConsoleLogger
import java.io.BufferedReader
import java.io.File
import java.io.IOException
import java.io.InputStreamReader
import java.io.FileInputStream
import java.util.*

class ManageBuild (private val javaFilesPath: String, private var outFolder : String, private val indicator: ProgressIndicator) {
    private fun isGradleProject() : Boolean {
        val gradleFiles = listOf(
            "build.gradle",
            "build.gradle.kts",
            "settings.gradle",
            "settings.gradle.kts",
            "gradlew",
            "gradlew.bat"
        )

        val isGradle = gradleFiles.any { fileName ->
            File(javaFilesPath, fileName).exists()
        }

        return isGradle
    }

    private fun findGradleVersion(projectDir: File): String? {
        // 방법 1: gradle.properties 파일에서 버전 확인
        val gradlePropertiesFile = File(projectDir, "gradle.properties")

        if (gradlePropertiesFile.exists()) {
            val properties = Properties()
            try {
                FileInputStream(gradlePropertiesFile).use {
                    Properties().load(it)
                    properties.getProperty("gradleVersion")?.let {
                        MyConsoleLogger.println("Gradle version: $it")
                        return it
                    }
                }
            } catch (e: IOException) {
                MyConsoleLogger.println("Error reading gradle.properties: ${e.message}")
                return null
            }

        }

        // 방법 2: gradle/wrapper/gradle-wrapper.properties 파일에서 버전 확인
        val wrapperPropertiesFile = File(projectDir, "gradle/wrapper/gradle-wrapper.properties")
        if (wrapperPropertiesFile.exists()) {
            val properties = Properties()
            try {
                FileInputStream(wrapperPropertiesFile).use {
                    properties.load(it)
                }
            } catch (e: IOException) {
                MyConsoleLogger.println("Error reading gradle-wrapper.properties: ${e.message}")
                return null
            }

            val distributionUrl = properties.getProperty("distributionUrl") ?: return null

            // URL에서 버전 추출 (예: gradle-7.4.2-bin.zip)
            val versionRegex = "gradle-([\\d.]+)".toRegex()
            val matchResult = versionRegex.find(distributionUrl)
            MyConsoleLogger.println("Gradle version: ${matchResult?.groupValues?.get(1)}")
            return matchResult?.groupValues?.get(1)
        }

        return null
    }

    fun runGradle(fractionValue : Double) {
        indicator.text = "Building with Gradle..."
        indicator.fraction = fractionValue

        isGradleProject().let {
            if(!it) {
                MyConsoleLogger.println("Not a gradle project")
                return
            }
        }

        findGradleVersion(File(javaFilesPath))?.let {
            MyConsoleLogger.println("Gradle version: $it")
            if (it < "8.0.0") {
                MyConsoleLogger.println("Gradle version is lower than 8.0")
                return
            }
        }

        try {
            // 프로세스 빌더를 생성합니다.
            val osName = System.getProperty("os.name").lowercase(Locale.getDefault())

            val processBuilder = when {
                "windows" in osName -> ProcessBuilder("gradle.bat", "jar")
                "linux" in osName-> ProcessBuilder("gradle", "jar")
                // "mac" in osName -> ProcessBuilder("./gradlew", "jar")
                else -> throw IllegalArgumentException("Unsupported OS: $osName")
            }

            processBuilder.directory(File(outFolder))

            // 프로세스의 출력을 캡처할 수 있도록 리디렉션합니다.
            processBuilder.redirectErrorStream(true)

            try {
                // 프로세스를 시작합니다.
                val process = processBuilder.start()
                MyConsoleLogger.println("jar build started")
                // 프로세스의 출력을 읽습니다.
                val reader = BufferedReader(InputStreamReader(process.inputStream))
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    MyConsoleLogger.println("gradle output: $line")
                }

                // 프로세스가 종료될 때까지 대기합니다.
                val exitCode = process.waitFor()
                if (exitCode == 0) {
                    MyConsoleLogger.println("jar builded successfully")
                } else {
                    MyConsoleLogger.println("Error in jar building : $exitCode")
                }
            } catch (e: InterruptedException) {
                MyConsoleLogger.println("Canceled by user")
            }
        } catch (e: IOException) {
            MyConsoleLogger.println("Error in jar building process: ${e.message}")
        }
        indicator.fraction = fractionValue + 0.1
    }
}