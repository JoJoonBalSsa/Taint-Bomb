package io.namaek2.plugins.services

import com.intellij.openapi.progress.ProgressIndicator
import io.namaek2.plugins.toolWindow.MyConsoleLogger
import java.io.*
import java.nio.file.Files
import java.nio.file.StandardOpenOption
import java.security.MessageDigest
import java.util.*

class RunPyScripts(private var javaFilesPath: String, private var outputFolder : String,  private val indicator: ProgressIndicator) {
    private val scriptNames = mutableListOf<String>()
    private val scriptHashes = mutableListOf<String>()
    private var tempFilePath = ""

    init {
        indicator.text = "Initializing Python scripts..."
        indicator.fraction = 0.2  // Assuming folder copy took 50%

        readHashInfo()
        copyScripts()
        if(compareFileHashes()) {
            executePythonScript()
            runGradle()
        }

        indicator.fraction = 0.95
        indicator.text = "Python scripts execution completed."
    }

    private fun readHashInfo(){
        indicator.text = "Reading python check_hash file..."
        indicator.fraction = 0.22
        MyConsoleLogger.println("Reading python check_hash file...")

        val hashFileListPath = javaClass.getResourceAsStream("/pyscripts/check_hash")
        readHash(hashFileListPath)
    }

    private fun readHash(hashFileListPath: InputStream?) {
        val fileLists = hashFileListPath?.bufferedReader()?.readLines()
            ?: throw IllegalArgumentException("$hashFileListPath : check_hash file not found")

        for(fileList in fileLists) {
            val parts = fileList.split(" ")
            if (parts.size == 2) {
                scriptNames.add(parts[0])
                scriptHashes.add(parts[1])
            } else {
                MyConsoleLogger.println("Invalid line: $fileList")
            }
        }
    }

    private fun copyScripts() {
        indicator.text = "Copying scripts..."
        indicator.fraction = 0.25
        MyConsoleLogger.println("Copying scripts...")

        tempFilePath = javaFilesPath + "/temp"
        val result = File(tempFilePath).mkdir()

        if (result) {
            MyConsoleLogger.println("Directory created successfully")
        } else {
            MyConsoleLogger.println("Directory already exists")
        }

        for (scriptName in scriptNames) {
            val scriptStream = javaClass.getResourceAsStream("/pyscripts/$scriptName" + ".py")
            val scriptContent = scriptStream?.bufferedReader()?.use { it.readText() }
                ?: throw IllegalArgumentException("Script not found: $scriptName")

            val tempFile = createNamedTempFile(scriptName, ".py").toPath()
            MyConsoleLogger.println(tempFile.toString())

            scriptContent.toByteArray().let { Files.write(tempFile, it, StandardOpenOption.WRITE) }
            MyConsoleLogger.println("$scriptName created successfully")
        }
    }

    private fun createNamedTempFile(prefix: String, suffix: String): File {
        val fileName = "$prefix$suffix"
        val tempFolder = File(tempFilePath)

        return File(tempFolder, fileName).apply { createNewFile() }
    }

    private fun compareFileHashes(): Boolean {
        indicator.text = "Comparing file hashes..."
        indicator.fraction = 0.3
        MyConsoleLogger.println("Comparing file hashes...")
        for (i in 0..scriptNames.size - 1) {
            val fileName = scriptNames[i] + ".py"
            val expectedHash = scriptHashes[i]

            val file = File(tempFilePath, fileName)
            if (file.exists()) {
                try {
                    val actualHash = calculateSHA256(file)
                    if (actualHash == expectedHash) {
                        MyConsoleLogger.println("File $fileName matches the expected hash.")
                    } else {
                        MyConsoleLogger.println("File $fileName does not match the expected hash.")
                        return false
                    }
                }
                catch (e: IOException) {
                    MyConsoleLogger.println("File doesn't exist: ${e.message}")
                    return false
                }
            } else {
                MyConsoleLogger.println("File $fileName does not exist.")
                return false
            }
        }
        return true
    }

    private fun calculateSHA256(file: File): String {
        val buffer = ByteArray(8192)  // 버퍼 크기를 8KB로 증가
        val md = MessageDigest.getInstance("SHA-256")
        FileInputStream(file).use { fis ->
            var numRead: Int
            while (fis.read(buffer).also { numRead = it } != -1) {
                md.update(buffer, 0, numRead)
            }
        }
        val hashBytes = md.digest()
        return hashBytes.joinToString("") { "%02x".format(it) }
    }

    private fun readJavaCode(path: String): String {
        val scriptStream = javaClass.getResourceAsStream("/java/" + path)
        val javaCode = scriptStream?.bufferedReader()?.use { it.readText() }
            ?: throw IllegalArgumentException("Script not found: $path")

        return javaCode
    }

    private fun executePythonScript() {
        indicator.text = "Executing Python script..."
        indicator.fraction = 0.35
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
            val scriptPath = tempFilePath + "/main.py"
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
                }
            } catch (e: InterruptedException) {
                MyConsoleLogger.println("Canceled by user")
            }
        } catch (e: IOException) {
            MyConsoleLogger.println("Error in script execution process: ${e.message}")
        }
        indicator.fraction = 0.85
    }

    private fun runGradle() {
        indicator.text = "Running Gradle..."
        indicator.fraction = 0.90
        try {
            // 프로세스 빌더를 생성합니다.
            val osName = System.getProperty("os.name").lowercase(Locale.getDefault())

            val processBuilder = when {
                "windows" in osName -> ProcessBuilder("gradle.bat", "jar")
                "linux" in osName-> ProcessBuilder("gradle", "jar")
                "mac" in osName -> ProcessBuilder("./gradlew", "jar")
                else -> throw IllegalArgumentException("Unsupported OS: $osName")
            }

            processBuilder.directory(File(outputFolder))

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
        indicator.fraction = 0.95
    }
}