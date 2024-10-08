package io.namaek2.plugins.services

import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.progress.ProgressIndicator
import io.namaek2.plugins.toolWindow.MyConsoleLogger
import java.io.BufferedReader
import java.io.File
import java.io.IOException
import java.io.InputStreamReader
import java.nio.file.*
import kotlin.io.path.Path


class TasksManager(private val javaFilesPath: String, private var outFolder : String, private var tempFolder : String, private val indicator: ProgressIndicator) {
    init {
        val manageHash = ManageHash(tempFolder, indicator)
        val manageScripts = ManageScripts(javaFilesPath, outFolder, tempFolder, indicator)
        val manageBuild = ManageBuild(javaFilesPath, outFolder, indicator)

        indicator.text = "Deleting past obfuscated directory..."
        deleteDirectory(File(outFolder), 0.0)
        copyDirectory(Path(javaFilesPath), Path(outFolder), 0.10)

        manageHash.parseHashInfo(0.22)
        copyScripts(manageHash.getScriptNames(), 0.25)

        if(manageHash.compareFileHashes(0.30)) {
            val venvPath = prepareVenv(tempFolder)
            if(manageScripts.executePythonScript(venvPath, 0.35)) {
                manageBuild.runGradle(0.8)
            } else {
                thisLogger().error("Error running python scripts")
            }
        }

        indicator.text = "Deleting temp directory..."
        deleteDirectory(File(tempFolder), 0.95)
    }

    private fun prepareVenv(path: String): String {
        val venvPath = File(path, "venv")
        val isWindows = System.getProperty("os.name").lowercase().contains("win")
        val pythonExecutable = if (isWindows) "python" else "python3"
        val venvPythonPath = if (isWindows) "${venvPath}\\Scripts\\python.exe" else "${venvPath}/bin/python"

        try {
            // Create virtual environment
            MyConsoleLogger.println("Creating virtual environment...")
            val createVenvProcess = ProcessBuilder(pythonExecutable, "-m", "venv", venvPath.toString())
                .redirectErrorStream(true)
                .start()
            createVenvProcess.inputStream.bufferedReader().use { reader ->
                reader.lines().forEach(::println)
            }
            if (createVenvProcess.waitFor() != 0) {
                throw IOException("Failed to create virtual environment")
            }

            // Install pycryptodome using the venv's pip
            MyConsoleLogger.println("Installing libraries...")
            val installScript = "$tempFolder/installScripts.py"

            val installProcess = ProcessBuilder(venvPythonPath, installScript)
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

            MyConsoleLogger.println("Virtual environment created and python libraries installed successfully at: $venvPath")
            return venvPythonPath
        } catch (e: IOException) {
            MyConsoleLogger.println("An error occurred: ${e.message}")
            throw e
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
                    MyConsoleLogger.println("Copied: $sourcePath")

                    copiedFiles++
                    indicator.fraction = fractionValue * (copiedFiles.toDouble() / totalFiles)
                    indicator.text = "Copying files... (${copiedFiles}/${totalFiles})"
                }
            }
        }
    }

    private fun copyScripts(scriptNames : MutableList<String>, fractionValue: Double) {
        indicator.text = "Copying scripts..."
        indicator.fraction = fractionValue
        MyConsoleLogger.println("Copying scripts...")

        val result = File(tempFolder).mkdir()
        if (result) {
            MyConsoleLogger.println("Directory created successfully")
        } else {
            MyConsoleLogger.println("Directory already exists")
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
        MyConsoleLogger.println(scriptFile.toString())

        scriptContent.toByteArray().let { Files.write(scriptFile, it, StandardOpenOption.WRITE) }
        MyConsoleLogger.println("$scriptName created successfully")
    }

    private fun deleteDirectory(directory: File, fractionValue: Double = 0.0) {
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
}