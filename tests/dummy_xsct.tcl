# This is a dummy TCL script, which emulates the behaviour of the XSCT_server.

# Based on https://wiki.tcl-lang.org/page/The+simplest+possible+socket+demonstration

set run 1

proc accept {chan addr port} {          ;# Make a proc to accept connections
    while {1} {
        set cmd [gets $chan]
        puts "$addr:$port says $cmd"    ;# Receive a string
        if {[catch {set ans [eval $cmd]} errmsg]} {
            set ans "error $ans"
        } else {
            set ans "okay $ans"
        }
        after 100
        puts $chan $ans                 ;# Send the answer back
        flush $chan
        if {$cmd == "exit"} {
            close $chan                 ;# Close the socket (automatically flushes)
            set run 0
            break
        }
    }
}                                        ;#
socket -server accept 4567               ;# Create a server socket
vwait run
