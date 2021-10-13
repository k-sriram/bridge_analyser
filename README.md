# bridge_analyser
Analyses which point ranges score how much tricks with a double dummy solver.

Requires python package ddstable.
```
python -m pip install ddstable
```

Running the dds-analysis.py creates a results.json and games.pbn file.
The results.json file is a dict. If dumped into the variable 'data', then
```
data[trump][points][fitsize][smallersize][tricks]
```
represents number games where, the team had 'points' in HCP, 'fitsize' number of cards in 'trump',
'smallersize' number of trumps in the shorter hand, and double dummy solver reported 'tricks' number of tricks taken.
For No trumps,
```
data['NT'][points][blocker][tricks]
```
'bloker' is 0 or 1 depending on all 4 four suits are blocked or not.
