import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random
import heapq
from collections import defaultdict
import sys


class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__(self, gb, trail, val_sh, var_sh, cc):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

        self.isFirstVariable = True

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck(self):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them

        Return: a tuple of a dictionary and a bool. The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
    """

    def forwardChecking(self):
        modified = dict()  # Key = modified variables : Value = modified domain

        ## perform initial constraint checking (no push required)
        if self.isFirstVariable:
            # iterate assigned variables
            self.isFirstVariable = False

            for v in self.network.variables:
                if v.isAssigned():
                    for n in self.network.getNeighborsOfVariable(v):

                        if n.isChangeable() and not n.isAssigned() and n.getDomain().contains(v.getAssignment()):
                            # prune value from domain
                            n.removeValueFromDomain(v.getAssignment())
                            modified[n] = n.getDomain()

                        if n.size() == 0:
                            return (modified, False)

        # constraint checking for newly assigned variables
        else:
            v = self.trail.trailStack[-1][0]

            if v.isAssigned():
                for n in self.network.getNeighborsOfVariable(v):

                    if n.isChangeable() and not n.isAssigned() and n.getDomain().contains(v.getAssignment()):
                        self.trail.push(n)
                        n.removeValueFromDomain(v.getAssignment())
                        modified[n] = n.getDomain()

                    if n.size() == 0:
                        return (modified, False)

        return (modified, True)  # Modified variable : Modified domain, IfConsistent

    # =================================================================
    # Arc Consistency (Already Implemented)
    # =================================================================
    def arcConsistency(self):
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(
                        av.getAssignment()):
                    neighbor.removeValueFromDomain(av.getAssignment())
                    if neighbor.domain.size() == 1:
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)

    """
        Part 3: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation 
        and check the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them

        Return: a pair of a dictionary and a bool. 

        The dictionary contains all variables that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.

        The bool is true if assignment is consistent, false otherwise.
    """

    def norvigCheck(self):

        assigned = dict()
        modified, consistent = self.forwardChecking()

        if not consistent:
            return (assigned, False)

        for c in self.network.constraints:

            Counter = defaultdict(list)

            for var in c.vars:
                for val in var.getValues():  # the value in the domain
                    Counter[val].append(var)

            if len(Counter.keys()) < self.gameboard.N:
                return (assigned, False)

            for val in Counter.keys():

                if len(Counter[val]) == 1:

                    var = Counter[val][0]

                    if var.isChangeable() and not var.isAssigned() and var.getDomain().contains(val):
                        self.trail.push(var)

                        var.assignValue(val)
                        assigned[var] = val

                        for n in self.network.getNeighborsOfVariable(var):

                            if n.isChangeable() and not n.isAssigned() and n.getDomain().contains(val):
                                self.trail.push(n)
                                n.removeValueFromDomain(var.getAssignment())

                            if n.size() == 0:
                                return (assigned, False)

        return (assigned, True)

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """

    def getTournCC(self):
        return self.norvigCheck()[1]

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable(self):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 2: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """

    def getMRV(self):
        """
        Return unassigned nodes with the fewest legal values (aka. smallest domain)
        """
        min_remaining_value = int(sys.maxsize)  # current smallest domain
        min_var = None  # variable with the smallest domain

        # iterate all unassigned variables
        for v in self.network.variables:

            # if the domain size of a variable is less than the current minimum, assign it as the variable with the smallest domain
            if not v.isAssigned() and v.size() < min_remaining_value:
                min_remaining_value = v.size()
                min_var = v

        return min_var

    """
        Part 3: Implement the Minimum Remaining Value Heuristic with Degree Heuristic as a Tie Breaker

        Degree Heuristic = "most-constraining-variable heuristic"

        If there’s a tie between two unassigned variables, we can simply pick the unassigned variable that’s involved in the most constraints. 

        Return: The unassigned variable with the smallest domain and affecting the *most unassigned neighbors*.

        If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the *list of Variables*.
        If there is only one variable, return the list of size 1 containing that variable.
    """

    def MRVwithTieBreaker(self):

        min_vars = [self.getfirstUnassignedVariable()]

        for v in self.network.variables:

            if not v.isAssigned():

                if v.size() < min_vars[0].size():

                    min_vars = [v]

                elif v.size() == min_vars[0].size():

                    v_degree = len([a for a in self.network.getNeighborsOfVariable(v) if not a.isAssigned()])

                    min_var_degree = len(
                        [b for b in self.network.getNeighborsOfVariable(min_vars[0]) if not b.isAssigned()])

                    if v_degree == min_var_degree:
                        min_vars.append(v)

                    elif v_degree > min_var_degree:
                        min_vars = [v]

        return min_vars

    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """

    def getTournVar(self):
        return self.MRVwithTieBreaker()[0]

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder(self, v):
        values = v.domain.values
        return sorted(values)  # domain values sorted in ascending order

    """
        Part 2: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The Least Constraining Value is first and the Most Constraining Value is last
    """

    def getValuesLCVOrder(self, v):

        freq = dict()  # key = value in v's domain, value = frequency that this value appears in v's neighbor's domain

        neighbors = self.network.getNeighborsOfVariable(v)  # get all neighbors of v

        for val in v.getValues():

            freq[val] = 0  # for all values in v's domain, set freq to 0 as default

            for n in neighbors:

                # loop through n's neighbors
                # if n is not assigned, n is changeable, and n's domain contains value
                # increase the val frequency

                if n.isChangeable() and not n.isAssigned() and n.getDomain().contains(val):
                    freq[val] += 1

        return sorted(freq.keys(),
                      key=lambda x: freq[x])  # rank v's domain values based on frequency in ascending order

    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """

    def getTournVal(self, v):
        return self.getValuesLCVOrder(v)

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve(self, time_left=600):
        if time_left <= 60:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if (v == None):
            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues(v):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push(v)

            # Assign the value
            v.assignValue(i)

            # Propagate constraints, check consistency, recur
            if self.checkConsistency():
                elapsed_time = time.time() - start_time
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1

            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()

        return 0

    def checkConsistency(self):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()[1]

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable(self):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()[0]

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues(self, v):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder(v)

        if self.valHeuristics == "tournVal":
            return self.getTournVal(v)

        else:
            return self.getValuesInOrder(v)

    def getSolution(self):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)
