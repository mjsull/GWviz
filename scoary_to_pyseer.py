import os
import sys

from Bio import pairwise2

def translate_dna(dna):
    code = {'ttt': 'F', 'tct': 'S', 'tat': 'Y', 'tgt': 'C',
            'ttc': 'F', 'tcc': 'S', 'tac': 'Y', 'tgc': 'C',
            'tta': 'L', 'tca': 'S', 'taa': '*', 'tga': '*',
            'ttg': 'L', 'tcg': 'S', 'tag': '*', 'tgg': 'W',
            'ctt': 'L', 'cct': 'P', 'cat': 'H', 'cgt': 'R',
            'ctc': 'L', 'ccc': 'P', 'cac': 'H', 'cgc': 'R',
            'cta': 'L', 'cca': 'P', 'caa': 'Q', 'cga': 'R',
            'ctg': 'L', 'ccg': 'P', 'cag': 'Q', 'cgg': 'R',
            'att': 'I', 'act': 'T', 'aat': 'N', 'agt': 'S',
            'atc': 'I', 'acc': 'T', 'aac': 'N', 'agc': 'S',
            'ata': 'I', 'aca': 'T', 'aaa': 'K', 'aga': 'R',
            'atg': 'M', 'acg': 'T', 'aag': 'K', 'agg': 'R',
            'gtt': 'V', 'gct': 'A', 'gat': 'D', 'ggt': 'G',
            'gtc': 'V', 'gcc': 'A', 'gac': 'D', 'ggc': 'G',
            'gta': 'V', 'gca': 'A', 'gaa': 'E', 'gga': 'G',
            'gtg': 'V', 'gcg': 'A', 'gag': 'E', 'ggg': 'G'
            }
    protein = ''
    dna = dna.lower()
    for i in range(0, len(dna), 3):
        if dna[i:i + 3] in code:
            protein += code[dna[i:i + 3]]
        else:
            protein += 'X'
    return protein


def reverse_compliment(seq):
    complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A', 'a': 't', 'c': 'g', 'g': 'c', 't': 'a'}
    return "".join(complement.get(base, base) for base in reversed(seq))


def get_genes_promoter(gff_folder, prom_region=100):
    gene_dict = {}
    seqDict = {}
    for i in os.listdir(gff_folder):
        with open(os.path.join(gff_folder, i)) as f:
            getseq = False
            for zline in f:
                if zline.startswith('#'):
                    continue
                elif zline.startswith('>'):
                    getseq = True
                    name = zline.split()[0][1:]
                    seqDict[name] = ''
                elif getseq:
                    seqDict[name] += zline.rstrip()
                else:
                    ncontig, prod, cds, gstart, gstop, qual, strand, score, extra = zline.rstrip().split('\t')
                    id, gene, product, ref_acc = 'n/a', 'n/a', 'n/a', 'n/a'
                    for stuff in extra.split(';'):
                        if stuff.startswith('ID='):
                            id = stuff.split('=')[1]
                        if stuff.startswith('Name='):
                            gene = stuff.split('=')[1]
                        if stuff.startswith('product='):
                            product = stuff.split('=')[1]
                        if stuff.startswith(
                                'inference=ab initio prediction:Prodigal:2.6,similar to AA sequence:usa300reference.gbk:'):
                            ref_acc = stuff.split(':')[-1]
                    gene_dict[id] = [ncontig, int(gstart), int(gstop), strand, id, gene, product, ref_acc]
    for j in gene_dict:
        contig, start, stop, strand, id, gene, product, ref_acc = gene_dict[j]
        if strand == '+':
            prot = translate_dna(seqDict[contig][start-1:stop])
            prom = seqDict[contig][start-1-prom_region:start-1]
        else:
            prot = translate_dna(reverse_compliment(seqDict[contig][start-1:stop]))
            prom = reverse_compliment(seqDict[contig][stop:stop+prom_region])
        gene_dict[j] += [prot, prom]
    return(gene_dict)



def get_operons(operon_file, gff_file):
    operon_dict = {}
    gene_name_dict = {}
    with open(gff_file) as f:
        for zline in f:
            if zline.startswith('#'):
                continue
            elif zline.startswith('>'):
                break
            ncontig, prod, cds, gstart, gstop, qual, strand, score, extra = zline.rstrip().split('\t')
            id, gene, product, ref_acc = 'n/a', 'n/a', 'n/a', 'n/a'
            for stuff in extra.split(';'):
                if stuff.startswith('ID='):
                    id = stuff.split('=')[1]
                elif stuff.startswith('Name='):
                    gene = stuff.split('=')[1]

                gene_name_dict[gene] = id

    with open(operon_file) as f:
        f.readline()
        for line in f:
            if len(line.split()) == 1:
                operon = line.split()[0]
            else:
                if line.split()[0] in gene_name_dict:
                    id = gene_name_dict[line.split()[0]]
                else:
                    id = line.split()[0]
                operon_dict[id] = operon
    return(operon_dict)


def process_roary(roary_file, operon_dict, gene_dict, outfile, frameshift=False, nonsyn=False, get_prom=False, maxmm=5):
    with open(roary_file) as f, open(outfile, 'w') as out:
        names = f.readline().rstrip()[1:-1].split('","')[14:]
        out.write("gene\t" + '\t'.join(names) + '\n')
        operon_in_out = {}
        for line in f:
            outline = []
            splitline = line.rstrip()[1:-1].split('","')
            the_name = splitline[0]
            genes = splitline[14:]
            freq_dict = {}
            operon = None
            seqlist = []
            seqlist2 = []
            for i in genes:
                if i == '':
                    continue
                if '\t' in i:
                    for j in i.split('\t'):
                        if j in operon_dict:
                            operon = operon_dict[j]
                        seqlist.append(gene_dict[j][8])
                        seqlist2.append(gene_dict[j][9])
                else:
                    if i in operon_dict:
                        operon = operon_dict[i]
                    seqlist.append(gene_dict[i][8])
                    seqlist2.append(gene_dict[i][9])
            for seq in seqlist:
                if seq in freq_dict:
                    freq_dict[seq] += 1
                else:
                    freq_dict[seq] = 1
            alist = []
            for i in freq_dict:
                alist.append((freq_dict[i], i))
            alist.sort(reverse=True)
            most_common_prot = alist[0][1]
            freq_dict = {}
            for seq in seqlist2:
                if seq in freq_dict:
                    freq_dict[seq] += 1
                else:
                    freq_dict[seq] = 1
            alist = []
            for i in freq_dict:
                alist.append((freq_dict[i], i))
            alist.sort(reverse=True)
            most_common_prom = alist[0][1]
            for z in genes:
                if '\t' in z:
                    the_genes = z.split('\t')
                else:
                    the_genes = [z]
                for i in the_genes:
                    gotit = True
                    if not i == '':
                        contig, gstart, gstop, strand, id, gene, product, ref_acc, prot, prom = gene_dict[i]
                    else:
                        prom = ''
                    if i == '':
                        gotit = False
                    elif prot == most_common_prot:
                        pass
                    elif nonsyn and prot != most_common_prot:
                        gotit = False
                    elif frameshift:
                        align = pairwise2.align.globalxx(most_common_prot, prot)
                        a1 = align[0][0]
                        a2 = align[0][1]
                        mm = 0
                        for pos in range(len(a1)):
                            if a1[pos] != a2[pos]:
                                mm += 1
                        if mm >= maxmm:
                            gotit = False
                    if get_prom and prom != most_common_prom:
                        gotit = False
                    if gotit:
                        break
                if gotit:
                    outline.append("1")
                else:
                    outline.append("0")
            if not operon is None:
                if operon in operon_in_out:
                    for num, op in enumerate(operon_in_out[operon]):
                        if op == '1' and outline[num] == '1':
                            pass
                        else:
                            operon_in_out[operon][num] = '0'
                else:
                    operon_in_out[operon] = outline
            else:
                out.write(the_name + '\t')
                out.write('\t'.join(outline) + '\n')
        for i in operon_in_out:
            out.write('operon_' + i + '\t' + '\t'.join(operon_in_out[i]) + '\n')






gene_dict = get_genes_promoter(sys.argv[1])
operon_dict = get_operons(sys.argv[2], sys.argv[3])
process_roary(sys.argv[4], operon_dict, gene_dict, sys.argv[5])