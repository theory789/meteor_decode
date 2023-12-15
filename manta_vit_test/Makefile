SOURCES :=                                      \
    hdl/                                        \
    obj/                                        \
    xdc/                                        \
    sim/                                        \
		ip/ 																				\

.PHONY: flash
flash:
		openFPGALoader -b arty_s7_50 obj/final.bit

.PHONY: build
build:
		./remote/r.py build.py build.tcl $(SOURCES)

# .PHONY: recorder
# recorder:
#     cp build/sim.py build.py
#     ./remote/r.py build.py xsim_run.tcl $(SOURCES)
#     open dump.vcd vcd/recorder_example.vcd

# .PHONY: pdm
# pdm:
#     iverilog -g2012 -o vcd/pdm.out sim/pdm_tb.sv hdl/pdm.sv
#     vvp vcd/pdm.out
#     open vcd/pdm.vcd vcd/pdm_example.vcd

.PHONY: clean
clean:
		rm -rf obj/*
		rm -rf vcd/*
		rm -rf vivado.log
