import numpy as np
dt = np.array([1,2,3,4,5,6])
dt[1::2]
power = 'x8'
power = int(power[1:])

power

a = np.linspace(1,10,10)
a
b = np.linspace(0,9,10)
type((a,b))

str((1,2))
a = {}
a['s'] = 1
a
x = (1,2,3)
str(x[0])+' '+str(x[1])
[float(x) for x in'0, 2'.split(' ')]
import string
dict = {}
for n in range(26):
    dict[list(string.ascii_lowercase)[n]] = list(string.ascii_lowercase)[-n-1]
dict
dict2 = {'qw2':1,'ax4':4}
dict2['q'+'w'+'2']
'time_x_limit'[0:4]

'hahahaha'[0:4]


a = [0,1,2]
a


a = [0,1,2]
a

while True:
    break

for n,x in enumerate('abc',1):
    print(n,x)
''.join(sorted('1348620003')[::-1])
lst = ['1','2','33','454','34','33']
index = lst[:-1].index(lst[-1])
len(lst)-index-1
False == 0
a = []
a
a.append('1')
a
'l' in []
['0'][:-1]

a = [('a',1),('b',2),('c',3)]


bool(1)

dt
dt/2

'123 456'.split(' ')

np.array([1,2,3,10,4,5,6]).argmax()
