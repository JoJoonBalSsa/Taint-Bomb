package io.JoJoonBalSsa.TaintBomb.services

import com.intellij.openapi.progress.ProgressIndicator
import io.JoJoonBalSsa.TaintBomb.toolWindow.MyConsoleLogger
import io.JoJoonBalSsa.TaintBomb.toolWindow.MyConsoleViewer
import java.io.*
import java.util.concurrent.TimeUnit

class ManageObfuscate(
    private val javaFilesPath: String,
    private var outputFolder: String,
    private var tempFolder: String,
    manageHash: ManageHash,
    venvPath: String,
    osName: String,
    private val indicator: ProgressIndicator
) {
    init {
        indicator.text = "Checking Java code syntax..."
        manageHash.compareFileHashes(0.25)
        initCheckJavaSyntax(venvPath, javaFilesPath, 0.3)

        executePythonScript(venvPath, osName)
    }

    private fun readJavaCode(path: String): String {
        val scriptStream = javaClass.getResourceAsStream("/java/" + path)
        val javaCode = scriptStream?.bufferedReader()?.use { it.readText() }
            ?: throw IllegalArgumentException("Script not found: $path")

        return javaCode
    }

    private fun executePythonScript(venvPath : String, osName : String) {
        indicator.text = "Removing comments..."
        MyConsoleViewer.println("Removing comments...")
        runPythonScript(venvPath, "removeComments", outputFolder, 0.35)
        //checkJavaSyntax(venvPath, outputFolder, 0.4)

//        indicator.text = "Encrypting strings..."
//        MyConsoleViewer.println("Encrypting strings...")
//        runStringObfuscate(venvPath, "stringObfuscate", outputFolder, osName, 0.45)
//        //checkJavaSyntax(venvPath, outputFolder, 0.5)

        indicator.text = "Analysing code..."
        MyConsoleViewer.println("Analysing code...")
        runPythonScript(venvPath, "main", outputFolder, 0.55)

        indicator.text = "Level obfuscation activated..."
        MyConsoleViewer.println("Level obfuscation activated...")
        runPythonScript(venvPath, "levelObfuscate", outputFolder, 0.65)
        // checkJavaSyntax(venvPath, outputFolder, 0.7)

//        indicator.text = "Identifier obfuscating..."
//        MyConsoleViewer.println("Identifier obfuscating...")
//        runPythonScript(venvPath, "identifierObfuscate", outputFolder, 0.75)
//        //checkJavaSyntax(venvPath, outputFolder, 0.8)
    }

    private fun checkJavaSyntax(venvPath:String, javaFilesPath: String, fractionValue: Double) {
        indicator.fraction = fractionValue

        val exitCode = runScript(venvPath, "checkJavaSyntax", javaFilesPath)

        if (exitCode != 0) {
            MyConsoleViewer.println("ObfuscationSyntaxError.")
            MyConsoleLogger.logPrint("obfuscation syntax error occurred.")
            throw IOException("obfuscation syntax error occurred.")
        }
    }

    private fun initCheckJavaSyntax(venvPath:String, javaFilesPath: String, fractionValue: Double) {
        indicator.fraction = fractionValue

        val exitCode = runScript(venvPath, "checkJavaSyntax", javaFilesPath)

        if (exitCode == 0) {
            MyConsoleViewer.println("This code is supported")
            MyConsoleLogger.logPrint("This code is supported")
        } else {
            MyConsoleViewer.println("JavaSyntaxError.")
            MyConsoleViewer.println("\n!!!!!!   CODE SYNTAX IS NOT SUPPORTED   !!!!!!")
            MyConsoleViewer.println("The code must be based on the Java language spec available at : ")
            MyConsoleViewer.println("http://docs.oracle.com/javase/specs/jls/se8/html/.")
            MyConsoleViewer.println("\nthe process will be continued but it might be go wrong\n")

            MyConsoleLogger.logPrint("java syntax error occurred.")
        }
    }

    private fun runStringObfuscate(
        venvPath: String,
        scriptName: String,
        outFolder: String,
        osName: String,
        fractionValue: Double
    ) : Int{
        indicator.fraction = fractionValue

        try{
            val stringDecryptJava = readJavaCode("stringDecrypt$osName.java")
            val keyDecryptJava = readJavaCode("keyDecrypt$osName.java")

            val installScript = "$tempFolder/$scriptName.py"
            val pythonProcess = ProcessBuilder(venvPath, "-u", installScript, outFolder, keyDecryptJava, stringDecryptJava)
                .redirectErrorStream(true)
                .start()
            val reader = BufferedReader(InputStreamReader(pythonProcess.inputStream))
            var line: String?
            while (reader.readLine().also { line = it } != null) {
                MyConsoleLogger.logPrint("$scriptName output: $line")
            }

            return pythonProcess.waitFor()
        } catch (e: InterruptedException) {
            MyConsoleViewer.println("Canceled by user")
            MyConsoleLogger.logPrint("Canceled by user")
            throw e
        } catch (e: IOException) {
            MyConsoleViewer.println("An error occurred: ${e.message}")
            MyConsoleLogger.logPrint("An error occurred: ${e.message}")
            throw e
        }
    }

    private fun runPythonScript(venvPath: String, scriptName: String, outFolder: String, fractionValue: Double) {
        indicator.fraction = fractionValue
        runScript(venvPath, scriptName, outFolder)
        return
    }

    private fun runScript(venvPath: String, scriptName: String, outFolder: String) : Int{
        val installScript = "$tempFolder/$scriptName.py"
        val pythonProcess = ProcessBuilder(venvPath, "-u", installScript, outFolder)
            .redirectErrorStream(true)
            .start()

        val outputThread = Thread {
            try {
                val reader = BufferedReader(InputStreamReader(pythonProcess.inputStream))
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    MyConsoleLogger.logPrint("$scriptName output: $line")
                }
            } catch (e: IOException) {
                MyConsoleLogger.logPrint("Error reading output from $scriptName: ${e.message}")
            }
        }

        outputThread.start()

        if (scriptName == "main") {
            var completed = false
            try {
                completed = pythonProcess.waitFor(60, TimeUnit.SECONDS)
            } catch (e: InterruptedException) {
                MyConsoleViewer.println("Canceled by user")
                MyConsoleLogger.logPrint("Canceled by user")
                pythonProcess.destroy()
                outputThread.interrupt()
                return -1
            } catch (e: IOException) {
                MyConsoleViewer.println("An error occurred: ${e.message}")
                MyConsoleLogger.logPrint("An error occurred: ${e.message}")
                pythonProcess.destroy()
                outputThread.interrupt()
                return -1
            }

            if (!completed) {
                pythonProcess.destroy()
                if (pythonProcess.isAlive) {
                    pythonProcess.destroyForcibly()
                }
                MyConsoleLogger.logPrint("$scriptName execution timed out.")
                outputThread.interrupt()
                return -1
            }
        } else {
            try {
                pythonProcess.waitFor()
            } catch (e: InterruptedException) {
                MyConsoleViewer.println("Canceled by user")
                MyConsoleLogger.logPrint("Canceled by user")
                pythonProcess.destroy()
                outputThread.interrupt()
                return -1
            } catch (e: IOException) {
                MyConsoleViewer.println("An error occurred: ${e.message}")
                MyConsoleLogger.logPrint("An error occurred: ${e.message}")
                pythonProcess.destroy()
                outputThread.interrupt()
                return -1
            }
        }

        // 프로세스 종료 후 outputThread를 최대 5초 동안 대기
        try {
            outputThread.join(5000) // 5초 동안 스레드 종료 대기
            if (outputThread.isAlive) {
                MyConsoleLogger.logPrint("Output thread is still running after 5 seconds. Interrupting...")
                outputThread.interrupt()
                outputThread.join(1000) // 인터럽트 후 1초 더 대기
                if (outputThread.isAlive) {
                    MyConsoleLogger.logPrint("Output thread could not be interrupted. It may be blocked.")
                }
            }
        } catch (e: InterruptedException) {
            MyConsoleLogger.logPrint("Interrupted while waiting for output thread to finish: ${e.message}")
        }
        return pythonProcess.exitValue()
    }
}