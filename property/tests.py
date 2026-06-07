from django.test import TestCase

# Create your tests here.
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=50)

def fun_test(**kwargs):



    print (kwargs['a'])
    print (kwargs['b'])
    # print (c)
    #
def fun_test(*args):



    print (args[0])
    print (args[1])



if __name__ == '__main__':
    for count in range(0, 100):
        a=(count,count-1)
        executor.submit(fun_test, *a)
        # fun_test(count,count-1,count+1)
