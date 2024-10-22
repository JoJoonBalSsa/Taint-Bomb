package io.JoJoonBalSsa.TaintBomb.toolWindow

import com.intellij.openapi.components.service
import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBPanel
import com.intellij.ui.components.JBScrollPane

import com.intellij.ui.content.ContentFactory
import io.JoJoonBalSsa.TaintBomb.MyBundle
import io.JoJoonBalSsa.TaintBomb.services.TaintBombService
import javax.swing.JButton
import javax.swing.JTextArea


class TaintBombFactory : ToolWindowFactory {
    
    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val taintBomb = TaintBomb(toolWindow)

        var content = ContentFactory.getInstance().createContent(taintBomb.getContent(), "Execute Tab", false)
        toolWindow.contentManager.addContent(content)

        val consolePanel = JTextArea()
        val scrollPane = JBScrollPane(consolePanel)
        content = ContentFactory.getInstance().createContent(scrollPane, "Log", false)
        MyConsoleLogger.setConsole(consolePanel)
        toolWindow.contentManager.addContent(content)
    }

    override fun shouldBeAvailable(project: Project) = true

    class TaintBomb(toolWindow: ToolWindow) {
        private val service = toolWindow.project.service<TaintBombService>()

//        private lateinit var mainJPanel: JPanel
//        private lateinit var label1 : JLabel
//        private lateinit var label2 : JLabel
//        private lateinit var label3 : JLabel
//
//        private var jButton = JButton()
//
//        private val consolePanel = JTextArea()
//        private var scrollPane = JScrollPane(consolePanel)
//
//
//        fun getContent() = mainJPanel.apply {
//            MyConsoleViewer.setConsole(consolePanel)
//            jButton.apply {
//                addActionListener{
//                    service.startTaintBomb()
//                }
//            }
//        }


        fun getContent() = JBPanel<JBPanel<*>>().apply {
            val label1 = JBLabel(MyBundle.message("obfuscateLabel1"))
            val label2 = JBLabel(MyBundle.message("obfuscateLabel2"))
            val label3 = JBLabel(MyBundle.message("obfuscateLabel3"))

            val consolePanel = JTextArea()
            val scrollPane = JBScrollPane(consolePanel)

            add(label1)
            add(label2)
            add(label3)
            add(JButton(MyBundle.message("obfuscate")).apply {
                addActionListener {
                    label1.text = MyBundle.message("obfuscateLabel1")
                    label2.text = MyBundle.message("obfuscateLabel2")
                    label3.text = MyBundle.message("obfuscateLabel3")
                    service.startTaintBomb()
                }
            })
            MyConsoleViewer.setConsole(consolePanel)
            add(scrollPane)
        }
    }
}
