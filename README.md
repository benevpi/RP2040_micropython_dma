# RP2040_micropython_dma
testing out some (stolen) DMA code for RP2040 Micropython. Heavy inspiration and some code from https://iosoft.blog/2021/10/26/pico-adc-dma/

This DMAs into a PIO TX FIFO. It *should* work on almost any PIO program. RX FIFOs can be made to work.

Limitations
===========
As far as I can see, there's no way to access the DMA interrupts.
