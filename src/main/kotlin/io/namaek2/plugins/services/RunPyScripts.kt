package io.namaek2.plugins.services


import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader
import java.nio.file.Files
import java.nio.file.StandardOpenOption

class RunPyScripts {
    fun executePythonScripts(javaFilesPath: String, outputFolder: String) {
        try {
            // python_scripts 파일 읽기
            val scriptListStream = javaClass.getResourceAsStream("/pyscripts/python_scripts")
            val scriptNames = scriptListStream?.bufferedReader()?.readLines()
                ?: throw IllegalArgumentException("python_scripts file not found")

            for (scriptName in scriptNames) {
                executeSinglePythonScript(javaFilesPath, outputFolder, scriptName)
            }
        } catch (e: Exception) {
            println("Error in script execution process: ${e.message}")
        }
    }

    fun executeSinglePythonScript(javaFilesPath: String, outputFolder: String, scriptName: String) {
        // 스크립트 파일을 읽습니다.
        val scriptStream = javaClass.getResourceAsStream("/pyscripts/$scriptName.py")
        val scriptContent = scriptStream?.bufferedReader()?.use { it.readText() }
            ?: throw IllegalArgumentException("Script not found: $scriptName")

        // 임시 파일을 생성합니다.
        val tempFile = Files.createTempFile(scriptName, ".py")
        scriptContent.toByteArray().let { Files.write(tempFile, it, StandardOpenOption.WRITE) }
        println("$scriptName created successfully")

        // 프로세스 빌더를 생성합니다.
        val scriptPath = tempFile.toAbsolutePath().toString()
        val processBuilder = ProcessBuilder("python", scriptPath, javaFilesPath, outputFolder)

        val currentDir = System.getProperty("user.dir")
        processBuilder.directory(File(currentDir))

        // 프로세스의 출력을 캡처할 수 있도록 리디렉션합니다.
        processBuilder.redirectErrorStream(true)

        try {
            // 프로세스를 시작합니다.
            val process = processBuilder.start()
            println("$scriptName started")
            // 프로세스의 출력을 읽습니다.
            val reader = BufferedReader(InputStreamReader(process.inputStream))
            var line: String?
            while (reader.readLine().also { line = it } != null) {
                println("$scriptName output: $line")
            }

            // 프로세스가 종료될 때까지 대기합니다.
            val exitCode = process.waitFor()
            if (exitCode == 0) {
                println("$scriptName executed successfully")
            } else {
                println("Error in $scriptName execution : $exitCode")
            }
        } catch (e: InterruptedException) {
            e.printStackTrace()
        }
        // 임시 파일 삭제
        Files.delete(tempFile)
    }
}