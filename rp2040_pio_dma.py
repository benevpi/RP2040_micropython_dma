import rp2040_device
from machine import Pin
from rp2 import PIO, StateMachine, asm_pio
from time import sleep
import array
import uctypes
from uctypes import BF_POS, BF_LEN, UINT32, BFUINT32, struct

GPIO_BASE       = 0x40014000
GPIO_CHAN_WIDTH = 0x08
GPIO_PIN_COUNT  = 30
PAD_BASE        = 0x4001c000
PAD_PIN_WIDTH   = 0x04
ADC_BASE        = 0x4004c000
PIO0_BASE       = 0x50200000
PIO1_BASE       = 0x50300000
DMA_BASE        = 0x50000000
DMA_CHAN_WIDTH  = 0x40
DMA_CHAN_COUNT  = 12

DMA_SIZE_BYTE = 0x0
DMA_SIZE_HALFWORD = 0x1
DMA_SIZE_WORD = 0x2

# DMA: RP2040 datasheet 2.5.7
DMA_CTRL_TRIG_FIELDS = {
    "AHB_ERROR":   31<<BF_POS | 1<<BF_LEN | BFUINT32,
    "READ_ERROR":  30<<BF_POS | 1<<BF_LEN | BFUINT32,
    "WRITE_ERROR": 29<<BF_POS | 1<<BF_LEN | BFUINT32,
    "BUSY":        24<<BF_POS | 1<<BF_LEN | BFUINT32,
    "SNIFF_EN":    23<<BF_POS | 1<<BF_LEN | BFUINT32,
    "BSWAP":       22<<BF_POS | 1<<BF_LEN | BFUINT32,
    "IRQ_QUIET":   21<<BF_POS | 1<<BF_LEN | BFUINT32,
    "TREQ_SEL":    15<<BF_POS | 6<<BF_LEN | BFUINT32,
    "CHAIN_TO":    11<<BF_POS | 4<<BF_LEN | BFUINT32,
    "RING_SEL":    10<<BF_POS | 1<<BF_LEN | BFUINT32,
    "RING_SIZE":    6<<BF_POS | 4<<BF_LEN | BFUINT32,
    "INCR_WRITE":   5<<BF_POS | 1<<BF_LEN | BFUINT32,
    "INCR_READ":    4<<BF_POS | 1<<BF_LEN | BFUINT32,
    "DATA_SIZE":    2<<BF_POS | 2<<BF_LEN | BFUINT32,
    "HIGH_PRIORITY":1<<BF_POS | 1<<BF_LEN | BFUINT32,
    "EN":           0<<BF_POS | 1<<BF_LEN | BFUINT32
}
# Channel-specific DMA registers
DMA_CHAN_REGS = {
    "READ_ADDR_REG":       0x00|UINT32,
    "WRITE_ADDR_REG":      0x04|UINT32,
    "TRANS_COUNT_REG":     0x08|UINT32,
    "CTRL_TRIG_REG":       0x0c|UINT32,
    "CTRL_TRIG":          (0x0c,DMA_CTRL_TRIG_FIELDS)
}

# General DMA registers
DMA_REGS = {
    "INTR":               0x400|UINT32,
    "INTE0":              0x404|UINT32,
    "INTF0":              0x408|UINT32,
    "INTS0":              0x40c|UINT32,
    "INTE1":              0x414|UINT32,
    "INTF1":              0x418|UINT32,
    "INTS1":              0x41c|UINT32,
    "TIMER0":             0x420|UINT32,
    "TIMER1":             0x424|UINT32,
    "TIMER2":             0x428|UINT32,
    "TIMER3":             0x42c|UINT32,
    "MULTI_CHAN_TRIGGER": 0x430|UINT32,
    "SNIFF_CTRL":         0x434|UINT32,
    "SNIFF_DATA":         0x438|UINT32,
    "FIFO_LEVELS":        0x440|UINT32,
    "CHAN_ABORT":         0x444|UINT32
}

DREQ_PIO0_TX0, DREQ_PIO0_RX0, DREQ_PIO1_TX0 = 0, 4, 8
DREQ_PIO1_RX0, DREQ_SPI0_TX,  DREQ_SPI0_RX  = 12, 16, 17
DREQ_SPI1_TX,  DREQ_SPI1_RX,  DREQ_UART0_TX = 18, 19, 20
DREQ_UART0_RX, DREQ_UART1_TX, DREQ_UART1_RX = 21, 22, 23
DREQ_I2C0_TX,  DREQ_I2C0_RX,  DREQ_I2C1_TX  = 32, 33, 34
DREQ_I2C1_RX,  DREQ_ADC                     = 35, 36



DMA_CHANS = [struct(DMA_BASE + n*DMA_CHAN_WIDTH, DMA_CHAN_REGS) for n in range(0,DMA_CHAN_COUNT)]
DMA_DEVICE = struct(DMA_BASE, DMA_REGS)


GPIO_FUNC_SPI, GPIO_FUNC_UART, GPIO_FUNC_I2C = 1, 2, 3
GPIO_FUNC_PWM, GPIO_FUNC_SIO, GPIO_FUNC_PIO0 = 4, 5, 6
GPIO_FUNC_NULL = 0x1f

DMA_CH0_AL3_TRANS_COUNT = DMA_BASE + 0x38


class PIO_DMA_Transfer():
    def __init__(self, dma_channel, sm_num, block_size, transfer_count):
        self.dma_chan = DMA_CHANS[dma_channel]
        self.channel_number = dma_channel
       
        if (sm_num >= 0 and sm_num < 4):
            self.dma_chan.WRITE_ADDR_REG = PIO0_BASE + 0x10 + sm_num *4
            self.dma_chan.CTRL_TRIG.TREQ_SEL = sm_num
        elif (sm_num < 8):
            self.dma_chan.WRITE_ADDR_REG = PIO1_BASE + 0x10 + (sm_num-4) *4
            self.dma_chan.CTRL_TRIG.TREQ_SEL = sm_num + 4
        
        if (block_size == 8):
            self.dma_chan.CTRL_TRIG.DATA_SIZE = DMA_SIZE_BYTE
        if (block_size == 16):
            self.dma_chan.CTRL_TRIG.DATA_SIZE = DMA_SIZE_HALFWORD
        if (block_size == 32):
            self.dma_chan.CTRL_TRIG.DATA_SIZE = DMA_SIZE_WORD
            
        self.dma_chan.TRANS_COUNT_REG = transfer_count
        
        #Do I just always want these?
        self.dma_chan.CTRL_TRIG.INCR_WRITE = 0
        self.dma_chan.CTRL_TRIG.INCR_READ = 1
            
    def start_transfer(self, buffer):
        self.dma_chan.READ_ADDR_REG = uctypes.addressof(buffer)
        self.dma_chan.CTRL_TRIG.EN = 1

    def transfer_count(self):
        return self.dma_chan.TRANS_COUNT_REG
    
    def busy(self):
        if self.dma_chan.CTRL_TRIG.DATA_SIZE == 1:
            return True
        else:
            return False
        
    def abort_transfer(self):
        pass
    
    def chain_to(self, channel):
        self.dma_chan.CTRL_TRIG.CHAIN_TO = channel
        
    def get_number(self):
        return self.channel_number
        


    
#looping transfers
#note -- see datasheet 2.5.7
#location of registers is -- AL3 transcount / read address trigger.
#Writing to these (from one DMA channel) will re-trigger a second DMA channel
#need to set write ring.
#could also set read ring?
#out_buff = array.array('L', ((x if (x<1000) else (2000-x)) for x in range(NSAMPLES)))

class DMA_Control_Block:
    def __init__(self, this_chan, that_chan, read_address, transfer_count, loops):
        self.dma_chan = DMA_CHANS[this_chan]
        
        #note -- need to set this up to get the right location
        #but for now just always control channel 0
        self.dma_chan.WRITE_ADDR_REG = DMA_CH0_AL3_TRANS_COUNT
        self.dma_chan.CTRL_TRIG.DATA_SIZE = DMA_SIZE_WORD
        self.dma_chan.TRANS_COUNT_REG = 2 # two transfers. One is the count, one is the read_address.
        #Then pauses until the other channel chains back to this.
        
        self.buffer = array.array('L', (x for x in range(2*loops)))
        for x in range(loops):
            self.buffer[2*x] = transfer_count
            self.buffer[2*x+1] = read_address
            
        self.start_address = uctypes.addressof(self.buffer)
        #set up read ring
        that_chan.chain_to(this_chan)
        
        self.dma_chan.CTRL_TRIG.INCR_WRITE = 1
        self.dma_chan.CTRL_TRIG.INCR_READ = 1
        
        self.dma_chan.CTRL_TRIG.RING_SEL = 1
        self.dma_chan.CTRL_TRIG.RING_SIZE = 3 # 1u<<3 bytes / 8 bytes
        self.dma_chan.CTRL_TRIG.TREQ_SEL = 0x3f # unpaced transfer
        
    def start_chain(self):
        self.dma_chan.READ_ADDR_REG = self.start_address
        self.dma_chan.CTRL_TRIG.EN = 1
        
    def transfer_count(self):
        return self.dma_chan.TRANS_COUNT_REG
    
    def get_read_address(self):
        return self.dma_chan.READ_ADDR_REG
    
    def busy(self):
        if self.dma_chan.CTRL_TRIG.DATA_SIZE == 1:
            return True
        else:
            return False

