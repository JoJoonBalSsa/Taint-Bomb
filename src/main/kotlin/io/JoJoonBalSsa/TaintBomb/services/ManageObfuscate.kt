package io.JoJoonBalSsa.TaintBomb.services

import com.intellij.openapi.progress.ProgressIndicator
import io.JoJoonBalSsa.TaintBomb.toolWindow.MyConsoleLogger
import io.JoJoonBalSsa.TaintBomb.toolWindow.MyConsoleViewer
import io.JoJoonBalSsa.TaintBomb.settings.TaintBombSettings
import kotlinx.html.B
import java.io.*
import java.util.concurrent.TimeUnit

class ManageObfuscate(
    private val javaFilesPath: String,
    private var outputFolder: String,
    private var tempFolder: String,
    manageHash: ManageHash,
    private val venvPath: String,
    private val osName: String,
    private val indicator: ProgressIndicator
) {
    private val settings = TaintBombSettings.getInstance()

    companion object {
        private const val OUTPUT_THREAD_TIMEOUT_MS = 5000L
        private const val OUTPUT_THREAD_INTERRUPT_WAIT_MS = 1000L
        private const val MAIN_SCRIPT_TIMEOUT_SECONDS = 60L
        private const val STEP_SIZE = 0.08
    }

    init {
        indicator.text = "Checking Java code syntax..."
        manageHash.compareFileHashes(0.25)
        checkJavaSyntax(0.3)
        executePythonScript()
    }

    private fun readJavaCode(path: String): String {
        return javaClass.getResourceAsStream("/java/$path")
            ?.bufferedReader()
            ?.use { it.readText() }
            ?: throw IllegalArgumentException("Script not found: $path")
    }

    private fun executePythonScript() {
        var currentFraction = 0.35

        executeOptionalScript(
            enabled = true, //settings.enableRemoveComments,
            scriptName = "removeComments",
            displayText = "Removing comments",
            disabledMessage = "remove comments",
            currentFraction = currentFraction
        )
        currentFraction += STEP_SIZE

        if (settings.enableStringEncryption) {
            indicator.text = "Encrypting strings..."
            logAndPrint("Encrypting strings...")
            runStringObfuscate(currentFraction)
            currentFraction += STEP_SIZE
        } else {
            logSkipped("string obfuscation")
        }

        indicator.text = "Analysing code..."
        logAndPrint("Analysing code...")
        runAnalysisObfuscate(currentFraction)
        currentFraction += STEP_SIZE

        indicator.text = "Running differential obfuscating..."
        logAndPrint("Running differential obfuscating...")
        runLevelObfuscate(currentFraction)
        currentFraction += STEP_SIZE

        executeOptionalScript(
            enabled = settings.enableIdentifierObfuscation,
            scriptName = "identifierObfuscate",
            displayText = "Identifier obfuscating",
            disabledMessage = "identifier obfuscation",
            currentFraction = currentFraction
        )
    }

    private fun executeOptionalScript(
        enabled: Boolean,
        scriptName: String,
        displayText: String,
        disabledMessage: String,
        currentFraction: Double
    ) {
        if (enabled) {
            indicator.text = "$displayText..."
            logAndPrint("$displayText...")
            runPythonScript(scriptName, currentFraction)
        } else {
            logSkipped(disabledMessage)
        }
    }

    private fun checkJavaSyntax(fractionValue: Double) {
        indicator.fraction = fractionValue
        val exitCode = runScript("checkJavaSyntax", javaFilesPath)

        if (exitCode == 0) {
            logAndPrint("This code is supported")
        } else {
            MyConsoleViewer.apply {
                println("JavaSyntaxError.")
                println("\n!!!!!!   CODE SYNTAX IS NOT SUPPORTED   !!!!!!")
                println("The code must be based on the Java language spec available at : ")
                println("http://docs.oracle.com/javase/specs/jls/se8/html/.")
                println("\nthe process will be continued but it might be go wrong\n")
            }
            MyConsoleLogger.logPrint("java syntax error occurred.")
        }
    }

    private fun runStringObfuscate(fractionValue: Double) {
        indicator.fraction = fractionValue

        try {
            val stringDecryptJava = readJavaCode("stringDecrypt$osName.java")
            val keyDecryptJava = readJavaCode("keyDecrypt$osName.java")

            val scriptPath = "$tempFolder/stringObfuscate.py"
            val args = listOf(venvPath, "-u", scriptPath, outputFolder, keyDecryptJava, stringDecryptJava)

            executeProcess(args, "stringObfuscate", timeout = null)
        } catch (e: InterruptedException) {
            logAndPrint("Canceled by user")
            throw e
        } catch (e: IOException) {
            logAndPrint("An error occurred: ${e.message}")
            throw e
        }
    }

    private fun runAnalysisObfuscate(fractionValue: Double) {
        indicator.fraction = fractionValue
        val timeout = MAIN_SCRIPT_TIMEOUT_SECONDS

        try {
            val scriptPath = "$tempFolder/main.py"
            val args = listOf(venvPath, "-u", scriptPath, outputFolder, settings.apiKey, settings.enableOperatorObfuscation.toString(), settings.enableMethodSplitting.toString(), settings.enableInsertDummyCode.toString())

            executeProcess(args, "main", timeout = null)
        } catch (e: InterruptedException) {
            logAndPrint("Canceled by user")
            throw e
        } catch (e: IOException) {
            logAndPrint("An error occurred: ${e.message}")
            throw e
        }
    }

    private fun runLevelObfuscate(fractionValue: Double) {
        indicator.fraction = fractionValue

        try {
            val scriptPath = "$tempFolder/levelObfuscate.py"
            val args = listOf(venvPath, "-u", scriptPath, outputFolder, settings.enableOperatorObfuscation.toString(), settings.enableMethodSplitting.toString(), settings.enableInsertDummyCode.toString())

            executeProcess(args, "levelObfuscate.py", timeout = null)
        } catch (e: InterruptedException) {
            logAndPrint("Canceled by user")
            throw e
        } catch (e: IOException) {
            logAndPrint("An error occurred: ${e.message}")
            throw e
        }
    }

    private fun runPythonScript(scriptName: String, fractionValue: Double) {
        indicator.fraction = fractionValue
        runScript(scriptName, outputFolder)
    }

    private fun runScript(scriptName: String, outFolder: String): Int {
        val scriptPath = "$tempFolder/$scriptName.py"
        val args = buildScriptArgs(scriptPath, outFolder, scriptName)
        val timeout = if (scriptName == "main") MAIN_SCRIPT_TIMEOUT_SECONDS else null

        return executeProcess(args, scriptName, timeout)
    }

    private fun buildScriptArgs(scriptPath: String, outFolder: String, scriptName: String): List<String> {
        return listOf(venvPath, "-u", scriptPath, outFolder)
    }

    private fun executeProcess(
        args: List<String>,
        scriptName: String,
        timeout: Long?
    ): Int {
        val process = ProcessBuilder(args)
            .redirectErrorStream(true)
            .start()

        val outputThread = createOutputReaderThread(process, scriptName)
        outputThread.start()

        return try {
            val exitCode = waitForProcess(process, timeout, scriptName)
            waitForOutputThread(outputThread)
            exitCode
        } catch (e: InterruptedException) {
            handleProcessInterruption(process, outputThread, "Canceled by user")
            -1
        } catch (e: IOException) {
            handleProcessInterruption(process, outputThread, "An error occurred: ${e.message}")
            -1
        }
    }

    private fun createOutputReaderThread(process: Process, scriptName: String): Thread {
        return Thread {
            try {
                BufferedReader(InputStreamReader(process.inputStream)).use { reader ->
                    reader.lineSequence().forEach { line ->
                        MyConsoleLogger.logPrint("$scriptName output: $line")
                    }
                }
            } catch (e: IOException) {
                MyConsoleLogger.logPrint("Error reading output from $scriptName: ${e.message}")
            }
        }
    }

    private fun waitForProcess(process: Process, timeout: Long?, scriptName: String): Int {
        return if (timeout != null) {
            val completed = process.waitFor(timeout, TimeUnit.SECONDS)
            if (!completed) {
                process.destroy()
                if (process.isAlive) {
                    process.destroyForcibly()
                }
                MyConsoleLogger.logPrint("$scriptName execution timed out.")
                return -1
            }
            process.exitValue()
        } else {
            process.waitFor()
            process.exitValue()
        }
    }

    private fun waitForOutputThread(thread: Thread) {
        try {
            thread.join(OUTPUT_THREAD_TIMEOUT_MS)
            if (thread.isAlive) {
                MyConsoleLogger.logPrint("Output thread is still running after ${OUTPUT_THREAD_TIMEOUT_MS}ms. Interrupting...")
                thread.interrupt()
                thread.join(OUTPUT_THREAD_INTERRUPT_WAIT_MS)
                if (thread.isAlive) {
                    MyConsoleLogger.logPrint("Output thread could not be interrupted. It may be blocked.")
                }
            }
        } catch (e: InterruptedException) {
            MyConsoleLogger.logPrint("Interrupted while waiting for output thread to finish: ${e.message}")
        }
    }

    private fun handleProcessInterruption(process: Process, outputThread: Thread, message: String) {
        logAndPrint(message)
        process.destroy()
        outputThread.interrupt()
    }

    private fun logAndPrint(message: String) {
        MyConsoleViewer.println(message)
        MyConsoleLogger.logPrint(message)
    }

    private fun logSkipped(feature: String) {
        MyConsoleViewer.println("Skipping $feature (disabled in configuration)")
        MyConsoleLogger.logPrint("Skipping $feature - disabled")
    }
}
