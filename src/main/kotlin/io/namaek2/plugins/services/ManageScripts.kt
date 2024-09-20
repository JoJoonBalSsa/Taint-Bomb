package io.namaek2.plugins.services

import com.intellij.openapi.progress.ProgressIndicator
import io.namaek2.plugins.toolWindow.MyConsoleLogger
import java.io.*
import java.util.*

class ManageScripts(private var javaFilesPath: String, private var outputFolder : String, private var tempFolder : String, private val indicator: ProgressIndicator) {
    private fun readJavaCode(path: String): String {
        val scriptStream = javaClass.getResourceAsStream("/java/" + path)
        val javaCode = scriptStream?.bufferedReader()?.use { it.readText() }
            ?: throw IllegalArgumentException("Script not found: $path")

        return javaCode
    }

    fun executePythonScript(fractionValue : Double): Boolean {
        indicator.text = "Executing Python script..."
        indicator.fraction = fractionValue
        try{
            val osName = System.getProperty("os.name").lowercase(Locale.getDefault())
            val stringDecryptJava = when {
                "windows" in osName -> readJavaCode("stringDecryptWin.java")
                "linux" in osName-> readJavaCode("stringDecryptLin.java")
                "mac" in osName -> readJavaCode("stringDecryptLin.java")
                else -> throw IllegalArgumentException("Unsupported OS: $osName")
            }

            val keyDecryptJava = when {
                "windows" in osName -> readJavaCode("keyDecryptWin.java")
                "linux" in osName-> readJavaCode("keyDecryptLin.java")
                "mac" in osName -> readJavaCode("keyDecryptLin.java")
                else -> throw IllegalArgumentException("Unsupported OS: $osName")
            }

            // 프로세스 빌더를 생성합니다.
            val scriptPath = tempFolder + "/main.py"
            val processBuilder = ProcessBuilder("python", scriptPath, outputFolder, keyDecryptJava, stringDecryptJava)

            val currentDir = System.getProperty("user.dir")
            processBuilder.directory(File(currentDir))
            print("currentDir: $currentDir")

            // 프로세스의 출력을 캡처할 수 있도록 리디렉션합니다.
            processBuilder.redirectErrorStream(true)

            try {
                // 프로세스를 시작합니다.
                val process = processBuilder.start()
                MyConsoleLogger.println("main started")
                // 프로세스의 출력을 읽습니다.
                val reader = BufferedReader(InputStreamReader(process.inputStream))
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    MyConsoleLogger.println("main output: $line")
                }

                // 프로세스가 종료될 때까지 대기합니다.
                val exitCode = process.waitFor()
                if (exitCode == 0) {
                    MyConsoleLogger.println("main executed successfully")
                } else {
                    MyConsoleLogger.println("Error in main execution : $exitCode")
                    return false
                }
            } catch (e: InterruptedException) {
                MyConsoleLogger.println("Canceled by user")
            }
        } catch (e: IOException) {
            MyConsoleLogger.println("Error in script execution process: ${e.message}")
        }
        indicator.fraction = 0.85
        return true
    }
}