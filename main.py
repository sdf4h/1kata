from itertools import combinations


def solve_mine(mapStr, n):   return MineSweeper(mapStr, n).solve()

class MineSweeper(object):

    IS_DEBUG = False
    around   = [ (dx,dy) for dx in range(-1,2) for dy in range(-1,2) if (dx,dy) != (0,0) ]
    
    def __init__(self, mapStr, nMines):
        lines = mapStr.split('\n')
        mapDct, unknowns, posToWorkOn = {}, set(), set()
        for x,line in enumerate(lines):
            for y,c in enumerate(line.split(' ')):
                mapDct[(x,y)] = c
                if c == '?': unknowns.add((x,y))
                else:        posToWorkOn.add((x,y))
    
        self.map         = mapDct
        self.unknowns    = unknowns
        self.posToWorkOn = posToWorkOn
        self.flagged     = set()
        self.nMines      = nMines
        self.lX          = len(lines)
        self.lY          = len(lines[0].split(' '))
        
    
    
    def __str__(self):                return '\n'.join(' '.join( self.map[(x,y)] for y in range(self.lY)) for x in range(self.lX) )
    
    def getValAt(self,pos):           return int(self.map[pos])
    
    def getneighbors(self, pos):      return { (pos[0]+dx,pos[1]+dy) for dx,dy in self.around }
    
    def printDebug(self):             print(" \n------------\n{}\nRemaining mines: {}".format(self, self.nMines-len(self.flagged))) if self.IS_DEBUG else None
    
    def lookaroundThisPos(self, pos):
        neighbors = self.getneighbors(pos)
        return {'?': neighbors & self.unknowns,
                'x': neighbors & self.flagged}
        
    
    """ MAIN FUNCTION """
    def solve(self):
        
        self.printDebug()
        while True:
            while True:
                archivePosToWorkOn = self.posToWorkOn.copy()            # Archive to check against modifications
                
                self.openAndFlag_OnTheFly();       self.printDebug()    # Open and flag in the map while simple matches can be found
                self.complexSearch_OpenAndFlag();  self.printDebug()    # Use more complex algorithm to find mines or unknown positions that are surely openable
                
                if archivePosToWorkOn == self.posToWorkOn: break        # Repeat these two "simple" steps until its not possible to go further in the resolution
            
            self.complexSearch_CombineApproach()                        # Use witted combinatory approach to go further (if possible)
            
            if archivePosToWorkOn == self.posToWorkOn:
                break; self.printDebug()                                # Repeat these to "simple" steps until its not possible to go further in the resolution
        
        
        if len(self.flagged) == self.nMines:                            # If no more mines remaining but some unknown cases still there
            self.openThosePos(self.unknowns.copy())
            
        elif len(self.flagged) + len(self.unknowns) == self.nMines:     # If all the remaining "?" are mines, flag them
            self.flagThosePos(self.unknowns.copy())
        
        self.printDebug()
        
        return '?' if self.unknowns else str(self)
        
    
    def openAndFlag_OnTheFly(self):
        while True:
            openables, workDonePos = set(), set()
            for pos in self.posToWorkOn:                                    # Run through all the positions that might neighbors to open
                openables, workDonePos = [ baseSet|newPart for baseSet,newPart in zip((openables, workDonePos), self.openablePosaround_FlagOnTheFly(pos)) ]
            
            self.openThosePos(openables)                                    # After the exit of the loop, modification of self.posToWorkOn is possible, so:
            self.posToWorkOn -= workDonePos                                 # remove the pos with full number of mines from the working set (to fasten the executions)
            if not openables and not workDonePos: break     
    
    
    def openablePosaround_FlagOnTheFly(self, pos):
        around = self.lookaroundThisPos(pos)
        
        if self.getValAt(pos) == len(around['?']) + len(around['x']):       # If all the unknomn cases can be flagged (or if they are already!)...
            self.flagThosePos(around['?'])                                  # flag them (if not already done)
            return (set(), {pos})                                           # return the current position to remove it from self.posToWorkOn ("We're done with you..." / This behaviour will identify the "done" positions generated by the "witted approach")
            
        return (around['?'], {pos}) if self.getValAt(pos) == len(around['x']) else (set(), set())  
        
        
    def openThosePos(self, posToOpen):
        for pos in posToOpen:
            self.map[pos] = str(open(*pos))                                 # Open squares and update the map
            if self.map[pos] != '0': self.posToWorkOn.add(pos)              # Update slef.posToWorkOn if needed
        self.unknowns -= posToOpen                                          # Remove opened squares from the unknown positions
    
    
    def flagThosePos(self, posToFlag):
        for pos in posToFlag: self.map[pos] = 'x'                           # Flag mines
        self.unknowns -= posToFlag                                          # Remove flagged squares from the unknown positions
        self.flagged  |= posToFlag                                          # update the set of flagged positions
    
    
    def complexSearch_OpenAndFlag(self):
        markables, openables = set(), set()
        for pos in self.posToWorkOn:
            newMark, newOpen = self.intelligencia_OpenAndFlag(pos)
            markables |= newMark
            openables |= newOpen
            
        self.flagThosePos(markables)
        self.openThosePos(openables)
        
                
    def intelligencia_OpenAndFlag(self, pos):
        around       = self.lookaroundThisPos(pos)                          # Cases around the current position
        rMines        = [self.getValAt(pos)-len(around['x']), 0]            # Prepare an array with the number of remaining mines to find for the current position and the neighbor that will be worked on later
        neighToWorkOn = self.getneighbors(pos) & self.posToWorkOn           # Search for neighbors (only usefull ones, meaning: self.getValAt(posneighbor) is a number and this neighbor still miss some mines)
            
        markables, openables = set(), set()                                 # markables: position that will be flagged / openables: positions that will be open... of course... / fullUnion: stroe all the squares
        knownParts = []                                                     # knownParts: list of the intersections of the '?' cases of all the neighbors of the current pos and the current neighbor
        
        for pos2 in neighToWorkOn:
            around2  = self.lookaroundThisPos(pos2)                                         # Cases around the neighbor that is worked on right now
            rMines[1] = self.getValAt(pos2) - len(around2['x'])                             # Update the number of mines still to find for the current neighbor
            onlys     = [ around['?'] - around2['?'], around2['?'] - around['?'] ]          # Define the '?' that are owned only by the current "pos", and only by the current neighbor ("pos2")
            mInter    = max( n-len(only) for n,only in zip(rMines, onlys) )                 # Define the minimum (yes "minimum", even if "max" is used!) number of mines that have to be in the '?' that are commun to "pos" and it's current neighbor pos2"
            
            if mInter <= 0 or 1 not in rMines: continue                                     # If these conditions are met, there is nothing "extrapolable" at the current position, so continue the iteration
            
            currentIntersect = around['?'] & around2['?']
            if currentIntersect: knownParts.append(currentIntersect)                        # Store (if it exists) the current intersection of '?' cases for further checks

            for i in range(2):                                                              # Work on the two current LOCATIONS (pos, pos2)
                if len(onlys[i]) == rMines[i]-mInter:  markables |= onlys[i]                # The number of '?' cases that are only around the treated LOCATION matches the number mines of this LOCATION that are out of the interesction "pos & pos2". So, those cases will be flagged
                elif mInter == rMines[i]:              openables |= onlys[i]                # If the number of mines surely present in the intersection "pos & pos2" matches the number of mines still to found arorund the treated LOCATION, all the cases out of the intersection for the current LOCATION can be opened
            
        # Final check on the different intersections parts:
        fullIntersection = {posInter for posSet in knownParts for posInter in posSet}       # Union of all the intersections for the current position and its differente neighbors
        if len(knownParts) == rMines[0] and sum( len(s) for s in knownParts) == len(fullIntersection): 
            openables |= around['?'] - fullIntersection                                     # If some '?' cases are still unchecked while we can be sure that all the remaining mines are elsewhere (even without knowing their exact location), the leftovers can be opened
        
        return markables, openables
        
        
        
    def complexSearch_CombineApproach(self):
        rMines = self.nMines - len(self.flagged)                                            # number of remaining mines to find
        matchPos = []
        
        if rMines != 0:
            
            borderUnknowns = { pos2 for pos in self.posToWorkOn for pos2 in self.lookaroundThisPos(pos)['?'] }      # '?' that are joined to the current posToWorkOn...
            borderUnknowns |= { pos2 for pos in borderUnknowns for pos2 in self.lookaroundThisPos(pos)['?'] }       # ...then add the "next layer" of "?", ot be able to make more guesses on the remaining farther squares
            
            for n in range(rMines if not (self.unknowns-borderUnknowns) else 1, min(rMines, len(borderUnknowns)-1)+1):
                for posMines in combinations(borderUnknowns, n):
                    setPosMines = set(posMines)
                    for pos in self.posToWorkOn:
                        around = self.lookaroundThisPos(pos)
                        if self.getValAt(pos) != len(around['x']) + len(around ['?'] & setPosMines): break
                    else:
                        matchPos.append(setPosMines)                                                                # if the for loop execute until its end, the current position is valid. Archive it.
            
            untouched = borderUnknowns - {flagPos for s in matchPos for flagPos in s}                               # search for '?' that are never marked in any of the valid combinations
        
            if len(matchPos) == 1:  self.flagThosePos(matchPos[0])                                                  # Flag the found mines if only 1 match
            self.openThosePos(untouched)                                       
