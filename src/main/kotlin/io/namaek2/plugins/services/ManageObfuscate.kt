package io.namaek2.plugins.services

import com.intellij.openapi.progress.ProgressIndicator
import io.namaek2.plugins.toolWindow.MyConsoleLogger
import java.io.*

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
        runPythonScript(venvPath, "removeComments", outputFolder, 0.35)
        checkJavaSyntax(venvPath, outputFolder, 0.4)

        indicator.text = "Encrypting strings..."
        runStringObfuscate(venvPath, "stringObfuscate", outputFolder, osName, 0.45)
        checkJavaSyntax(venvPath, outputFolder, 0.5)

        indicator.text = "Analysing code..."
        runPythonScript(venvPath, "main", outputFolder, 0.55)
        checkJavaSyntax(venvPath, outputFolder, 0.6)

        indicator.text = "Level obfuscation activated..."
        runPythonScript(venvPath, "levelObfuscate", outputFolder, 0.65)
        checkJavaSyntax(venvPath, outputFolder, 0.7)

        indicator.text = "Identifier obfuscating..."
        runPythonScript(venvPath, "identifierObfuscate", outputFolder, 0.75)
        checkJavaSyntax(venvPath, outputFolder, 0.8)
    }

    private fun checkJavaSyntax(venvPath:String, javaFilesPath: String, fractionValue: Double) {
        indicator.fraction = fractionValue

        val exitCode = runScript(venvPath, "checkJavaSyntax", javaFilesPath)

        if (exitCode != 0) {
            MyConsoleLogger.println("obfuscation syntax error occurred.")
            throw IOException("obfuscation syntax error occurred.")
        }
    }

    private fun initCheckJavaSyntax(venvPath:String, javaFilesPath: String, fractionValue: Double) {
        indicator.fraction = fractionValue

        val exitCode = runScript(venvPath, "checkJavaSyntax", javaFilesPath)

        if (exitCode == 0) {
            MyConsoleLogger.println("This code is supported")
        } else {
            MyConsoleLogger.println("JavaSyntaxError.")
            MyConsoleLogger.println("\n!!!!!!   CODE SYNTAX IS NOT SUPPORTED   !!!!!!")
            MyConsoleLogger.println("The code must be based on the Java language spec available at : ")
            MyConsoleLogger.println("http://docs.oracle.com/javase/specs/jls/se8/html/.")
            throw IOException("syntax error occurred.")
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
            val pythonProcess = ProcessBuilder(venvPath, installScript, outFolder, keyDecryptJava, stringDecryptJava)
                .redirectErrorStream(true)
                .start()
            val reader = BufferedReader(InputStreamReader(pythonProcess.inputStream))
            var line: String?
            while (reader.readLine().also { line = it } != null) {
                MyConsoleLogger.println("$scriptName output: $line")
            }

            return pythonProcess.waitFor()
        } catch (e: InterruptedException) {
            MyConsoleLogger.println("Canceled by user")
            throw e
        } catch (e: IOException) {
            MyConsoleLogger.println("An error occurred: ${e.message}")
            throw e
        }
    }

    private fun runPythonScript(venvPath: String, scriptName: String, outFolder: String, fractionValue: Double) : Int{
        indicator.fraction = fractionValue
        try{
            return runScript(venvPath, scriptName, outFolder)
        } catch (e: InterruptedException) {
            MyConsoleLogger.println("Canceled by user")
            throw e
        } catch (e: IOException) {
            MyConsoleLogger.println("An error occurred: ${e.message}")
            throw e
        }
    }

    private fun runScript(venvPath: String, scriptName: String, outFolder: String) : Int{
        val installScript = "$tempFolder/$scriptName.py"
        val pythonProcess = ProcessBuilder(venvPath, installScript, outFolder)
            .redirectErrorStream(true)
            .start()
        val reader = BufferedReader(InputStreamReader(pythonProcess.inputStream))
        var line: String?
        while (reader.readLine().also { line = it } != null) {
            MyConsoleLogger.println("$scriptName output: $line")
        }

        return pythonProcess.waitFor()
    }
}