push {r4,r5,r6,lr}
ldr r4, =0x400d04dc
ldrh r6, [r4,#2]
cmp r6,#0
bne registered
ldr r3, =0x4004d88d
blx r3
cmp r0,#0
beq allocation_failed
strh r0,[r4,#2]
mov r6,r0
registered:
ldrb r5,[r4]
cmp r5,#0
beq no_monitor
cmp r5,#2
bhi off
ldr r3,=0x40073614
ldr r3,[r3]
cmp r3,#1
beq no_monitor
cmp r5,#1
beq with_monitor
off:
movs r0,#1
movs r1,#0
ldr r3,=0x4001b215
blx r3
mov r0,r6
movs r1,#108
movs r2,#0
ldr r3,=0x4004d905
blx r3
movs r5,#0
movs r0,#8
b announce
no_monitor:
mov r0,r6
movs r1,#108
movs r2,#1
ldr r3,=0x4004d905
blx r3
movs r0,#0
movs r1,#0
ldr r3,=0x4001b215
blx r3
movs r5,#1
movs r0,#9
b announce
with_monitor:
movs r0,#0
movs r1,#0
ldr r3,=0x4001b215
blx r3
mov r0,r6
movs r1,#108
movs r2,#0
ldr r3,=0x4004d905
blx r3
movs r5,#2
movs r0,#9
announce:
strb r5,[r4]
ldr r3,=0x4001ac15
blx r3
movs r0,#1
pop {r4,r5,r6,pc}
allocation_failed:
movs r0,#1
movs r1,#0
ldr r3,=0x4001b215
blx r3
movs r5,#0
strb r5,[r4]
movs r0,#8
ldr r3,=0x4001ac15
blx r3
movs r0,#0
pop {r4,r5,r6,pc}