import numpy as np
import scipy.optimize as sp
import math as m
import sys
import itertools

NUM_FEATURES = 3

def extract_data(filename):

    labels = []
    fvecs = []
    r = []
    n = []
    s = []

    i = 0
	
    input_file = open(filename, 'r')
    for line in input_file.readlines():
        row = line.split(",")
        #for j in xrange(0, mlp.NUM_CLASSES):
        #  labels.append(float(row[mlp.NUM_FEATURES+j]))
        labels.append(float(row[NUM_FEATURES]))
        #labels.append(np.log10(float(row[len(row)-1])))
        #fvecs.append([float(x) for x in row[0:NUM_FEATURES]])
        r.append(float(row[0]))
        n.append(float(row[1]))
        s.append(float(row[2]))
        i = i + 1
		
    input_file.close()
    # Convert the array of float arrays into a numpy float matrix.
    fvecs_np = np.matrix(fvecs).astype(np.float32).transpose()

    # Convert the array of int labels into a numpy array.
    labels_np = np.array(labels).astype(dtype=np.float32)
    num_labels = i;
    #print(len(labels_np))
    #print(i)
    #_labels_np = np.reshape(labels_np, (i,mlp.NUM_CLASSES))
    #print(_labels_np[0].shape)
    #print(fvecs_np)
    
    np_r = np.array(r)
    np_n = np.array(n)
    np_s = np.array(s)

    #print(np_r)
    #print(np_n)
    #print(np_s) 

    return np_r, np_n, np_s, labels_np, num_labels

operators = []
append3_operators = []
functions = []

def _mul(x, g, h, p1, p2):
    r, n, s = x
    return (p1*g(r)) * (p2*h(n))

def _add(x, g, h, p1, p2):
    r, n, s = x
    return (p1*g(r)) + (p2*h(n))

def _div(x, g, h, p1, p2, epsilon=1e-10):
    r, n, s = x
    return (p1*g(r)) / (p2*h(n+epsilon))

def append3_mul(x, g, h, p3):
    r, n, s = x
    return g * (p3*h(s))

def append3_add(x, g, h, p3):
    r, n, s = x
    return g + (p3*h(s))

def append3_div(x, g, h, p3, epsilon=1e-10):
    r, n, s = x
    return g / (p3*h(s+epsilon))

def _log10(x, epsilon=1e-10):
    return np.log10(x+epsilon)

def _inv(x, epsilon=1e-10):
    return 1.0/(x+epsilon)

def _sqrt(x):
    return np.sqrt(x)

def _id(x):
    return x

#def f(x, p1, p2):
#    #return p1*x[0,:] * p2*x[1,:]
#    #return p1/x[0,:]**2 + p2/np.log10(x[1,:]+1e-10)
#    #print(c)
#    return operators[c[0]](x, functions[c[1]], functions[c[2]], p1, p2)


def main():
    if len(sys.argv) < 2:
        print("Missing score distribution CSV file")
        exit()
    runtimes, nodes, submits,train_labels, num_examples = extract_data(sys.argv[1])
    #print(train_data.shape)

    w = np.zeros(num_examples)
    for i in range(0,num_examples):
        #w[i] = STDEV
        w[i] = 1.0 / (runtimes[i] * nodes[i])

    #print(train_labels.shape)   
   
    functions.append(_log10)
    functions.append(_inv)
    functions.append(_sqrt)
    functions.append(_id)

    operators.append(_mul)
    operators.append(_add)
    operators.append(_div)

    append3_operators.append(append3_mul)
    append3_operators.append(append3_add)
    append3_operators.append(append3_div)   
    #combinations = [[0,1],[0,2],[1,2]]

    #permutations = set(list(itertools.permutations([0,1,2,3], NUM_FEATURES))) | set(list(itertools.combinations_with_replacement([0,1,2,3], NUM_FEATURES)))
    permutations = set(list(itertools.product([0,1,2,3], repeat=NUM_FEATURES)))

    all_c = []
    all_score = []
    all_popt = []

    op_labels = ["*", "+", "/"]
    f_labels = ["log10", "inv", "sqrt", "id"]  

    for op in range(0,3):
        for append_op in range(0,3):
            for perm in permutations:
                #print(perm)
                c = [op, append_op, perm[0], perm[1], perm[2]]
                all_c.append(c)

                def f(x, p1, p2, p3):
                    r, n, s = x
                    #return p1*np.log10(x[0,:]+1e-10) + p2*np.sqrt(x[1,:]) #debug: score=0.0094622
                    #return np.log10(p1*x[0,:]+1e-10) + np.sqrt(p2*x[1,:]) #debug: score=0.9761412
                    #return ((1.0/p1*x[0,:])**3) * p2*x[1,:] #WFP3
                    _f = operators[c[0]]((r, n, s), functions[c[2]], functions[c[3]], p1, p2)
                    return append3_operators[c[1]]((r, n, s), _f, functions[c[4]], p3)
    
                popt, pcov = sp.curve_fit(f, (runtimes, nodes, submits), train_labels, sigma=w, absolute_sigma=True)    
                #popt, pcov = sp.curve_fit(f, (runtimes, nodes, submits), train_labels, sigma=None)
                all_popt.append(popt)
	
                p1 = popt[0]
                p2 = popt[1]
                p3 = popt[2]
                #print(train_data[:,0])
                #print(pcov)
                #residuals = train_labels - f(train_data,p1,p2)
                #print(f(train_data[:,0],p1,p2))
                #print(train_labels[0])
                #fres = sum(residuals**2)
                #print(fres)
                residuals = 0.0
                for i in range(0, len(train_labels)):
                    residuals += np.absolute(train_labels[i] - f((runtimes[i], nodes[i], submits[i]),p1,p2,p3))
                    #print("%.7f %.7f" % (train_labels[i],f(train_data[:,i],p1,p2)))

                score = (residuals/len(train_labels))
                #if np.isinf(score) or np.isnan(score):
                #  score = 1.0
                #print(c, score)
                all_score.append(score)
         
                #print("[%s(runtime) %s %s(#nodes) %s %s(submit)],%.7f" % (f_labels[c[2]], op_labels[c[0]], f_labels[c[3]], op_labels[c[1]], f_labels[c[4]], score))

    #print(all_c)

    for i in range(0,len(all_c)):
        max_score_index = np.argmax(all_score)
        print("(%.10f x %s(runtime)) %s (%.10f x %s(#cores)) %s (%.10f x %s(submit)),fitness=%.7f" % (all_popt[max_score_index][0],f_labels[all_c[max_score_index][2]], op_labels[all_c[max_score_index][0]], all_popt[max_score_index][1],f_labels[all_c[max_score_index][3]], op_labels[all_c[max_score_index][1]], all_popt[max_score_index][2],f_labels[all_c[max_score_index][4]], all_score[max_score_index]))
        all_score[max_score_index] = -1.0
    
if __name__ == '__main__':
    main()
