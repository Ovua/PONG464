; PONG 464 - Amstrad CPC 464, Z80 + Locomotive BASIC 1.0
        org &9000
START:
        ld a,10
        ld (PLAYER_Y),a
        ld (CPU_Y),a
        ld a,40
        ld (BALL_X),a
        ld a,13
        ld (BALL_Y),a
        ld a,1
        ld (VX),a
        ld (VY),a
        xor a
        ld (RESULT),a
        ld (FRAME),a
        ld (AI_TICK),a
        ld a,255
        call DRAW_ALL
GAME_LOOP:
        call &BD19              ; vertical sync: 50 Hz
        ld a,(FRAME)
        inc a
        cp 3                   ; update logic at ~16.7 Hz
        jr z,STEP
        ld (FRAME),a
        jr GAME_LOOP
STEP:
        xor a
        ld (FRAME),a
        ld a,66                ; ESC: key number (8*8+2)
        call &BB1E
        jr z,NOT_ESC
        ld a,3
        ld (RESULT),a
        ret
NOT_ESC:
        xor a
        call DRAW_ALL          ; erase previous positions
        call READ_KEYS
        call MOVE_CPU
        call MOVE_BALL        ; A = 0 or score 1/2
        or a
        jr z,CONTINUE
        ld (RESULT),a
        ret
CONTINUE:
        ld a,255
        call DRAW_ALL
        jr GAME_LOOP

; DRAW_ALL A = 0 (erase) or 255 (white ink3 in MODE 1)
DRAW_ALL:
        ld (COLOR),a
        ld b,3                 ; player paddle: x-byte=3
        ld a,(PLAYER_Y)
        ld c,a
        ld d,3                 ; 3 character rows high
        ld a,(COLOR)
        call DRAW_BLOCK
        ld b,75                ; CPU paddle
        ld a,(CPU_Y)
        ld c,a
        ld d,3
        ld a,(COLOR)
        call DRAW_BLOCK
        ld a,(BALL_X)
        ld b,a
        ld a,(BALL_Y)
        ld c,a
        ld d,1
        ld a,(COLOR)
        call DRAW_BLOCK
        ret

; DRAW_BLOCK: A=byte, B=x byte (0..78), C=text row (0..24), D=height (rows)

DRAW_BLOCK:
        push af
        push de
        push bc
        ld hl,&C000
        ld a,c
        ld bc,80
BLOCK_Y:
        or a
        jr z,BLOCK_X
        add hl,bc
        dec a
        jr BLOCK_Y
BLOCK_X:
        pop bc                  ; B = x
        ld c,b
        ld b,0
        add hl,bc
        pop de                  ; D = height
        pop af                  ; A = fill byte
        ld b,d
BLOCK_ROW:
        push hl
        ld d,8
BLOCK_SCAN:
        ld (hl),a
        inc hl
        ld (hl),a
        dec hl
        ld c,a
        ld a,h
        add a,8                ; next scanline = +&800
        ld h,a
        ld a,c
        dec d
        jr nz,BLOCK_SCAN
        pop hl
        ld c,a
        ld a,l
        add a,80               ; next character row = +80
        ld l,a
        jr nc,BLOCK_NEXT
        inc h
BLOCK_NEXT:
        ld a,c
        djnz BLOCK_ROW
        ret

READ_KEYS:
        ld a,67                ; Q
        call &BB1E
        jr nz,KEY_UP
        ld a,0                 ; cursor UP
        call &BB1E
        jr z,KEY_DOWN_TEST
KEY_UP:
        ld a,(PLAYER_Y)
        cp 4
        jr z,KEY_DOWN_TEST
        dec a
        ld (PLAYER_Y),a
KEY_DOWN_TEST:
        ld a,69                ; A
        call &BB1E
        jr nz,KEY_DOWN
        ld a,2                 ; cursor DOWN
        call &BB1E
        ret z
KEY_DOWN:
        ld a,(PLAYER_Y)
        cp 21
        ret z
        inc a
        ld (PLAYER_Y),a
        ret

; CPU follows the ball three out of four updates
MOVE_CPU:
        ld a,(AI_TICK)
        inc a
        and 3
        ld (AI_TICK),a
        ret z
        ld a,(CPU_Y)
        inc a                  ; centre of CPU paddle
        ld b,a
        ld a,(BALL_Y)
        cp b
        ret z
        jr c,CPU_UP
        ld a,(CPU_Y)
        cp 21
        ret z
        inc a
        ld (CPU_Y),a
        ret
CPU_UP:
        ld a,(CPU_Y)
        cp 4
        ret z
        dec a
        ld (CPU_Y),a
        ret

; Move ball one logical cell diagonally; bounce from top/bottom & paddles.
MOVE_BALL:
        ld a,(VY)
        ld b,a
        ld a,(BALL_Y)
        add a,b
        cp 4
        jr nc,CHECK_BOTTOM
        ld a,1
        ld (VY),a
        ld a,5
CHECK_BOTTOM:
        cp 24
        jr c,STORE_Y
        ld a,255
        ld (VY),a
        ld a,22
STORE_Y:
        ld (BALL_Y),a
        ld a,(VX)
        ld b,a
        ld a,(BALL_X)
        add a,b
        ld (BALL_X),a
        cp 5
        jr nz,CHECK_CPU_HIT
        ld a,(PLAYER_Y)
        ld b,a
        ld a,(BALL_Y)
        call IN_PADDLE
        jr nc,CHECK_CPU_HIT
        ld a,1
        ld (VX),a
        ld a,(PLAYER_Y)
        inc a                  ; deflect by hit position
        ld b,a
        ld a,(BALL_Y)
        cp b
        jr z,CHECK_CPU_HIT
        jr c,PLAYER_DEFLECT_UP
        ld a,1
        jr PLAYER_STORE_VY
PLAYER_DEFLECT_UP:
        ld a,255
PLAYER_STORE_VY:
        ld (VY),a
CHECK_CPU_HIT:
        ld a,(BALL_X)
        cp 73
        jr nz,CHECK_SCORES
        ld a,(CPU_Y)
        ld b,a
        ld a,(BALL_Y)
        call IN_PADDLE
        jr nc,CHECK_SCORES
        ld a,255
        ld (VX),a
        ld a,(CPU_Y)
        inc a
        ld b,a
        ld a,(BALL_Y)
        cp b
        jr z,CHECK_SCORES
        jr c,CPU_DEFLECT_UP
        ld a,1
        jr CPU_STORE_VY
CPU_DEFLECT_UP:
        ld a,255
CPU_STORE_VY:
        ld (VY),a
CHECK_SCORES:
        ld a,(BALL_X)
        cp 2
        jr nz,CHECK_RIGHT_SCORE
        ld a,2                ; CPU scores
        ret
CHECK_RIGHT_SCORE:
        cp 76
        jr nz,NO_SCORE
        ld a,1                ; player scores
        ret
NO_SCORE:
        xor a
        ret

; Carry set if BALL_Y is within B..B+2
; Entry A=ball Y, B=paddle top. Clobbers A & C.
IN_PADDLE:
        ld c,a
        ld a,b
        cp c
        jr z,HIT
        inc a
        cp c
        jr z,HIT
        inc a
        cp c
        jr z,HIT
        or a                   ; carry clear (not a hit)
        ret
HIT:
        scf
        ret

; Game state memory. BASIC loader reads RESULT via PEEK.
PLAYER_Y: db 10
CPU_Y:    db 10
BALL_X:   db 40
BALL_Y:   db 13
VX:       db 1
VY:       db 1
FRAME:    db 0
AI_TICK:  db 0
RESULT:   db 0
COLOR:    db 0
END_CODE:
