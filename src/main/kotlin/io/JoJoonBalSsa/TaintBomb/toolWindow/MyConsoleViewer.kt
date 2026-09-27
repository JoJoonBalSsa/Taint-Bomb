package io.JoJoonBalSsa.TaintBomb.toolWindow

import javax.swing.JTextArea

object MyConsoleViewer {
    private var console: JTextArea? = null

    fun setConsole(console: JTextArea) {
        MyConsoleViewer.console = console
    }

    fun println(message: String) {
        console?.let {
            it.append("$message\n")
            it.caretPosition = it.document.length
        }
    }

    fun clearConsole() {
        console?.text = ""
    }
}
