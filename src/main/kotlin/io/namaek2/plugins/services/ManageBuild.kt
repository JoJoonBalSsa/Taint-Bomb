package io.namaek2.plugins.services

import com.intellij.openapi.progress.ProgressIndicator
import io.namaek2.plugins.toolWindow.MyConsoleLogger
import java.io.BufferedReader
import java.io.File
import java.io.IOException
import java.io.InputStreamReader
import java.util.*

class ManageBuild (private val javaFilesPath: String, private var outFolder : String, private val indicator: ProgressIndicator) {
      fun runGradle(fractionValue : Double) {
        indicator.text = "Running Gradle..."
        indicator.fraction = fractionValue

        try {
            // 프로세스 빌더를 생성합니다.
            val osName = System.getProperty("os.name").lowercase(Locale.getDefault())

            val processBuilder = when {
                "windows" in osName -> ProcessBuilder("gradle.bat", "jar")
                "linux" in osName-> ProcessBuilder("gradle", "jar")
                "mac" in osName -> ProcessBuilder("./gradlew", "jar")
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