package io.JoJoonBalSsa.TaintBomb

import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.fileEditor.OpenFileDescriptor
import com.intellij.testFramework.fixtures.BasePlatformTestCase
import io.JoJoonBalSsa.TaintBomb.services.TasksManager
import org.jetbrains.org.objectweb.asm.ClassReader
import org.jetbrains.org.objectweb.asm.ClassVisitor
import org.jetbrains.org.objectweb.asm.MethodVisitor
import org.jetbrains.org.objectweb.asm.Opcodes

class ReportEditorCompatibilityTest : BasePlatformTestCase() {
    fun testReportOpenerUsesDescriptorNavigation() {
        val calls = mutableListOf<String>()
        TasksManager::class.java.getResourceAsStream("TasksManager.class")!!.use { bytecode ->
            ClassReader(bytecode).accept(object : ClassVisitor(Opcodes.ASM9) {
                override fun visitMethod(
                    access: Int, name: String, descriptor: String, signature: String?, exceptions: Array<out String>?
                ): MethodVisitor = object : MethodVisitor(Opcodes.ASM9) {
                    override fun visitMethodInsn(opcode: Int, owner: String, name: String, descriptor: String, isInterface: Boolean) {
                        calls.add("$owner.$name")
                    }
                }
            }, ClassReader.SKIP_DEBUG or ClassReader.SKIP_FRAMES)
        }
        assertFalse(calls.contains("com/intellij/openapi/fileEditor/FileEditorManager.openTextEditor"))
        assertTrue(calls.contains("com/intellij/openapi/fileEditor/OpenFileDescriptor.navigateInEditor"))
    }

    fun testDescriptorNavigationOpensMarkdownReports() {
        val manager = FileEditorManager.getInstance(project)
        for (name in listOf("analysis_result.md", "llm_analysis_result.md")) {
            val report = myFixture.addFileToProject(name, "# Report\n$name\n")
            val file = report.virtualFile
            try {
                assertTrue(OpenFileDescriptor(project, file).navigateInEditor(project, true))
                assertTrue(manager.isFileOpen(file))
                assertEquals(report.text, manager.selectedTextEditor!!.document.text)
            } finally {
                manager.closeFile(file)
            }
        }
    }
}
