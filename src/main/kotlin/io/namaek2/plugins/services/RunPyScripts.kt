package io.namaek2.plugins.services


import java.io.File
import java.nio.file.Files
import java.nio.file.StandardOpenOption

class RunPyScripts {
    fun runPythonScript(javaFilesPath: String, outputFolder: String) {
        val currentDir = System.getProperty("user.dir")

        // 스크립트 파일을 읽습니다.
        val scriptStream = javaClass.getResourceAsStream("/pyscripts/drawCallGraph.py")
        val scriptContent = scriptStream?.bufferedReader()?.use { it.readText() }

        // 임시 파일을 생성합니다.
        val tempFile = Files.createTempFile("drawCallGraph", ".py")
        scriptContent?.toByteArray()?.let { Files.write(tempFile, it, StandardOpenOption.WRITE) }

        // 프로세스 빌더를 생성합니다.
        val scriptPath = tempFile.toAbsolutePath().toString()
        val processBuilder = ProcessBuilder("python", scriptPath, javaFilesPath, outputFolder)
        processBuilder.directory(File(currentDir))

        // 프로세스의 출력을 캡처할 수 있도록 리디렉션합니다.
        processBuilder.redirectErrorStream(true)

        try {
            // 프로세스를 시작합니다.
            val process = processBuilder.start()

            // 프로세스의 출력을 읽습니다.
            val reader = process.inputStream.bufferedReader()
            val output = StringBuilder()
            reader.useLines { lines -> lines.forEach { output.append(it).append("\n") } }

            // 프로세스가 종료될 때까지 대기합니다.
            val exitCode = process.waitFor()

            // 프로세스의 종료 코드를 출력합니다.
            println("Process exited with code: $exitCode")
            // 프로세스의 출력을 출력합니다.
            println("Process output:\n$output")

        } catch (e: InterruptedException) {
            e.printStackTrace()
        }
    }
}