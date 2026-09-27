package io.JoJoonBalSsa.TaintBomb

import com.intellij.openapi.progress.EmptyProgressIndicator
import com.intellij.openapi.util.SystemInfo
import com.intellij.testFramework.fixtures.BasePlatformTestCase
import io.JoJoonBalSsa.TaintBomb.services.ManageBuild
import org.junit.Assume.assumeFalse
import java.io.File
import java.nio.file.Files

class ManageBuildTest : BasePlatformTestCase() {
    fun testGradleBuildUsesCopiedWrapperWithoutExecutableBit() {
        assumeFalse("Unix wrapper execution test", SystemInfo.isWindows)
        val root = Files.createTempDirectory("taint-bomb-wrapper-").toFile()
        try {
            val source = File(root, "original project").apply { mkdirs() }
            val output = File(root, "obfuscated project").apply { mkdirs() }
            File(source, "gradlew").writeText("exit 97\n")
            val wrapper = File(output, "gradlew").apply {
                writeText("printf '%s\\n' \"\$PWD\" \"\$@\" > wrapper-invocation.txt\n")
            }
            assertTrue(wrapper.setExecutable(false, false))
            assertFalse(wrapper.canExecute())

            ManageBuild(source.path, output.path, EmptyProgressIndicator())
                .runBuildManager(0.8, "gradle")

            val invocation = File(output, "wrapper-invocation.txt")
            assertTrue("The copied project wrapper was not executed", invocation.isFile)
            assertEquals(listOf(output.canonicalPath, "jar"), invocation.readLines())
            assertFalse("Do not chmod the copied wrapper", wrapper.canExecute())
            assertFalse(File(source, "wrapper-invocation.txt").exists())
        } finally {
            root.deleteRecursively()
        }
    }

    fun testWindowsGradleCommandConstructionUsesRelativeWrapper() {
        val root = Files.createTempDirectory("taint-bomb-windows-command-").toFile()
        try {
            val source = File(root, "original project").apply { mkdirs() }
            val output = File(root, "obfuscated & project").apply { mkdirs() }
            val wrapper = File(output, "gradlew.bat").apply { writeText("@echo off\r\n") }
            val manageBuild = ManageBuild(source.path, output.path, EmptyProgressIndicator())

            // Command construction only; this does not execute cmd.exe on Linux.
            val wrapperCommand = manageBuild.gradleProcessBuilder("windows", "assembleRelease")
            assertEquals(
                listOf("cmd.exe", "/d", "/c", ".\\gradlew.bat", "assembleRelease"),
                wrapperCommand.command()
            )
            assertEquals(output.canonicalFile, wrapperCommand.directory().canonicalFile)

            assertTrue(wrapper.delete())
            val fallbackCommand = manageBuild.gradleProcessBuilder("windows", "jar")
            assertEquals(listOf("gradle.bat", "jar"), fallbackCommand.command())
            assertEquals(output.canonicalFile, fallbackCommand.directory().canonicalFile)
        } finally {
            root.deleteRecursively()
        }
    }
}
