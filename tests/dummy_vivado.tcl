# This is a dummy TCL script, which emulates the behaviour of the XSCT_server.

# Based on https://wiki.tcl-lang.org/page/The+simplest+possible+socket+demonstration

set run 1

proc do {cmd} {          ;# Do a command
    puts [eval $cmd]
    if {$cmd == "exit"} {
        set run 0
        break
    }
}

proc main { } {
    while {$run} {
        gets stdin cmd
        do $cmd
    }
}

main