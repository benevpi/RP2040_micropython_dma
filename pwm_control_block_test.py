import rp2040_pio_dma
from machine import Pin
from rp2 import PIO, StateMachine, asm_pio
import uctypes
import array
import time

@asm_pio(sideset_init=PIO.OUT_LOW)
def pwm_prog():
    pull() . side(0)
    mov(x, osr) 
    mov(y, isr) 
    label("pwmloop")
    jmp(x_not_y, "skip")
    nop()         .side(1)
    label("skip")
    jmp(y_dec, "pwmloop")
    
pwm_sm = StateMachine(0, pwm_prog, freq=1000000, sideset_base=Pin(25))

max_count = 1000

pwm_sm.put(max_count)
pwm_sm.exec("pull()")
pwm_sm.exec("mov(isr, osr)")

pwm_sm.active(1)

DMA_CHAN = 0
NSAMPLES = max_count*2

pwm_dma = rp2040_pio_dma.PIO_DMA_Transfer(0, 0, 32, 0)
out_buff = array.array('L', ((x if (x<1000) else (2000-x)) for x in range(NSAMPLES)))


pwm_dma.start_transfer(out_buff)

#time.sleep(5)
#print("starting")

#(self, this_chan, that_chan, read_address, transfer_count, loops):
    
pwm_control = rp2040_pio_dma.DMA_Control_Block(1, pwm_dma, uctypes.addressof(out_buff), 2000, 3)

print("read address: ", pwm_control.get_read_address())
pwm_control.start_chain()
print("read address: ", pwm_control.get_read_address())
print("control busy: ", pwm_control.busy())

print("pwm busy: ", pwm_dma.busy())
