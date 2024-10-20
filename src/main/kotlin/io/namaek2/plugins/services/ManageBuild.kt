package io.namaek2.plugins.services

import com.intellij.openapi.progress.ProgressIndicator
import io.namaek2.plugins.toolWindow.MyConsoleLogger
import io.namaek2.plugins.toolWindow.MyConsoleViewer
import java.io.*
import java.util.*


class ManageBuild (private val javaFilesPath: String, private var outFolder : String, private val indicator: ProgressIndicator) {
    fun runBuildManager(fractionValue: Double, buildManager: String) {
        indicator.fraction = fractionValue

        if (buildManager == "gradle") {
            runGradle()
        }
        else if (buildManager == "maven") {
            runMaven()
        }
        indicator.fraction = fractionValue + 0.1
    }

    private fun runMaven(){
        indicator.text = "Building with Maven..."

        try {
            // 프로세스 빌더를 생성합니다.
            val osName = System.getProperty("os.name").lowercase(Locale.getDefault())

            val processBuilder = when {
                "windows" in osName -> ProcessBuilder("mvn", "-f", "$outFolder/pom.xml", "package")
                "linux" in osName-> ProcessBuilder("mvn", "-f", "$outFolder/pom.xml", "package")
                "mac" in osName -> ProcessBuilder("mvn", "-f", "$outFolder/pom.xml", "package")
                else -> throw IllegalArgumentException("Unsupported OS: $osName")
            }

            processBuilder.directory(File(javaFilesPath))
            processBuilder.redirectErrorStream(true)

            try {
                // 프로세스를 시작합니다.
                val process = processBuilder.start()
                MyConsoleViewer.println("jar build started")
                MyConsoleLogger.logPrint("jar build started")
                // 프로세스의 출력을 읽습니다.
                val reader = BufferedReader(InputStreamReader(process.inputStream))
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    MyConsoleLogger.logPrint("maven output: $line")
                }

                // 프로세스가 종료될 때까지 대기합니다.
                val exitCode = process.waitFor()
                if (exitCode == 0) {
                    MyConsoleViewer.println("obfuscated jar built successfully in obfuscated_project_folder")
                    MyConsoleLogger.logPrint("obfuscated jar built successfully in obfuscated_project_folder")
                } else {
                    MyConsoleViewer.println("Error in jar building : $exitCode")
                    MyConsoleLogger.logPrint("Error in jar building : $exitCode")
                }
            } catch (e: InterruptedException) {
                MyConsoleViewer.println("Canceled by user")
                MyConsoleLogger.logPrint("Canceled by user")
            }
        } catch (e: IOException) {
            MyConsoleViewer.println("Error in jar building process: ${e.message}")
            MyConsoleLogger.logPrint("Error in jar building process: ${e.message}")
        }
    }

    private fun runGradle() {
        indicator.text = "Building with Gradle..."

        try {
            // 프로세스 빌더를 생성합니다.
            val osName = System.getProperty("os.name").lowercase(Locale.getDefault())

            val processBuilder = when {
                "windows" in osName -> ProcessBuilder("gradle.bat", "jar")
                "linux" in osName-> ProcessBuilder("gradle", "jar")
                "mac" in osName -> ProcessBuilder("gradle", "jar")
                else -> throw IllegalArgumentException("Unsupported OS: $osName")
            }

            processBuilder.directory(File(outFolder))
            processBuilder.redirectErrorStream(true)

            try {
                // 프로세스를 시작합니다.
                val process = processBuilder.start()
                MyConsoleViewer.println("jar build started")
                MyConsoleLogger.logPrint("jar build started")
                // 프로세스의 출력을 읽습니다.
                val reader = BufferedReader(InputStreamReader(process.inputStream))
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    MyConsoleLogger.logPrint("gradle output: $line")
                }

                // 프로세스가 종료될 때까지 대기합니다.
                val exitCode = process.waitFor()
                if (exitCode == 0) {
                    MyConsoleViewer.println("obfuscated jar built successfully in obfuscated_project_folder")
                    MyConsoleLogger.logPrint("obfuscated jar built successfully in obfuscated_project_folder")
                } else {
                    MyConsoleViewer.println("Error in jar building : $exitCode")
                    MyConsoleLogger.logPrint("Error in jar building : $exitCode")
                }
            } catch (e: InterruptedException) {
                MyConsoleViewer.println("Canceled by user")
                MyConsoleLogger.logPrint("Canceled by user")
            }
        } catch (e: IOException) {
            MyConsoleViewer.println("Error in jar building process: ${e.message}")
            MyConsoleLogger.logPrint("Error in jar building process: ${e.message}")
        }
    }

    fun checkBuildManager() : String {
        var buildManager: String? = null
        if (isGradleProject()) {
            checkGradleVersion()
            buildManager = "gradle"
        }
        else if (isMavenProject()) {
            buildManager = "maven"
        }
        else {
            MyConsoleViewer.println("Build manager not found\n")
            MyConsoleLogger.logPrint("Check project has build.gradle or pom.xml or something else.\n")
            MyConsoleLogger.logPrint("Build manager not found")
            throw IllegalArgumentException("Build manager not found")
        }

        return buildManager
    }

    private fun checkGradleVersion(){
        findGradleVersion(File(javaFilesPath))?.let {
            MyConsoleLogger.logPrint("Gradle version: $it")
            if (it < "8.0.0") {
                MyConsoleViewer.println("Build might not be supported cause Gradle version is lower than 8.0")
                MyConsoleLogger.logPrint("Build is not supported cause Gradle version is lower than 8.0")
            }
        }
    }

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

    private fun isMavenProject() : Boolean {
        val mavenFiles = listOf(
            "pom.xml"
        )

        val isMaven = mavenFiles.any { fileName ->
            File(javaFilesPath, fileName).exists()
        }

        return isMaven
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
                        return it
                    }
                }
            } catch (e: IOException) {
                MyConsoleViewer.println("Error reading gradle.properties: ${e.message}")
                MyConsoleLogger.logPrint("Error reading gradle.properties: ${e.message}")
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
                MyConsoleLogger.logPrint("Error reading gradle-wrapper.properties: ${e.message}")
                return null
            }

            val distributionUrl = properties.getProperty("distributionUrl") ?: return null

            // URL에서 버전 추출 (예: gradle-7.4.2-bin.zip)
            val versionRegex = "gradle-([\\d.]+)".toRegex()
            val matchResult = versionRegex.find(distributionUrl)
            MyConsoleLogger.logPrint("Gradle version: ${matchResult?.groupValues?.get(1)}")
            return matchResult?.groupValues?.get(1)
        }

        return null
    }
}