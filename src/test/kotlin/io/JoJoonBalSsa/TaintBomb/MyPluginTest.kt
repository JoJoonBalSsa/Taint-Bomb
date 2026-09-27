package io.JoJoonBalSsa.TaintBomb

import com.intellij.openapi.components.service
import com.intellij.testFramework.fixtures.BasePlatformTestCase
import io.JoJoonBalSsa.TaintBomb.services.TaintBombService

class MyPluginTest : BasePlatformTestCase() {
    fun testProjectService() {
        assertSame(project.service<TaintBombService>(), project.service<TaintBombService>())
    }

    fun testBundleMessages() {
        assertEquals("Project service: sample", MyBundle.message("projectService", "sample"))
        assertEquals("Project service: sample", MyBundle.messagePointer("projectService", "sample").get())
        assertEquals("click here to obfuscate", MyBundle.message("obfuscateButton"))
    }
}
