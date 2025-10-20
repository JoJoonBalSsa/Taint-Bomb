package io.JoJoonBalSsa.TaintBomb.settings

import com.intellij.openapi.components.*
import com.intellij.util.xmlb.XmlSerializerUtil

@State(
    name = "TaintBombSettings",
    storages = [Storage("taintBombSettings.xml")]
)
@Service
class TaintBombSettings : PersistentStateComponent<TaintBombSettings> {
    // var enableRemoveComments: Boolean = true
    var enableStringEncryption: Boolean = true
    var enableMethodSplitting: Boolean = true
    var enableInsertDummyCode: Boolean = true
    var enableOperatorObfuscation: Boolean = true
    var enableIdentifierObfuscation: Boolean = true

    var apiKey: String = ""

    companion object {
        fun getInstance(): TaintBombSettings {
            return service<TaintBombSettings>()
        }
    }

    override fun getState(): TaintBombSettings = this

    override fun loadState(state: TaintBombSettings) {
        XmlSerializerUtil.copyBean(state, this)
    }
}
