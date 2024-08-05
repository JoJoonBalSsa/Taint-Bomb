package io.namaek2.plugins.toolWindow

import com.intellij.openapi.components.service
import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBPanel
import com.intellij.ui.content.ContentFactory
import io.namaek2.plugins.MyBundle
import io.namaek2.plugins.services.MyProjectService
import javax.swing.JButton


class TaintBombFactory : ToolWindowFactory {
    
    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val taintBomb = TaintBomb(toolWindow)
        val content = ContentFactory.getInstance().createContent(taintBomb.getContent(), null, false)
        toolWindow.contentManager.addContent(content)
    }

    override fun shouldBeAvailable(project: Project) = true

    class TaintBomb(toolWindow: ToolWindow) {

        private val service = toolWindow.project.service<MyProjectService>()

        fun getContent() = JBPanel<JBPanel<*>>().apply {
            val label = JBLabel(MyBundle.message("obfuscateLabel"))
            add(label)
            add(JButton(MyBundle.message("obfuscate")).apply {
                addActionListener {
                    label.text = MyBundle.message("obfuscateLabel", service.runPythonTask())
                }
            })
        }
    }
}
