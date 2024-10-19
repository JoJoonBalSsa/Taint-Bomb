package io.namaek2.plugins.services

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.fileEditor.OpenFileDescriptor
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.LocalFileSystem
import io.namaek2.plugins.toolWindow.MyConsoleLogger
import io.namaek2.plugins.toolWindow.MyConsoleViewer
import java.io.*


class TasksManager(private val project : Project, private val javaFilesPath: String, private var outFolder : String, private var tempFolder : String, private val indicator: ProgressIndicator) {
    init {
        val preTask = ManagePreTask(javaFilesPath, outFolder, tempFolder, indicator)
        val venvPath = preTask.getVenvPath()
        val manageHash = preTask.getManageHash()

        val manageBuild = ManageBuild(javaFilesPath, outFolder, indicator)
        val buildManager = manageBuild.checkBuildManager()

        ManageObfuscate(javaFilesPath, outFolder, tempFolder, manageHash, venvPath, preTask.getOS(), indicator)
        manageBuild.runBuildManager(0.8, buildManager)

        openFileInEditorAsync(project, outFolder)

        indicator.text = "Deleting temp directory..."
        preTask.deleteDirectory(File(tempFolder), 0.95)
    }

    fun openFileInEditorAsync(project: Project, outFolder: String) {
        ApplicationManager.getApplication().invokeLater {
            val filePath = "$outFolder/analysis_result.md"
            val file = LocalFileSystem.getInstance().findFileByPath(filePath)

            if (file != null) {
                file.refresh(false, false) // Refresh the VFS
                if (file.exists()) {
                    try {
                        FileEditorManager.getInstance(project).openTextEditor(
                            OpenFileDescriptor(project, file),
                            true // requestFocus
                        )
                        MyConsoleLogger.logPrint("File opened successfully: $filePath")
                    } catch (e: Exception) {
                        MyConsoleLogger.logPrint("Error opening file: ${e.message}")
                    }
                } else {
                    MyConsoleLogger.logPrint("File does not exist: $filePath")
                }
            } else {
                MyConsoleLogger.logPrint("File not found: $filePath")
            }
        }
    }

}
