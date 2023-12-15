`timescale 1ns / 1ps
`default_nettype none // prevents system from inferring an undeclared logic (good practice)

module top_level(
  input wire clk_100mhz,
  input wire [15:0] sw, //all 16 input slide switches
  input wire  uart_rxd,
  input wire [3:0] btn, //all four momentary button switches
  output logic [15:0] led, //16 green output LEDs (located right above switches)
  output logic uart_txd,
  output logic [2:0] rgb0, //rgb led
  output logic [2:0] rgb1 //rgb led
  );

  //
  //shut up those rgb LEDs (active high):
  assign rgb1= 0;
  assign rgb0 = 0;

  logic sys_rst;
  assign sys_rst = btn[0];

  logic manta_valid_out;
  logic manta_valid_out_prev;
  logic manta_vit_desc;
  logic signed [7:0] manta_soft_inp;
  logic manta_valid_in;
  logic manta_valid_in_prev;
  logic [5:0] manta_last_state;
  logic manta_rst;

  manta manta_inst (
      .clk(clk_100mhz),
      .rx(uart_rxd),
      .tx(uart_txd),
      .valid_out(manta_valid_out), 
      .vit_desc(manta_vit_desc), 
      .soft_inp(manta_soft_inp), 
      .last_state(manta_last_state),
      .manta_rst(manta_rst),
      .valid_in(manta_valid_in));
  
  logic signed [7:0] soft_inp;
  logic ready_in;
  logic vit_desc;
  logic valid_out;
  logic sm_out_deb;
  logic valid_inp_vit;

  logic clk_wiz_81;
  logic locked;
   clk_wiz_0 clk_81
   (
    // Clock out ports
    .clk_out1(clk_wiz_81),     // output clk_out1
    // Status and control signals
    .reset(sys_rst), // input reset
    .locked(locked),       // output locked
   // Clock in ports
    .clk_in1(clk_100mhz)      // input clk_in1
);

 logic [5:0] last_state;

logic soft_inp_0;
logic soft_inp_1;
logic valid_in_vit_0;
logic valid_in_vit_1;
logic vit_desc_0;
logic vit_desc_1;
logic ready_in_0;
logic ready_in_1;
logic last_state_0;
logic last_state_1;
logic valid_out_0;
logic valid_out_1;
logic sys_rst_0;
logic sys_rst_1;

always_ff @(posedge clk_100mhz) begin
  soft_inp_0 <= manta_soft_inp;
  soft_inp_1 <= soft_inp_0;
  valid_in_vit_0 <= valid_inp_vit;
  valid_in_vit_1 <= valid_in_vit_0;
  vit_desc_0 <= vit_desc;
  vit_desc_1 <= vit_desc_0;
  ready_in_0 <= ready_in;
  ready_in_1 <= ready_in_0;
  last_state_0 <= last_state;
  last_state_1 <= last_state_0;
  valid_out_0 <= valid_out;
  valid_out_1 <= valid_out_0;
  sys_rst_0 <= sys_rst + manta_rst;
  sys_rst_1 <= sys_rst_0;
end

  viterbi dut (
      .clk(clk_wiz_81),
      .sys_rst(sys_rst_1),
      .soft_inp(soft_inp_1),
      .valid_in_vit(valid_in_vit_1),
      .vit_desc(vit_desc_1),
      .ready_in(ready_in_1),
      .last_state(last_state_1),
      .valid_out_vit(valid_out_1)
  );

  always_ff @(posedge clk_100mhz) begin
    if (sys_rst | manta_rst) begin
      manta_valid_out <= 0;
      manta_valid_out_prev <= 0;
      manta_valid_in_prev <= 0;
      valid_inp_vit <= 0;
    end else begin
      manta_valid_in_prev <= manta_valid_in;
      valid_inp_vit <= manta_valid_in & ~manta_valid_in_prev;
      manta_valid_out_prev <= valid_out;
      if (~manta_valid_out_prev & valid_out) begin
        manta_valid_out <= 1;
        manta_vit_desc <= vit_desc;
        manta_last_state <= last_state;
      end
    end
  end

endmodule // top_level

`default_nettype wire

