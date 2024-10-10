package io.namaek2.plugins.services

import com.intellij.openapi.progress.ProgressIndicator
import java.io.*


class TasksManager(private val javaFilesPath: String, private var outFolder : String, private var tempFolder : String, private val indicator: ProgressIndicator) {
    init {
        val preTask = ManagePreTask(javaFilesPath, outFolder, tempFolder, indicator)
        val venvPath = preTask.getVenvPath()
        val manageHash = preTask.getManageHash()

        val manageBuild = ManageBuild(javaFilesPath, outFolder, indicator)
        // manageBuild.checkGradleVersion()

        ManageObfuscate(javaFilesPath, outFolder, tempFolder, manageHash, venvPath, preTask.getOS(), indicator)
        manageBuild.runGradle(0.8)


        indicator.text = "Deleting temp directory..."
        preTask.deleteDirectory(File(tempFolder), 0.95)
    }
}