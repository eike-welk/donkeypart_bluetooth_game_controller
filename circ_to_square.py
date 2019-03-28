############################################################
# Mapping a Circle to a Square
############################################################

# Script for `ipython --pylab`

# The formula is taken from:
#   http://squircular.blogspot.com/2015/09/mapping-circle-to-square.html
#
# Run this script from inside Ipython with:
#   `run -i circ_to_square.py`

def max0(x):
    return maximum(x, 0)

def to_square(u, v):
    sqrt2 = sqrt(2)
    x = 0.5 * ( sqrt(max0(2 + 2 * u * sqrt2 + u*u - v*v ))
              - sqrt(max0(2 - 2 * u * sqrt2 + u*u - v*v )))
    y = 0.5 * ( sqrt(max0(2 + 2 * v * sqrt2 - u*u + v*v ))
              - sqrt(max0(2 - 2 * v * sqrt2 - u*u + v*v )))
    return x, y

alpha = linspace(0, pi/2, 100)

u = 0.9 * cos(alpha)
v = 0.9 * sin(alpha)
x, y = to_square(u, v)
scatter(x, y)

u = 0.99 * cos(alpha)
v = 0.99 * sin(alpha)
x, y = to_square(u, v)
scatter(x, y)

u = 1.0 * cos(alpha)
v = 1.0 * sin(alpha)
x, y = to_square(u, v)
scatter(x, y)

u = 1.01 * cos(alpha)
v = 1.01 * sin(alpha)
x, y = to_square(u, v)
scatter(x, y)

u = 1.1 * cos(alpha)
v = 1.1 * sin(alpha)
x, y = to_square(u, v)
scatter(x, y)

show()
