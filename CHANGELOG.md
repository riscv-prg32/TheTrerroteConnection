# Changelog

## Unreleased

The road from Pozzuoli now goes inland to Casoria before turning back to the sea: six legs instead of five,
Pozzuoli → Casoria, Casoria → Torregaveta, Torregaveta → Mondragone, Mondragone → Baia Domizia. A new view of
Casoria, painted like the others. Patrizia now waits by the road at the finish of the last leg. The cartridge has
about 1.5 KB left in its 64 KiB slot. Not yet run on the board.

## 1.0.1 (2026-10-30)

From the first run on a physical ESP32-C6. A button press landing on a frame with no game tick is no longer lost.
The frame rate in play rises from about 10 to about 17 fps: rows are sent as runs of colour, only the part of a row that
changed is sent, sky and road are flushed separately, and the ground no longer alternates in bands. The sound
has still not been heard, and the journey has not been completed on the board.

## 1.0.0 (2026-10-30)

First release: a tribute to il Grande Maestro Tony Tammaro. Five legs from the Villa Comunale of Naples to Baia
Domizia, by Ape Car and ferry; 24 watermelons that fly on when you stop and can be stolen; stalls, potholes,
tamarri, the mozzarella truck and Patrizia's five foods. Pseudo-3D road, row compositor on the 8-bit indexed
framebuffer, seven views painted after the real places, original soundtrack on eight SID-like voices. Validated
by the Cartridge Store's ingestion code; not yet run on ESP32-C6 hardware.
