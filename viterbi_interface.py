import time
import sys
import os
import numpy as np
import struct
# sys.path.append('/home/sammy/.local/bin')
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
    wait_time = 0
    valid_count = 0
    last_state_file = "last_state.txt"
    first_invalid = 0

    if (os.path.exists(last_state_file) and os.stat(last_state_file).st_size != 0):
        m.lab8_io_core.manta_rst.set(1) # set the value val3_out to be val3
        m.lab8_io_core.valid_in.set(0) # set the value val3_out to be val3
        time.sleep(0.01)
        m.lab8_io_core.manta_rst.set(0) # set the value val3_out to be val3
        time.sleep(0.01)
        with open(last_state_file, 'r') as f:
            last_state = int(f.read())
            last_state = bin(last_state & 0b111111)[2:].zfill(6)
            # print(f"last_state: {last_state}")
            state = 0b000000
            for i in range(1, 7):
                inp_bit = 1 if  (last_state[-i] == '1') else 0
                soft_inps = conv_calc(state, inp_bit) 
                m.lab8_io_core.soft_inp.set(soft_inps[0]) # set the value val3_out to be val3
                m.lab8_io_core.valid_in.set(1) # set the value val4_out to be val4
                time.sleep(0.001)
                m.lab8_io_core.valid_in.set(0) # set the value val4_out to be val4
                time.sleep(0.001)
                m.lab8_io_core.soft_inp.set(soft_inps[1]) # set the value val3_out to be val3
                m.lab8_io_core.valid_in.set(1) # set the value val4_out to be val4
                time.sleep(0.001)
                m.lab8_io_core.valid_in.set(0) # set the value val4_out to be val4
                time.sleep(0.001)
                state = ((state >> 1) | (inp_bit << 5)) & 0b111111
    else:
        first_invalid = 6
    for i in range(0, length, 2):
        soft_inp = int(soft_cadu[i])
        soft_inp = struct.unpack('I', struct.pack('i', soft_inp))[0] & 0xFF
        m.lab8_io_core.soft_inp.set(soft_inp) # set the value val3_out to be val3
        m.lab8_io_core.valid_in.set(1) # set the value val4_out to be val4
        time.sleep(0.001)
        soft_inp = int(soft_cadu[i+1])
        soft_inp = struct.unpack('I', struct.pack('i', soft_inp))[0] & 0xFF
        m.lab8_io_core.valid_in.set(0) # set the value val4_out to be val4
        time.sleep(0.001)
        m.lab8_io_core.soft_inp.set(soft_inp) # set the value val3_out to be val3
        m.lab8_io_core.valid_in.set(1) # set the value val4_out to be val4
        m.lab8_io_core.valid_in.set(0) # set the value val4_out to be val4
        time.sleep(0.001)
        valid_out = m.lab8_io_core.valid_out.get() # read in the output from our divider
        vit_desc = m.lab8_io_core.vit_desc.get() # read in the output from our divider
        # last_state = m.lab8_io_core.last_state.get()
        if (valid_out == 1):
            if first_invalid < 6:
                first_invalid += 1
                # print("Invalid from reset")
            else: 
                vit_desc_out.append(vit_desc)
                valid_count += 1
                # print(f"Vit_desc: {vit_desc}")
                # print(valid_count)


    count_low = 0
    count_missed = 0
    while (valid_count < length // 2):
        m.lab8_io_core.soft_inp.set(0xFF) # set the value val3_out to be val3
        m.lab8_io_core.valid_in.set(1) # set the value val4_out to be val4
        time.sleep(0.001)
        m.lab8_io_core.valid_in.set(0) # set the value val4_out to be val4
        time.sleep(0.001)
        m.lab8_io_core.soft_inp.set(0xFF) # set the value val3_out to be val3
        m.lab8_io_core.valid_in.set(1) # set the value val4_out to be val4
        time.sleep(0.001)
        m.lab8_io_core.valid_in.set(0) # set the value val4_out to be val4
        time.sleep(0.001)
        valid_out = m.lab8_io_core.valid_out.get() # read in the output from our divider
        vit_desc = m.lab8_io_core.vit_desc.get() # read in the output from our divider
        last_state = m.lab8_io_core.last_state.get()
        vit_desc_out.append(vit_desc)
        if (valid_out == 1):
            print(valid_count)
            valid_count += 1
            if (vit_desc == 0):
                count_missed += 1
            else:
                count_missed = 0
        print(f"Count missed: {count_missed}")


    with open('viterbi.txt', 'wb') as f:
        byte_buff = []
        byte_count = 0
        for i in vit_desc_out: 
            byte_buff.append(str(i))
            # print(f"str_i: {str(i)}")
            if (len(byte_buff) == 8):
                byte_value = int(''.join(byte_buff), 2) & 0b11111111
                f.write(byte_value.to_bytes(1, byteorder='little')) # Try big later 
                byte_buff.clear()
    with open(last_state_file, 'w') as f:
        f.write(str(last_state))
    with open('viterbi_save.txt', 'ab') as f:
        a = np.array(vit_desc_out)
        np.savetxt(f, a, fmt='%.1e')

if __name__ == '__main__': 
    length = sys.argv[1]
    print("LENNGITH: ")
    print(length)
    with open('soft_cadu.txt', 'rb') as f:
        data = np.fromfile(f, dtype=np.int8)
    if int(length):
        print(f"len-dat: {len(data)}")
        viterbi(len(data), data)
    else: 
        print("Length 0")

