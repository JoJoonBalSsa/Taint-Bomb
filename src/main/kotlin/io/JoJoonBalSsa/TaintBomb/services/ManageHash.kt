package io.JoJoonBalSsa.TaintBomb.services

import com.intellij.openapi.progress.ProgressIndicator
import io.JoJoonBalSsa.TaintBomb.toolWindow.MyConsoleLogger
import io.JoJoonBalSsa.TaintBomb.toolWindow.MyConsoleViewer
import java.io.File
import java.io.FileInputStream
import java.io.IOException
import java.io.InputStream
import java.security.MessageDigest

class ManageHash(private val scriptFolder : String, private val indicator: ProgressIndicator) {
    private var scriptNames = mutableListOf<String>()
    private var scriptHashes = mutableListOf<String>()

    fun getScriptNames(): MutableList<String> {
        val scripts = scriptNames
        return scripts
    }

    fun compareFileHashes(fractionValue: Double) {
        indicator.text = "Comparing file hashes..."
        indicator.fraction = fractionValue
        MyConsoleViewer.println("Comparing file hashes...")
        MyConsoleLogger.logPrint("Comparing file hashes...")

        for (i in 0..scriptNames.size - 1) {
            val fileName = scriptNames[i] + ".py"
            val expectedHash = scriptHashes[i]

            val file = File(scriptFolder, fileName)
            if (file.exists()) {
                try {
                    val actualHash = calculateSHA256(file)
                    if (actualHash == expectedHash) {
                        // MyConsoleLogger.println("File $fileName matches the expected hash.")
                    } else {
                        MyConsoleViewer.println("File $fileName does not match the expected hash.")
                        MyConsoleLogger.logPrint("File $fileName does not match the expected hash.")
                        throw IllegalArgumentException("File $fileName does not match the expected hash.")
                    }
                }
                catch (e: IOException) {
                    MyConsoleViewer.println("Error reading file: ${e.message}")
                    MyConsoleLogger.logPrint("Error reading file: ${e.message}")
                    throw IllegalArgumentException("Error reading file: ${e.message}")
                }
            } else {
                MyConsoleViewer.println("File $fileName does not exist.")
                MyConsoleLogger.logPrint("File $fileName does not exist.")
                throw IllegalArgumentException("File $fileName does not exist.")
            }
        }
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

    fun parseHashInfo(fractionValue : Double){
        indicator.text = "Reading python check_hash file..."
        indicator.fraction = fractionValue
        MyConsoleLogger.logPrint("Reading python check_hash file...")

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
                MyConsoleLogger.logPrint("Invalid line: $fileList")
            }
        }
    }
}