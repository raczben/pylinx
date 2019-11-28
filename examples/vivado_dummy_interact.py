import pylinx
import os

if __name__ == "__main__":
    
    vivado = pylinx.Vivado(executable='tclsh', args=[], prompt='% ')
    try:
        vivado.interact()
        while True:
            cmd = input()
            try:
                vivado.interact(cmd)
            except Exception as e:
                if cmd == 'exit':
                    break
                raise
            
    finally:
        vivado.exit()
        