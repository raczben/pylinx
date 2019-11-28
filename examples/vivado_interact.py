import pylinx
import os

if __name__ == "__main__":
    
    linux_vivado_path = "~/Xilinx/Vivado/2017.4/bin/vivado"
    linux_vivado_path = os.path.expanduser(linux_vivado_path)
    
    vivado = pylinx.Vivado(executable=linux_vivado_path)
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
        