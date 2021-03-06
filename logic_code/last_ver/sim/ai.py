from map_st import *
import kernel
import time

class AI:
    def __init__(self, must_print = True, ramp = True):
        self.memory = Map(10, 10)
        self.pos = [0, 0]
        self.d = 0
        self.queued = []
        self.checkramp = ramp
        self.mprint = must_print
        self.memory.setPrint(must_print)

    def to_the(self, side):
        gdir = self.conv_tog(side)
        return self.s_to_coords(gdir)

    def s_to_coords(self, gdir):
        if gdir == 0:
            return [self.pos[0], self.pos[1] - 1]
        if gdir == 1:
            return [self.pos[0] + 1, self.pos[1]]
        if gdir == 2:
            return [self.pos[0], self.pos[1] + 1]
        if gdir == 3:
            return [self.pos[0] - 1, self.pos[1]]

    def conv_tog(self, side):
        return (side + self.d)%4

    def immediate(self):
        if self.memory.isblack(self.pos):
            return (2, 1)
        if not self.memory.wallto(self.pos,
                self.conv_tog(0)) and not self.memory.visited(
                        self.s_to_coords(self.conv_tog(0))):
            return (0, 1)
        if not self.memory.wallto(self.pos, 
                self.conv_tog(1)) and not self.memory.visited(
                        self.s_to_coords(self.conv_tog(1))):
            return (1, 1)
        if not self.memory.wallto(self.pos, 
                self.conv_tog(3)) and not self.memory.visited(
                        self.s_to_coords(self.conv_tog(3))):
            return (3, 1)
        return (1, 2)

    def method(self):
        if self.memory.isblack(self.pos):
            return 0
        for i in range(4):
            if not self.memory.wallto(self.pos,
                    self.conv_tog(i)) and not self.memory.visited(
                    self.s_to_coords(self.conv_tog(i))):
                return 0
        return 1

    def turnMove(self, d0, d1):
        if self.mprint:
            print "Has to turn from",d0,"to",d1
        rcnt = (d1 - d0 + 4)%4
        if rcnt == 3:
            return (3, 1)
        else:
            return (1, rcnt)

    def apply(self, action):
        if action[0] is list or action[0] is tuple:
            for act in action:
                self.apply(act)
            return
        if self.mprint:
            print "Applying:",action
        if action[0] == 0 or action[0] == 2:
            for i in range(action[1]):
                self.pos = self.to_the(action[0])
        if action[0] == 1:
            self.d += action[1]
            self.d %= 4
        if action[0] == 3:
            self.d += action[1]*4
            self.d -= action[1]
            self.d %= 4

    def PF(self, targ = -1):
        aclst = []
        path = self.memory.PF(self.pos, targ)
        if self.mprint:
            print "Map found path:", path
        if len(path) == 0:
            return False
        td = self.d
        for i in range(0, len(path) - 1):
            diff = (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
            nd = 0
            if self.mprint:
                print "Diff:",diff
            if diff == (0, -1): 
                nd = 0
            elif diff == (1, 0):
                nd = 1
            elif diff == (0, 1):
                nd = 2
            elif diff == (-1, 0):
                nd = 3
            else:
                return (-1, -1)
            if td != nd:
                aclst = [self.turnMove(td, nd)] + aclst
                td = nd
            
            aclst = [(0, 1)] + aclst

        fcnt = 0 

        if self.mprint:
            print "Brute aclist:",aclst

        finlist = []

        for i in aclst:
            if i != (0, 1) and fcnt > 0:
                finlist = [(0, fcnt)] + finlist
                finlist = [i] + finlist
                fcnt = 0
            elif i == (0, 1):
                fcnt += 1
            else:
                finlist = [i] + finlist
        if fcnt > 0:
            finlist = [(0, fcnt)] + finlist

        if self.mprint:
            print "Generated action list:",finlist
        return finlist

    def scan_tile(self):
        walls = []
        walls += [kernel.wallf()]
        walls += [kernel.wallr()]
        walls += [kernel.wallb()]
        walls += [kernel.walll()]

        if self.mprint:
            for i in range(4):
                print "Wall to",i,":",walls[i]

        for i in range(4):
            if i != 2:
                self.memory.setWallTo(self.pos, self.conv_tog(i), walls[i])
        self.memory.setBlack(self.pos, kernel.isblack())
        self.memory.setVisited(self.pos)
        if self.mprint:
            self.memory.printMap()
        
        if kernel.isramp() and self.checkramp:
            self.memory.setBlack(self.pos)
            self.apply((1, 2))
            self.apply((0, 1))

            secfloor = AI(False, self.mprint)
            secfloor.memory.setVisited((0, 1))
            secfloor.memory.setBlack((0, 1))
            secfloor.memory.setVisited((0, 0))
            secfloor.memory.setWallu((0, 0), False)
            secfloor.memory.setWallr((0, 0), True)
            secfloor.memory.setWalll((0, 0), True)
            secfloor.memory.setWalld((0, 0), False)
            secfloor.apply((0, 1))

            kernel.upramp()
            secfloor.loop()
            kernel.downramp()

    def goback(self):
        if self.pos == [0, 0]:
            if self.mprint:
                print "Already here!"
            return False
        if self.mprint:
            print "Going back..."
        actions = self.PF([0, 0])
        if not actions:
            return False
        self.queued += actions
        return True

    def loop(self):
        over = False
        while not over:
            time.sleep(.2)
            #kernel.printMap()
            self.scan_tile()
            if len(self.queued) > 0:
                action = self.queued[0]
                if self.mprint:
                    print "que TODO:",action
                success = kernel.apply(action)
                self.apply(success)
                if tuple(success) == tuple(action):
                    self.queued = self.queued[1:]
                else:
                    self.queued = []
            else:
                met = self.method()
                if met == 0:
                    action = self.immediate()
                    if self.mprint:
                        print "imm TODO:",action
                    success = kernel.apply(action)
                    self.apply(success)
                elif met == 1:
                    actions = self.PF()
                    if actions == False:
                        over = not self.goback()
                    else:
                        self.queued += actions
