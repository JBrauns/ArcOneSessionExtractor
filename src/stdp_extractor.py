import re
import argparse
import math

# NOTE(joshua): wordline - 0, bitline - 1, resistance - 2,
# amplitude - 3, pulse_width - 4, tag - 5, read_tag - 6, read_voltage - 7

class Stdp_Test_Point:
    def __init__(self, pos_init, r_init, amp_init, pw_init, v_init):
        # NOTE(joshua): Wordline, bitline
        self.pos = pos_init
        self.r = r_init
        self.amp = amp_init
        self.pw = pw_init
        self.v = v_init

class Stdp_Block:
    def __init__(self, index, wl, bl, r, amp, pw, tag, read_tag, v):
        self.index = index
        self.stdb_begin = Stdp_Test_Point([wl, bl], r, amp, pw, v)

        self.test_points_after = []
        self.test_points_after_dt = []
        self.test_points_before = []
        self.test_points_before_dt = []

    def end(self, wl, bl, r, amp, pw, tag, read_tag, v):
        self.stdb_end = Stdp_Test_Point([wl, bl], r, amp, pw, v)
        
    def add_test_point(self, wl, bl, r, amp, pw, tag, read_tag, v):
        pos = [wl, bl]
        
        dt_before_match = re.search("(?<=dt=)-?\d.\d+(?=\ before)", tag)
        if(dt_before_match):
            dt_before = dt_before_match.group(0)
            if(dt_before != ""):
                self.test_points_before_dt.append(dt_before)
                self.test_points_before.append(Stdp_Test_Point(pos, r, amp, pw, v))
        else:
            dt_after_match = re.search("(?<=dt=)-?\d.\d+(?=\ after)", tag)
            if(dt_after_match):
                dt_after = dt_after_match.group(0)
                self.test_points_after_dt.append(dt_after)
                self.test_points_after.append(Stdp_Test_Point(pos, r, amp, pw, v))

    def format_content(self, sep, logarithmic):
        dest = ""
        test_point_count = len(self.test_points_after)

        print("In format_content %d count %d" % (self.index, test_point_count))

        if(len(self.test_points_after) == len(self.test_points_before)):
            if(len(self.test_points_after) == len(self.test_points_after_dt) and
               len(self.test_points_before) == len(self.test_points_before_dt)):
                
                for test_point_index in range(0, test_point_count):
                    tp_before = self.test_points_before[test_point_index]
                    tp_after = self.test_points_after[test_point_index]

                    r_after = float(tp_after.r)
                    r_before = float(tp_before.r)
                    if((r_after != float('inf')) and (r_before != float('inf'))):
                        dest += self.test_points_after_dt[test_point_index].replace(".", ",") + sep

                        r_delta = r_before - r_after
                        r_0 = min(r_after, r_before)

                        r_out = r_delta / r_0
                        if(logarithmic):
                            sign = 1.0 if (r_out >= 0) else -1.0
                            r_out = sign*math.log(r_out*sign)
                        
                        dest += str(r_delta).replace(".", ",") + sep
                        dest += str(r_0).replace(".", ",") + sep
                        dest += str(r_out).replace(".", ",")
                        dest += "\n"
            else:
                print("Unqueal count of tp and tp_delta: %after=d,%d before=%d,%d" %
                      (len(self.test_points_after), len(self.test_points_after_dt) ,
                       len(self.test_points_after), len(self.test_points_before_dt)))
        else:
            print("Unequal count of before and after testpoints: %d,%d" %
                  (len(self.test_points_after), len(self.test_points_before)))

        return(dest)
            

def get_file_content(path):
    with open(path, "r") as src:
        result = src.readlines()

    return(result)

def write_file_content(path, content):
    with open(path, "w") as dest:
        dest.write(content)

parser = argparse.ArgumentParser(description="STDP extracter")
parser.add_argument("-d", dest="dest", help="Destination of extraction")
parser.add_argument("-s", dest="src", help="Source of stdp data")

args = parser.parse_args()

print("Args: src=%s\ndest=%s" % (args.src, args.dest))
src_lines = get_file_content(args.src)

src_line_index = 0
parse_block = False

stdp_block_current_index = 0
stdp_blocks = []
stdp_count = 0
for src_line in src_lines:
    # NOTE(joshua): wordline - 0, bitline - 1, resistance - 2,
    # amplitude - 3, pulse_width - 4, tag - 5, read_tag - 6, read_voltage - 7
    cells = src_line.split(",")

    if(len(cells) >= 8):
        tag = cells[5]
        if(tag == "stdp_s"):
            parse_block = True
            stdp_blocks.append(Stdp_Block(stdp_block_current_index, cells[0], cells[1], cells[2], cells[3],
                                          cells[4], cells[5], cells[6], cells[7]))
            # print("STDP block start @line: %d" % src_line_index)
            stdp_count = src_line_index
            
        elif(tag == "stdp_e"):
            parse_block = False
            stdp_blocks[stdp_block_current_index].end(cells[0], cells[1], cells[2], cells[3],
                                                      cells[4], cells[5], cells[6], cells[7])
            stdp_count = src_line_index - stdp_count
            #print("STDP block end @line: %d" % src_line_index)
            #print("STDP count: %d" % stdp_count)
            stdp_block_current_index += 1

        elif(parse_block):
            stdp_blocks[stdp_block_current_index].add_test_point(cells[0], cells[1], cells[2], cells[3],
                                                                 cells[4], cells[5], cells[6], cells[7])
            
    src_line_index += 1

print("STDP block count: %d" % (len(stdp_blocks)))

for block_index in range(0, len(stdp_blocks)):
    path_out = args.dest.replace(".csv", ("_" + str(block_index) + ".csv"))
    write_file_content(path_out, stdp_blocks[block_index].format_content(";", False))
    print("File %s written!" % path_out)

