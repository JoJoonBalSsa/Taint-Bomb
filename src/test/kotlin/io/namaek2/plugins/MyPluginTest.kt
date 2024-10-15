package io.namaek2.plugins


import com.intellij.openapi.components.service
import com.intellij.openapi.project.Project
import com.intellij.testFramework.TestDataPath
import com.intellij.testFramework.fixtures.BasePlatformTestCase
import io.namaek2.plugins.services.TaintBombService

@TestDataPath("\$CONTENT_ROOT/src/test/testData")
class MyPluginTest : BasePlatformTestCase() {
    fun testProjectService() {
        val projectService = project.service<TaintBombService>()
        projectService.startTaintBomb(Project)
      }

    override fun getTestDataPath() = "src/test/testData/rename"
}
