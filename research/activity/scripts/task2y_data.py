"""Hand-transcribed inputs for the Sellafield B205 (Magnox reprocessing plant) civil throughput added to build_nuc2.py (task 2.y, D64, NUCLEAR_SPEC 12 item A2).
Financial year (FY) label = year ending 31 March (FY2001 = April 2000 - March 2001), the same convention as THORP in task2x_data.py. Values in tHM (tU).
Chart readings were taken from the rendered PDF pages by pixel measurement of the bar tops (axis calibrated on the printed 0 and 1200 labels / on the two printed
values 607 and 233 in the NDA figure); reading error is about +-10 t.
"""
# IPFM RR5 'The Legacy of Reprocessing in the United Kingdom' (2005), Figure 4 'Magnox Reprocessing Throughput (tons per year)', source BNFL Sellafield Ltd and NDA.
# Bars are labelled 1997...2008 (actual) and 2009-2016 (projected 600). The bars labelled 2001-2007 match the NDA MOP 9 financial years 2000/01-2006/07
# (366, 790, 770, 1,045, 1,015, 255, 595), so a label is the FY ending year. Used for FY1997-FY2000 only.
IPFM_FY={1997:604.0,1998:523.0,1999:467.0,2000:503.0}
# NDA, The Magnox Operating Programme (MOP 9), 2012, Figure 4.1 'Annual Reprocessing Performance since 2000' (financial years 2000/01 - 2011/12).
# FY2011 (233) and FY2012 (607) are printed in the text (section 8, 'limited to 233 tU', 'reached 607 tU'); the other bars are chart readings.
MOP9_FY={2001:364.0,2002:787.0,2003:765.0,2004:1040.0,2005:1013.0,2006:256.0,2007:593.0,2008:458.0,2009:512.0,2010:449.0,2011:233.0,2012:607.0}
MOP9_PRINTED={2011,2012}
REMAINING_APR2012=3800.0     # tU of Magnox fuel still to reprocess in April 2012 (MOP 9 section 4.1)
# CORE briefing 04/14: 2011/12-2013/14 three-year total completed 1,338 t (target 2,159 t); Roche (2015): FY2013/14 470 t (target 664 t).
THREE_YEAR_2012_14=1338.0
FY2014=470.0
FY2013=THREE_YEAR_2012_14-MOP9_FY[2012]-FY2014     # derived by difference: 261 t
# Sellafield Ltd annual reviews: 2016/17 466 t (target 457); 2018/19 341.5 t (target 450).
FY2017=466.0
FY2019=341.5
# Last feed 17 July 2022 (IPFM blog 2022, S1609): April-17 July 2022 is 3.5 of 12 months of a financial year.
STUB_2022_FRAC=3.5/12
ETA_MAGNOX=0.27          # thermal efficiency, as build_nuc.py (ETA['magnox'])
BURNUP_MAGNOX=5.0        # GWd/tHM, task instruction (build_nuc.py uses 5.5-6 for its own discharge model)
