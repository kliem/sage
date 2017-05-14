r"""
CryptoMiniSat Solver.

This solver relies on Python bindings provided by upstream cryptominisat, and
replaces the cython interface (written by Martin Albrecht in 2012) that does not
work with recent versions of cryptominisat anymore.

The ``cryptominisat`` package should be installed on your Sage installation.

AUTHORS:

- Thierry Monteil (2017): first version
"""

#*****************************************************************************
#       Copyright (C) 2017 Thierry Monteil <sage!lma.metelu.net>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#  as published by the Free Software Foundation; either version 2 of
#  the License, or (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************


from .satsolver import SatSolver

class CryptoMiniSat(SatSolver):
    def __init__(self, verbosity=0, confl_limit=None, threads=None):
        """
        Constuct a new CryptoMiniSat Solver.

        INPUT:

        - ``verbosity`` -- an integer between 0 and 15 (default: 0). Verbosity.

        - 'confl_limit' -- an integer (default: ``None``). Abort after this many
          conflicts. If set to ``None``, never aborts.

        - ``threads`` -- an integer (default: None). The number of thread to
          use. If set to ``None``, the number of threads used corresponds to the
          number of cpus.

        EXAMPLES::

            sage: from sage.sat.solvers.cryptominisat import CryptoMiniSat
            sage: solver = CryptoMiniSat()                                  # optional - cryptominisat
        """
        if threads is None:
            from sage.parallel.ncpus import ncpus
            threads = ncpus()
        if confl_limit is None:
            from sys import maxint
            confl_limit = maxint
        from sage.misc.package import PackageNotFoundError
        try:
            from pycryptosat import Solver
        except ImportError:
            raise PackageNotFoundError("cryptominisat")
        self._solver = Solver(verbose=int(verbosity), confl_limit=int(confl_limit), threads=int(threads))
        self._vars = set()
        self._clauses = []

    def var(self, decision=None):
        """
        Return a *new* variable.

        INPUT:

        - ``decision`` - accepted for compatibility with other solvers, ignored.

        EXAMPLES::

            sage: from sage.sat.solvers.cryptominisat import CryptoMiniSat
            sage: solver = CryptoMiniSat()                                  # optional - cryptominisat
            sage: solver.var()                                              # optional - cryptominisat
            1

            sage: solver.add_clause((-1,2,-4))                              # optional - cryptominisat
            sage: solver.var()                                              # optional - cryptominisat
            5
        """
        if len(self._vars) == 0:
            return 1
        else:
            return max(self._vars) + 1

    def nvars(self):
        """
        Return the number of variables.

        EXAMPLES::

            sage: from sage.sat.solvers.cryptominisat import CryptoMiniSat
            sage: solver = CryptoMiniSat()                                  # optional - cryptominisat

            sage: solver.nvars()                                            # optional - cryptominisat
            0

            sage: solver.add_clause((1,-2,4))                               # optional - cryptominisat
            sage: solver.nvars()                                            # optional - cryptominisat
            3
        """
        return len(self._vars)

    def add_clause(self, lits):
        """
        Add a new clause to set of clauses.

        INPUT:

        - ``lits`` - a tuple of nonzero integers.

        .. note::

            If any element ``e`` in ``lits`` has ``abs(e)`` greater
            than the number of variables generated so far, then new
            variables are created automatically.

        EXAMPLES::

            sage: from sage.sat.solvers.cryptominisat import CryptoMiniSat
            sage: solver = CryptoMiniSat()                                  # optional - cryptominisat
            sage: solver.add_clause((1, -2 , 3))                            # optional - cryptominisat
        """
        if 0 in lits:
            raise ValueError("0 should not appear in the clause: {}".format(lits))
        # cryptominisat does not handle Sage integers
        lits = tuple(int(i) for i in lits)
        self._vars.update(abs(i) for i in lits)
        self._solver.add_clause(lits)
        self._clauses.append((lits, False, None))

    def add_xor_clause(self, lits, rhs=True):
        r"""
        Add a new XOR clause to set of clauses.

        INPUT:

        - ``lits`` -- a tuple of positive integers.

        - ``rhs`` -- boolean (default: ``True``). Whether this XOR clause should
          be evaluated to ``True`` or ``False``.

        EXAMPLES::

            sage: from sage.sat.solvers.cryptominisat import CryptoMiniSat
            sage: solver = CryptoMiniSat()                                  # optional - cryptominisat
            sage: solver.add_xor_clause((1, 2 , 3), False)                  # optional - cryptominisat
        """
        if 0 in lits:
            raise ValueError("0 should not appear in the clause: {}".format(lits))
        # cryptominisat does not handle Sage integers
        lits = tuple(int(i) for i in lits)
        self._vars.update(abs(i) for i in lits)
        self._solver.add_xor_clause(lits, rhs)
        self._clauses.append((lits, True, rhs))

    def __call__(self, assumptions=None):
        """
        Solve this instance.

        OUTPUT:

        - If this instance is SAT: A tuple of length ``nvars()+1``
          where the ``i``-th entry holds an assignment for the
          ``i``-th variables (the ``0``-th entry is always ``None``).

        - If this instance is UNSAT: ``False``.

        EXAMPLES::

            sage: from sage.sat.solvers.cryptominisat import CryptoMiniSat
            sage: solver = CryptoMiniSat()                                  # optional - cryptominisat
            sage: solver.add_clause((1,2))                                  # optional - cryptominisat
            sage: solver.add_clause((-1,2))                                 # optional - cryptominisat
            sage: solver.add_clause((-1,-2))                                # optional - cryptominisat
            sage: solver()                                                  # optional - cryptominisat
            (None, False, True)

            sage: solver.add_clause((1,-2))                                 # optional - cryptominisat
            sage: solver()                                                  # optional - cryptominisat
            False
        """
        satisfiable,assignments = self._solver.solve()
        if satisfiable:
            return assignments
        else:
            return False

    def __repr__(self):
        """
        TESTS::

            sage: from sage.sat.solvers.cryptominisat import CryptoMiniSat
            sage: solver = CryptoMiniSat()                                  # optional - cryptominisat
            sage: solver                                                    # optional - cryptominisat
            CryptoMiniSat solver: 0 variables, 0 clauses.
        """
        return "CryptoMiniSat solver: {} variables, {} clauses.".format(self.nvars(), len(self.clauses()))

    def clauses(self, filename=None):
        """
        Return original clauses.

        INPUT:

        - ``filename'' - if not ``None`` clauses are written to ``filename`` in
          DIMACS format (default: ``None``)

        OUTPUT:

            If ``filename`` is ``None`` then a list of ``lits, is_xor, rhs``
            tuples is returned, where ``lits`` is a tuple of literals,
            ``is_xor`` is always ``False`` and ``rhs`` is always ``None``.

            If ``filename`` points to a writable file, then the list of original
            clauses is written to that file in DIMACS format.

        EXAMPLES::

            sage: from sage.sat.solvers import CryptoMiniSat
            sage: solver = CryptoMiniSat()                              # optional - cryptominisat
            sage: solver.add_clause((1,2,3,4,5,6,7,8,-9))               # optional - cryptominisat
            sage: solver.add_xor_clause((1,2,3,4,5,6,7,8,9), rhs=True)  # optional - cryptominisat
            sage: solver.clauses()                                      # optional - cryptominisat
            [((1, 2, 3, 4, 5, 6, 7, 8, -9), False, None),
            ((1, 2, 3, 4, 5, 6, 7, 8, 9), True, True)]

        DIMACS format output::

            sage: from sage.sat.solvers import CryptoMiniSat
            sage: solver = CryptoMiniSat()                      # optional - cryptominisat
            sage: solver.add_clause((1, 2, 3))                  # optional - cryptominisat
            sage: solver.add_clause((1, 2, -3))                 # optional - cryptominisat
            sage: fn = tmp_filename()                           # optional - cryptominisat
            sage: solver.clauses(fn)                            # optional - cryptominisat
            sage: print(open(fn).read())                        # optional - cryptominisat
            p cnf 3 2
            1 2 3 0
            1 2 -3 0
            <BLANKLINE>

        Note that in cryptominisat, the DIMACS standard format is augmented with
        the following extension: having an ``x`` in front of a line makes that
        line an XOR clause i Note that cryptominisat has its own 

            sage: solver.add_xor_clause((1,2,4), rhs=True)      # optional - cryptominisat
            sage: solver.clauses(fn)                            # optional - cryptominisat
            sage: print(open(fn).read())                        # optional - cryptominisat
            p cnf 4 3
            1 2 3 0
            1 2 -3 0
            x1 2 4 0
            <BLANKLINE>

        Note that inverting an xor-clause is equivalent to inverting one of the
        variables::

            sage: solver.add_xor_clause((1,2,5),rhs=False)      # optional - cryptominisat
            sage: solver.clauses(fn)                            # optional - cryptominisat
            sage: print(open(fn).read())                        # optional - cryptominisat
            p cnf 5 4
            1 2 3 0
            1 2 -3 0
            x1 2 4 0
            x1 2 -5 0
            <BLANKLINE> 
        """
        if filename is None:
            return self._clauses
        else:
            from sage.sat.solvers.dimacs import DIMACS
            DIMACS.render_dimacs(self._clauses, filename, self.nvars())

