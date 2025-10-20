package io.JoJoonBalSsa.TaintBomb.services

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.fileEditor.OpenFileDescriptor
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.LocalFileSystem
import io.JoJoonBalSsa.TaintBomb.toolWindow.MyConsoleLogger
import io.JoJoonBalSsa.TaintBomb.toolWindow.MyConsoleViewer
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

        openFileInEditorAsync(project, outFolder, "/analysis_result.md")
        openFileInEditorAsync(project, outFolder, "/llm_analysis_result.md")

        indicator.text = "Deleting temp directory..."
        preTask.deleteDirectory(File(tempFolder), 0.95)
    }

    fun openFileInEditorAsync(project: Project, outFolder: String, fileName: String) {
        ApplicationManager.getApplication().invokeLater {
            val filePath = "$outFolder$fileName"

            var file = LocalFileSystem.getInstance().findFileByPath(filePath)

            if (file == null) {
                // 파일이 null인 경우 VFS를 새로고침하고 다시 시도합니다.
                LocalFileSystem.getInstance().refreshAndFindFileByPath(filePath)?.let {
                    file = it
                    MyConsoleLogger.logPrint("File found after refresh: $filePath")
                }
            }

            if (file != null) {
                file!!.refresh(false, false)
                if (file!!.exists()) {
                    try {
                        FileEditorManager.getInstance(project).openTextEditor(
                            OpenFileDescriptor(project, file!!),
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