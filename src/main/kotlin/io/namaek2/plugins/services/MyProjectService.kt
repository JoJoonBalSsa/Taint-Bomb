package io.namaek2.plugins.services

import com.intellij.openapi.components.Service
import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.project.Project
import io.namaek2.plugins.MyBundle
import io.namaek2.plugins.toolWindow.MyConsoleLogger
import java.nio.file.*
import kotlin.io.path.*

@Service(Service.Level.PROJECT)
class MyProjectService(project: Project) {
    private val projectFolder = project.basePath
    init {
        thisLogger().info(MyBundle.message("projectService", project.name))
        // thisLogger().warn("Don't forget to remove all non-needed sample code files with their corresponding registration entries in `plugin.xml`.")
    }

    fun runPythonTask() {
        val javaFilesPath = projectFolder
        val outFolder = projectFolder + "/obfuscated_project_folder"

        if (javaFilesPath != null) {
            copyFolder(Path(javaFilesPath), Path(outFolder))
            RunPyScripts(javaFilesPath, outFolder)
        } else {
            thisLogger().error("Project path is null")
        }
    }

    private fun copyFolder(source: Path, destination: Path) {
        Files.walk(source).forEach { sourcePath ->
            if(!sourcePath.toString().contains("obfuscated_project_folder")) {
                val targetPath = destination.resolve(source.relativize(sourcePath))
                if (Files.isDirectory(sourcePath)) {
                    Files.createDirectories(targetPath)
                } else {
                    Files.copy(sourcePath, targetPath, StandardCopyOption.REPLACE_EXISTING)

                    MyConsoleLogger.println("Copied: $sourcePath")
                }
            }
        }
    }

}
