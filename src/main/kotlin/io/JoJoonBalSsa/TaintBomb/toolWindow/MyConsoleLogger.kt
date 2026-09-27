package io.JoJoonBalSsa.TaintBomb.toolWindow

import javax.swing.JTextArea

object MyConsoleLogger {
    private var console: JTextArea? = null

    fun setConsole(console: JTextArea) {
        MyConsoleLogger.console = console
    }

    fun logPrint(message: String) {
        console?.let {
            it.append("$message\n")
            it.caretPosition = it.document.length
        }
    }

    fun clearConsole() {
        console?.text = ""
    }
}
