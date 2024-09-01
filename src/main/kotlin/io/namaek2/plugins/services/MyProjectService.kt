package io.namaek2.plugins.services

import com.intellij.openapi.components.Service
import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.project.Project
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.progress.Task
import io.namaek2.plugins.MyBundle
import io.namaek2.plugins.toolWindow.MyConsoleLogger
import java.nio.file.*
import kotlin.io.path.*

@Service(Service.Level.PROJECT)
class MyProjectService(private val project: Project) {
    private val projectFolder = project.basePath

    init {
        thisLogger().info(MyBundle.message("projectService", project.name))
    }

    fun runPythonTask() {
        val javaFilesPath = projectFolder
        val outFolder = projectFolder + "/obfuscated_project_folder"

        MyConsoleLogger.clearConsole()

        if (javaFilesPath != null) {
            ProgressManager.getInstance().run(object : Task.Backgroundable(project, "Running Python Task") {
                override fun run(indicator: ProgressIndicator) {
                    indicator.isIndeterminate = false

                    // Copying folder
                    indicator.text = "Copying project folder..."
                    indicator.fraction = 0.0
                    copyFolder(Path(javaFilesPath), Path(outFolder), indicator)

                    RunPyScripts(javaFilesPath, outFolder, indicator)
                }
            })
        } else {
            thisLogger().error("Project path is null")
        }
    }

    private fun copyFolder(source: Path, destination: Path, indicator: ProgressIndicator) {
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
                    indicator.fraction = 0.5 * (copiedFiles.toDouble() / totalFiles)
                    indicator.text = "Copying files... (${copiedFiles}/${totalFiles})"
                }
            }
        }
    }
}