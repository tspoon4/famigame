.include "scrolling.inc"

.importzp ppu_batch_len
.import ppu_batch
.importzp scroll_x
.importzp scroll_y
.importzp scroll_nmt
.import mapper_mirror

.export scroll_state
.export scroll_event
.export scroll_event_param
.export scroll_init
.export scroll_update


.segment "ZEROPAGE"
__scroll_fill_src: .res 2 ; Has to be in ZEROPAGE (indirect addressing)

.segment "BSS"
scroll_state: .res 1
scroll_event: .res 1
scroll_event_param: .res 2
__scroll_fill_ppu: .res 2
__scroll_fill_cnt: .res 1
__scroll_tick_incx: .res 1
__scroll_tick_incy: .res 1
__scroll_tick_cnt: .res 1
__scroll_tick_nmt: .res 1


.segment "CODE"
; Function that initializes the scrolling system
scroll_init:

	ldx #$0
	stx scroll_state
	stx scroll_event
	rts


; Function that updates the scrolling system
scroll_update:

	ldx scroll_state
	cpx #SCROLL_IDLE
	beq :+
		jmp @end_idle	; Jump needed because of long condition
		:
		ldx scroll_event
		cpx #SCROLL_FILL
		bne :++
			stx scroll_state
			lda scroll_event_param
			sta __scroll_fill_src
			lda scroll_event_param+1
			sta __scroll_fill_src+1
			lda #16
			sta __scroll_fill_cnt
			lda #$0
			sta __scroll_fill_ppu
			lda #$20
			ldx scroll_nmt
			bne :+
				lda #$24
			:
			sta __scroll_fill_ppu+1
		:
		ldx scroll_event
		cpx #SCROLL_TICK
		beq :+
			jmp @end_idle
			:
			stx scroll_state
			ldy scroll_event_param
			cpy #SCROLL_LEFT
			bne :+
				lda #16
				sta __scroll_tick_cnt
				lda #$F0				; $F0 is -16
				sta __scroll_tick_incx
				lda #0
				sta __scroll_tick_incy
				lda scroll_nmt
				eor #$01
				sta scroll_nmt
				sta __scroll_tick_nmt
			:
			cpy #SCROLL_RIGHT
			bne :+
				lda #16
				sta __scroll_tick_cnt
				sta __scroll_tick_incx
				lda #0
				sta __scroll_tick_incy
				lda scroll_nmt
				eor #$01
				sta __scroll_tick_nmt
			:
			cpy #SCROLL_UP
			bne :+
				lda #15
				sta __scroll_tick_cnt
				lda #0
				sta __scroll_tick_incx
				lda #$F1				; $F1 is -15
				sta __scroll_tick_incy
				lda #240
				sta scroll_y
				lda scroll_nmt
				pha
				eor #$01
				sta __scroll_tick_nmt
				pla
				asl
				eor #$02
				sta scroll_nmt
				lda #$80
				sta mapper_mirror
			:
			cpy #SCROLL_DOWN
			bne :+
				lda #15
				sta __scroll_tick_cnt
				sta __scroll_tick_incy
				lda #0
				sta __scroll_tick_incx
				lda scroll_nmt
				pha
				eor #$01
				sta __scroll_tick_nmt
				pla
				asl
				sta scroll_nmt
				lda #$80
				sta mapper_mirror
			:
	@end_idle:

	ldx scroll_state
	cpx #SCROLL_FILL
	bne @end_fill
		; Add ppu batch command to the list
		ldx ppu_batch_len
		lda __scroll_fill_ppu+1
		sta ppu_batch, x
		inx
		lda __scroll_fill_ppu
		sta ppu_batch, x
		inx
		lda #32
		sta ppu_batch, x
		inx
	
		; Append data to the command
		ldy #0
		:
			lda (__scroll_fill_src), y
			sta ppu_batch, x
			inx
			iny
			lda (__scroll_fill_src), y
			sta ppu_batch, x
			inx
			iny
			cpy #64
			bne :-
		stx ppu_batch_len
	
		; Increment scroll_srcaddr and scroll_ppuaddr
		clc
		lda #64	
		adc __scroll_fill_src
		sta __scroll_fill_src
		lda #0
		adc __scroll_fill_src+1
		sta __scroll_fill_src+1
		clc
		lda #64	
		adc __scroll_fill_ppu
		sta __scroll_fill_ppu
		lda #0
		adc __scroll_fill_ppu+1
		sta __scroll_fill_ppu+1
		
		; Manage fill counter to check if we are done
		; If so, we go back to idle state and switch nametable buffer
		dec __scroll_fill_cnt
		bne :+
			lda #SCROLL_IDLE
			sta scroll_state
		:
	@end_fill:

	ldx scroll_state
	cpx #SCROLL_TICK
	bne @end_tick
		clc
		lda scroll_x
		adc __scroll_tick_incx
		sta scroll_x
		clc
		lda scroll_y
		adc __scroll_tick_incy
		sta scroll_y

		dec __scroll_tick_cnt
		bne :+
			lda #0
			sta scroll_x
			sta scroll_y
			lda __scroll_tick_nmt
			sta scroll_nmt
			lda #0
			sta mapper_mirror
			lda #SCROLL_IDLE
			sta scroll_state
		:
	@end_tick:

	; Reset event
	lda #0
	sta scroll_event
	rts


