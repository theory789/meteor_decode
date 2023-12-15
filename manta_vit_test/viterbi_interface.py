import time
from manta import Manta
m = Manta('viterbi.yaml') # create manta python instance using yaml

def conv_calc(state, in_bit, noise=False):
  # returns the output (i, q) for the given input state
  g1 = ((in_bit << 6) | state) & 0b1111001
  g2 = ((in_bit << 6) | state) & 0b1011011
  if not noise:
      return convert_to_signed_rep((count_ones(g1), count_ones(g2)))
  midpts = [0xC0 if not i else 0x3F for i in (count_ones(g1), count_ones(g2))]
  return [max(-128, (b + int(random.gauss(0, 15))), 127) & 0xff \
            for b in midpts]

def count_ones(n):
  return bin(n).count('1') % 2
  
def convert_to_signed_rep(inp): 
    """ Converts an array of zeros and ones to 8 bit hex values where 0 maps to 8'h80 and 
    1 maps to 8'h7F
    """
    return [0x80 if not i else 0x7F for i in inp]

def viterbi(length, soft_cadu):
    """ Viterbi decodes the soft_cadu bits and outputs values it can trace back"""
    vit_desc_out = []
    for i in range(0, length, 2):
        soft_inp = soft_cadu[i]
        time.sleep(0.1) 
        m.lab8_io_core.soft_inp.set(soft_inp) # set the value val3_out to be val3
        m.lab8_io_core.valid_in.set(1) # set the value val4_out to be val4
        soft_inp = soft_cadu[i+1]
        time.sleep(0.1)
        m.lab8_io_core.valid_in.set(0) # set the value val4_out to be val4
        time.sleep(0.1) 
        m.lab8_io_core.soft_inp.set(soft_inp) # set the value val3_out to be val3
        m.lab8_io_core.valid_in.set(1) # set the value val4_out to be val4
        time.sleep(0.01)
        m.lab8_io_core.valid_in.set(0) # set the value val4_out to be val4
        time.sleep(0.01)
        valid_out = m.lab8_io_core.valid_out.get() # read in the output from our divider
        vit_desc = m.lab8_io_core.vit_desc.get() # read in the output from our divider
        if (valid_out == 1):
            vit_desc_out.append(vit_desc)
            print(f"Vit_desc: {vit_desc}")
    return bytes(vit_desc_out)

if __name__ == '__main__': 
    inp_size = 400
    state = 0b000000
    inp_bit = 1
    out_seen = []
    states = []
    inputs = []
    noise = False
    for i in range(inp_size):
        out_seen.extend(conv_calc(state, inp_bit, noise))
        state = ((state >> 1) | (inp_bit << 5)) & 0b111111
        inputs.append(inp_bit)
        states.append(state)
        inp_bit = 1 if not inp_bit else 0
    viterbi(140, out_seen)
