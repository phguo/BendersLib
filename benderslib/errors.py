# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from . import __url__


class BendersError(Exception):
    """Base class for exceptions in benderslib."""

    code = None
    description = "A generic error in the BendersLib library."

    def __init__(self, message=None, **kwargs):
        if message is None:
            message = self.description

        self.message = message
        self.context = kwargs
        super().__init__(self.message)

    def __str__(self):
        code_str = f"[{self.code}] " if self.code else ""
        context_str = ""
        if self.context:
            context_str = " Context: " + ", ".join(f"{k}={v}" for k, v in self.context.items())

        return f"{code_str}{self.message}{context_str}\nSee {self._help_url}"

    @property
    def _help_url(self):
        """URL to the documentation for this error type.

        For example:
        https://benders.dev/api/errors.html#benderslib.errors.BendersError
        """
        return __url__ + "/api/errors.html#benderslib.errors." + self.__class__.__name__


# Benders Solver Errors

class BendersSolverError(BendersError):
    """Exception raised for errors in the solver."""
    code = 1000
    description = "An error occurred during the Benders decomposition algorithm."


# Solver Backends Errors

class BendersBackendError(BendersError):
    """Exception raised for errors in the backend solver."""
    code = 2000
    description = "An error occurred in the backend solver."


class BendersNotImplementedError(BendersBackendError, NotImplementedError):
    """Exception raised for unimplemented features or when the underlying solver does not support the functionality.

    This can be caused by:

    - Using a Constraint Programming (CP) solver for master problems.
    - Using CP solver for subproblems in dual-based Benders methods.
    - The underlying solvers lacking certain features required by BendersLib.
    """
    code = 2001
    description = "This is not yet implemented in BendersLib."


# Master Problem Errors


class BendersMasterError(BendersError):
    """Exception raised for errors in the master problem."""
    code = 3000
    description = "An error occurred in the master problem."


class UnexpectedMasterStatusError(BendersMasterError):
    """Exception raised when the master problem solver returns an unexpected status."""
    code = 3001
    description = "The master problem solver returned an unexpected status."


class MismatchedProbabilityError(BendersMasterError):
    """Exception raised when the number of probabilities (weights) does not match the number of scenarios."""
    code = 3002
    description = "The the number of probabilities (weights) does not match the number of scenarios."


class UnboundedMasterError(BendersMasterError):
    """Raised when the master relaxation is unbounded without proving the original problem unbounded."""
    code = 3003
    description = "The master problem is unbounded: add valid constraints or bounds."


# Subproblem Errors


class BendersSubError(BendersError):
    """Exception raised for errors in the subproblem."""
    code = 4000
    description = "An error occurred in the subproblem."


class UnexpectedSubStatusError(BendersSubError):
    """Exception raised when the subproblem solver returns an unexpected status."""
    code = 4001
    description = "The subproblem solver returned an unexpected status."


# Benders Cut Errors

class BendersCutError(BendersError):
    """Exception raised for errors in the cut generation."""
    code = 5000
    description = "An error occurred during cut generation."


class UnsupportedCutError(BendersCutError):
    """Exception raised when an unsupported cut type is used."""
    code = 5001
    description = "The specified cut type is not supported."


# Callback Errors

class BendersCallbackError(BendersError):
    """Exception raised for errors in the callback functions."""
    code = 6000
    description = "An error occurred in a callback function."
