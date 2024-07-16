package io.namaek2.plugins


import com.intellij.openapi.components.service
import com.intellij.testFramework.TestDataPath
import com.intellij.testFramework.fixtures.BasePlatformTestCase
import io.namaek2.plugins.services.MyProjectService

@TestDataPath("\$CONTENT_ROOT/src/test/testData")
class MyPluginTest : BasePlatformTestCase() {
    fun testProjectService() {
        val projectService = project.service<MyProjectService>()
        projectService.runPythonTask()
      }

    override fun getTestDataPath() = "src/test/testData/rename"
}
