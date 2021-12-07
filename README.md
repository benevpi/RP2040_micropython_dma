# RP2040_micropython_dma
testing out some (stolen) DMA code for RP2040 Micropython. Heavy inspiration and some code from https://iosoft.blog/2021/10/26/pico-adc-dma/

This DMAs into a PIO TX FIFO. It *should* work on almost any PIO program. RX FIFOs can be made to work.

Now implemented control blocks so there's one DMA chain that can DMA into another to restart it (or start it at another point). This doesn't allow infinate looping (you'd need the interrupts for that).

Actually, you can (sort of) do infinate transfers. You can reset the read address of the control channel while the other channel is running. Since this only has to happen within the window of the entire control chain, you likely have several seconds to reset it, so it ends up being very non-time specific. I've added the reset() method for this. Is it possible for this to go wrong? Maybe? If it reset the transfer address between the two transfers it'd get out of sync, but given that it's an unpaced transfer, it'd have to happen on the exact clock cyle. If you're not willing to take this risk, use C/C++

Limitations
===========
As far as I can see, there's no way to access the DMA interrupts.
