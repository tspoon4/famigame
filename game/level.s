.include "level.inc"

.import scroll_state
.import scroll_event
.import scroll_event_param
.import scroll_update	;-- Init hack
.importzp scroll_nmt	;-- Init hack

.export level_state
.export level_event
.export level_event_param
.export level_init
.export level_update

.segment "BSS"
level_state: .res 1
level_event: .res 1
level_event_param: .res 1
__level_screen_x: .res 1
__level_screen_y: .res 1
__level_scroll_dir: .res 1

.segment "RODATA"
mylevel1:
.incbin "level.nmt"

; Tuning level size
LEVEL_WEXP = 1
LEVEL_HEXP = 1
; Deduced constants, don't modify!
LEVEL_WADD = 4
LEVEL_HADD = LEVEL_WADD << LEVEL_WEXP
LEVEL_WMASK = (LEVEL_WADD << LEVEL_WEXP) - 1
LEVEL_HMASK = (LEVEL_HADD << LEVEL_HEXP) - 1


.segment "CODE"
; Function that initializes the level system
level_init:

	ldx #0
	stx level_state
	stx level_event
	stx __level_screen_x
	stx __level_screen_y

	; Initialize the background
	lda #SCROLL_FILL
	sta scroll_event
	lda #<mylevel1
	sta scroll_event_param
	lda #>mylevel1
	sta scroll_event_param+1
	; Hack to fill the first nametable
	lda #1
	sta scroll_nmt
	jsr scroll_update
	lda #0
	sta scroll_nmt

	rts


; Function that updates the scrolling system
level_update:

	ldx level_state
	cpx #LEVEL_IDLE
	bne @end_idle
		ldx level_event
		cpx #LEVEL_CHANGE
		bne @end_idle
			stx level_state
			ldx level_event_param
			stx __level_scroll_dir ; Store scrolling direction for screen change
			cpx #LEVEL_LEFT
			bne :+
				sec
				lda __level_screen_x
				sbc #LEVEL_WADD
				and #LEVEL_WMASK
				sta __level_screen_x
			:
			cpx #LEVEL_RIGHT
			bne :+
				clc
				lda __level_screen_x
				adc #LEVEL_WADD
				and #LEVEL_WMASK
				sta __level_screen_x
			:
			cpx #LEVEL_UP
			bne :+
				sec
				lda __level_screen_y
				sbc #LEVEL_HADD
				and #LEVEL_HMASK
				sta __level_screen_y
			:
			cpx #LEVEL_DOWN
			bne :+
				clc
				lda __level_screen_y
				adc #LEVEL_HADD
				and #LEVEL_HMASK
				sta __level_screen_y
			:

			lda #SCROLL_FILL
			sta scroll_event
			lda #<mylevel1
			sta scroll_event_param

			clc
			lda #>mylevel1
			adc __level_screen_x
			adc __level_screen_y
			sta scroll_event_param+1
			jmp @end_change	; Skip LEVEL_CHANGE for this update
	@end_idle:

	ldx level_state
	cpx #LEVEL_CHANGE
	bne @end_change
		ldx scroll_state
		bne @end_change ;-- Compare with #SCROLL_IDLE that is #0
			lda #SCROLL_TICK
			sta scroll_event
			lda __level_scroll_dir
			sta scroll_event_param
			lda #LEVEL_IDLE
			sta level_state
	@end_change:

	; Reset event
	lda #0
	sta level_event
	rts


