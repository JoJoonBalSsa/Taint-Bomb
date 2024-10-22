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

import javax.swing.BoxLayout
import javax.swing.Box
import java.awt.Component
import java.awt.Dimension
import javax.swing.JSeparator

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

        fun getContent() = JBPanel<JBPanel<*>>().apply {
            layout = BoxLayout(this, BoxLayout.Y_AXIS) // 수직 방향 레이아웃 설정

            val label1 = JBLabel(MyBundle.message("warningTitle")).apply {
                alignmentX = Component.CENTER_ALIGNMENT  // 중앙 정렬
            }
            val label2 = JBLabel(MyBundle.message("warning1")).apply {
                alignmentX = Component.CENTER_ALIGNMENT
            }
            val label3 = JBLabel(MyBundle.message("warning2")).apply {
                alignmentX = Component.CENTER_ALIGNMENT
            }

            val separator = JSeparator().apply {
                alignmentX = Component.CENTER_ALIGNMENT
                maximumSize = Dimension(200, 1)  // 구분선의 너비를 200픽셀로 제한
            }

            val consolePanel = JTextArea()
            val scrollPane = JBScrollPane(consolePanel).apply {
                alignmentX = Component.CENTER_ALIGNMENT
            }

            val button = JButton(MyBundle.message("obfuscateButton")).apply {
                alignmentX = Component.CENTER_ALIGNMENT
                addActionListener {
                    service.startTaintBomb()
                }
            }

            // 컴포넌트들 사이에 간격 추가
            add(Box.createVerticalStrut(10))
            add(label1)
            add(separator)
            add(Box.createVerticalStrut(5))
            add(label2)
            add(Box.createVerticalStrut(5))
            add(label3)
            add(Box.createVerticalStrut(10))
            add(button)
            add(Box.createVerticalStrut(10))

            MyConsoleViewer.setConsole(consolePanel)
            add(scrollPane)
        }
    }
}
