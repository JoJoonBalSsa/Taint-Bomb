package io.JoJoonBalSsa.TaintBomb.services

import kotlin.io.path.Path
import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.progress.ProgressIndicator
import io.JoJoonBalSsa.TaintBomb.toolWindow.MyConsoleLogger
import io.JoJoonBalSsa.TaintBomb.toolWindow.MyConsoleViewer
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
        MyConsoleViewer.println("Preparing obfuscation...")
        osName = checkOS()

        indicator.text = "Deleting past directory..."
        deleteDirectory(File(outFolder), 0.0)
        deleteDirectory(File(tempFolder), 0.02)

        indicator.text = "Copying project directory..."
        copyDirectory(Path(javaFilesPath), Path(outFolder), 0.05)

        indicator.text = "Parsing hash info..."
        manageHash.parseHashInfo(0.15)

        indicator.text = "Copying scripts..."
        copyScripts(manageHash.getScriptNames(), 0.2)

        indicator.text = "Preparing Python venv..."
        venvPath = prepareVenv(tempFolder, 0.22)

        indicator.text = "Installing Python libraries..."
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
            "mac" in osName -> "Lin"
            else -> {
                MyConsoleViewer.println("Unsupported OS: $osName")
                MyConsoleLogger.logPrint("Unsupported OS: $osName")
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
                MyConsoleViewer.println("Failed to create virtual environment")
                throw IOException("Failed to create virtual environment")
            }

        } catch (e: IOException) {
            MyConsoleViewer.println("An error occurred: ${e.message}")
            MyConsoleLogger.logPrint("An error occurred: ${e.message}")
            throw e
        }

        return venvPythonPath
    }

    private fun prepareLibraries(venvPath: String, fractionValue: Double) {
        indicator.fraction = fractionValue
        // Install pycryptodome using the venv's pip
        MyConsoleLogger.logPrint("Installing libraries...")
        val installScript = "$tempFolder/installScripts.py"

        val installProcess = ProcessBuilder(venvPath, installScript)
            .redirectErrorStream(true)
            .start()
        val reader = BufferedReader(InputStreamReader(installProcess.inputStream))
        var line: String?
        while (reader.readLine().also { line = it } != null) {
            MyConsoleLogger.logPrint("installing output: $line")
        }

        if (installProcess.waitFor() != 0) {
            MyConsoleLogger.logPrint("Failed to installing python libraries. Is the network connected?")
            throw IOException("Failed to installing python libraries")
        }
    }

    private fun copyDirectory(source: Path, destination: Path, fractionValue: Double) {
        // 제외할 디렉토리 목록 정의
        val excludedDirs = listOf(
            "obfuscated_project_folder",
            "build",
            "temp",
            ".git",
            "test",
            "docs"
        )

        // 경로가 제외된 디렉토리인지 확인하는 함수
        fun isExcludedDirectory(path: Path): Boolean {
            return excludedDirs.any { excluded ->
                // 현재 경로의 모든 상위 디렉토리를 확인
                path.nameCount > 0 && path.any { pathPart ->
                    pathPart.toString() == excluded
                }
            }
        }

        val totalFiles = Files.walk(source)
            .filter { path ->
                !isExcludedDirectory(source.relativize(path))
            }
            .count()

        var copiedFiles = 0

        Files.walk(source).forEach { sourcePath ->
            // 상대 경로를 구하고 해당 경로가 제외 디렉토리에 속하는지 확인
            val relativePath = source.relativize(sourcePath)
            val shouldCopy = !isExcludedDirectory(relativePath)

            if (shouldCopy) {
                val targetPath = destination.resolve(relativePath)
                if (Files.isDirectory(sourcePath)) {
                    Files.createDirectories(targetPath)
                } else {
                    Files.copy(sourcePath, targetPath, StandardCopyOption.REPLACE_EXISTING)
                    MyConsoleLogger.logPrint("Copied: $sourcePath")
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
        MyConsoleLogger.logPrint("Copying scripts...")

        val result = File(tempFolder).mkdir()
        if (result) {
            MyConsoleLogger.logPrint("Directory created successfully")
        } else {
            MyConsoleLogger.logPrint("Directory already exists")
        }

        for (scriptName in scriptNames) {
            copyScript(scriptName)
        }
    }

    private fun copyScript(scriptName : String) {
        // Try different possible paths for the script
        val possiblePaths = listOf(
            "/pyscripts/$scriptName.py",
            "/pyscripts/analysis/core/$scriptName.py",
            "/pyscripts/analysis/data/$scriptName.py",
            "/pyscripts/analysis/utils/$scriptName.py",
            "/pyscripts/analysis/reporting/$scriptName.py"
        )

        var scriptStream: InputStream? = null
        var foundPath: String? = null

        for (path in possiblePaths) {
            scriptStream = javaClass.getResourceAsStream(path)
            if (scriptStream != null) {
                foundPath = path
                break
            }
        }

        val scriptContent = scriptStream?.bufferedReader()?.use { it.readText() }
            ?: throw IllegalArgumentException("Script not found: $scriptName (tried paths: ${possiblePaths.joinToString(", ")})")

        val scriptFile = File(tempFolder, "$scriptName.py").apply { createNewFile() }.toPath()
        MyConsoleLogger.logPrint("$scriptFile (from $foundPath)")

        scriptContent.toByteArray().let { Files.write(scriptFile, it, StandardOpenOption.WRITE) }
        MyConsoleLogger.logPrint("$scriptName created successfully")
    }
}