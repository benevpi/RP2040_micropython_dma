import rp2040_pio_dma
from machine import Pin
from rp2 import PIO, StateMachine, asm_pio
import array

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
NSAMPLES = max_count

pwm_dma = rp2040_pio_dma.PIO_DMA_Transfer(0, 0, 32, max_count)
out_buff = array.array('L', (x for x in range(NSAMPLES)))
pwm_dma.start_transfer(out_buff)


