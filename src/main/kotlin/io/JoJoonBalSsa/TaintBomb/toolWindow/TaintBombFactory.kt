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
import io.JoJoonBalSsa.TaintBomb.settings.TaintBombSettings
import javax.swing.JButton
import javax.swing.JTextArea

import javax.swing.BoxLayout
import javax.swing.Box
import java.awt.Component
import java.awt.Dimension
import javax.swing.BorderFactory
import javax.swing.JCheckBox
import javax.swing.JLabel
import javax.swing.JSeparator
import javax.swing.JTextField

class TaintBombFactory : ToolWindowFactory {

    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val taintBomb = TaintBomb(toolWindow)

        // Execute Tab
        var content = ContentFactory.getInstance().createContent(taintBomb.getContent(), "Execution", false)
        toolWindow.contentManager.addContent(content)

        // Configuration Tab
        val configPanel = ConfigurationPanel()
        content = ContentFactory.getInstance().createContent(configPanel.getContent(), "Configuration", false)
        toolWindow.contentManager.addContent(content)

        // Log Tab
        val consolePanel = JTextArea()
        val scrollPane = JBScrollPane(consolePanel)
        content = ContentFactory.getInstance().createContent(scrollPane, "Logs", false)
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

    class ConfigurationPanel {
        private val settings = TaintBombSettings.getInstance()

        fun getContent() = JBPanel<JBPanel<*>>().apply {
            layout = BoxLayout(this, BoxLayout.Y_AXIS)

            val apiKeyLabel = JLabel("API Key:").apply {
                alignmentX = Component.LEFT_ALIGNMENT
            }

            val apiKeyField = JTextField(settings.apiKey).apply {
                alignmentX = Component.LEFT_ALIGNMENT
                maximumSize = Dimension(Int.MAX_VALUE, preferredSize.height) // 가로로 늘어나도록
                toolTipText = "Enter API key here"
                // 입력 시 설정값 업데이트
                document.addDocumentListener(object : javax.swing.event.DocumentListener {
                    override fun insertUpdate(e: javax.swing.event.DocumentEvent) = update()
                    override fun removeUpdate(e: javax.swing.event.DocumentEvent) = update()
                    override fun changedUpdate(e: javax.swing.event.DocumentEvent) = update()
                    private fun update() {
                        settings.apiKey = text
                    }
                })
            }

            val titleLabel = JBLabel("Obfuscation Features Configuration").apply {
                alignmentX = Component.CENTER_ALIGNMENT
                font = font.deriveFont(16f)
            }

            val separator = JSeparator().apply {
                alignmentX = Component.CENTER_ALIGNMENT
                maximumSize = Dimension(300, 1)
            }

//            val removeCommentsCheckBox = JCheckBox("Remove Comments", settings.enableRemoveComments).apply {
//                alignmentX = Component.LEFT_ALIGNMENT
//                addActionListener {
//                    settings.enableRemoveComments = isSelected
//                }
//            }

            val stringEncryptionCheckBox = JCheckBox("String Encryption", settings.enableStringEncryption).apply {
                alignmentX = Component.LEFT_ALIGNMENT
                addActionListener {
                    settings.enableStringEncryption = isSelected
                }
            }

            val identifierObfuscationCheckBox = JCheckBox("Identifier Obfuscation", settings.enableIdentifierObfuscation).apply {
                alignmentX = Component.LEFT_ALIGNMENT
                addActionListener {
                    settings.enableIdentifierObfuscation = isSelected
                }
            }

            val operatorObfuscationCheckBox = JCheckBox("Operator Obfuscation", settings.enableOperatorObfuscation).apply {
                alignmentX = Component.LEFT_ALIGNMENT
                addActionListener {
                    settings.enableOperatorObfuscation = isSelected
                }
            }

            val methodSplittingCheckBox = JCheckBox("Method Splitting", settings.enableMethodSplitting).apply {
                alignmentX = Component.LEFT_ALIGNMENT
                addActionListener {
                    settings.enableMethodSplitting = isSelected
                }
            }

            val insertDummyCodeCheckBox = JCheckBox("Inserting Dummy codes", settings.enableInsertDummyCode).apply {
                alignmentX = Component.LEFT_ALIGNMENT
                addActionListener {
                    settings.enableInsertDummyCode = isSelected
                }
            }

            val descriptionArea = JTextArea().apply {
                text = """
                    checkbox explanation will be added later.
                """.trimIndent()
                isEditable = false
                lineWrap = true
                wrapStyleWord = true
                background = parent?.background
                alignmentX = Component.LEFT_ALIGNMENT
            }

            val descriptionScrollPane = JBScrollPane(descriptionArea).apply {
                preferredSize = Dimension(400, 150)
                alignmentX = Component.LEFT_ALIGNMENT
            }

            add(Box.createVerticalStrut(10))
            add(apiKeyLabel)
            add(Box.createVerticalStrut(5))
            add(apiKeyField)
            add(Box.createVerticalStrut(10))

            add(Box.createVerticalStrut(15))
            add(titleLabel)
            add(Box.createVerticalStrut(10))
            add(separator)
            add(Box.createVerticalStrut(15))
//            add(removeCommentsCheckBox)
//            add(Box.createVerticalStrut(8))
            add(stringEncryptionCheckBox)
            add(Box.createVerticalStrut(8))
            add(identifierObfuscationCheckBox)
            add(Box.createVerticalStrut(8))
            add(operatorObfuscationCheckBox)
            add(Box.createVerticalStrut(8))
            add(methodSplittingCheckBox)
            add(Box.createVerticalStrut(8))
            add(insertDummyCodeCheckBox)
            add(Box.createVerticalStrut(15))
            add(descriptionScrollPane)
            add(Box.createVerticalGlue())

            border = BorderFactory.createEmptyBorder(10, 20, 10, 20)
        }
    }
}
