# Changelog

## 1.1.0 (2026-11-04)

The road from Pozzuoli now goes inland to Casoria before turning back to the sea: six legs instead of five,
Pozzuoli → Casoria, Casoria → Torregaveta, Torregaveta → Mondragone, Mondragone → Baia Domizia. A new view of
Casoria, painted like the others. Patrizia now waits by the road at the finish of the last leg.

The cartridge now uses PRG32's 128 KiB profile (package 96,155 bytes, measured; it no longer fits the 64 KiB profile) and every asset was redone, to make the road a
Neapolitan street and not another arcade racer:

- **The street.** Basalt setts, asphalt and worn asphalt by section; pavements instead of rumble strips; zebra
  crossings in town; double-parked cars with their hazards on, which traffic steers round; washing lines across the
  lane, shrines, bins. Each leg ends at its town's road sign.
- **Stalls need a stop.** Pull over on the stall's side and stop; the melons are handed over one at a time. Driving
  past loses the stall. Time limits are 2 to 11 s longer.
- **A delivery docket** at the top: time, melons, takings and the route.
- **Art.** All sprites redrawn with outlines and shading; views with 64 colours instead of 32, softer skies, sea foam,
  shaded houses.
- **Sound.** The accompaniment varies through each song: bass approaches, walking bass, fills, held chords. New
  sounds for a melon sold and a stall missed.

Run briefly on the board (firmware `82b8925`, 128 KiB profile): menus and leg 1 work, about 18.5 fps driving
(median, measured). The rest of the journey has not been driven on the board. The Store splash and icon are new: a
QEMU frame of the attract mode and the redrawn Trerrote.

The bundle's cartridge was then run on the board (firmware `c53c491-dirty`): menus, pause, leg 1 up to the Molo
Beverello and the missed-ferry screen work; about 22 fps driving (median, measured).

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
