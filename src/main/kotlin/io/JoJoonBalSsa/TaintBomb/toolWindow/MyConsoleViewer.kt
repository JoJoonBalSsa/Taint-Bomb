package io.JoJoonBalSsa.TaintBomb.toolWindow

import javax.swing.JTextArea

object MyConsoleViewer {
    private var console: JTextArea? = null

    fun setConsole(console: JTextArea) {
        MyConsoleViewer.console = console
    }

    fun println(message: String) {
        console?.append("$message\n")
    }

    fun clearConsole() {
        console?.text = ""
    }
}
