package io.namaek2.plugins.services

import kotlin.io.path.Path
import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.progress.ProgressIndicator
import io.namaek2.plugins.toolWindow.MyConsoleLogger
import java.io.*
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardCopyOption
import java.nio.file.StandardOpenOption
import java.util.*

class ManagePreTask(private val javaFilesPath: String, private var outFolder : String, private var tempFolder : String, private val indicator: ProgressIndicator) {
    private var venvPath = ""
    private var manageHash = ManageHash(tempFolder, indicator)
    private var osName = ""
    init {
        indicator.text = "Preparing obfuscation..."
        osName = checkOS()

        deleteDirectory(File(outFolder), 0.0)
        copyDirectory(Path(javaFilesPath), Path(outFolder), 0.05)


        manageHash.parseHashInfo(0.15)
        copyScripts(manageHash.getScriptNames(), 0.2)


        venvPath = prepareVenv(tempFolder, 0.22)
        prepareLibraries(venvPath, 0.24)
    }

    fun getVenvPath(): String {
        val venvPythonPath = venvPath
        return venvPythonPath
    }

    fun getManageHash(): ManageHash {
        val hashInfo = manageHash
        return hashInfo
    }

    fun getOS() : String {
        val osn = osName
        return osn
    }

    private fun checkOS(): String {
        val osName = System.getProperty("os.name").lowercase(Locale.getDefault())
        return when {
            "windows" in osName -> "Win"
            "linux" in osName -> "Lin"
            // "mac" in osName -> "mac"
            else -> {
                MyConsoleLogger.println("Unsupported OS: $osName")
                throw IllegalArgumentException("Unsupported OS: $osName")
            }
        }
    }

    private fun prepareVenv(path: String, fractionValue: Double): String {
        indicator.fraction = fractionValue

        val venvPath = File(path, "venv")
        val isWindows = System.getProperty("os.name").lowercase().contains("win")
        val pythonExecutable = if (isWindows) "python" else "python3"
        val venvPythonPath = if (isWindows) "${venvPath}\\Scripts\\python.exe" else "${venvPath}/bin/python"

        try {
            // Create virtual environment
            val createVenvProcess = ProcessBuilder(pythonExecutable, "-m", "venv", venvPath.toString())
                .redirectErrorStream(true)
                .start()
            createVenvProcess.inputStream.bufferedReader().use { reader ->
                reader.lines().forEach(::println)
            }
            if (createVenvProcess.waitFor() != 0) {
                throw IOException("Failed to create virtual environment")
            }

        } catch (e: IOException) {
            MyConsoleLogger.println("An error occurred: ${e.message}")
            throw e
        }

        return venvPythonPath
    }

    private fun prepareLibraries(venvPath: String, fractionValue: Double) {
        indicator.fraction = fractionValue
        // Install pycryptodome using the venv's pip
        MyConsoleLogger.println("Installing libraries...")
        val installScript = "$tempFolder/installScripts.py"

        val installProcess = ProcessBuilder(venvPath, installScript)
            .redirectErrorStream(true)
            .start()
        val reader = BufferedReader(InputStreamReader(installProcess.inputStream))
        var line: String?
        while (reader.readLine().also { line = it } != null) {
            MyConsoleLogger.println("installing output: $line")
        }

        if (installProcess.waitFor() != 0) {
            throw IOException("Failed to installing python libraries")
        }
    }

    private fun copyDirectory(source: Path, destination: Path, fractionValue: Double) {
        val totalFiles = Files.walk(source).count()
        var copiedFiles = 0

        Files.walk(source).forEach { sourcePath ->
            if (!sourcePath.toString().contains("obfuscated_project_folder")) {
                val targetPath = destination.resolve(source.relativize(sourcePath))

                if (Files.isDirectory(sourcePath)) {
                    Files.createDirectories(targetPath)
                } else {
                    Files.copy(sourcePath, targetPath, StandardCopyOption.REPLACE_EXISTING)
                    // MyConsoleLogger.println("Copied: $sourcePath")

                    copiedFiles++
                    indicator.fraction = fractionValue * (copiedFiles.toDouble() / totalFiles)
                    indicator.text = "Copying files... (${copiedFiles}/${totalFiles})"
                }
            }
        }
    }

    fun deleteDirectory(directory: File, fractionValue: Double) {
        indicator.fraction = fractionValue

        try {
            deleteFile(directory)
        } catch (e: IOException) {
            thisLogger().error("Error deleting directory: ${e.message}")
        }
    }

    private fun deleteFile(directory: File) {
        if (directory.exists() && directory.isDirectory) {
            directory.listFiles()?.forEach { file ->
                if (file.isDirectory) {
                    deleteFile(file)
                } else {
                    file.delete()
                }
            }
            directory.delete()
        }
    }

    private fun copyScripts(scriptNames : MutableList<String>, fractionValue: Double) {
        indicator.text = "Copying scripts..."
        indicator.fraction = fractionValue
        // MyConsoleLogger.println("Copying scripts...")

        val result = File(tempFolder).mkdir()
        if (result) {
            // MyConsoleLogger.println("Directory created successfully")
        } else {
            // MyConsoleLogger.println("Directory already exists")
        }

        for (scriptName in scriptNames) {
            copyScript(scriptName)
        }
    }

    private fun copyScript(scriptName : String) {
        val scriptStream = javaClass.getResourceAsStream("/pyscripts/$scriptName.py")
        val scriptContent = scriptStream?.bufferedReader()?.use { it.readText() }
            ?: throw IllegalArgumentException("Script not found: $scriptName")

        val scriptFile = File(tempFolder, "$scriptName.py").apply { createNewFile() }.toPath()
        // MyConsoleLogger.println(scriptFile.toString())

        scriptContent.toByteArray().let { Files.write(scriptFile, it, StandardOpenOption.WRITE) }
        // MyConsoleLogger.println("$scriptName created successfully")
    }
}