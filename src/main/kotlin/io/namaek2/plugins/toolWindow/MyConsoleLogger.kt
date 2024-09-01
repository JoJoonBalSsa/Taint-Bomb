package io.namaek2.plugins.toolWindow

import javax.swing.JTextArea

object MyConsoleLogger {
    private var console: JTextArea? = null

    fun setConsole(console: JTextArea) {
        this.console = console
    }

    fun println(message: String) {
        console?.append("$message\n")
    }

    fun clearConsole() {
        console?.text = ""
    }
}
