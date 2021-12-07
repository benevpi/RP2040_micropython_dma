import rp2040_device
from machine import Pin
from rp2 import PIO, StateMachine, asm_pio
from time import sleep
import array
import uctypes

#setup PWM state machine

max_count = 1000

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

pwm_sm.put(max_count)
pwm_sm.exec("pull()")
pwm_sm.exec("mov(isr, osr)")

pwm_sm.active(0)

#setup DMA

DMA_CHAN = 0
NSAMPLES = max_count * 10
RATE = 100

dma_chan = rp2040_device.DMA_CHANS[DMA_CHAN]
dma = rp2040_device.DMA_DEVICE

out_buff = array.array('L', (int (x/10) for x in range(NSAMPLES)))

dma_chan.CTRL_TRIG_REG = 0 # blank the whole register
dma_chan.CTRL_TRIG.CHAIN_TO = DMA_CHAN # disable DMA chaining
#dma_chan.READ_ADDR_REG = uctypes.addressof(out_buff)
dma_chan.WRITE_ADDR_REG = rp2040_device.PIO0_TX0
dma_chan.TRANS_COUNT_REG = NSAMPLES
dma_chan.CTRL_TRIG.TREQ_SEL = rp2040_device.DREQ_PIO0_TX0
dma_chan.CTRL_TRIG.INCR_WRITE = 0
dma_chan.CTRL_TRIG.INCR_READ = 1


dma_chan.CTRL_TRIG.DATA_SIZE = rp2040_device.DMA_SIZE_WORD
#print(dma_chan.TRANS_COUNT_REG)

#dma_chan.CTRL_TRIG.EN = 1 # enable?
pwm_sm.active(1)

def start_transfer(buffer):
    print("busy before: ", dma_chan.CTRL_TRIG.BUSY)
    dma_chan.READ_ADDR_REG = uctypes.addressof(buffer)
    print("read Address: ", dma_chan.READ_ADDR_REG)
    print("buffer address: ", uctypes.addressof(out_buff))
    #pwm_sm.active(0)
    dma_chan.CTRL_TRIG.EN = 1
    #pwm_sm.active(1)
    print("busy after: ", dma_chan.CTRL_TRIG.BUSY)

def transfer_count():
    return dma_chan.TRANS_COUNT_REG

start_transfer(out_buff)
