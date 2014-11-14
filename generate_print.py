#!/usr/bin/env python
import math

frac_bits = 15
flag_bits = 2
int_bits = 15

# characters in the integer is given by the base 10 log of the maximum number
int_chars = int(math.ceil(math.log(2**int_bits,10)))

#characters in the base-10 significand is exactly the number of bits
#  0.5, 0.25, 0.125, etc.
# Each step involves extending another power of ten down...
frac_chars = frac_bits

sign_char = 1
point_char = 1

sign_loc = 0
int_loc = sign_char
point_loc = sign_char + int_chars
frac_loc = sign_char + int_chars + point_char
length = sign_char + int_chars + point_char + frac_chars

########


bits = [2**i for i in range(-15, 15)]
dec_patterns = ["%022.15f"%(b) for b in bits]

def patternsat(n):
    return [ ( (i + flag_bits),p[n]) for i,p in enumerate(dec_patterns)]

def poly_for(n):
    patterns = patternsat(n)
    patterns = [(bit,p) for bit,p in patterns if p != '0']
    terms = ["(%c * bit%d)"%(p, bit) for bit, p in patterns]
    return " + ".join(terms)


print """#include "ftfp.h"

/*********
 * This file is autogenerated by generate_print.py.
 * Please don't modify it manually.
 *********/

void fix_print(char* buffer, fixed f) {
  uint8_t isinfpos = FIX_IS_INF_POS(f);
  uint8_t isinfneg = FIX_IS_INF_NEG(f);
  uint8_t isnan = FIX_IS_NAN(f);
  uint8_t excep = isinfpos | isinfneg | isnan;

  uint32_t carry = 0;
  uint32_t scratch = 0;
  uint32_t neg = f >> 31;

  f = fix_abs(f);"""

print "\n".join(["  uint32_t bit%d = (((f) >> (%d))&1);"%(i,i) for i in range(2,32)])

# start at the end and move forward...
for position in reversed(range(frac_loc, frac_loc+frac_chars)):
    poly = poly_for(position)
    print "  scratch = %s + carry;"%(poly)
    print "  buffer[%d] = ((%d + (scratch %% 10)) * (1-excep) + (excep * %d));"%(position, ord('0'), ord(' ')), "carry = scratch / 10;"

print
print "  buffer[%d] = excep*%d + (1-excep)*%d;"%(point_loc, ord(' '), ord('.'))
print

extra_polynomials = {
        1: " + (isnan * %d) + (isinfpos | isinfneg) * %d"%(ord('N'), ord('I')),
        2: " + (isnan * %d) + (isinfpos | isinfneg) * %d"%(ord('a'), ord('n')),
        3: " + (isnan * %d) + (isinfpos | isinfneg) * %d"%(ord('N'), ord('f')),
        }

for position in reversed(range(int_loc,int_loc+int_chars)):
    poly = poly_for(position)
    print "  scratch = %s + carry;"%(poly)
    print "  buffer[%d] = ((%d + (scratch %% 10)) * (1-excep)) %s;"%(position, ord('0'),
        extra_polynomials.get(position, "+ (excep * %d)"%(ord(' ')))), "carry = scratch / 10;"

print """
  uint8_t n = (neg*(1-excep) + isinfneg);
  buffer[0] = %d * n + %d * (1-n);
"""%(ord('-'), ord(' '))

print "  buffer[%d] = '\\0';"%(length);

print """}
"""

