package io.namaek2.plugins.services

import java.io.*
import java.nio.file.Files
import java.nio.file.StandardOpenOption
import java.security.MessageDigest
import java.util.*

class RunPyScripts(private var javaFilesPath: String, private var outputFolder : String) {
    private val scriptNames = mutableListOf<String>()
    private val scriptHashes = mutableListOf<String>()
    private var tempFilePath = ""

    init {
        readHashInfo()
        copyScripts()
        if(compareFileHashes()) {
            executePythonScript()
            runGradle()
        }
        deleteTempFiles()
    }

    private fun readHashInfo(){
        println("Reading check_hash file...")
        val hashFileListPath = javaClass.getResourceAsStream("/pyscripts/check_hash")
        val fileLists = hashFileListPath?.bufferedReader()?.readLines()
            ?: throw IllegalArgumentException("check_hash file not found")

        for(fileList in fileLists){
            val parts = fileList.split(" ")
            if (parts.size == 2) {
                scriptNames.add(parts[0])
                scriptHashes.add(parts[1])
            } else {
                println("Invalid line: $fileList")
            }
        }
    }

    private fun copyScripts() {
        println("Copying scripts...")

        tempFilePath = javaFilesPath + "/temp"
        val result = File(tempFilePath).mkdir()

        if (result) {
            println("Directory created successfully")
        } else {
            println("Directory already exists")
        }

        for (scriptName in scriptNames) {
            val scriptStream = javaClass.getResourceAsStream("/pyscripts/$scriptName" + ".py")
            val scriptContent = scriptStream?.bufferedReader()?.use { it.readText() }
                ?: throw IllegalArgumentException("Script not found: $scriptName")

            val tempFile = createNamedTempFile(scriptName, ".py").toPath()
            println(tempFile.toString())

            scriptContent.toByteArray().let { Files.write(tempFile, it, StandardOpenOption.WRITE) }
            println("$scriptName created successfully")
        }
    }

    private fun createNamedTempFile(prefix: String, suffix: String): File {
        val fileName = "$prefix$suffix"
        val tempFolder = File(tempFilePath)

        return File(tempFolder, fileName).apply { createNewFile() }
    }

    private fun compareFileHashes(): Boolean {
        println("Comparing file hashes...")
        for (i in 0..scriptNames.size - 1) {
            val fileName = scriptNames[i] + ".py"
            val expectedHash = scriptHashes[i]

            val file = File(tempFilePath, fileName)
            if (file.exists()) {
                val actualHash = calculateMD5(file)
                if (actualHash == expectedHash) {
                    println("File $fileName matches the expected hash.")
                } else {
                    println("File $fileName does not match the expected hash.")
                    return false
                }
            } else {
                println("File $fileName does not exist.")
                return false
            }
        }
        return true
    }

    private fun calculateMD5(file: File): String {
        val buffer = ByteArray(1024)
        val md = MessageDigest.getInstance("MD5")
        FileInputStream(file).use { fis ->
            var numRead: Int
            while (fis.read(buffer).also { numRead = it } != -1) {
                md.update(buffer, 0, numRead)
            }
        }
        val hashBytes = md.digest()
        val sb = StringBuilder()
        for (b in hashBytes) {
            sb.append(String.format("%02x", b))
        }
        return sb.toString()
    }

    private fun readJavaCode(path: String): String {

        val scriptStream = javaClass.getResourceAsStream("/java/" + path)
        val javaCode = scriptStream?.bufferedReader()?.use { it.readText() }
            ?: throw IllegalArgumentException("Script not found: $path")

        return javaCode
    }

    private fun executePythonScript() {
        try{
            val keyDecryptJava = readJavaCode("keyDecrypt.java")
            var stringDecryptJava = ""
            when (System.getProperty("os.name").lowercase(Locale.getDefault())) {
                "windows" -> stringDecryptJava = readJavaCode("stringDecryptWin.java")
                // "linux" -> println("Linux 운영 체제입니다.")
                // "mac os x" -> println("macOS 운영 체제입니다.")
                else -> stringDecryptJava = readJavaCode("stringDecryptLin.java")
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
                println("main started")
                // 프로세스의 출력을 읽습니다.
                val reader = BufferedReader(InputStreamReader(process.inputStream))
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    println("main output: $line")
                }

                // 프로세스가 종료될 때까지 대기합니다.
                val exitCode = process.waitFor()
                if (exitCode == 0) {
                    println("main executed successfully")
                } else {
                    println("Error in main execution : $exitCode")
                }
            } catch (e: InterruptedException) {
                e.printStackTrace()
            }
        } catch (e: Exception) {
            println("Error in script execution process: ${e.message}")
        }
    }

    private fun runGradle() {
        try {
            // 프로세스 빌더를 생성합니다.
            val processBuilder = ProcessBuilder("gradle", "jar")

            processBuilder.directory(File(outputFolder))

            // 프로세스의 출력을 캡처할 수 있도록 리디렉션합니다.
            processBuilder.redirectErrorStream(true)

            try {
                // 프로세스를 시작합니다.
                val process = processBuilder.start()
                println("jar build started")
                // 프로세스의 출력을 읽습니다.
                val reader = BufferedReader(InputStreamReader(process.inputStream))
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    println("gradle output: $line")
                }

                // 프로세스가 종료될 때까지 대기합니다.
                val exitCode = process.waitFor()
                if (exitCode == 0) {
                    println("jar builded successfully")
                } else {
                    println("Error in jar building : $exitCode")
                }
            } catch (e: InterruptedException) {
                e.printStackTrace()
            }
        } catch (e: Exception) {
            println("Error in jar building process: ${e.message}")
        }
    }

    private fun deleteTempFiles() {
        for (scriptName in scriptNames) {
            val tempPath = File(tempFilePath + "/$scriptName.py")
            if (tempPath.exists()) {
                tempPath.delete()
                println("$scriptName deleted successfully")
            } else {
                println("$scriptName does not exist")
            }
        }

        val tempPath = File(tempFilePath)

        try{
            tempPath.delete()
            println("$tempFilePath deleted successfully")
        } catch (e: Exception) {
            println("Error in deleting temp folder: ${e.message}")
        }
    }
}