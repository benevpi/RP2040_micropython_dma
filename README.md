# RP2040_micropython_dma
testing out some (stolen) DMA code for RP2040 Micropython. Heavy inspiration and some code from https://iosoft.blog/2021/10/26/pico-adc-dma/

This DMAs into a PIO TX FIFO. It *should* work on almost any PIO program. RX FIFOs can be made to work.

Now implemented control blocks so there's one DMA chain that can DMA into another to restart it (or start it at another point). This doesn't allow infinate looping (you'd need the interrupts for that).

Limitations
===========
As far as I can see, there's no way to access the DMA interrupts.
