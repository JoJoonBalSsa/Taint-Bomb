package io.JoJoonBalSsa.TaintBomb.services

import com.intellij.openapi.components.Service
import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.project.Project
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.progress.Task
import io.JoJoonBalSsa.TaintBomb.MyBundle
import io.JoJoonBalSsa.TaintBomb.toolWindow.MyConsoleLogger
import io.JoJoonBalSsa.TaintBomb.toolWindow.MyConsoleViewer


@Service(Service.Level.PROJECT)
class TaintBombService(private val project: Project) {
    private val projectFolder = project.basePath

    init {
        thisLogger().info(MyBundle.message("projectService", project.name))
    }

    fun startTaintBomb() {
        val javaFilesPath = projectFolder
        val outFolder = "$projectFolder/obfuscated_project_folder"
        val tempFolder = "$projectFolder/temp_asdf_qwer"
        MyConsoleLogger.clearConsole()
        MyConsoleViewer.clearConsole()

        if (javaFilesPath != null) {
            ProgressManager.getInstance().run(object : Task.Backgroundable(project, "Running tasks...") {
                override fun run(indicator: ProgressIndicator) {
                    indicator.isIndeterminate = false

                    TasksManager(project, javaFilesPath, outFolder, tempFolder, indicator)
                }
            })
        } else {
            thisLogger().error("Project path is null")
        }
    }
}