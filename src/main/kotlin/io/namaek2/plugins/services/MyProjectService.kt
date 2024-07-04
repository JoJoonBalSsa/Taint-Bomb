package io.namaek2.plugins.services

import com.intellij.openapi.components.Service
import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.project.Project
import io.namaek2.plugins.MyBundle

@Service(Service.Level.PROJECT)
class MyProjectService(project: Project) {
    private val projectFolder = project.basePath
    init {
        thisLogger().info(MyBundle.message("projectService", project.name))
        thisLogger().warn("Don't forget to remove all non-needed sample code files with their corresponding registration entries in `plugin.xml`.")
    }

    fun runPythonTask() {
        val javaFilesPath = projectFolder
        val outFolder = projectFolder
        val pythonScript = RunPyScripts()
        if (javaFilesPath != null) {
            if (outFolder != null) {
                pythonScript.runPythonScript(javaFilesPath, outFolder)
            } else {
                thisLogger().error(MyBundle.message("noOutputFolder"))
            }
        }
    }
}
