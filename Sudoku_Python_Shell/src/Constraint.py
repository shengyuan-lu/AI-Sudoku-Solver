import Variable

"""
    Constraint represents a NotEquals constraint on a set of variables.
    Used to ensure none of the variables contained in the constraint have the same assignment.
"""

class Constraint:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self ):
        self.vars = [] # list of Variable objects. None of these variables can have the same assignment

    # ==================================================================
    # Modifiers
    # ==================================================================

    def addVariable ( self, v ):
        self.vars.append( v )

    # ==================================================================
    # Accessors
    # ==================================================================

    # Amount of variables in this constraint
    def size ( self ):
        return len(self.vars)

    # Returns true if v is in the constraint, false otherwise
    def contains ( self, v ):
        return v in self.vars

    # Returns whether or not the a variable in the constraint has been modified
    def isModified ( self ):
        for var in self.vars:
            if var.isModified():
                return True

        return False

    # Returns true if constraint is consistent, false otherwise
    def isConsistent ( self ):
        for var in self.vars:

            # skip unassigned variables
            if not var.isAssigned():
                continue

            for otherVar in self.vars:

                # skip same variable, because they always equal
                if var == otherVar:
                    continue

                # if found two variables with the same assignment, return False
                if otherVar.isAssigned() and otherVar.getAssignment() == var.getAssignment():
                    return False

        return True

    # ==================================================================
    # String representation
    # ==================================================================

    def __str__ ( self ):
        output = "{"
        delim = ""

        for v in self.vars:
            output += delim + v.name
            delim = ","

        output += "}"
        return output
