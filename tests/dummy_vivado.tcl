# This is a dummy TCL script, which emulates the behaviour of the Vivado.

global objects

proc get_property {propName objectName} {
    eval "global $objectName"
    set varname "${objectName}($propName)"
    set ret [subst $$varname]
    puts $ret
}

proc set_property {propName value objectName} {
    eval "global $objectName"
    eval "set ${objectName}($propName) $value"
}

