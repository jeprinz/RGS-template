#!/usr/bin/env python
# ---------------------------------------------------------------------
#  File:        analysis.py
#  Description: HO1: Analyze the results of RGS and find the best cuts.
#               Definitions:
#                 1. A one-sided cut is a threshold on a single
#                    variable.
#                    e.g., x > xcut
#                 2. A cut-point is the AND of a sequence of cuts. This
#                    can be visualized as a point in the space of cuts.
#                 3. A two-sided cut is a two-sided threshold.
#                    e.g., (x > xlow) and (x < xhigh)
#                 4. A staircase cut is the OR of cut-points.
# ---------------------------------------------------------------------
#  Created:     10-Jan-2015 Harrison B. Prosper and Sezen Sekmen
# ---------------------------------------------------------------------
import os, sys, re
from string import *
from rgsutil import *
from time import sleep
from ROOT import *

sys.path.append('../../python')

# ---------------------------------------------------------------------
def cut(event):
    return False
# ---------------------------------------------------------------------
def main():
    print "="*80
    print "\t=== HO1: obtain best one-sided cuts ==="
    print "="*80

    NAME = 'CUTS'
    
    resultsfilename = "%s.root" % NAME

    treename = "RGS"
    print "\n\topen RGS file: %s"  % resultsfilename
    ntuple = Ntuple(resultsfilename, treename)
    
    variables = ntuple.variables()
    for name, count in variables:
        print "\t\t%-30s\t%5d" % (name, count)        
    print "\tnumber of cut-points: ", ntuple.size()
  
    # -------------------------------------------------------------
    # Plot results of RGS, that is, the fraction of events that
    # pass a given cut-point.
    #  1. Loop over cut points and compute a significance measure
    #     for each cut-point.
    #  2. Find cut-point with highest significance.
    # -------------------------------------------------------------
    # Set up a standard Root graphics style (see histutil.py in the
    # python directory).
    setStyle()

    # Create a 2-D histogram for ROC plot
    msize = 0.30  # marker size for points in ROC plot
    
    xbins =   50  # number of bins in x (background)
    xmin  =  0.0  # lower bound of x
    xmax  =  0.1  # upper bound of y

    ybins =   50
    ymin  =  0.0
    ymax  =  0.3

    color = kBlue+1
    hist  = mkhist2("hroc",
                    "#font[12]{#epsilon_{B}}",
                    "#font[12]{#epsilon_{S}}",
                    xbins, xmin, xmax,
                    ybins, ymin, ymax,
                    color=color)
    hist.SetMinimum(0)
    hist.SetMarkerSize(msize)


    # loop over all cut-points, compute a significance measure Z
    # for each cut-point, and find the cut-point with the highest
    # significance and the associated cuts.
    print "\tfilling ROC plot..."	
    bestZ = -1      # best Z value
    bestrow = -1    # row with best cut-point 
    bestCutsValues = -1


    totals = ntuple.totals()

    t_signal, et1 = totals[0]
    t_background, et2 = totals[1]

    for row, cuts in enumerate(ntuple):
        c_signal = cuts.countsignal
        c_background = cuts.countbackground
        
        fs = c_signal / t_signal
        fb = c_background / t_background
                
        #  Plot fs vs fb
        hist.Fill(fb, fs)
        	
        # Compute measure of significance
        #   Z  = sign(LR) * sqrt(2*|LR|)
        # where LR = log(Poisson(s+b|s+b)/Poisson(s+b|b))
        Z = signalSignificance(c_signal, c_background)
        if Z > bestZ:
            bestZ = Z
            bestrow = row
	    bestCutsValues = cuts

    # -------------------------------------------------------------            
    # Write out best cut
    # -------------------------------------------------------------
    #bestcuts = writeHZZResults('r_%s.txt' % NAME,
    #                           '%s.cuts'  % NAME,
    #                           ntuple, variables,
    #                           bestrow, bestZ,
    #                           totals)
    
    #print('Result: best ntuple row:')
    #print(bestrow)
    #ntuple.read(bestrow)
    #print('fJetPT %f fJetD0max %f fptTop %f ptOfe %f ' % (ntuple('fJetPT'), ntuple('fJetD0max'), ntuple('fptTop'), ntuple('ptOfe')))
    #print('with "Z" of %d' % bestZ)

    bestcuts = writeResults('results_%s.txt' % NAME,
                                '%s.cuts' % NAME,
                                ntuple, variables,
                                bestrow, bestZ, bestCutsValues#, outerhull)
				)

    
# ---------------------------------------------------------------------
def writeResults(filename, varfilename, ntuple, variables,
                     bestrow, bestZ, bestCutsValues#, outerhull):
		     ):
    
    cutdir  = {}
    cutdirs = []
    for t in getCutDirections(varfilename):
        token = t[0]
        if token[0] == '\\':
            continue
        else:
            cutdirs.append(t)
            cutdir[token] = t[1]

    totals = ntuple.totals()
    ntuple.read(bestrow)
    
    out = open(filename, 'w')

    #Do yields
    print 
    record = "Yields before optimization"
    out.write('%s\n' % record); print record
    
    record = "\tbackground:   %12.1f +/- %-10.1f" % (totals[0][0],
                                                   totals[0][1])
    out.write('%s\n' % record); print record

    record = "\tsignal:    %12.1f +/- %-10.1f" % (totals[1][0],
                                                   totals[1][1])
    out.write('%s\n' % record); print record    

    record = "Yields after optimization (and relative efficiencies)"
    out.write('%s\n' % record); print record    

    for name, count in variables:        
        if not (name[0:5] in ['count', 'fract']): continue
        var = ntuple(name)
        record = "\t%-15s %10.3f" % (name, var)
        out.write('%s\n' % record); print record                    
        if name[0:5] == "fract":
            print
            out.write('\n')
    
    #Do significance
    b = totals[0][0]
    s = totals[1][0]
    Z = signalSignificance(s, b)

    record = "\nZ values"
    out.write('%s\n' % record); print record
    
    record = "  before optimization:  %10.3f" % Z
    out.write('%s\n' % record); print record

    record = "  after optimization:   %10.3f" % bestZ
    out.write('%s\n' % record); print record    

    record = "Best cuts"
    out.write('\n%s\n' % record); print; print record

    bestcuts = {}
    
    for name, cdir in cutdirs:    
        var = ntuple(name)
        bestcuts[name] = var
        #print name, var
        if type(var) == type(0.0):
            rec = '%3s %6.2f' % (cutdir[name], var)
            record = "\t%-10s\t%10s" % (name, rec)
            out.write('%s\n' % record); print record
        else:
            record = "\t%-10s\t%10.2f\t%10.2f" % (name,
                                                    min(var[0], var[1]),
                                                    max(var[0], var[1]))
            out.write('%s\n' % record); print record            
    print
    out.write('\n')

    out.close()
    return bestcuts

try:
    main()
except KeyboardInterrupt:
    print "bye!"
