import sys
import os
import subprocess


with open(sys.argv[1]) as f:
    for line in f:
        query, ref = line.split()
        for i in os.listdir(sys.argv[2]):
            if query in i:
                query_file = sys.argv[2] + '/' + i
            elif ref in i:
                ref_file = sys.argv[2] + '/' + i
        print 'python ' + os.path.dirname(sys.argv[0]) + '/getVar.py -qg ' + query_file + ' -rg ' + ref_file + ' -w ' + sys.argv[3] + ' -o ' + query + '_vs_' + ref
        subprocess.Popen('python ' + os.path.dirname(sys.argv[0]) + '/getVar.py -qg ' + query_file + ' -rg ' + ref_file + ' -w ' + sys.argv[3] + ' -o ' + query + '_vs_' + ref, shell=True).wait()
